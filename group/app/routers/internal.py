"""
Internal API endpoints for inter-service communication.

These endpoints are not exposed to end users and should only be
called by other microservices within the trusted network.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from uuid import UUID
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import json

from app.db import get_db, Group, Message
from app.services import chat_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/broadcast/{group_id}", status_code=status.HTTP_200_OK)
async def broadcast_to_group(
    group_id: UUID,
    message: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Broadcast a message to all members of a group via WebSocket AND save to DB.
    
    This endpoint is called by other services (e.g., safety service)
    to send system messages to group members.
    
    Args:
        group_id: Group to broadcast to
        message: Message payload to broadcast (arbitrary JSON)
                 Should contain: type, user_id, user_name, and message-specific fields
        
    Returns:
        Broadcast status and member count
    """
    try:
        # 1. Verify group exists
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found"
            )
        
        # 2. Save message to database (for chat history)
        # Use user_id from message payload as sender
        sender_id = message.get("user_id")
        if sender_id:
            # Create message record with JSON content
            db_message = Message(
                group_id=group_id,
                sender_id=UUID(sender_id) if isinstance(sender_id, str) else sender_id,
                content=json.dumps(message),  # Store full payload as JSON
                sent_at=datetime.now(timezone.utc)
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            logger.info(f"Saved system message {db_message.id} to group {group_id}")
        
        # 3. Broadcast message to all connected members via WebSocket
        member_count = await chat_manager.broadcast_system_message(group_id, message)
        
        logger.info(f"Broadcasted message to {member_count} members in group {group_id}")
        
        return {
            "success": True,
            "group_id": str(group_id),
            "members_notified": member_count,
            "message_type": message.get("type", "unknown")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to broadcast to group {group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message"
        )


@router.patch("/update-alert/{group_id}/{alert_id}", status_code=status.HTTP_200_OK)
async def update_alert_in_messages(
    group_id: UUID,
    alert_id: UUID,
    update_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update a safety alert message in the database.
    
    This endpoint is used to update the resolved status of safety alerts
    stored in the messages table.
    
    Args:
        group_id: Group containing the message
        alert_id: Alert ID to update
        update_data: Fields to update (e.g., {"resolved": true, "resolved_at": "..."})
        
    Returns:
        Update status
    """
    try:
        # Find the message containing this alert_id
        messages = db.query(Message).filter(
            Message.group_id == group_id
        ).all()
        
        updated = False
        for msg in messages:
            try:
                # Parse message content as JSON
                content = json.loads(msg.content)
                
                # Check if this message is the alert we're looking for
                if content.get("type") == "safety_alert" and content.get("alert_id") == str(alert_id):
                    # Update the content with new fields
                    content.update(update_data)
                    msg.content = json.dumps(content)
                    updated = True
                    break
            except (json.JSONDecodeError, KeyError):
                continue
        
        if updated:
            db.commit()
            logger.info(f"Updated alert {alert_id} in group {group_id} messages")
            return {"success": True, "alert_id": str(alert_id), "updated": True}
        else:
            logger.warning(f"Alert {alert_id} not found in group {group_id} messages")
            return {"success": True, "alert_id": str(alert_id), "updated": False}
        
    except Exception as e:
        logger.error(f"Failed to update alert in messages: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert message"
        )
