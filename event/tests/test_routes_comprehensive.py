"""
Comprehensive tests for app/routers/events.py to achieve 70%+ coverage.

These tests focus on covering all business logic paths in the routes.
Uses TestClient with dependency overrides for proper testing.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from sqlalchemy.orm import Session


class MockQuery:
    """Mock SQLAlchemy Query object that properly chains methods."""

    def __init__(self, return_value=None, return_list=None, count_value=0):
        self._return_value = return_value
        self._return_list = return_list if return_list is not None else []
        self._count_value = count_value
        self._filters = []
        self._order = None
        self._limit = None
        self._offset = None

    def filter(self, *args, **kwargs):
        """Chain filter calls."""
        self._filters.append((args, kwargs))
        return self

    def first(self):
        """Return first result."""
        return self._return_value

    def all(self):
        """Return all results."""
        return self._return_list

    def count(self):
        """Return count."""
        return self._count_value

    def order_by(self, *args):
        """Chain order_by."""
        self._order = args
        return self

    def limit(self, n):
        """Chain limit."""
        self._limit = n
        return self

    def offset(self, n):
        """Chain offset."""
        self._offset = n
        return self

    def join(self, *args, **kwargs):
        """Chain join."""
        return self


def create_mock_user(user_id=None, keycloak_id=None):
    """Create a properly mocked User object."""
    user = Mock()
    user.id = user_id or uuid4()
    user.keycloak_id = keycloak_id or "550e8400-e29b-41d4-a716-446655440000"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    user.profile_picture_url = None
    user.bio = None
    user.interests = []
    user.reputation = 0.0
    user.is_active = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


class MockEvent:
    """Simple mock event class that allows attribute assignment."""
    pass


def create_mock_event(event_id=None, creator_id=None, **overrides):
    """Create a properly mocked Event object."""
    event = MockEvent()
    event.id = event_id or uuid4()
    event.creator_id = creator_id or uuid4()
    event.name = overrides.get('name', "Test Event")
    event.description = overrides.get('description', "Test Description")
    event.event_type = overrides.get('event_type', "concert")
    event.address = overrides.get('address', "123 Main St")
    event.latitude = overrides.get('latitude', None)
    event.longitude = overrides.get('longitude', None)
    event.event_start = overrides.get('event_start', datetime.now(timezone.utc) + timedelta(hours=2))
    event.event_end = overrides.get('event_end', datetime.now(timezone.utc) + timedelta(hours=4))
    event.max_attendees = overrides.get('max_attendees', None)
    event.is_public = overrides.get('is_public', True)
    event.is_cancelled = overrides.get('is_cancelled', False)
    event.created_at = datetime.now(timezone.utc)
    event.updated_at = datetime.now(timezone.utc)

    return event


def create_mock_attendee(user_id, event_id, status="going"):
    """Create a properly mocked EventAttendee object."""
    attendee = Mock()
    attendee.user_id = user_id
    attendee.event_id = event_id
    attendee.status = status
    attendee.created_at = datetime.now(timezone.utc)
    attendee.updated_at = datetime.now(timezone.utc)
    return attendee


class TestCreateEventRouteLogic:
    """Test all logic paths in create_event endpoint."""

    def test_create_event_with_description_and_location(self):
        """Test create event with optional fields."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id, "email": mock_user.email}

        def override_get_db():
            db = MagicMock(spec=Session)

            # Setup query responses
            queries = []

            def create_query(model):
                from app.db import User, EventAttendee

                if model == User:
                    q = MockQuery(return_value=mock_user)
                elif model == EventAttendee:
                    q = MockQuery(count_value=0)
                else:
                    q = MockQuery()

                queries.append(q)
                return q

            db.query = create_query
            db.add = Mock()
            db.commit = Mock()

            def mock_refresh(obj):
                obj.id = uuid4()
                obj.created_at = datetime.now(timezone.utc)
                obj.updated_at = datetime.now(timezone.utc)

            db.refresh = mock_refresh
            db.rollback = Mock()

            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                event_data = {
                    "name": "Concert Event",
                    "description": "A great concert",
                    "event_type": "concert",
                    "address": "456 Music Ave",
                    "latitude": "40.7128",
                    "longitude": "-74.0060",
                    "event_start": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
                    "event_end": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
                    "max_attendees": 100
                }

                response = client.post("/api/v1/events", json=event_data)

                # Should succeed
                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    def test_create_event_user_not_in_database(self):
        """Test create event when authenticated user doesn't have profile."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user", "email": "test@test.com"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                event_data = {
                    "name": "Test",
                    "address": "123 St",
                    "event_start": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
                    "event_end": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()
                }

                response = client.post("/api/v1/events", json=event_data)

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestGetEventRouteLogic:
    """Test all logic paths in get_event endpoint."""

    def test_get_event_with_user_attendance(self):
        """Test get event when current user is an attendee."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id)
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id, "going")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                from app.db import User, Event, EventAttendee

                call_count[0] += 1

                if call_count[0] == 1:  # User lookup
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:  # Event lookup
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [3, 4]:  # Attendee counts
                    return MockQuery(count_value=10)
                elif call_count[0] == 5:  # Current user attendance
                    return MockQuery(return_value=mock_attendee)
                elif call_count[0] == 6:  # Creator lookup
                    return MockQuery(return_value=mock_user)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["user_status"] == "going"
                assert data["participant_count"] == 10
        finally:
            app.dependency_overrides.clear()

    def test_get_event_with_max_attendees_full(self):
        """Test get event that has reached max capacity."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, max_attendees=10)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Going count = 10 (full)
                    return MockQuery(count_value=10)
                elif call_count[0] == 4:  # Interested count
                    return MockQuery(count_value=5)
                elif call_count[0] == 5:  # User attendance
                    return MockQuery(return_value=None)
                elif call_count[0] == 6:  # Creator
                    return MockQuery(return_value=mock_user)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 200
                data = response.json()
                assert data["is_full"] is True
                assert data["participant_count"] == 10
        finally:
            app.dependency_overrides.clear()

    def test_get_private_event_as_creator(self):
        """Test getting private event as the creator."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, is_public=False)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [3, 4]:
                    return MockQuery(count_value=0)
                elif call_count[0] == 5:
                    return MockQuery(return_value=None)
                elif call_count[0] == 6:
                    return MockQuery(return_value=mock_user)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}")

                # Creator can view their own private event
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_get_private_event_as_participant(self):
        """Test getting private event as a participant."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        different_creator = uuid4()
        mock_event = create_mock_event(creator_id=different_creator, is_public=False)
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Privacy check - is participant
                    return MockQuery(return_value=mock_attendee)
                elif call_count[0] in [4, 5]:  # Counts
                    return MockQuery(count_value=5)
                elif call_count[0] == 6:  # User attendance
                    return MockQuery(return_value=mock_attendee)
                elif call_count[0] == 7:  # Creator
                    creator = create_mock_user(user_id=different_creator)
                    return MockQuery(return_value=creator)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}")

                # Participant can view private event
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestUpdateEventRouteLogic:
    """Test all logic paths in update_event endpoint."""

    def test_update_event_no_fields(self):
        """Test update with no fields returns current event."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] in [1, 3]:  # User lookups
                    return MockQuery(return_value=mock_user)
                elif call_count[0] in [2, 4]:  # Event lookups
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [5, 6]:  # Counts
                    return MockQuery(count_value=0)
                elif call_count[0] == 7:  # Attendance
                    return MockQuery(return_value=None)
                elif call_count[0] == 8:  # Creator
                    return MockQuery(return_value=mock_user)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.put(f"/api/v1/events/{mock_event.id}", json={})

                # No-op update returns 200
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_update_event_ended(self):
        """Test update event that already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        past_time = datetime.now(timezone.utc) - timedelta(hours=5)
        mock_event = create_mock_event(
            creator_id=mock_user.id,
            event_start=past_time - timedelta(hours=2),
            event_end=past_time
        )

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"name": "New Name"}
                )

                assert response.status_code == 400
                assert "already started" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_update_event_start_validation(self):
        """Test update with invalid event_start."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            def create_query(model):
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Try to set event_start too soon
                soon_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"event_start": soon_time.isoformat()}
                )

                assert response.status_code == 400
                assert "30 minutes" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_update_event_uncancel_with_valid_time(self):
        """Test uncancelling event with valid future time."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(
            creator_id=mock_user.id,
            is_cancelled=True,
            event_start=datetime.now(timezone.utc) + timedelta(hours=2)
        )

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] in [1, 3]:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] in [2, 4]:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [5, 6]:
                    return MockQuery(count_value=0)
                elif call_count[0] == 7:
                    return MockQuery(return_value=None)
                elif call_count[0] == 8:
                    return MockQuery(return_value=mock_user)
                else:
                    return MockQuery()

            db.query = create_query
            db.commit = Mock()
            db.refresh = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"is_cancelled": False}
                )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_update_event_lat_lng_together(self):
        """Test updating latitude requires longitude."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, latitude=None, longitude=None)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Try to set only latitude
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"latitude": "40.7128"}
                )

                assert response.status_code == 422
                assert "latitude and longitude" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_update_event_reduce_max_attendees_validation(self):
        """Test reducing max_attendees below current participants."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, max_attendees=50)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                from app.db import EventAttendee
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Current going count = 30
                    return MockQuery(count_value=30)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Try to reduce to 20 when 30 people already going
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"max_attendees": 20}
                )

                assert response.status_code == 400
                assert "Cannot reduce max_attendees" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_update_event_end_before_start(self):
        """Test updating event_end to before event_start."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Set end before current start
                new_end = mock_event.event_start - timedelta(hours=1)
                response = client.put(
                    f"/api/v1/events/{mock_event.id}",
                    json={"event_end": new_end.isoformat()}
                )

                assert response.status_code == 422
                assert "event_end" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestDeleteEventRouteLogic:
    """Test all logic paths in delete_event endpoint."""

    def test_delete_event_not_found(self):
        """Test delete non-existent event."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{uuid4()}")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_already_ended(self):
        """Test delete event that already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        mock_event = create_mock_event(
            creator_id=mock_user.id,
            event_start=past_time - timedelta(hours=2),
            event_end=past_time,
            is_cancelled=False
        )

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 400
                assert "already started" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


