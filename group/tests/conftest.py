"""
Pytest configuration and shared fixtures for Group & Chat Service tests.

Note: Unit tests test API layer without real database.
For full integration testing with database, see test_integration.py
"""
import pytest
import os
from typing import Generator
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client() -> Generator:
    """
    Create a test client for API testing.
    Tests endpoints without requiring database connection.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_user():
    """Mock authenticated user for testing."""
    return {
        "keycloak_id": str(uuid4()),
        "email": "test@example.com",
        "sub": str(uuid4()),
        "preferred_username": "testuser"
    }


@pytest.fixture
def mock_user2():
    """Second mock user for multi-user tests."""
    return {
        "keycloak_id": str(uuid4()),
        "email": "test2@example.com",
        "sub": str(uuid4()),
        "preferred_username": "testuser2"
    }


@pytest.fixture
def auth_headers(mock_user):
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
        "service_url": os.getenv("GROUP_SERVICE_URL", "http://localhost:8002"),
    }
