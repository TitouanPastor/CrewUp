"""
SQLAlchemy ORM models (database tables).
"""
from sqlalchemy import Column, String, Float, Boolean, TIMESTAMP, ARRAY, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid as uuid_lib

from app.db.database import Base


class User(Base):
    """
    User table matching database/schema.sql.
    
    This is the ORM representation of the users table.
    SQLAlchemy will map this class to SQL queries automatically.
    """
    __tablename__ = "users"
    
    # Primary key (UUID)
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid_lib.uuid4,
        server_default=text("uuid_generate_v4()")
    )
    
    # Keycloak integration
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Profile
    bio = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)
    interests = Column(ARRAY(String), default=[], nullable=False)
    
    # Reputation system
    reputation = Column(
        Float,
        default=0.0,
        nullable=False,
        server_default="0.0"
    )
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('reputation >= 0 AND reputation <= 5', name='valid_reputation'),
    )
    
    def __repr__(self):
        return f"<User {self.email} (reputation={self.reputation})>"
