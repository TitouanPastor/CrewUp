"""Additional tests for users router to improve coverage."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


class MockQuery:
    """Mock SQLAlchemy Query."""

    def __init__(self, return_value=None):
        self._return_value = return_value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._return_value


def create_mock_user(user_id=None, keycloak_id=None, email="test@example.com"):
    """Create a mock User object."""
    user = Mock()
    user.id = user_id or uuid4()
    user.keycloak_id = keycloak_id or "test-keycloak-123"
    user.email = email
    user.first_name = "Test"
    user.last_name = "User"
    user.bio = None
    user.interests = []
    return user


class TestCreateUserEdgeCases:
    """Test edge cases in create_user endpoint."""

    def test_create_user_missing_email_in_token(self):
        """Test create_user when email missing from token."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        def override_get_current_user():
            return {
                "keycloak_id": "test-id",
                # Missing email
                "first_name": "Test",
                "last_name": "User"
            }

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post("/api/v1/users")

                assert response.status_code == 400
                assert "Email not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_create_user_integrity_error(self):
        """Test create_user with database integrity error."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        def override_get_current_user():
            return {
                "keycloak_id": "test-id",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            db.add = Mock()
            db.commit = Mock(side_effect=IntegrityError("", "", ""))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post("/api/v1/users")

                assert response.status_code == 409
                assert "already exists" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_create_user_generic_exception(self):
        """Test create_user with generic database error."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        def override_get_current_user():
            return {
                "keycloak_id": "test-id",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            db.add = Mock()
            db.commit = Mock(side_effect=Exception("Database connection lost"))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post("/api/v1/users")

                assert response.status_code == 500
                assert "Failed to create user" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestUpdateUserEdgeCases:
    """Test edge cases in update_user endpoint."""

    def test_update_user_generic_exception(self):
        """Test update_user with database error."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=mock_user)
            db.commit = Mock(side_effect=Exception("Database error"))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.put(
                    "/api/v1/users/me",
                    json={"bio": "Updated bio"}
                )

                assert response.status_code == 500
                assert "Failed to update" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_no_auth(self):
        """Test health endpoint works without authentication."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/users/health")

            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            assert response.json()["service"] == "user-service"


class TestUsersRoot:
    """Test users root endpoint."""

    def test_users_root_returns_endpoints(self):
        """Test users root returns available endpoints."""
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/v1/users")

            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "user-service"
            assert "endpoints" in data
            assert "POST /api/v1/users" in data["endpoints"]
