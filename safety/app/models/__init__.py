"""
Pydantic models for Safety Service.
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==================== Enums ====================

class AlertType(str, Enum):
    """Valid alert types."""
    HELP = "help"
    EMERGENCY = "emergency"
    OTHER = "other"


# ==================== Safety Alert Models ====================

class SafetyAlertCreate(BaseModel):
    """Request to create a safety alert."""
    
    group_id: UUID = Field(..., description="Group to send alert to")
    latitude: Optional[float] = Field(None, description="User's current latitude", ge=-90, le=90)
    longitude: Optional[float] = Field(None, description="User's current longitude", ge=-180, le=180)
    alert_type: str = Field("help", description="Type of alert: help, emergency, other")
    message: Optional[str] = Field(None, description="Optional message", max_length=500)
    
    @field_validator("alert_type")
    @classmethod
    def validate_alert_type(cls, v: str) -> str:
        """Validate alert type is one of the allowed values."""
        valid_types = {t.value for t in AlertType}
        if v not in valid_types:
            raise ValueError(f"Invalid alert type. Must be one of: {', '.join(valid_types)}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_id": "123e4567-e89b-12d3-a456-426614174000",
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "help",
                "message": "Need assistance"
            }
        }
    )


class SafetyAlertResponse(BaseModel):
    """Safety alert response."""
    
    id: UUID
    user_id: UUID
    group_id: UUID
    latitude: Optional[float]
    longitude: Optional[float]
    alert_type: str
    message: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    resolved_by_user_id: Optional[UUID]
    is_resolved: bool = False
    
    # User details
    user_email: Optional[str] = None
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_user(cls, alert, user):
        """Create response with user details."""
        return cls(
            id=alert.id,
            user_id=alert.user_id,
            group_id=alert.group_id,
            latitude=float(alert.latitude) if alert.latitude else None,
            longitude=float(alert.longitude) if alert.longitude else None,
            alert_type=alert.alert_type,
            message=alert.message,
            created_at=alert.created_at,
            resolved_at=alert.resolved_at,
            resolved_by_user_id=alert.resolved_by_user_id,
            is_resolved=alert.resolved_at is not None,
            user_email=user.email if user else None,
            user_first_name=user.first_name if user else None,
            user_last_name=user.last_name if user else None
        )


class SafetyAlertListResponse(BaseModel):
    """List of safety alerts with pagination."""
    
    alerts: list[SafetyAlertResponse]
    total: int
    limit: int
    offset: int


class ResolveAlertRequest(BaseModel):
    """Request to mark an alert as resolved."""
    
    resolved: bool = Field(True, description="Mark as resolved")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resolved": True
            }
        }
    )


# ==================== WebSocket Broadcast Model ====================

class AlertBroadcast(BaseModel):
    """Alert broadcast message for WebSocket."""
    
    type: str = "safety_alert"
    alert_id: UUID
    user_id: UUID
    user_name: str
    alert_type: str
    message: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    created_at: datetime
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "safety_alert",
                "alert_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "user_name": "John Doe",
                "alert_type": "help",
                "message": "Need assistance",
                "latitude": 65.584819,
                "longitude": 22.154984,
                "created_at": "2025-11-25T12:00:00Z"
            }
        }
    )
