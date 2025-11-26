"""
Pytest configuration and shared fixtures for Safety Service tests.

Note: Unit tests test API layer without real database.
For full integration testing with database, see test_integration_auth.py
"""
# IMPORTANT: Set test mode BEFORE importing app
# This ensures TESTING variable is read correctly during app initialization
import os
os.environ["TESTING"] = "true"

import pytest
from typing import Generator
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone

from app.main import app
from app.db import Base, get_db, User, Event, Group, GroupMember, SafetyAlert


# Create in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_user(db_session):
    """Create a mock user."""
    user = User(
        id=uuid4(),
        keycloak_id="test-keycloak-id",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_event(db_session, mock_user):
    """Create a mock event that is currently in progress."""
    from app.db import Event
    event_obj = Event(
        id=uuid4(),
        creator_id=mock_user.id,
        name="Test Party",
        description="Test event description",
        event_type="party",
        address="123 Test Street",
        latitude=65.584819,
        longitude=22.154984,
        event_start=datetime.now(timezone.utc) - timedelta(hours=1),  # Started 1 hour ago
        event_end=datetime.now(timezone.utc) + timedelta(hours=2),    # Ends in 2 hours
        is_cancelled=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(event_obj)
    db_session.commit()
    db_session.refresh(event_obj)
    return event_obj


@pytest.fixture
def mock_group(db_session, mock_event):
    """Create a mock group."""
    group = Group(
        id=uuid4(),
        event_id=mock_event.id,
        name="Test Group",
        description="Test group description",
        max_members=10,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def mock_group_member(db_session, mock_user, mock_group):
    """Create a group membership."""
    member = GroupMember(
        group_id=mock_group.id,
        user_id=mock_user.id,
        is_admin=False,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def mock_current_user(mock_user):
    """Mock current user data from token."""
    return {
        "keycloak_id": mock_user.keycloak_id,
        "email": mock_user.email,
        "first_name": mock_user.first_name,
        "last_name": mock_user.last_name,
        "username": "testuser"
    }


@pytest.fixture(scope="function")
def client(db_session, mock_current_user):
    """Create a test client with database session override and authentication."""
    from app.middleware import get_current_user
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_current_user():
        return mock_current_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def unauth_client(db_session):
    """Create a test client without authentication override for testing auth."""
    from app.middleware import get_current_user
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    # Don't override get_current_user - let real auth middleware handle it
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authed_client() -> Generator:
    """
    Create a test client for API testing.
    Tests endpoints without requiring database connection.
    Test mode is enabled, so auth returns None (unauthenticated).
    """
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def mock_user_dict():
    """Mock authenticated user for testing (dict format)."""
    return {
        "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }


@pytest.fixture
def mock_user2_dict():
    """Second mock user for multi-user tests (dict format)."""
    return {
        "keycloak_id": "660e8400-e29b-41d4-a716-446655440001",
        "email": "test2@example.com",
        "first_name": "Test",
        "last_name": "User2",
        "username": "testuser2"
    }


@pytest.fixture
def auth_headers(mock_user_dict):
    """Mock authorization headers."""
    return {"Authorization": "Bearer mock-token"}


# Environment variables for integration tests
@pytest.fixture(scope="session")
def integration_env():
    """Load environment variables for integration tests."""
    from dotenv import load_dotenv
    load_dotenv(".env.test")
    return {
        "keycloak_url": os.getenv("KEYCLOAK_SERVER_URL"),
        "keycloak_realm": os.getenv("KEYCLOAK_REALM"),
        "keycloak_client_id": os.getenv("KEYCLOAK_CLIENT_ID"),
        "user1_email": os.getenv("TEST_USER1_EMAIL"),
        "user1_password": os.getenv("TEST_USER1_PASSWORD"),
        "user2_email": os.getenv("TEST_USER2_EMAIL"),
        "user2_password": os.getenv("TEST_USER2_PASSWORD"),
        "service_url": os.getenv("SAFETY_SERVICE_URL", "http://localhost:8003"),
        "database_url": os.getenv("DATABASE_URL", "postgresql://crewup:crewup_dev_password@localhost:5432/crewup"),
    }
