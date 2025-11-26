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

from app.db import get_db, Group
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
    Broadcast a message to all members of a group via WebSocket.
    
    This endpoint is called by other services (e.g., safety service)
    to send system messages to group members.
    
    Args:
        group_id: Group to broadcast to
        message: Message payload to broadcast (arbitrary JSON)
        
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
        
        # 2. Broadcast message to all connected members
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
