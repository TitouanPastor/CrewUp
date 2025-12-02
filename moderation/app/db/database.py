"""
Database connection and ORM models for Moderation Service.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
import uuid

from app.config import config

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    config.get_database_url(),
    pool_pre_ping=True,
    echo=config.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class User(Base):
    """
    Read-only User model for checking if users exist.

    This table is managed by the user service.
    The moderation service only reads from it to verify user existence.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    keycloak_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    bio = Column(Text)
    profile_picture_url = Column(Text)
    reputation = Column(DECIMAL(3, 2), default=0.00)
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(keycloak_id={self.keycloak_id}, email={self.email})>"


class ModerationAction(Base):
    """
    Model for tracking moderation actions.

    This table logs all moderation actions taken by moderators.
    """
    __tablename__ = "moderation_actions"

    id = Column(Integer, primary_key=True, index=True)
    moderator_id = Column(String, nullable=False, index=True)  # Keycloak user ID
    action_type = Column(String, nullable=False)  # e.g., "ban_user", "delete_content", "warn_user"
    target_type = Column(String, nullable=False)  # e.g., "user", "event", "group", "message"
    target_id = Column(String, nullable=False, index=True)  # ID of the target entity
    reason = Column(Text, nullable=False)  # Reason for the action
    details = Column(Text, nullable=True)  # Additional details (JSON or text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ModerationAction(id={self.id}, type={self.action_type}, target={self.target_type}:{self.target_id})>"


# Dependency to get database session
def get_db():
    """
    FastAPI dependency for database sessions.

    Usage:
        @router.get("/endpoint")
        async def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create all tables
def init_db():
    """Initialize database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
