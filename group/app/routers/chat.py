"""
WebSocket chat endpoint for real-time group messaging.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging
import json
from datetime import datetime

from app.db import get_db, Group, GroupMember, Message
from app.models import WSMessageIn, WSMessageOut, WSError
from app.services import ChatManager, chat_manager
from app.middleware import verify_token_ws
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws/groups", tags=["websocket"])


@router.websocket("/{group_id}")
async def websocket_chat(
    websocket: WebSocket,
    group_id: UUID,
    token: str = Query(..., description="JWT token for authentication"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time group chat.
    
    Protocol:
    1. Client connects with JWT token in query param
    2. Server validates token and group membership
    3. Bidirectional JSON messages
    4. Server broadcasts to all group members
    
    Client message types:
    - "message": Send a chat message
    - "typing": Send typing indicator
    
    Server message types:
    - "message": Chat message
    - "member_joined": User joined the group
    - "member_left": User left the group
    - "typing": User typing status
    - "error": Error occurred
    """
    user_id = None
    username = None
    
    try:
        # Validate JWT token
        token_payload = await verify_token_ws(token)
        keycloak_id = token_payload["sub"]
        
        # Get user from database
        from app.db.models import User
        user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
        
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="User profile not found")
            return
        
        user_id = user.id
        
        # Build username from first_name + last_name, fallback to email
        first_name = token_payload.get("given_name", "")
        last_name = token_payload.get("family_name", "")
        if first_name and last_name:
            username = f"{first_name} {last_name}"
        elif first_name:
            username = first_name
        else:
            username = token_payload.get("email", "Unknown")
        
        # Check if group exists
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Group not found")
            return
        
        # Check if user is a member
        is_member = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id
        ).first()
        
        if not is_member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not a group member")
            return
        
        # Connect to chat
        await chat_manager.connect(group_id, websocket, user_id, username)
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                # Parse message
                message_data = json.loads(data)
                ws_message = WSMessageIn(**message_data)
                
                # Handle different message types
                if ws_message.type == "message":
                    # Check rate limit
                    if not chat_manager.check_rate_limit(user_id):
                        await chat_manager.send_error(
                            websocket,
                            code="RATE_LIMIT_EXCEEDED",
                            message=f"Maximum {config.MESSAGE_RATE_LIMIT} messages per minute"
                        )
                        continue
                    
                    # Validate message content
                    if not ws_message.content or len(ws_message.content) > config.MAX_MESSAGE_LENGTH:
                        await chat_manager.send_error(
                            websocket,
                            code="MESSAGE_TOO_LONG",
                            message=f"Message must be 1-{config.MAX_MESSAGE_LENGTH} characters"
                        )
                        continue
                    
                    # Save message to database
                    try:
                        new_message = Message(
                            group_id=group_id,
                            sender_id=user_id,
                            content=ws_message.content
                        )
                        db.add(new_message)
                        db.commit()
                        db.refresh(new_message)
                        
                        # Broadcast to all group members
                        broadcast_msg = WSMessageOut(
                            type="message",
                            id=new_message.id,
                            user_id=user_id,
                            username=username,
                            content=new_message.content,
                            timestamp=new_message.sent_at
                        )
                        
                        await chat_manager.broadcast_message(group_id, broadcast_msg)
                        
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Failed to save message: {e}")
                        await chat_manager.send_error(
                            websocket,
                            code="MESSAGE_SAVE_FAILED",
                            message="Failed to save message"
                        )
                
                elif ws_message.type == "typing":
                    # Broadcast typing indicator (ephemeral, not saved)
                    is_typing = ws_message.is_typing or False
                    await chat_manager.broadcast_typing(
                        group_id=group_id,
                        user_id=user_id,
                        username=username,
                        is_typing=is_typing,
                        exclude_websocket=websocket
                    )
                
                else:
                    await chat_manager.send_error(
                        websocket,
                        code="INVALID_MESSAGE_TYPE",
                        message=f"Unknown message type: {ws_message.type}"
                    )
            
            except json.JSONDecodeError:
                await chat_manager.send_error(
                    websocket,
                    code="PARSE_ERROR",
                    message="Invalid JSON"
                )
            except ValueError as e:
                await chat_manager.send_error(
                    websocket,
                    code="VALIDATION_ERROR",
                    message=str(e)
                )
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await chat_manager.send_error(
                    websocket,
                    code="INTERNAL_ERROR",
                    message="Failed to process message"
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={username}, group={group_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error")
        except:
            pass
    
    finally:
        # Disconnect and notify others
        if user_id and username:
            await chat_manager.disconnect(group_id, websocket, user_id, username)