class TestJoinEventRouteLogic:
    """Test all logic paths in join_event endpoint."""

    def test_join_event_already_ended(self):
        """Test joining event that already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_event = create_mock_event(
            is_cancelled=False,
            event_start=past_time - timedelta(hours=2),
            event_end=past_time
        )

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(f"/api/v1/events/{mock_event.id}/join")

                assert response.status_code == 400
                assert "already started" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_full(self):
        """Test joining event at capacity."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(is_cancelled=False, max_attendees=10)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                from app.db import EventAttendee
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Existing attendee check
                    return MockQuery(return_value=None)
                elif call_count[0] == 4:  # Going count = 10
                    return MockQuery(count_value=10)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/v1/events/{mock_event.id}/join",
                    json={"status": "going"}
                )

                assert response.status_code == 400
                assert "full" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_update_existing_attendance(self):
        """Test updating existing attendance status."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(is_cancelled=False, max_attendees=10)
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id, "interested")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Existing attendee - yes
                    return MockQuery(return_value=mock_attendee)
                elif call_count[0] == 4:  # Going count
                    return MockQuery(count_value=5)
                else:
                    return MockQuery()

            db.query = create_query
            db.commit = Mock()
            db.add = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Change from interested to going
                response = client.post(
                    f"/api/v1/events/{mock_event.id}/join",
                    json={"status": "going"}
                )

                assert response.status_code == 200
                assert "joined event" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_already_going_idempotent(self):
        """Test joining when already going (idempotent)."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(is_cancelled=False, max_attendees=10)
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id, "going")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Existing attendee - going
                    return MockQuery(return_value=mock_attendee)
                elif call_count[0] == 4:  # Going count (will subtract 1 for self)
                    return MockQuery(count_value=5)
                else:
                    return MockQuery()

            db.query = create_query
            db.commit = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Join when already going
                response = client.post(
                    f"/api/v1/events/{mock_event.id}/join",
                    json={"status": "going"}
                )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestLeaveEventRouteLogic:
    """Test all logic paths in leave_event endpoint."""

    def test_leave_event_already_ended(self):
        """Test leaving event that already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_event = create_mock_event(
            event_start=past_time - timedelta(hours=2),
            event_end=past_time
        )

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                return MockQuery(return_value=mock_user if call_count[0] == 1 else mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}/leave")

                assert response.status_code == 400
                assert "already started" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_leave_event_already_not_going(self):
        """Test leaving when already marked as not_going (idempotent)."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event()
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id, "not_going")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:
                    return MockQuery(return_value=mock_attendee)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}/leave")

                assert response.status_code == 200
                assert "left event" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()

    def test_leave_event_success(self):
        """Test successfully leaving an event."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event()
        mock_attendee = create_mock_attendee(mock_user.id, mock_event.id, "going")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:
                    return MockQuery(return_value=mock_attendee)
                else:
                    return MockQuery()

            db.query = create_query
            db.commit = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}/leave")

                assert response.status_code == 200
                assert "left event" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()


class TestListEventsRouteLogic:
    """Test all logic paths in list_events endpoint."""

    def test_list_events_with_user_status_filter(self):
        """Test list events filtered by user's RSVP status."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        mock_user = create_mock_user()
        mock_events = [create_mock_event() for _ in range(3)]

        def override_get_optional_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            # Create a query that properly chains
            query = MockQuery(return_list=mock_events, count_value=3)
            query_with_user = MockQuery(return_value=mock_user)

            call_count = [0]

            def create_query(model):
                from app.db import User, Event
                call_count[0] += 1

                if model == User:
                    return query_with_user
                elif model == Event:
                    return query
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/events?status=going")

                # Should require auth
                assert response.status_code in [200, 401]
        finally:
            app.dependency_overrides.clear()

    def test_list_events_with_creator_filter(self):
        """Test list events by creator."""
        from app.main import app
        from app.db import get_db

        creator_id = uuid4()
        mock_events = [create_mock_event(creator_id=creator_id) for _ in range(2)]

        def override_get_db():
            db = MagicMock(spec=Session)
            query = MockQuery(return_list=mock_events, count_value=2)
            db.query = lambda model: query
            return db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events?creator_id={creator_id}")

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_list_events_location_filtering(self):
        """Test list events with location filter."""
        from app.main import app
        from app.db import get_db

        # Create events with coordinates
        event1 = create_mock_event(latitude=40.7128, longitude=-74.0060)
        event2 = create_mock_event(latitude=40.7589, longitude=-73.9851)
        mock_events = [event1, event2]

        def override_get_db():
            db = MagicMock(spec=Session)
            query = MockQuery(return_list=mock_events, count_value=2)
            db.query = lambda model: query
            return db

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Search near NYC
                response = client.get("/api/v1/events?latitude=40.7128&longitude=-74.0060&radius_km=10")

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()


