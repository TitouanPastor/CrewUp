"""
Test configuration and fixtures.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from uuid import uuid4

# IMPORTANT: Set test mode BEFORE importing app
os.environ["TESTING"] = "true"

# Set test environment
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["KEYCLOAK_SERVER_URL"] = "http://test-keycloak:8080"
os.environ["KEYCLOAK_REALM"] = "test-realm"
os.environ["GROUP_SERVICE_URL"] = "http://test-group-service:8002"
os.environ["EVENT_SERVICE_URL"] = "http://test-event-service:8001"

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


@pytest.fixture
def mock_user(db_session):
    """Create a mock user."""
    user = User(
        id=uuid4(),
        keycloak_id="test-keycloak-id",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_event(db_session, mock_user):
    """Create a mock event that is currently in progress."""
    event = Event(
        id=uuid4(),
        creator_id=mock_user.id,
        name="Test Party",
        description="Test event description",
        event_type="party",
        address="123 Test Street",
        latitude=65.584819,
        longitude=22.154984,
        event_start=datetime.utcnow() - timedelta(hours=1),  # Started 1 hour ago
        event_end=datetime.utcnow() + timedelta(hours=2),    # Ends in 2 hours
        is_cancelled=False,
        created_at=datetime.utcnow()
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def mock_group(db_session, mock_event):
    """Create a mock group."""
    group = Group(
        id=uuid4(),
        event_id=mock_event.id,
        name="Test Group",
        description="Test group description",
        max_members=10,
        created_at=datetime.utcnow()
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
        joined_at=datetime.utcnow()
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def mock_auth_token():
    """Mock authentication token."""
    return "Bearer mock-jwt-token"


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
