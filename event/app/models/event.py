"""
Pydantic models for Event Service request/response validation.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Literal
from datetime import datetime, timedelta, timezone
from uuid import UUID
from decimal import Decimal


# ==================== Event Models ====================

class EventCreate(BaseModel):
    """Create event request model."""
    name: str = Field(..., min_length=1, max_length=255, description="Event name")
    description: Optional[str] = Field(None, description="Event description")
    event_type: Optional[Literal['bar', 'club', 'concert', 'party', 'restaurant', 'outdoor', 'sports', 'other']] = Field(
        'other',
        description="Type of event (defaults to 'other')"
    )
    address: str = Field(..., min_length=1, description="Event location address")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")
    event_start: datetime = Field(..., description="Event start time (ISO 8601 with timezone)")
    event_end: datetime = Field(..., description="Event end time (ISO 8601 with timezone)")
    max_attendees: Optional[int] = Field(None, description="Maximum number of attendees (null for unlimited, or >= 2)")
    is_public: bool = Field(True, description="Whether event is publicly visible")

    @field_validator("name", "address")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate string fields are not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("event_start")
    @classmethod
    def validate_event_start(cls, v: datetime) -> datetime:
        """Validate event_start is at least 30 minutes in the future."""
        now = datetime.now(timezone.utc)
        min_start_time = now + timedelta(minutes=30)

        # Ensure datetime is timezone-aware
        if v.tzinfo is None:
            raise ValueError("event_start must include timezone information")

        if v < min_start_time:
            raise ValueError("Event must start at least 30 minutes from now")

        return v

    @field_validator("max_attendees")
    @classmethod
    def validate_max_attendees(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_attendees is null or >= 2."""
        if v is not None and v < 2:
            raise ValueError("max_attendees must be at least 2 or null for unlimited capacity")
        return v

    @model_validator(mode='after')
    def validate_dates_and_location(self):
        """Validate event_end >= event_start and lat/lng pair."""
        # Validate event_end >= event_start
        if self.event_end < self.event_start:
            raise ValueError("event_end must be after or equal to event_start")

        # Validate lat/lng both provided or neither
        has_lat = self.latitude is not None
        has_lng = self.longitude is not None

        if has_lat != has_lng:
            raise ValueError("Both latitude and longitude must be provided together, or neither")

        return self


class EventUpdate(BaseModel):
    """Update event request model - all fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Event name")
    description: Optional[str] = Field(None, description="Event description (null to clear)")
    event_type: Optional[Literal['bar', 'club', 'concert', 'party', 'restaurant', 'outdoor', 'sports', 'other']] = Field(
        None,
        description="Type of event"
    )
    address: Optional[str] = Field(None, min_length=1, description="Event location address")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitude (-90 to 90)")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitude (-180 to 180)")
    event_start: Optional[datetime] = Field(None, description="Event start time (ISO 8601 with timezone)")
    event_end: Optional[datetime] = Field(None, description="Event end time (ISO 8601 with timezone)")
    max_attendees: Optional[int] = Field(None, description="Maximum number of attendees (null for unlimited, or >= 2)")
    is_public: Optional[bool] = Field(None, description="Whether event is publicly visible")
    is_cancelled: Optional[bool] = Field(None, description="Whether event is cancelled")

    @field_validator("name", "address")
    @classmethod
    def not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Validate string fields are not empty or whitespace if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Field cannot be empty")
        return v.strip() if v else v

    @field_validator("max_attendees")
    @classmethod
    def validate_max_attendees(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_attendees is >= 2 if provided (or can be None/explicitly null)."""
        if v is not None and v < 2:
            raise ValueError("max_attendees must be at least 2 or null for unlimited capacity")
        return v


class EventResponse(BaseModel):
    """Event response model."""
    id: UUID
    creator_id: UUID
    name: str
    description: Optional[str]
    event_type: Optional[str]
    address: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    event_start: datetime
    event_end: Optional[datetime]
    max_attendees: Optional[int]
    is_public: bool
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime

    # Creator details
    creator_first_name: Optional[str] = Field(None, description="Creator's first name")
    creator_last_name: Optional[str] = Field(None, description="Creator's last name")
    creator_profile_picture: Optional[str] = Field(None, description="Creator's profile picture URL")

    # Additional computed fields
    participant_count: int = Field(..., description="Number of users with status 'going'")
    interested_count: int = Field(0, description="Number of users with status 'interested'")
    is_full: bool = Field(..., description="Whether event is at capacity")
    user_status: Optional[str] = Field(None, description="Current user's RSVP status if authenticated")

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    """List of events response."""
    events: List[EventResponse]
    total: int
    limit: int
    offset: int


# ==================== Attendee Models ====================

class JoinEventRequest(BaseModel):
    """Join event request model."""
    status: Literal['going', 'interested', 'not_going'] = Field('going', description="RSVP status")


class AttendeeResponse(BaseModel):
    """Event attendee response model."""
    user_id: UUID
    keycloak_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class AttendeeListResponse(BaseModel):
    """List of attendees response."""
    event_id: UUID
    total_participants: int = Field(..., description="Total count of participants (filtered by status if applicable)")
    going_count: int = Field(..., description="Count of users with status 'going'")
    interested_count: int = Field(..., description="Count of users with status 'interested'")
    attendees: Optional[List[AttendeeResponse]] = Field(None, description="List of attendees if include_details=true")
