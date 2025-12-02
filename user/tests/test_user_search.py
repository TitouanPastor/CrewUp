"""
Unit and integration tests for user search endpoint.

Tests cover:
- Successful search by first name, last name, email
- Case-insensitive search
- Partial match search
- Empty query validation
- Multiple results
- No results found
- Result limit (50 users max)
- Ban status included in results
- Authentication required
"""
import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.db.database import Base, get_db
from app.db.models import User
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
        "keycloak_id": "test-search-user-123",
        "email": "searcher@example.com",
        "first_name": "Test",
        "last_name": "Searcher",
        "username": "testsearcher"
    }


# Test client
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """
    Ensure tables exist before tests.
    Does NOT drop tables - keeps data intact for other services.
    """
    # Save existing overrides
    original_overrides = app.dependency_overrides.copy()

    # Set up dependency overrides for this test module
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    # Create uuid extension if not exists
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    yield

    # Cleanup: Only delete test user data
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE keycloak_id LIKE 'test-search-%'"))
        conn.commit()

    # Restore original dependency overrides
    app.dependency_overrides = original_overrides


@pytest.fixture
def db_session():
    """Provide a database session for test setup."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_users(db_session):
    """Create sample users for search testing."""
    users = [
        User(
            keycloak_id="test-search-alice-001",
            email="alice@example.com",
            first_name="Alice",
            last_name="Anderson",
            is_banned=False,
            is_active=True
        ),
        User(
            keycloak_id="test-search-bob-002",
            email="bob@example.com",
            first_name="Bob",
            last_name="Brown",
            is_banned=True,  # Banned user
            is_active=True
        ),
        User(
            keycloak_id="test-search-charlie-003",
            email="charlie.davis@example.com",
            first_name="Charlie",
            last_name="Davis",
            is_banned=False,
            is_active=True
        ),
        User(
            keycloak_id="test-search-diana-004",
            email="diana@test.com",
            first_name="Diana",
            last_name="Evans",
            is_banned=False,
            is_active=False  # Inactive user
        ),
        User(
            keycloak_id="test-search-alice-005",
            email="alice.wilson@example.com",
            first_name="Alice",
            last_name="Wilson",  # Another Alice
            is_banned=False,
            is_active=True
        ),
    ]

    for user in users:
        db_session.add(user)

    db_session.commit()

    for user in users:
        db_session.refresh(user)

    return users


@pytest.fixture
def auth_headers():
    """Mock authorization headers."""
    return {"Authorization": "Bearer fake-token-for-testing"}


# ==================== Success Cases ====================

def test_search_by_first_name(sample_users, auth_headers):
    """Test searching users by first name."""
    response = client.get("/api/v1/users/search?query=Alice", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "users" in data
    assert "total" in data
    assert data["total"] == 2  # Two Alices

    # Verify both Alices are returned
    first_names = [user["first_name"] for user in data["users"]]
    assert first_names.count("Alice") == 2


def test_search_by_last_name(sample_users, auth_headers):
    """Test searching users by last name."""
    response = client.get("/api/v1/users/search?query=Brown", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["users"][0]["last_name"] == "Brown"
    assert data["users"][0]["first_name"] == "Bob"


def test_search_by_email(sample_users, auth_headers):
    """Test searching users by email."""
    response = client.get("/api/v1/users/search?query=charlie.davis@example.com", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    assert data["users"][0]["email"] == "charlie.davis@example.com"
    assert data["users"][0]["first_name"] == "Charlie"


def test_search_partial_match(sample_users, auth_headers):
    """Test searching with partial match."""
    response = client.get("/api/v1/users/search?query=ali", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should match both Alice users
    assert data["total"] == 2
    for user in data["users"]:
        assert "ali" in user["first_name"].lower() or "ali" in user["email"].lower()


def test_search_case_insensitive(sample_users, auth_headers):
    """Test that search is case-insensitive."""
    # Test uppercase
    response1 = client.get("/api/v1/users/search?query=ALICE", headers=auth_headers)
    # Test lowercase
    response2 = client.get("/api/v1/users/search?query=alice", headers=auth_headers)
    # Test mixed case
    response3 = client.get("/api/v1/users/search?query=AlIcE", headers=auth_headers)

    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200

    # All should return the same results
    data1 = response1.json()
    data2 = response2.json()
    data3 = response3.json()

    assert data1["total"] == data2["total"] == data3["total"] == 2


def test_search_returns_ban_status(sample_users, auth_headers):
    """Test that search results include ban status."""
    response = client.get("/api/v1/users/search?query=Bob", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    user = data["users"][0]

    # Verify all required fields are present
    assert "id" in user
    assert "keycloak_id" in user
    assert "email" in user
    assert "first_name" in user
    assert "last_name" in user
    assert "is_banned" in user
    assert "is_active" in user

    # Bob is banned
    assert user["is_banned"] is True
    assert user["first_name"] == "Bob"


def test_search_returns_active_status(sample_users, auth_headers):
    """Test that search results include active status."""
    response = client.get("/api/v1/users/search?query=Diana", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 1
    user = data["users"][0]

    # Diana is inactive
    assert user["is_active"] is False
    assert user["first_name"] == "Diana"


def test_search_by_email_domain(sample_users, auth_headers):
    """Test searching by email domain."""
    response = client.get("/api/v1/users/search?query=example.com", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should match all users with @example.com
    assert data["total"] >= 4
    for user in data["users"]:
        assert "example.com" in user["email"]


def test_search_no_results(sample_users, auth_headers):
    """Test search with no matching results."""
    response = client.get("/api/v1/users/search?query=NonExistentUser", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["users"] == []


def test_search_with_whitespace(sample_users, auth_headers):
    """Test search with leading/trailing whitespace."""
    response = client.get("/api/v1/users/search?query=  Alice  ", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should trim whitespace and find results
    assert data["total"] == 2


# ==================== Error Cases ====================

def test_search_empty_query(auth_headers):
    """Test search with empty query."""
    response = client.get("/api/v1/users/search?query=", headers=auth_headers)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_whitespace_only_query(auth_headers):
    """Test search with whitespace-only query."""
    response = client.get("/api/v1/users/search?query=   ", headers=auth_headers)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_search_missing_query_parameter(auth_headers):
    """Test search without query parameter."""
    response = client.get("/api/v1/users/search", headers=auth_headers)

    assert response.status_code == 422  # Validation error


def test_search_requires_authentication():
    """Test that search endpoint requires authentication."""
    # No override_get_current_user for this test
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/api/v1/users/search?query=Alice")

    # Should fail without authentication
    assert response.status_code == 401

    # Restore override
    app.dependency_overrides[get_current_user] = override_get_current_user


# ==================== Edge Cases ====================

def test_search_special_characters(sample_users, auth_headers):
    """Test search with special characters in query."""
    # Should not crash, just return no results if no match
    response = client.get("/api/v1/users/search?query=@#$%", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    # May or may not find results depending on data
    assert "users" in data
    assert "total" in data


def test_search_sql_injection_protection(sample_users, auth_headers):
    """Test that search is protected against SQL injection."""
    # Try SQL injection attack
    response = client.get("/api/v1/users/search?query=' OR '1'='1", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should not return all users (SQL injection would do that)
    # Should treat it as a literal string search
    assert data["total"] == 0  # No user with this in their name/email


def test_search_result_limit(db_session, auth_headers):
    """Test that search limits results to 50 users."""
    # Create 60 test users with similar names
    users = []
    for i in range(60):
        user = User(
            keycloak_id=f"test-search-limit-{i:03d}",
            email=f"testlimit{i}@example.com",
            first_name="TestLimit",
            last_name=f"User{i}",
            is_banned=False,
            is_active=True
        )
        users.append(user)
        db_session.add(user)

    db_session.commit()

    # Search for all TestLimit users
    response = client.get("/api/v1/users/search?query=TestLimit", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should limit to 50 results
    assert data["total"] == 50
    assert len(data["users"]) == 50

    # Cleanup
    for user in users:
        db_session.delete(user)
    db_session.commit()


def test_search_returns_all_required_fields(sample_users, auth_headers):
    """Test that all required fields are returned in search results."""
    response = client.get("/api/v1/users/search?query=Alice", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["total"] > 0
    user = data["users"][0]

    # Verify all required fields
    required_fields = ["id", "keycloak_id", "email", "first_name", "last_name", "is_banned", "is_active"]
    for field in required_fields:
        assert field in user, f"Missing required field: {field}"


def test_search_multiple_words(sample_users, auth_headers):
    """Test searching with multiple words."""
    response = client.get("/api/v1/users/search?query=Alice Anderson", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should search for the entire string "Alice Anderson"
    # May or may not match depending on how the query is constructed
    # The current implementation will search for exact partial match
    assert "users" in data
    assert "total" in data


def test_search_numeric_query(sample_users, auth_headers):
    """Test searching with numeric query."""
    response = client.get("/api/v1/users/search?query=123", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Should not crash, may or may not find results
    assert "users" in data
    assert "total" in data
