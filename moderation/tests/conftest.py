"""
Pytest configuration and fixtures for moderation service tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch
import os

from app.main import app
from app.db import Base, get_db, User, ModerationAction


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_moderator():
    """Mock moderator user data."""
    return {
        "keycloak_id": "moderator-uuid-1234",
        "email": "moderator@test.com",
        "first_name": "Test",
        "last_name": "Moderator",
        "username": "test_moderator",
        "roles": {
            "realm": ["Moderator"],
            "client": []
        }
    }


@pytest.fixture
def moderator_user(db_session, mock_moderator):
    """Create a moderator user in the database."""
    user = User(
        keycloak_id=mock_moderator["keycloak_id"],
        email=mock_moderator["email"],
        first_name=mock_moderator["first_name"],
        last_name=mock_moderator["last_name"],
        is_active=True,
        is_banned=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular user in the database."""
    user = User(
        keycloak_id="user-uuid-5678",
        email="user@test.com",
        first_name="Regular",
        last_name="User",
        is_active=True,
        is_banned=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def banned_user(db_session):
    """Create a banned user in the database."""
    user = User(
        keycloak_id="banned-user-uuid-9999",
        email="banned@test.com",
        first_name="Banned",
        last_name="User",
        is_active=True,
        is_banned=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_jwt_payload(mock_moderator):
    """Mock JWT token payload for a moderator."""
    return {
        "sub": mock_moderator["keycloak_id"],
        "email": mock_moderator["email"],
        "given_name": mock_moderator["first_name"],
        "family_name": mock_moderator["last_name"],
        "preferred_username": mock_moderator["username"],
        "realm_access": {
            "roles": ["Moderator"]
        },
        "resource_access": {}
    }


@pytest.fixture
def mock_jwt_payload_regular_user():
    """Mock JWT token payload for a regular user (no moderator role)."""
    return {
        "sub": "user-uuid-5678",
        "email": "user@test.com",
        "given_name": "Regular",
        "family_name": "User",
        "preferred_username": "regular_user",
        "realm_access": {
            "roles": []
        },
        "resource_access": {}
    }


@pytest.fixture
def mock_verify_token(mock_moderator):
    """Mock the get_current_moderator dependency to return a valid moderator."""
    from app.middleware import get_current_moderator

    async def mock_get_moderator():
        return mock_moderator

    # Override the dependency in the app
    app.dependency_overrides[get_current_moderator] = mock_get_moderator
    yield
    # Clean up
    if get_current_moderator in app.dependency_overrides:
        del app.dependency_overrides[get_current_moderator]


@pytest.fixture
def mock_rabbitmq_publisher_success():
    """Mock RabbitMQ publisher to always succeed."""
    with patch("app.services.rabbitmq_publisher.publish_user_ban", return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_rabbitmq_publisher_failure():
    """Mock RabbitMQ publisher to always fail."""
    with patch("app.services.rabbitmq_publisher.publish_user_ban", return_value=False) as mock:
        yield mock
