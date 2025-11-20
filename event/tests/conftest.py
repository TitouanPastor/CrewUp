"""
Pytest configuration and shared fixtures for Event Service tests.

Note: Unit tests test API layer without real database.
For full integration testing with database, see test_integration.py
"""
# IMPORTANT: Set test mode BEFORE importing app
# This ensures TESTING variable is read correctly during app initialization
import os
os.environ["TESTING"] = "true"

import pytest
from typing import Generator
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client() -> Generator:
    """
    Create a test client for API testing.
    Tests endpoints without requiring database connection.
    Test mode is enabled, so auth returns None (unauthenticated).
    """
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def mock_user():
    """Mock authenticated user for testing."""
    return {
        "keycloak_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser"
    }


@pytest.fixture
def mock_user2():
    """Second mock user for multi-user tests."""
    return {
        "keycloak_id": "660e8400-e29b-41d4-a716-446655440001",
        "email": "test2@example.com",
        "first_name": "Test",
        "last_name": "User2",
        "username": "testuser2"
    }


@pytest.fixture
def auth_headers(mock_user):
    """Mock authorization headers."""
    return {"Authorization": "Bearer mock-token"}


@pytest.fixture
def authed_client(mock_user):
    """
    Create a test client with mocked authentication.

    In test mode, get_current_user returns the MOCK_TEST_USER when a token is provided.
    Use this for testing endpoints that require authentication.
    """
    with TestClient(app, raise_server_exceptions=True) as test_client:
        # Add default authorization header for all requests
        test_client.headers = {"Authorization": "Bearer mock-test-token"}
        yield test_client


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
        "service_url": os.getenv("EVENT_SERVICE_URL", "http://localhost:8001"),
        "database_url": os.getenv("DATABASE_URL", "postgresql://crewup:crewup_dev_password@localhost:5432/crewup"),
    }
