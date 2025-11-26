"""
Safety alert API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import logging
import httpx

from app.db import get_db, User, SafetyAlert, Group, GroupMember, Event
from app.models import (
    SafetyAlertCreate,
    SafetyAlertResponse,
    SafetyAlertListResponse,
    ResolveAlertRequest,
    AlertBroadcast,
)
from app.middleware import get_current_user
from app.config import config
from app.utils import NotFoundException, BadRequestException, ForbiddenException


class SafetyException(HTTPException):
    """Custom exception for safety service."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["safety-alerts"])


# ==================== Helper Functions ====================

async def broadcast_alert_to_group(
    group_id: UUID,
    alert: SafetyAlert,
    user: User
) -> bool:
    """
    Broadcast safety alert to all members in a group via WebSocket.
    
    Makes HTTP call to group service internal endpoint.
    
    Args:
        group_id: Group ID to broadcast to
        alert: Safety alert object
        user: User who created the alert
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Build user name
        user_name = f"{user.first_name} {user.last_name}".strip()
        if not user_name:
            user_name = user.email
        
        # Create broadcast message
        broadcast_data = AlertBroadcast(
            type="safety_alert",
            alert_id=alert.id,
            user_id=alert.user_id,
            user_name=user_name,
            alert_type=alert.alert_type,
            message=alert.message,
            latitude=float(alert.latitude) if alert.latitude else None,
            longitude=float(alert.longitude) if alert.longitude else None,
            created_at=alert.created_at
        )
        
        # Send to group service
        url = f"{config.GROUP_SERVICE_URL}/api/v1/groups/internal/broadcast/{group_id}"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                url,
                json=broadcast_data.model_dump(mode='json')
            )
            response.raise_for_status()
        
        logger.info(f"Alert {alert.id} broadcast to group {group_id}")
        return True
        
    except httpx.TimeoutException:
        logger.error(f"Timeout broadcasting alert to group {group_id}")
        return False
    except httpx.HTTPError as e:
        logger.error(f"HTTP error broadcasting alert: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to broadcast alert: {e}")
        return False


def check_event_in_progress(event: Event) -> bool:
    """
    Check if an event is currently in progress.
    
    Args:
        event: Event to check
        
    Returns:
        True if event is in progress (between start and end time)
    """
    now = datetime.utcnow()
    
    # Event has started
    if event.event_start > now:
        return False
    
    # Event has ended (if end time specified)
    if event.event_end and event.event_end < now:
        return False
    
    # Event is cancelled
    if event.is_cancelled:
        return False
    
    return True


# ==================== API Endpoints ====================

@router.post("", response_model=SafetyAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_safety_alert(
    alert_data: SafetyAlertCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a safety alert and broadcast it to all group members.
    
    The alert will be sent to all members of the specified group via WebSocket
    if the associated event is currently in progress.
    
    Requires authentication and group membership.
    """
    try:
        # 1. Get user from database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise SafetyException(
                "User profile not found. Please complete your profile first.",
                status.HTTP_404_NOT_FOUND
            )
        
        # 2. Validate group exists
        group = db.query(Group).filter(Group.id == alert_data.group_id).first()
        if not group:
            raise NotFoundException("Group not found")
        
        # 3. Check user is member of the group
        is_member = db.query(GroupMember).filter(
            and_(
                GroupMember.group_id == alert_data.group_id,
                GroupMember.user_id == user.id
            )
        ).first()
        
        if not is_member:
            raise SafetyException(
                "You must be a member of this group to send alerts",
                status.HTTP_403_FORBIDDEN
            )
        
        # 4. Check if event is in progress
        event = db.query(Event).filter(Event.id == group.event_id).first()
        if not event:
            raise NotFoundException("Associated event not found")
        
        if not check_event_in_progress(event):
            raise SafetyException(
                "Safety alerts can only be sent during active events",
                status.HTTP_400_BAD_REQUEST
            )
        
        # 5. Validate alert type
        valid_alert_types = ["help", "emergency", "other"]
        if alert_data.alert_type not in valid_alert_types:
            raise SafetyException(
                f"Invalid alert type. Must be one of: {', '.join(valid_alert_types)}",
                status.HTTP_400_BAD_REQUEST
            )
        
        # 6. Create safety alert
        alert = SafetyAlert(
            user_id=user.id,
            group_id=alert_data.group_id,
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            alert_type=alert_data.alert_type,
            message=alert_data.message,
            created_at=datetime.utcnow()
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Safety alert {alert.id} created by user {user.id} in group {alert_data.group_id}")
        
        # 7. Broadcast alert to all group members via WebSocket
        await broadcast_alert_to_group(alert_data.group_id, alert, user)
        
        # 8. Return response with user details
        return SafetyAlertResponse.from_orm_with_user(alert, user)
        
    except (NotFoundException, BadRequestException, ForbiddenException, SafetyException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to create safety alert: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create safety alert"
        )


@router.get("", response_model=SafetyAlertListResponse)
async def list_safety_alerts(
    group_id: Optional[UUID] = Query(None, description="Filter by group ID"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List safety alerts.
    
    Returns alerts for groups the user is a member of.
    Can filter by group ID and resolved status.
    """
    try:
        # Get user from database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Build query - only show alerts from groups user is member of
        query = db.query(SafetyAlert).join(
            GroupMember,
            and_(
                GroupMember.group_id == SafetyAlert.group_id,
                GroupMember.user_id == user.id
            )
        )
        
        # Apply filters
        if group_id:
            query = query.filter(SafetyAlert.group_id == group_id)
        
        if resolved is not None:
            if resolved:
                query = query.filter(SafetyAlert.resolved_at.isnot(None))
            else:
                query = query.filter(SafetyAlert.resolved_at.is_(None))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        alerts = query.order_by(SafetyAlert.created_at.desc()).offset(offset).limit(limit).all()
        
        # Build responses with user details
        responses = [SafetyAlertResponse.from_orm_with_user(alert, alert.user) for alert in alerts]
        
        return SafetyAlertListResponse(
            alerts=responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except (NotFoundException, BadRequestException, ForbiddenException, SafetyException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to list safety alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list safety alerts"
        )


@router.get("/{alert_id}", response_model=SafetyAlertResponse)
async def get_safety_alert(
    alert_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific safety alert.
    
    Only accessible to members of the associated group.
    """
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Get alert
        alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
        if not alert:
            raise NotFoundException("Alert not found")
        
        # Check user is member of the group
        is_member = db.query(GroupMember).filter(
            and_(
                GroupMember.group_id == alert.group_id,
                GroupMember.user_id == user.id
            )
        ).first()
        
        if not is_member:
            raise SafetyException(
                "Access denied. You must be a group member to view this alert.",
                status.HTTP_403_FORBIDDEN
            )
        
        # Build response with user details
        return SafetyAlertResponse.from_orm_with_user(alert, alert.user)
        
    except (NotFoundException, BadRequestException, ForbiddenException, SafetyException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to get safety alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get safety alert"
        )


@router.patch("/{alert_id}/resolve", response_model=SafetyAlertResponse)
async def resolve_safety_alert(
    alert_id: UUID,
    resolve_data: ResolveAlertRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a safety alert as resolved.
    
    Only group admins or the alert creator can resolve alerts.
    """
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Get alert
        alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
        if not alert:
            raise NotFoundException("Alert not found")
        
        # Check permissions (must be alert creator or group admin)
        is_creator = alert.user_id == user.id
        is_admin = db.query(GroupMember).filter(
            and_(
                GroupMember.group_id == alert.group_id,
                GroupMember.user_id == user.id,
                GroupMember.is_admin == True
            )
        ).first()
        
        if not (is_creator or is_admin):
            raise SafetyException(
                "Access denied. Only the alert creator or group admins can resolve alerts.",
                status.HTTP_403_FORBIDDEN
            )
        
        # Update alert
        if resolve_data.resolved:
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by_user_id = user.id
        else:
            alert.resolved_at = None
            alert.resolved_by_user_id = None
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert_id} {'resolved' if resolve_data.resolved else 'unresolved'} by user {user.id}")
        
        # Build response with user details
        return SafetyAlertResponse.from_orm_with_user(alert, alert.user)
        
    except (NotFoundException, BadRequestException, ForbiddenException, SafetyException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


# Export router
alerts_router = router
__all__ = ["alerts_router"]
