"""
Comprehensive tests for event routes to increase coverage.
Focuses on error paths and edge cases not covered by existing tests.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ==================== Helper Classes ====================

class MockQuery:
    """Mock SQLAlchemy Query object that properly chains methods."""

    def __init__(self, return_value=None, return_list=None, count_value=0):
        self._return_value = return_value
        self._return_list = return_list if return_list is not None else []
        self._count_value = count_value

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._return_value

    def all(self):
        return self._return_list

    def count(self):
        return self._count_value

    def order_by(self, *args):
        return self

    def limit(self, n):
        return self

    def offset(self, n):
        return self


class MockUser:
    """Simple mock user class."""
    def __init__(self, user_id=None, keycloak_id=None):
        self.id = user_id or uuid4()
        self.keycloak_id = keycloak_id or "test-keycloak-id"
        self.email = "test@example.com"
        self.first_name = "Test"
        self.last_name = "User"
        self.profile_picture_url = None


class MockEvent:
    """Simple mock event class."""
    def __init__(self, event_id=None, creator_id=None, **kwargs):
        self.id = event_id or uuid4()
        self.creator_id = creator_id or uuid4()
        self.name = kwargs.get('name', "Test Event")
        self.description = kwargs.get('description', "Test Description")
        self.event_type = kwargs.get('event_type', "concert")
        self.address = kwargs.get('address', "123 Test St")
        self.latitude = kwargs.get('latitude', None)
        self.longitude = kwargs.get('longitude', None)
        self.event_start = kwargs.get('event_start', datetime.now(timezone.utc) + timedelta(hours=2))
        self.event_end = kwargs.get('event_end', datetime.now(timezone.utc) + timedelta(hours=4))
        self.max_attendees = kwargs.get('max_attendees', None)
        self.is_public = kwargs.get('is_public', True)
        self.is_cancelled = kwargs.get('is_cancelled', False)
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


class MockAttendee:
    """Simple mock attendee class."""
    def __init__(self, user_id, event_id, status="going"):
        self.user_id = user_id
        self.event_id = event_id
        self.status = status
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


# ==================== get_event Tests ====================

class TestGetEventCoverage:
    """Tests for get_event endpoint coverage gaps."""

    def test_get_event_user_not_found(self):
        """Test get_event when user profile doesn't exist in database."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{event_id}")

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_event_event_not_found(self):
        """Test get_event when event doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{event_id}")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_event_private_event_access_denied(self):
        """Test get_event returns 404 for private event when user is not participant."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        other_user = MockUser()
        mock_event = MockEvent(creator_id=other_user.id, is_public=False)

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
                    # Check for participant - return None (not a participant)
                    return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== delete_event Tests ====================

