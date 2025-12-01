"""
Database connection and ORM models for Moderation Service.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

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
