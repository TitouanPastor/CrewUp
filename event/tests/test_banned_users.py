"""
Unit tests for banned user restrictions in Event Service.

Tests verify that banned users receive 403 Forbidden errors when trying
to perform write operations on events.
"""
import pytest
from unittest.mock import Mock
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from app.main import app
from app.db import get_db
from app.middleware.auth import get_current_user


@pytest.fixture
def banned_user():
    """Mock banned user."""
    return {
        "keycloak_id": "banned-user-123",
        "email": "banned@example.com",
        "first_name": "Banned",
        "last_name": "User"
    }


@pytest.fixture
def regular_user():
    """Mock regular (not banned) user."""
    return {
        "keycloak_id": "regular-user-456",
        "email": "regular@example.com",
        "first_name": "Regular",
        "last_name": "User"
    }


def create_mock_user_db_object(keycloak_id, is_banned=False):
    """Create a mock User database object."""
    user = Mock()
    user.id = uuid4()
    user.keycloak_id = keycloak_id
    user.email = f"{keycloak_id}@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_banned = is_banned
    user.profile_picture_url = None
    return user


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Automatically clean up dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


def test_banned_user_cannot_create_event(banned_user):
    """Banned user receives 403 when trying to create an event."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to create event
    event_data = {
        "name": "Test Event",
        "description": "Test Description",
        "event_type": "party",
        "address": "123 Test St",
        "latitude": 45.0,
        "longitude": -75.0,
        "event_start": "2025-12-15T18:00:00+00:00",
        "event_end": "2025-12-15T22:00:00+00:00"
    }

    response = client.post(
        "/api/v1/events",
        json=event_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_update_event(banned_user):
    """Banned user receives 403 when trying to update an event."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to update event
    event_id = uuid4()
    update_data = {
        "name": "Updated Event Name"
    }

    response = client.put(
        f"/api/v1/events/{event_id}",
        json=update_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_delete_event(banned_user):
    """Banned user receives 403 when trying to delete an event."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to delete event
    event_id = uuid4()

    response = client.delete(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_join_event(banned_user):
    """Banned user receives 403 when trying to join an event."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to join event
    event_id = uuid4()
    join_data = {
        "status": "going"
    }

    response = client.post(
        f"/api/v1/events/{event_id}/join",
        json=join_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_leave_event(banned_user):
    """Banned user receives 403 when trying to leave an event."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to leave event
    event_id = uuid4()

    response = client.delete(
        f"/api/v1/events/{event_id}/leave",
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_get_participants(banned_user):
    """Banned user receives 403 when trying to get event participants."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_banned_user_obj
        mock_db.query.return_value = mock_query
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Attempt to get participants
    event_id = uuid4()

    response = client.get(
        f"/api/v1/events/{event_id}/participants",
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user gets 403
    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_regular_user_can_create_event(regular_user):
    """Regular (non-banned) user can create events."""
    # Setup: Mock regular user and database
    mock_regular_user_obj = create_mock_user_db_object(regular_user["keycloak_id"], is_banned=False)

    # Mock event that will be "created"
    mock_event = Mock()
    mock_event.id = uuid4()
    mock_event.creator_id = mock_regular_user_obj.id
    mock_event.name = "Test Event"
    mock_event.description = "Test Description"
    mock_event.event_type = "party"
    mock_event.address = "123 Test St"
    mock_event.latitude = 45.0
    mock_event.longitude = -75.0
    mock_event.event_start = datetime.now(timezone.utc) + timedelta(days=13)
    mock_event.event_end = datetime.now(timezone.utc) + timedelta(days=13, hours=4)
    mock_event.max_attendees = None
    mock_event.is_public = True
    mock_event.is_cancelled = False
    mock_event.created_at = datetime.now(timezone.utc)
    mock_event.updated_at = datetime.now(timezone.utc)
    mock_event.__dict__ = {
        'id': mock_event.id,
        'creator_id': mock_event.creator_id,
        'name': mock_event.name,
        'description': mock_event.description,
        'event_type': mock_event.event_type,
        'address': mock_event.address,
        'latitude': mock_event.latitude,
        'longitude': mock_event.longitude,
        'event_start': mock_event.event_start,
        'event_end': mock_event.event_end,
        'max_attendees': mock_event.max_attendees,
        'is_public': mock_event.is_public,
        'is_cancelled': mock_event.is_cancelled,
        'created_at': mock_event.created_at,
        'updated_at': mock_event.updated_at
    }

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_regular_user_obj
        mock_query.filter.return_value.count.return_value = 0  # No participants yet
        mock_db.query.return_value = mock_query
        mock_db.add = Mock()
        mock_db.commit = Mock()

        # Mock refresh to set the id and timestamps
        def mock_refresh(obj):
            obj.id = mock_event.id
            obj.created_at = mock_event.created_at
            obj.updated_at = mock_event.updated_at

        mock_db.refresh = mock_refresh
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: regular_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # Create event
    event_data = {
        "name": "Test Event",
        "description": "Test Description",
        "event_type": "party",
        "address": "123 Test St",
        "latitude": 45.0,
        "longitude": -75.0,
        "event_start": "2025-12-15T18:00:00+00:00",
        "event_end": "2025-12-15T22:00:00+00:00"
    }

    response = client.post(
        "/api/v1/events",
        json=event_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Regular user succeeds
    assert response.status_code == 201


def test_banned_user_can_view_event(banned_user):
    """Banned user can still view events (read-only access)."""
    # Setup: Mock banned user and database
    mock_banned_user_obj = create_mock_user_db_object(banned_user["keycloak_id"], is_banned=True)

    # Mock event
    event_id = uuid4()
    mock_event = Mock()
    mock_event.id = event_id
    mock_event.creator_id = mock_banned_user_obj.id
    mock_event.name = "Test Event"
    mock_event.description = "Test Description"
    mock_event.event_type = "party"
    mock_event.address = "123 Test St"
    mock_event.latitude = 45.0
    mock_event.longitude = -75.0
    mock_event.event_start = datetime.now(timezone.utc) + timedelta(days=1)
    mock_event.event_end = datetime.now(timezone.utc) + timedelta(days=1, hours=2)
    mock_event.max_attendees = None
    mock_event.is_public = True
    mock_event.is_cancelled = False
    mock_event.created_at = datetime.now(timezone.utc)
    mock_event.updated_at = datetime.now(timezone.utc)

    # Mock database query
    def mock_get_db_dependency():
        mock_db = Mock()

        def mock_query_side_effect(model):
            mock_query = Mock()
            # User query
            if model.__name__ == "User":
                mock_query.filter.return_value.first.return_value = mock_banned_user_obj
            # Event query
            elif model.__name__ == "Event":
                mock_query.filter.return_value.first.return_value = mock_event
            # EventAttendee query (count)
            else:
                mock_query.filter.return_value.count.return_value = 0
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect
        return mock_db

    # Override dependencies
    app.dependency_overrides[get_current_user] = lambda: banned_user
    app.dependency_overrides[get_db] = mock_get_db_dependency

    # Test client
    client = TestClient(app)

    # View event (read-only)
    response = client.get(
        f"/api/v1/events/{event_id}",
        headers={"Authorization": "Bearer mock-token"}
    )

    # Assert: Banned user CAN view events (200)
    assert response.status_code == 200