class TestDeleteEventCoverage:
    """Tests for delete_event endpoint coverage gaps."""

    def test_delete_event_user_not_found(self):
        """Test delete_event when user profile doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{event_id}")

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_event_not_found(self):
        """Test delete_event when event doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{event_id}")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_not_creator(self):
        """Test delete_event when user is not the creator."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        other_user = MockUser()
        mock_event = MockEvent(creator_id=other_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 403
                assert "Only the event creator" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_already_cancelled(self):
        """Test delete_event when event is already cancelled (idempotent)."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(creator_id=mock_user.id, is_cancelled=True)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 200
                assert "deleted successfully" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_already_started(self):
        """Test delete_event when event has already started."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(
            creator_id=mock_user.id,
            event_start=datetime.now(timezone.utc) - timedelta(hours=1)
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
                return MockQuery(return_value=mock_event)

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

    def test_delete_event_already_ended(self):
        """Test delete_event when event has already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(
            creator_id=mock_user.id,
            event_start=datetime.now(timezone.utc) + timedelta(hours=2),
            event_end=datetime.now(timezone.utc) - timedelta(hours=1)
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
                return MockQuery(return_value=mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 400
                assert "already ended" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_delete_event_db_exception(self):
        """Test delete_event when database throws an exception."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=mock_event)

            db.query = create_query
            db.commit = Mock(side_effect=Exception("Database error"))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}")

                assert response.status_code == 500
                assert "Failed to delete event" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== join_event Tests ====================

class TestJoinEventCoverage:
    """Tests for join_event endpoint coverage gaps."""

    def test_join_event_user_not_found(self):
        """Test join_event when user profile doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(f"/api/v1/events/{event_id}/join")

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_event_not_found(self):
        """Test join_event when event doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(f"/api/v1/events/{event_id}/join")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_cancelled_event(self):
        """Test join_event when event is cancelled."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(is_cancelled=True)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(f"/api/v1/events/{mock_event.id}/join")

                assert response.status_code == 400
                assert "cancelled event" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_new_attendee(self):
        """Test join_event creates new attendee record."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent()

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
                    # Going count for capacity check
                    return MockQuery(count_value=0)
                else:
                    # No existing attendee
                    return MockQuery(return_value=None)

            db.query = create_query
            db.add = Mock()
            db.commit = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/v1/events/{mock_event.id}/join",
                    json={"status": "going"}
                )

                assert response.status_code == 200
                assert "Successfully joined" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()

    def test_join_event_db_exception(self):
        """Test join_event when database throws an exception."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent()

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
                    return MockQuery(count_value=0)
                return MockQuery(return_value=None)

            db.query = create_query
            db.add = Mock()
            db.commit = Mock(side_effect=Exception("Database error"))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(f"/api/v1/events/{mock_event.id}/join")

                assert response.status_code == 500
                assert "Failed to join event" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== leave_event Tests ====================

class TestLeaveEventCoverage:
    """Tests for leave_event endpoint coverage gaps."""

    def test_leave_event_user_not_found(self):
        """Test leave_event when user profile doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{event_id}/leave")

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_leave_event_event_not_found(self):
        """Test leave_event when event doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{event_id}/leave")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_leave_event_already_started(self):
        """Test leave_event when event has already started."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(
            event_start=datetime.now(timezone.utc) - timedelta(hours=1)
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
                return MockQuery(return_value=mock_event)

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

    def test_leave_event_already_ended(self):
        """Test leave_event when event has already ended."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(
            event_start=datetime.now(timezone.utc) + timedelta(hours=2),
            event_end=datetime.now(timezone.utc) - timedelta(hours=1)
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
                return MockQuery(return_value=mock_event)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.delete(f"/api/v1/events/{mock_event.id}/leave")

                assert response.status_code == 400
                assert "already ended" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== list_events Tests ====================

class TestListEventsCoverage:
    """Tests for list_events endpoint coverage gaps."""

    def test_list_events_empty_date_range(self):
        """Test list_events returns empty when start_date_from > start_date_to."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        def override_get_optional_current_user():
            return None

        def override_get_db():
            db = MagicMock(spec=Session)
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # start_date_from is after start_date_to (use simple date format)
                future_date = "2025-12-15T12:00:00"
                past_date = "2025-12-01T12:00:00"

                response = client.get(
                    f"/api/v1/events?start_date_from={future_date}&start_date_to={past_date}"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["events"] == []
                assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()

    def test_list_events_with_is_public_filter(self):
        """Test list_events with is_public filter for authenticated user."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        mock_user = MockUser()
        mock_event = MockEvent(is_public=True)

        def override_get_optional_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            class ChainableQuery:
                def __init__(self, return_list=None, return_value=None):
                    self._return_list = return_list or []
                    self._return_value = return_value

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return len(self._return_list)

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                from app.db import Event, User, EventAttendee

                if model == User:
                    return ChainableQuery(return_value=mock_user)
                elif model == Event:
                    return ChainableQuery(return_list=[mock_event])
                elif model == EventAttendee:
                    return ChainableQuery(return_list=[])
                return ChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/events?is_public=true")

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_list_events_with_date_filters(self):
        """Test list_events with start_date_from and start_date_to filters."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        mock_event = MockEvent(is_public=True)

        def override_get_optional_current_user():
            return None

        def override_get_db():
            db = MagicMock(spec=Session)

            class ChainableQuery:
                def __init__(self, return_list=None, return_value=None):
                    self._return_list = return_list or []
                    self._return_value = return_value

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return len(self._return_list)

            def create_query(model):
                from app.db import Event, User, EventAttendee

                if model == Event:
                    return ChainableQuery(return_list=[mock_event])
                elif model == User:
                    return ChainableQuery(return_value=MockUser())
                elif model == EventAttendee:
                    return ChainableQuery(return_list=[])
                return ChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Use simple date format without timezone
                from_date = "2025-12-01T12:00:00"
                to_date = "2025-12-30T12:00:00"

                response = client.get(
                    f"/api/v1/events?start_date_from={from_date}&start_date_to={to_date}"
                )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_list_events_private_event_filtered(self):
        """Test list_events filters out private events user can't access."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        mock_user = MockUser()
        other_user = MockUser()
        # Private event created by another user
        private_event = MockEvent(creator_id=other_user.id, is_public=False)

        def override_get_optional_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            class ChainableQuery:
                def __init__(self, return_list=None, return_value=None, count_val=0):
                    self._return_list = return_list or []
                    self._return_value = return_value
                    self._count_val = count_val

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return self._count_val

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                from app.db import Event, User, EventAttendee

                if model == User:
                    return ChainableQuery(return_value=mock_user)
                elif model == Event:
                    return ChainableQuery(return_list=[private_event], count_val=1)
                elif model == EventAttendee:
                    # User is not a participant
                    return ChainableQuery(return_value=None, count_val=0)
                return ChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/events")

                assert response.status_code == 200
                # Private event should be filtered out
                data = response.json()
                assert len(data["events"]) == 0
        finally:
            app.dependency_overrides.clear()

    def test_list_events_is_full_calculation(self):
        """Test list_events correctly calculates is_full for events with max_attendees."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        mock_event = MockEvent(is_public=True, max_attendees=10)

        def override_get_optional_current_user():
            return None

        def override_get_db():
            db = MagicMock(spec=Session)

            class ChainableQuery:
                def __init__(self, return_list=None, return_value=None, count_val=0):
                    self._return_list = return_list or []
                    self._return_value = return_value
                    self._count_val = count_val

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return self._count_val

            def create_query(model):
                from app.db import Event, User, EventAttendee

                if model == Event:
                    return ChainableQuery(return_list=[mock_event], count_val=1)
                elif model == User:
                    return ChainableQuery(return_value=MockUser())
                elif model == EventAttendee:
                    # 10 going (same as max_attendees), so event is full
                    return ChainableQuery(return_list=[], count_val=10)
                return ChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/events")

                assert response.status_code == 200
                data = response.json()
                if len(data["events"]) > 0:
                    assert data["events"][0]["is_full"] == True
        finally:
            app.dependency_overrides.clear()

    def test_list_events_db_exception(self):
        """Test list_events when database throws an exception."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_optional_current_user

        def override_get_optional_current_user():
            return None

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = Mock(side_effect=Exception("Database error"))
            return db

        app.dependency_overrides[get_optional_current_user] = override_get_optional_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get("/api/v1/events")

                assert response.status_code == 500
                assert "Failed to list events" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== get_participants Tests ====================

class TestGetParticipantsCoverage:
    """Tests for get_participants endpoint coverage gaps."""

    def test_get_participants_user_not_found(self):
        """Test get_participants when user profile doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": "non-existent-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = lambda model: MockQuery(return_value=None)
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{event_id}/participants")

                assert response.status_code == 404
                assert "User profile not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_event_not_found(self):
        """Test get_participants when event doesn't exist."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        event_id = uuid4()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)
            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                if call_count[0] == 1:
                    return MockQuery(return_value=mock_user)
                return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{event_id}/participants")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_private_event_access_denied(self):
        """Test get_participants returns 404 for private event when user is not participant."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        other_user = MockUser()
        mock_event = MockEvent(creator_id=other_user.id, is_public=False)

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
                    # Check for participant - return None (not a participant)
                    return MockQuery(return_value=None)

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}/participants")

                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_invalid_status_filter(self):
        """Test get_participants with invalid attendee_status filter."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            class FullChainableQuery:
                def __init__(self, return_list=None, return_value=None, count_val=0):
                    self._return_list = return_list or []
                    self._return_value = return_value
                    self._count_val = count_val

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return self._count_val

            def create_query(model):
                from app.db import User, Event, EventAttendee

                if model == User:
                    return FullChainableQuery(return_value=mock_user)
                elif model == Event:
                    return FullChainableQuery(return_value=mock_event)
                elif model == EventAttendee:
                    return FullChainableQuery(count_val=0)
                return FullChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Use 'status' (the alias) instead of 'attendee_status'
                response = client.get(
                    f"/api/v1/events/{mock_event.id}/participants?status=invalid_status"
                )

                assert response.status_code == 422
                assert "Invalid status" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_with_status_filter(self):
        """Test get_participants with valid attendee_status filter."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(creator_id=mock_user.id)
        mock_attendee = MockAttendee(user_id=mock_user.id, event_id=mock_event.id, status="going")

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            class ChainableQuery:
                def __init__(self, return_list=None, return_value=None, count_val=0):
                    self._return_list = return_list or []
                    self._return_value = return_value
                    self._count_val = count_val

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def asc(self):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return self._count_val

            call_count = [0]

            def create_query(model):
                call_count[0] += 1
                from app.db import User, Event, EventAttendee

                if model == User:
                    return ChainableQuery(return_value=mock_user)
                elif model == Event:
                    return ChainableQuery(return_value=mock_event)
                elif model == EventAttendee:
                    return ChainableQuery(return_list=[mock_attendee], count_val=1)
                return ChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                # Use 'status' (the alias) instead of 'attendee_status'
                response = client.get(
                    f"/api/v1/events/{mock_event.id}/participants?status=going&include_details=true"
                )

                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_total_calculation(self):
        """Test get_participants returns total_participants (going + interested)."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()
        mock_event = MockEvent(creator_id=mock_user.id)

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id}

        def override_get_db():
            db = MagicMock(spec=Session)

            class FullChainableQuery:
                def __init__(self, return_list=None, return_value=None, count_val=0):
                    self._return_list = return_list or []
                    self._return_value = return_value
                    self._count_val = count_val

                def filter(self, *args, **kwargs):
                    return self

                def order_by(self, *args):
                    return self

                def limit(self, n):
                    return self

                def offset(self, n):
                    return self

                def all(self):
                    return self._return_list

                def first(self):
                    return self._return_value

                def count(self):
                    return self._count_val

            def create_query(model):
                from app.db import User, Event, EventAttendee

                if model == User:
                    return FullChainableQuery(return_value=mock_user)
                elif model == Event:
                    return FullChainableQuery(return_value=mock_event)
                elif model == EventAttendee:
                    # Both going and interested return 5 each
                    return FullChainableQuery(count_val=5)
                return FullChainableQuery()

            db.query = create_query
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.get(f"/api/v1/events/{mock_event.id}/participants")

                assert response.status_code == 200
                data = response.json()
                # Verify the response structure contains total_participants
                assert "total_participants" in data
                # going_count (5) + interested_count (5) = 10
                assert data["total_participants"] == 10
        finally:
            app.dependency_overrides.clear()

    def test_get_participants_db_exception(self):
        """Test get_participants when database throws an exception."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        def override_get_current_user():
            return {"keycloak_id": "test-user"}

        def override_get_db():
            db = MagicMock(spec=Session)
            db.query = Mock(side_effect=Exception("Database error"))
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                event_id = uuid4()
                response = client.get(f"/api/v1/events/{event_id}/participants")

                assert response.status_code == 500
                assert "Failed to retrieve event participants" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()


# ==================== create_event Exception Test ====================

class TestCreateEventCoverage:
    """Tests for create_event endpoint coverage gaps."""

    def test_create_event_db_exception(self):
        """Test create_event when database throws an exception."""
        from app.main import app
        from app.db import get_db
        from app.middleware import get_current_user

        mock_user = MockUser()

        def override_get_current_user():
            return {"keycloak_id": mock_user.keycloak_id, "email": mock_user.email}

        def override_get_db():
            db = MagicMock(spec=Session)

            def create_query(model):
                return MockQuery(return_value=mock_user)

            db.query = create_query
            db.add = Mock()
            db.commit = Mock(side_effect=Exception("Database error"))
            db.rollback = Mock()
            return db

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                event_data = {
                    "name": "Test Event",
                    "event_type": "concert",
                    "address": "123 Test St",
                    "event_start": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
                    "event_end": (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat(),
                }

                response = client.post("/api/v1/events", json=event_data)

                assert response.status_code == 500
                assert "Failed to create event" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()
