"""
Safety alert API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
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


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/safety", tags=["safety-alerts"])


class SafetyException(HTTPException):
    """Custom exception for safety-specific errors."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


# ==================== Helper Functions ====================

async def broadcast_alert_to_group(group_id: UUID, alert: SafetyAlert, user: User) -> bool:
    """Broadcast safety alert to group members via WebSocket (internal group service call)."""
    try:
        # Build user display name
        user_name = f"{user.first_name} {user.last_name}".strip() or user.email
        
        # Create broadcast payload
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
        
        # Call group service
        url = f"{config.GROUP_SERVICE_URL}/api/v1/groups/internal/broadcast/{group_id}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=broadcast_data.model_dump(mode='json'))
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


async def broadcast_alert_resolution(group_id: UUID, alert_id: UUID, resolver_name: str) -> bool:
    """Broadcast alert resolution to group members via WebSocket AND update message in DB."""
    try:
        resolved_at = datetime.now(timezone.utc).isoformat()
        
        # 1. Update the message in the database
        update_url = f"{config.GROUP_SERVICE_URL}/api/v1/groups/internal/update-alert/{group_id}/{alert_id}"
        update_data = {
            "resolved": True,
            "resolved_at": resolved_at,
            "resolved_by": resolver_name
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            update_response = await client.patch(update_url, json=update_data)
            update_response.raise_for_status()
            logger.info(f"Updated alert {alert_id} in database")
        
        # 2. Broadcast resolution via WebSocket
        broadcast_data = {
            "type": "alert_resolved",
            "alert_id": str(alert_id),
            "resolver_name": resolver_name,
            "resolved_at": resolved_at
        }
        
        broadcast_url = f"{config.GROUP_SERVICE_URL}/api/v1/groups/internal/broadcast/{group_id}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(broadcast_url, json=broadcast_data)
            response.raise_for_status()
        
        logger.info(f"Alert {alert_id} resolution broadcast to group {group_id}")
        return True
        
    except httpx.TimeoutException:
        logger.error(f"Timeout broadcasting resolution to group {group_id}")
        return False
    except httpx.HTTPError as e:
        logger.error(f"HTTP error broadcasting resolution: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to broadcast resolution: {e}")
        return False


def is_event_active(event: Event) -> bool:
    """
    Check if event is currently active with 2-hour margin.
    Event is considered active from 2h before start to 2h after end.
    Handles both timezone-aware and naive datetimes for compatibility.
    """
    now = datetime.now(timezone.utc)
    
    # 2-hour margin in seconds
    MARGIN_HOURS = 2
    MARGIN_SECONDS = MARGIN_HOURS * 60 * 60
    
    # Ensure timezone-aware datetimes (SQLite compatibility)
    start = event.event_start
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    
    end = event.event_end
    if end and end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    
    # Default end time if not specified (24h after start)
    if not end:
        from datetime import timedelta
        end = start + timedelta(hours=24)
    
    # Apply margin: 2h before start, 2h after end
    from datetime import timedelta
    active_start = start - timedelta(seconds=MARGIN_SECONDS)
    active_end = end + timedelta(seconds=MARGIN_SECONDS)
    
    # Check: within margin window and not cancelled
    return active_start <= now <= active_end and not event.is_cancelled


# ==================== API Endpoints ====================

@router.post("", response_model=SafetyAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_safety_alert(
    alert_data: SafetyAlertCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create and broadcast safety alert to group members."""
    try:
        # Get user profile
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise SafetyException("User profile not found. Complete your profile first.", status.HTTP_404_NOT_FOUND)
        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {user.keycloak_id} attempted to raise a safety alert")
            raise SafetyException("User has been banned from Crewup.", status.HTTP_403_FORBIDDEN)
        # Validate group exists
        group = db.query(Group).filter(Group.id == alert_data.group_id).first()
        if not group:
            raise NotFoundException("Group not found")
        
        # Check user is group member
        is_member = db.query(GroupMember).filter(
            and_(GroupMember.group_id == alert_data.group_id, GroupMember.user_id == user.id)
        ).first()
        
        if not is_member:
            raise SafetyException("You must be a member of this group to send alerts", status.HTTP_403_FORBIDDEN)
        
        # Check event is active
        event = db.query(Event).filter(Event.id == group.event_id).first()
        if not event:
            raise NotFoundException("Associated event not found")
        
        if not is_event_active(event):
            raise SafetyException("Safety alerts can only be sent during active events", status.HTTP_400_BAD_REQUEST)
        
        # Create alert
        alert = SafetyAlert(
            id=uuid4(),
            user_id=user.id,
            group_id=alert_data.group_id,
            batch_id=alert_data.batch_id or uuid4(),  # Use provided batch_id or generate new one
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            alert_type=alert_data.alert_type,
            message=alert_data.message,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert.id} created by user {user.id} in group {alert_data.group_id}")
        
        # Broadcast to group via WebSocket
        await broadcast_alert_to_group(alert_data.group_id, alert, user)
        
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
    """List safety alerts (groups user is member of)."""
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {user.keycloak_id} attempted to list the safety alerts")
            raise SafetyException("User has been banned from Crewup.", status.HTTP_403_FORBIDDEN)
        
        # Query alerts from user's groups
        query = db.query(SafetyAlert).join(
            GroupMember, and_(GroupMember.group_id == SafetyAlert.group_id, GroupMember.user_id == user.id)
        )
        
        # Apply filters
        if group_id:
            query = query.filter(SafetyAlert.group_id == group_id)
        
        if resolved is not None:
            query = query.filter(
                SafetyAlert.resolved_at.isnot(None) if resolved else SafetyAlert.resolved_at.is_(None)
            )
        
        # Get total and fetch with pagination
        total = query.count()
        alerts = query.order_by(SafetyAlert.created_at.desc()).offset(offset).limit(limit).all()
        
        return SafetyAlertListResponse(
            alerts=[SafetyAlertResponse.from_orm_with_user(alert, alert.user) for alert in alerts],
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


@router.get("/my-alerts", response_model=SafetyAlertListResponse)
async def get_my_alerts(
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    limit: int = Query(50, ge=1, le=100, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's own safety alerts."""
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {user.keycloak_id} attempted to list their safety alerts")
            raise SafetyException("User has been banned from Crewup.", status.HTTP_403_FORBIDDEN)
        
        # Query alerts created by this user
        query = db.query(SafetyAlert).filter(SafetyAlert.user_id == user.id)
        
        # Apply filters
        if resolved is not None:
            query = query.filter(
                SafetyAlert.resolved_at.isnot(None) if resolved else SafetyAlert.resolved_at.is_(None)
            )
        
        # Get total and fetch with pagination
        total = query.count()
        alerts = query.order_by(SafetyAlert.created_at.desc()).offset(offset).limit(limit).all()
        
        return SafetyAlertListResponse(
            alerts=[SafetyAlertResponse.from_orm_with_user(alert, alert.user) for alert in alerts],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except (NotFoundException, BadRequestException, ForbiddenException, SafetyException, HTTPException):
        raise
    except Exception as e:
        logger.error(f"Failed to get user alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user alerts"
        )


@router.get("/{alert_id}", response_model=SafetyAlertResponse)
async def get_safety_alert(
    alert_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific safety alert (group members only)."""
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {user.keycloak_id} attempted to check safety alert {alert_id}")
            raise SafetyException("User has been banned from Crewup.", status.HTTP_403_FORBIDDEN)
        
        # Get alert
        alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
        if not alert:
            raise NotFoundException("Alert not found")
        
        # Check group membership
        is_member = db.query(GroupMember).filter(
            and_(GroupMember.group_id == alert.group_id, GroupMember.user_id == user.id)
        ).first()
        
        if not is_member:
            raise SafetyException("Access denied: not a group member", status.HTTP_403_FORBIDDEN)
        
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
    """Mark alert as resolved (creator only). Resolves all alerts in the same batch."""
    try:
        # Get user
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            raise NotFoundException("User profile not found")
        
        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {user.keycloak_id} attempted to resolve safety alert {alert_id}")
            raise SafetyException("User has been banned from Crewup.", status.HTTP_403_FORBIDDEN)
        
        # Get alert
        alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
        if not alert:
            raise NotFoundException("Alert not found")
        
        # Check permissions (creator only)
        is_creator = alert.user_id == user.id
        
        if not is_creator:
            raise SafetyException("Access denied: only the alert creator can resolve it", status.HTTP_403_FORBIDDEN)
        
        # Get all alerts in the same batch
        batch_id = alert.batch_id or alert.id
        batch_alerts = db.query(SafetyAlert).filter(SafetyAlert.batch_id == batch_id).all()
        
        # Update all alerts in the batch
        resolver_name = f"{user.first_name} {user.last_name}".strip() or user.email
        resolved_time = datetime.now(timezone.utc) if resolve_data.resolved else None
        
        for batch_alert in batch_alerts:
            batch_alert.resolved_at = resolved_time
            batch_alert.resolved_by_user_id = user.id if resolve_data.resolved else None
        
        db.commit()
        
        # Refresh the original alert
        db.refresh(alert)
        
        logger.info(f"Alert batch {batch_id} ({'resolved' if resolve_data.resolved else 'unresolved'}) by user {user.id} - {len(batch_alerts)} alerts updated")
        
        # Broadcast resolution to all groups in the batch
        if resolve_data.resolved:
            for batch_alert in batch_alerts:
                await broadcast_alert_resolution(batch_alert.group_id, batch_alert.id, resolver_name)
        
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
