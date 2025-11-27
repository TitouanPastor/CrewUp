"""
Database models for Safety Service.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, DECIMAL, ForeignKey, Text, ARRAY, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


# UUID type that works with both PostgreSQL and SQLite
class UUID(TypeDecorator):
    """Platform-independent GUID type.
    
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36) storing as string.
    """
    impl = DECIMAL
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


from app.db.database import Base


class User(Base):
    """User model (read-only, managed by user service)."""
    __tablename__ = "users"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text)
    profile_picture_url = Column(Text)
    # interests = Column(ARRAY(Text))  # PostgreSQL only, skip for tests
    reputation = Column(DECIMAL(3, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Event(Base):
    """Event model (read-only, managed by event service)."""
    __tablename__ = "events"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    creator_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(String(50))
    address = Column(Text, nullable=False)
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    event_start = Column(DateTime(timezone=True), nullable=False)
    event_end = Column(DateTime(timezone=True))
    max_attendees = Column(Integer)
    is_public = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Group(Base):
    """Group model (read-only, managed by group service)."""
    __tablename__ = "groups"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(), ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    max_members = Column(Integer, default=10)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    event = relationship("Event")


class GroupMember(Base):
    """Group membership model (read-only, managed by group service)."""
    __tablename__ = "group_members"
    
    group_id = Column(UUID(), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)


class SafetyAlert(Base):
    """Safety alert model (managed by safety service)."""
    __tablename__ = "safety_alerts"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    group_id = Column(UUID(), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    batch_id = Column(UUID())  # Links alerts sent to multiple groups at once
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    alert_type = Column(String(50), default="help")
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by_user_id = Column(UUID(), ForeignKey("users.id", ondelete="SET NULL"))
    
    user = relationship("User", foreign_keys=[user_id])
    group = relationship("Group")
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
