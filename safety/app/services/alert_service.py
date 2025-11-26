"""
Business logic for safety alerts.
"""
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional
import logging

from app.db.models import SafetyAlert
from app.models import AlertCreate, AlertResponse, AlertListResponse
from app.utils.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class AlertService:
    """Service class for safety alert operations."""

    @staticmethod
    def create_alert(
        db: Session,
        user_id: UUID,
        alert_data: AlertCreate
    ) -> SafetyAlert:
        """
        Create a new safety alert.
        
        Args:
            db: Database session
            user_id: ID of user triggering alert
            alert_data: Alert creation data
            
        Returns:
            Created SafetyAlert instance
        """
        logger.info(f"Creating safety alert for user {user_id} at event {alert_data.event_id}")
        
        alert = SafetyAlert(
            user_id=user_id,
            event_id=alert_data.event_id,
            latitude=alert_data.latitude,
            longitude=alert_data.longitude,
            message=alert_data.message or "🚨 EMERGENCY ALERT - User needs help!"
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Safety alert {alert.id} created successfully")
        return alert

    @staticmethod
    def get_alert(db: Session, alert_id: UUID) -> SafetyAlert:
        """
        Get a safety alert by ID.
        
        Args:
            db: Database session
            alert_id: Alert ID
            
        Returns:
            SafetyAlert instance
            
        Raises:
            NotFoundException: If alert not found
        """
        alert = db.query(SafetyAlert).filter(SafetyAlert.id == alert_id).first()
        if not alert:
            raise NotFoundException(f"Alert {alert_id} not found")
        return alert

    @staticmethod
    def list_alerts(
        db: Session,
        user_id: Optional[UUID] = None,
        event_id: Optional[UUID] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AlertListResponse:
        """
        List safety alerts with optional filtering.
        
        Args:
            db: Database session
            user_id: Filter by user (optional)
            event_id: Filter by event (optional)
            is_resolved: Filter by resolution status (optional)
            limit: Max results
            offset: Results offset
            
        Returns:
            AlertListResponse with alerts and pagination
        """
        query = db.query(SafetyAlert)
        
        if user_id:
            query = query.filter(SafetyAlert.user_id == user_id)
        if event_id:
            query = query.filter(SafetyAlert.event_id == event_id)
        if is_resolved is not None:
            query = query.filter(SafetyAlert.is_resolved == is_resolved)
        
        total = query.count()
        alerts = query.order_by(SafetyAlert.created_at.desc()).offset(offset).limit(limit).all()
        
        return AlertListResponse(
            alerts=[AlertResponse.model_validate(a) for a in alerts],
            total=total,
            offset=offset,
            limit=limit
        )

    @staticmethod
    def resolve_alert(db: Session, alert_id: UUID, user_id: UUID) -> SafetyAlert:
        """
        Mark an alert as resolved.
        
        Args:
            db: Database session
            alert_id: Alert ID
            user_id: User resolving the alert (must be creator)
            
        Returns:
            Updated SafetyAlert instance
            
        Raises:
            NotFoundException: If alert not found
            PermissionError: If user is not the alert creator
        """
        alert = AlertService.get_alert(db, alert_id)
        
        if alert.user_id != user_id:
            raise PermissionError("Only alert creator can resolve it")
        
        if alert.is_resolved:
            logger.warning(f"Alert {alert_id} already resolved")
            return alert
        
        alert.is_resolved = True
        alert.resolved_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert_id} resolved by user {user_id}")
        return alert
