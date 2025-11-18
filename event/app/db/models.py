"""
SQLAlchemy ORM models for Event Service.
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, UUID, ForeignKey, CheckConstraint, Index, ARRAY, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class User(Base):
    """
    User model (read-only reference to users table).
    This service doesn't manage users, but needs to reference them.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    interests = Column(ARRAY(Text), default=list)
    reputation = Column(DECIMAL(3, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())


class Event(Base):
    """
    Event model - represents social events that users can attend.

    Attributes:
        id: Unique event identifier
        creator_id: User who created the event
        name: Event name
        description: Event description (optional)
        event_type: Type of event (bar, club, concert, etc.)
        address: Event location address
        latitude: Location latitude (optional)
        longitude: Location longitude (optional)
        event_start: When the event starts (timezone-aware)
        event_end: When the event ends (optional, timezone-aware)
        max_attendees: Maximum number of attendees (optional, unlimited if null)
        is_public: Whether event is publicly visible
        is_cancelled: Whether event has been cancelled
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=True)

    # Location
    address = Column(Text, nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)

    # Date & time (timezone-aware)
    event_start = Column(DateTime(timezone=True), nullable=False)
    event_end = Column(DateTime(timezone=True), nullable=True)

    max_attendees = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    is_cancelled = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    attendees = relationship("EventAttendee", back_populates="event", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[creator_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("max_attendees IS NULL OR max_attendees > 0", name="events_max_attendees_check"),
        CheckConstraint(
            "event_type IN ('bar', 'club', 'concert', 'party', 'restaurant', 'outdoor', 'sports', 'other')",
            name="events_type_check"
        ),
        Index("idx_events_start", "event_start"),
        Index("idx_events_creator", "creator_id"),
        Index("idx_events_type", "event_type"),
        Index("idx_events_location", "latitude", "longitude"),
    )


class EventAttendee(Base):
    """
    Event attendee model - tracks which users are attending which events and their RSVP status.

    Attributes:
        event_id: Event identifier
        user_id: User identifier
        status: RSVP status (going, interested, not_going)
        created_at: When the RSVP was created
        updated_at: When the RSVP was last updated
    """
    __tablename__ = "event_attendees"

    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    status = Column(String(20), nullable=False, default="going")
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    event = relationship("Event", back_populates="attendees")
    user = relationship("User", foreign_keys=[user_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('going', 'interested', 'not_going')", name="event_attendees_status_check"),
        Index("idx_event_attendees_user", "user_id"),
        Index("idx_event_attendees_status", "event_id", "status"),
    )
