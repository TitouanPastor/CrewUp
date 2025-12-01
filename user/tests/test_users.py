"""
Integration tests for User Service API.

Tests cover:
- User creation (POST /users)
- Get current user (GET /users/me)
- Update profile (PUT /users/me)
- Get public profile (GET /users/{id})
- Error cases (401, 404, 422)

Uses real PostgreSQL database for testing.
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db
from app.middleware.auth import get_current_user

# Test database (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://crewup:crewup_dev_password@localhost:5432/crewup"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user():
    """Override authentication for testing - returns mock user."""
    return {
        "keycloak_id": "test-keycloak-123",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe"
    }


# Override dependencies
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# Test client
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """
    Ensure tables exist before tests.
    Does NOT drop tables - keeps data intact for other services.
    """
    # Create uuid extension if not exists
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()
    
    # Create tables if they don't exist (won't affect existing data)
    Base.metadata.create_all(bind=engine)
    yield
    
    # Cleanup: Only delete test user data, don't drop tables
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE keycloak_id = 'test-keycloak-123'"))
        conn.commit()


@pytest.fixture
def mock_current_user():
    """Mock authenticated user from JWT token."""
    return {
        "keycloak_id": "test-keycloak-123",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "username": "johndoe"
    }


@pytest.fixture
def auth_headers():
    """Mock authorization headers."""
    return {"Authorization": "Bearer fake-token-for-testing"}


def test_health_check():
    """Test health endpoint (no auth required)."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "user-service"


def test_create_user_success(mock_current_user, auth_headers):
    """Test creating a new user profile."""
    response = client.post("/api/v1/users", headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "John"
    assert data["keycloak_id"] == "test-keycloak-123"
    assert "id" in data


def test_create_user_idempotent(mock_current_user, auth_headers):
    """Test creating user twice returns existing profile."""
    # First call - creates user
    response1 = client.post("/api/v1/users", headers=auth_headers)
    assert response1.status_code == 201
    
    # Second call - returns existing user (200 instead of 201)
    response2 = client.post("/api/v1/users", headers=auth_headers)
    assert response2.status_code == 200
    assert response1.json()["id"] == response2.json()["id"]


def test_get_current_user_not_found(mock_current_user, auth_headers):
    """Test GET /users/me when user doesn't exist."""
    response = client.get("/api/v1/users/me", headers=auth_headers)
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_current_user_success(mock_current_user, auth_headers):
    """Test GET /users/me after creating profile."""
    # Create user first
    client.post("/api/v1/users", headers=auth_headers)
    
    # Get profile
    response = client.get("/api/v1/users/me", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_update_profile_success(mock_current_user, auth_headers):
    """Test updating user profile."""
    # Create user
    client.post("/api/v1/users", headers=auth_headers)
    
    # Update profile
    update_data = {
        "bio": "Test bio",
        "interests": ["coding", "music"]
    }
    response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Test bio"
    assert "coding" in data["interests"]


def test_update_profile_validation_error(mock_current_user, auth_headers):
    """Test update with invalid data (bio too long)."""
    # Create user
    client.post("/api/v1/users", headers=auth_headers)
    
    # Try to update with bio > 500 chars
    update_data = {
        "bio": "x" * 501
    }
    response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)
    
    assert response.status_code == 422


def test_get_public_profile(mock_current_user, auth_headers):
    """Test getting another user's public profile."""
    # Create user
    create_response = client.post("/api/v1/users", headers=auth_headers)
    user_id = create_response.json()["id"]
    
    # Get public profile
    response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "email" not in data  # Email should NOT be in public response
    assert "keycloak_id" not in data  # Keycloak ID should NOT be exposed
    assert data["first_name"] == "John"


def test_get_public_profile_not_found(mock_current_user, auth_headers):
    """Test getting non-existent user profile."""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/users/{fake_uuid}", headers=auth_headers)
    
    assert response.status_code == 404


def test_missing_auth_header():
    """Test endpoints without Authorization header."""
    # Temporarily remove auth override to test real auth behavior
    original_override = app.dependency_overrides.get(get_current_user)
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/api/v1/users/me")
    assert response.status_code == 401  # No auth header returns 401 Unauthorized

    # Restore override for other tests
    if original_override:
        app.dependency_overrides[get_current_user] = original_override


def test_get_current_user_banned(mock_current_user, auth_headers):
    """Test GET /users/me when user is banned."""
    # Create user
    client.post("/api/v1/users", headers=auth_headers)

    # Manually ban the user in the database
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET is_banned = TRUE WHERE keycloak_id = 'test-keycloak-123'")
        )
        conn.commit()

    # Try to get profile
    response = client.get("/api/v1/users/me", headers=auth_headers)

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_update_profile_when_banned(mock_current_user, auth_headers):
    """Test PUT /users/me when user is banned."""
    # Create user
    client.post("/api/v1/users", headers=auth_headers)

    # Manually ban the user in the database
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET is_banned = TRUE WHERE keycloak_id = 'test-keycloak-123'")
        )
        conn.commit()

    # Try to update profile
    update_data = {
        "bio": "Trying to update while banned",
        "interests": ["hacking"]
    }
    response = client.put("/api/v1/users/me", json=update_data, headers=auth_headers)

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()
