"""
WebSocket Chat Manager for real-time group chat.

Manages WebSocket connections, message broadcasting, and user presence.
"""
from fastapi import WebSocket
from typing import Dict, Set, Optional
from uuid import UUID
from datetime import datetime
import logging
import asyncio
from collections import defaultdict, deque

from app.models import WSMessageOut, WSError

logger = logging.getLogger(__name__)


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
    
    Single-pod implementation (in-memory storage).
    For multi-pod scaling, replace with Redis pub/sub.
    """
    
    def __init__(self, max_messages_per_minute: int = 60):
        """Initialize chat manager."""
        # Group -> Set of (websocket, user_id, username)
        self.connections: Dict[UUID, Set[tuple[WebSocket, UUID, str]]] = defaultdict(set)
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_messages=max_messages_per_minute)
        
        logger.info("ChatManager initialized")
    
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
        self.connections[group_id].add((websocket, user_id, username))
        
        logger.info(f"User {username} ({user_id}) connected to group {group_id}")
        
        # Broadcast join notification to other members
        await self.broadcast_system_message(
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
        # Remove from connections
        self.connections[group_id].discard((websocket, user_id, username))
        
        # Clean up empty groups
        if not self.connections[group_id]:
            del self.connections[group_id]
        
        logger.info(f"User {username} ({user_id}) disconnected from group {group_id}")
        
        # Broadcast leave notification to remaining members
        await self.broadcast_system_message(
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
        
        Args:
            group_id: Target group
            message: Message to broadcast
            exclude_websocket: Optional WebSocket to exclude (e.g., sender)
        """
        if group_id not in self.connections:
            logger.warning(f"Attempted to broadcast to non-existent group {group_id}")
            return
        
        disconnected = []
        
        for ws, user_id, username in self.connections[group_id]:
            if ws == exclude_websocket:
                continue
            
            try:
                await ws.send_json(message.model_dump(mode="json"))
            except Exception as e:
                logger.error(f"Failed to send message to {username}: {e}")
                disconnected.append((ws, user_id, username))
        
        # Clean up disconnected clients
        for ws, user_id, username in disconnected:
            await self.disconnect(group_id, ws, user_id, username)
    
    async def broadcast_system_message(
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
        return len(self.connections.get(group_id, set()))


# Global instance
chat_manager = ChatManager()
