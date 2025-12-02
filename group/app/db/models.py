"""
SQLAlchemy ORM models for Group & Chat Service.
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
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now())
    updated_at = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now())


class Group(Base):
    """
    Group model - groups are created for specific events.
    
    Attributes:
        id: Unique group identifier
        event_id: Foreign key to event (not enforced in this service)
        name: Group name
        description: Optional description
        creator_id: User who created the group
        max_members: Maximum number of members (2-50)
        is_active: Soft delete flag
        created_at: Creation timestamp
    """
    __tablename__ = "groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_members = Column(Integer, nullable=False, default=10)
    is_private = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    
    # Relationships
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="group", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("max_members > 0", name="groups_max_members_check"),
        Index("idx_groups_event", "event_id"),
    )


class GroupMember(Base):
    """
    Group membership model - tracks which users are in which groups.
    
    Attributes:
        group_id: Group identifier
        user_id: User identifier
        joined_at: When the user joined
    """
    __tablename__ = "group_members"
    
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, primary_key=True, index=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="members")
    
    __table_args__ = (
        Index("idx_group_members_user", "user_id"),
    )


class Message(Base):
    """
    Chat message model - messages sent in group chats.
    
    Attributes:
        id: Unique message identifier
        group_id: Group this message belongs to
        sender_id: User who sent the message
        content: Message text content
        is_edited: Whether message was edited
        sent_at: When the message was sent
    """
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    
    # Relationships
    group = relationship("Group", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(trim(content)) > 0", name="non_empty_content"),
        Index("idx_messages_group", "group_id", "sent_at", postgresql_ops={"sent_at": "DESC"}),
    )
