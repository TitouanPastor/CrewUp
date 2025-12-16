"""
WebSocket Chat Manager for real-time group chat.

Manages WebSocket connections, message broadcasting, and user presence.
Supports multi-pod deployment via Redis Pub/Sub for message synchronization.
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional
from uuid import UUID
from datetime import datetime
import logging
import asyncio
import json
import os
from collections import defaultdict, deque

from app.models import WSMessageOut, WSError

logger = logging.getLogger(__name__)

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", None)
REDIS_CHANNEL_PREFIX = "chat:group:"


class RateLimiter:
    """Simple rate limiter for preventing spam."""
    
    def __init__(self, max_messages: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_messages: Maximum messages allowed in time window
            window_seconds: Time window in seconds
        """
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self.user_messages: Dict[UUID, deque] = defaultdict(lambda: deque(maxlen=max_messages))
    
    def is_allowed(self, user_id: UUID) -> bool:
        """
        Check if user is allowed to send a message.
        
        Args:
            user_id: User to check
            
        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow()
        user_queue = self.user_messages[user_id]
        
        # Remove old messages outside the window
        while user_queue and (now - user_queue[0]).total_seconds() > self.window_seconds:
            user_queue.popleft()
        
        # Check if under limit
        if len(user_queue) >= self.max_messages:
            return False
        
        # Add current message timestamp
        user_queue.append(now)
        return True


class ChatManager:
    """
    Manages WebSocket connections for group chats.
    
    Supports multi-pod deployment via Redis Pub/Sub.
    - Local connections are stored in-memory per pod
    - Messages are published to Redis and received by all pods
    - Each pod broadcasts to its local connections
    """
    
    def __init__(self, max_messages_per_minute: int = 60):
        """Initialize chat manager."""
        # Group (str) -> List of (websocket, user_id, username)
        # Using str keys and list to avoid UUID hashing issues
        self.connections: Dict[str, list[tuple[WebSocket, str, str]]] = defaultdict(list)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_messages=max_messages_per_minute)
        
        # Redis for multi-pod sync
        self.redis_client = None
        self.pubsub = None
        self._listener_task = None
        self._subscribed_groups: set[str] = set()
        
        logger.info("ChatManager initialized")
    
    async def init_redis(self):
        """Initialize Redis connection for pub/sub if configured."""
        if not REDIS_URL:
            logger.info("No REDIS_URL configured - running in single-pod mode")
            return
        
        try:
            import redis.asyncio as redis
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            logger.info(f"Connected to Redis for pub/sub: {REDIS_URL}")
        except ImportError:
            logger.warning("redis package not installed - running in single-pod mode")
            self.redis_client = None
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e} - running in single-pod mode")
            self.redis_client = None
    
    async def close_redis(self):
        """Close Redis connection."""
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
        
        if self.pubsub:
            await self.pubsub.close()
        
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def _subscribe_to_group(self, group_key: str):
        """Subscribe to Redis channel for a group."""
        if not self.pubsub or group_key in self._subscribed_groups:
            return
        
        channel = f"{REDIS_CHANNEL_PREFIX}{group_key}"
        await self.pubsub.subscribe(channel)
        self._subscribed_groups.add(group_key)
        logger.info(f"Subscribed to Redis channel: {channel}")
        
        # Start listener if not running
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._redis_listener())
    
    async def _unsubscribe_from_group(self, group_key: str):
        """Unsubscribe from Redis channel for a group."""
        if not self.pubsub or group_key not in self._subscribed_groups:
            return
        
        channel = f"{REDIS_CHANNEL_PREFIX}{group_key}"
        await self.pubsub.unsubscribe(channel)
        self._subscribed_groups.discard(group_key)
        logger.info(f"Unsubscribed from Redis channel: {channel}")
    
    async def _redis_listener(self):
        """Listen for messages from Redis pub/sub and broadcast locally."""
        logger.info("Redis listener started")
        try:
            async for message in self.pubsub.listen():
                if message["type"] != "message":
                    continue
                
                try:
                    # Parse the message
                    data = json.loads(message["data"])
                    channel = message["channel"]
                    group_key = channel.replace(REDIS_CHANNEL_PREFIX, "")
                    
                    # Don't process messages from this pod (identified by pod_id)
                    pod_id = os.getenv("HOSTNAME", "local")
                    if data.get("_pod_id") == pod_id:
                        continue
                    
                    # Remove internal fields before broadcasting
                    data.pop("_pod_id", None)
                    exclude_user_id = data.pop("_exclude_user_id", None)
                    
                    # Broadcast to local connections
                    await self._broadcast_local(group_key, data, exclude_user_id)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Redis message: {e}")
                except Exception as e:
                    logger.error(f"Error processing Redis message: {e}")
                    
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
    
    async def _broadcast_local(self, group_key: str, message_data: dict, exclude_user_id: str = None):
        """Broadcast message to local WebSocket connections only."""
        connections_list = self.connections.get(group_key, [])
        
        if not connections_list:
            return
        
        disconnected = []
        
        for ws, user_id, username in connections_list:
            # Skip excluded user
            if exclude_user_id and user_id == exclude_user_id:
                continue
            
            try:
                await ws.send_json(message_data)
            except Exception as e:
                logger.error(f"Failed to send message to {username}: {e}")
                disconnected.append((ws, user_id, username))
        
        # Clean up disconnected clients
        for ws, user_id, username in disconnected:
            self.connections[group_key] = [
                conn for conn in self.connections[group_key]
                if conn[0] is not ws
            ]
    
    async def _publish_to_redis(self, group_key: str, message_data: dict, exclude_user_id: str = None):
        """Publish message to Redis for other pods."""
        if not self.redis_client:
            return
        
        try:
            # Add metadata for filtering
            data = message_data.copy()
            data["_pod_id"] = os.getenv("HOSTNAME", "local")
            if exclude_user_id:
                data["_exclude_user_id"] = exclude_user_id
            
            channel = f"{REDIS_CHANNEL_PREFIX}{group_key}"
            await self.redis_client.publish(channel, json.dumps(data, default=str))
            logger.debug(f"Published message to Redis channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")
    
    async def connect(self, group_id: UUID, websocket: WebSocket, user_id: UUID, username: str):
        """
        Register new WebSocket connection.
        
        Args:
            group_id: Group the user is connecting to
            websocket: WebSocket connection
            user_id: User connecting
            username: Username for display
        """
        await websocket.accept()
        
        # Convert UUIDs to strings for consistent storage and lookup
        group_key = str(group_id)
        user_key = str(user_id)
        
        # Subscribe to Redis channel for this group (for multi-pod sync)
        await self._subscribe_to_group(group_key)
        
        # Add connection (avoid duplicates by checking if websocket already exists)
        existing = [conn for conn in self.connections[group_key] if conn[0] is websocket]
        if not existing:
            self.connections[group_key].append((websocket, user_key, username))
        
        logger.info(f"User {username} ({user_id}) connected to group {group_id}. Total connections in group: {len(self.connections[group_key])}")
        
        # Broadcast join notification to existing members (excluding the new member)
        await self.broadcast_member_event(
            group_id=group_id,
            message_type="member_joined",
            user_id=user_id,
            username=username,
            exclude_websocket=websocket
        )
    
    async def disconnect(self, group_id: UUID, websocket: WebSocket, user_id: UUID, username: str):
        """
        Unregister WebSocket connection.
        
        Args:
            group_id: Group the user is disconnecting from
            websocket: WebSocket connection
            user_id: User disconnecting
            username: Username for display
        """
        group_key = str(group_id)
        user_key = str(user_id)
        
        # Remove from connections by finding and removing the websocket
        self.connections[group_key] = [
            conn for conn in self.connections[group_key] 
            if conn[0] is not websocket
        ]
        
        # Clean up empty groups
        if not self.connections[group_key]:
            del self.connections[group_key]
        
        logger.info(f"User {username} ({user_id}) disconnected from group {group_id}")
        
        # Broadcast leave notification to remaining members
        await self.broadcast_member_event(
            group_id=group_id,
            message_type="member_left",
            user_id=user_id,
            username=username
        )
    
    async def send_personal_message(self, websocket: WebSocket, message: WSMessageOut):
        """
        Send message to a specific connection.
        
        Args:
            websocket: Target WebSocket
            message: Message to send
        """
        try:
            await websocket.send_json(message.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def send_error(self, websocket: WebSocket, code: str, message: str):
        """
        Send error message to a specific connection.
        
        Args:
            websocket: Target WebSocket
            code: Error code
            message: Error message
        """
        error = WSError(code=code, message=message)
        try:
            await websocket.send_json(error.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def broadcast_message(
        self,
        group_id: UUID,
        message: WSMessageOut,
        exclude_websocket: Optional[WebSocket] = None
    ):
        """
        Broadcast message to all connections in a group.
        Uses Redis pub/sub for multi-pod synchronization.
        
        Args:
            group_id: Target group
            message: Message to broadcast
            exclude_websocket: Optional WebSocket to exclude (e.g., sender)
        """
        group_key = str(group_id)
        message_data = message.model_dump(mode="json")
        
        # Find the user_id of the excluded websocket (sender)
        exclude_user_id = None
        if exclude_websocket:
            for ws, user_id, _ in self.connections.get(group_key, []):
                if ws is exclude_websocket:
                    exclude_user_id = user_id
                    break
        
        # Broadcast to local connections on this pod
        connections_list = self.connections.get(group_key, [])
        logger.info(f"Broadcasting message to group {group_id}: {len(connections_list)} local connections")
        
        disconnected = []
        
        for ws, user_id, username in connections_list:
            if ws is exclude_websocket:
                continue
            
            try:
                await ws.send_json(message_data)
                logger.debug(f"Message sent to {username}")
            except Exception as e:
                logger.error(f"Failed to send message to {username}: {e}")
                disconnected.append((ws, user_id, username))
        
        # Clean up disconnected clients
        for ws, user_id, username in disconnected:
            await self.disconnect(group_id, ws, UUID(user_id), username)
        
        # Publish to Redis for other pods (if Redis is configured)
        await self._publish_to_redis(group_key, message_data, exclude_user_id)
    
    async def broadcast_member_event(
        self,
        group_id: UUID,
        message_type: str,
        user_id: UUID,
        username: str,
        exclude_websocket: Optional[WebSocket] = None
    ):
        """
        Broadcast system notification (join/leave).
        
        Args:
            group_id: Target group
            message_type: Type of notification (member_joined, member_left)
            user_id: User ID
            username: Username
            exclude_websocket: Optional WebSocket to exclude
        """
        logger.info(f"Broadcasting {message_type} event for user {username} in group {group_id}")
        
        message = WSMessageOut(
            type=message_type,
            user_id=user_id,
            username=username,
            timestamp=datetime.utcnow()
        )
        
        await self.broadcast_message(
            group_id=group_id,
            message=message,
            exclude_websocket=exclude_websocket
        )
    
    async def broadcast_typing(
        self,
        group_id: UUID,
        user_id: UUID,
        username: str,
        is_typing: bool,
        exclude_websocket: Optional[WebSocket] = None
    ):
        """
        Broadcast typing indicator.
        
        Args:
            group_id: Target group
            user_id: User typing
            username: Username
            is_typing: Typing status
            exclude_websocket: WebSocket to exclude (sender)
        """
        message = WSMessageOut(
            type="typing",
            user_id=user_id,
            username=username,
            is_typing=is_typing,
            timestamp=datetime.utcnow()
        )
        
        await self.broadcast_message(
            group_id=group_id,
            message=message,
            exclude_websocket=exclude_websocket
        )
    
    async def broadcast_system_message(
        self,
        group_id: UUID,
        message: dict
    ) -> int:
        """
        Broadcast arbitrary system message to all group members.
        Used for inter-service communication (e.g., safety alerts).
        Uses Redis pub/sub for multi-pod synchronization.
        
        Args:
            group_id: Target group
            message: Message payload (arbitrary JSON)
            
        Returns:
            Number of members notified (on this pod only, other pods handle their own)
        """
        group_key = str(group_id)
        connections = self.connections.get(group_key, [])
        
        # Broadcast to local connections
        local_count = 0
        if connections:
            tasks = []
            for ws, _, _ in connections:
                tasks.append(ws.send_json(message))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            local_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"System message broadcast to {local_count}/{len(connections)} local members in group {group_id}")
        else:
            logger.info(f"No local connections in group {group_id} for system message")
        
        # Publish to Redis for other pods
        await self._publish_to_redis(group_key, message)
        
        return local_count
    
    def check_rate_limit(self, user_id: UUID) -> bool:
        """
        Check if user is allowed to send a message (rate limiting).
        
        Args:
            user_id: User to check
            
        Returns:
            True if allowed, False if rate limited
        """
        return self.rate_limiter.is_allowed(user_id)
    
    def get_connection_count(self, group_id: UUID) -> int:
        """
        Get number of active connections in a group.
        
        Args:
            group_id: Group to check
            
        Returns:
            Number of active connections
        """
        group_key = str(group_id)
        return len(self.connections.get(group_key, []))


# Global instance
chat_manager = ChatManager()