class TestGetParticipantsRouteLogic:
    """Test all logic paths in get_participants endpoint."""

    def test_get_participants_private_event_as_non_participant(self):
        """Test getting participants of private event as non-participant."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        different_creator = uuid4()
        mock_event = create_mock_event(creator_id=different_creator, is_public=False)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] == 3:  # Privacy check - not participant
                    return MockQuery(return_value=None)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}/participants")

                assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_with_details(self):
        """Test getting participants with full details."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, is_public=True)
        attendees = [create_mock_attendee(uuid4(), mock_event.id) for _ in range(5)]

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                from app.db import EventAttendee, User
                call_count[0] += 1

                if call_count[0] == 1:  # User
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:  # Event
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [3, 4]:  # Counts
                    return MockQuery(count_value=5)
                elif call_count[0] == 5:  # Attendee query for pagination
                    return MockQuery(return_list=attendees, count_value=5)
                else:  # User lookups for each attendee
                    return MockQuery(return_value=mock_user)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(
                    f"/api/v1/events/{mock_event.id}/participants?include_details=true"
                )

                assert response.status_code == 200
                data = response.json()
                assert "attendees" in data
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_without_details_with_status_filter(self):
        """Test getting participant counts with status filter."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = create_mock_user()
        mock_event = create_mock_event(creator_id=mock_user.id, is_public=True)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1

                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                elif call_count[0] == 2:
                    return MockQuery(return_value=mock_event)
                elif call_count[0] in [3, 4, 5]:  # Counts
                    return MockQuery(count_value=10)
                else:
                    return MockQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(
                    f"/api/v1/events/{mock_event.id}/participants?status=going&include_details=false"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["attendees"] is None
                assert "going_count" in data
        finally:
            app.dependency_overrides.clear()
