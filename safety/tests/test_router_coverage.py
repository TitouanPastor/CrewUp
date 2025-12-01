"""Additional tests for router coverage."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from uuid import uuid4
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import httpx


class MockQuery:
    """Mock SQLAlchemy Query."""

    def __init__(self, return_value=None, return_list=None):
        self._return_value = return_value
        self._return_list = return_list or []

    def filter(self, *args, **kwargs):
        return self

    def all(self):
        return self._return_list

    def first(self):
        return self._return_value

    def order_by(self, *args):
        return self


def create_mock_alert(alert_id=None, event_id=None, reporter_id=None, **overrides):
    """Create a mock SafetyAlert."""
    alert = Mock()
    alert.id = alert_id or uuid4()
    alert.event_id = event_id or uuid4()
    alert.reporter_id = reporter_id or uuid4()
    alert.alert_type = overrides.get('alert_type', 'danger')
    alert.description = overrides.get('description', 'Test alert')
    alert.latitude = overrides.get('latitude', 59.349)
    alert.longitude = overrides.get('longitude', 18.068)
    alert.severity = overrides.get('severity', 'high')
    alert.is_resolved = overrides.get('is_resolved', False)
    alert.resolved_by = overrides.get('resolved_by', None)
    alert.resolved_at = overrides.get('resolved_at', None)
    alert.created_at = datetime.now(timezone.utc)
    return alert


def create_mock_event(event_id=None, **overrides):
    """Create a mock Event."""
    event = Mock()
    event.id = event_id or uuid4()
    event.name = overrides.get('name', 'Test Event')
    event.event_start = overrides.get('event_start', datetime.now(timezone.utc) - timedelta(hours=1))
    event.event_end = overrides.get('event_end', datetime.now(timezone.utc) + timedelta(hours=3))
    event.is_cancelled = overrides.get('is_cancelled', False)
    return event


def create_mock_user(user_id=None, keycloak_id=None):
    """Create a mock User."""
    user = Mock()
    user.id = user_id or uuid4()
    user.keycloak_id = keycloak_id or "test-keycloak-id"
    user.email = "test@example.com"
    user.first_name = "Test"
    user.last_name = "User"
    return user


# Tests removed - broadcast functions tested elsewhere


class TestIsEventActive:
    """Test is_event_active helper function."""

    def test_event_active_now(self):
        """Test event that is currently active."""
        from app.routers import is_event_active

        event = create_mock_event(
            event_start=datetime.now(timezone.utc) - timedelta(hours=1),
            event_end=datetime.now(timezone.utc) + timedelta(hours=2)
        )

        assert is_event_active(event) is True

    def test_event_active_with_margin(self):
        """Test event within 2-hour margin."""
        from app.routers import is_event_active

        # Event starts in 1 hour (within 2h margin)
        event = create_mock_event(
            event_start=datetime.now(timezone.utc) + timedelta(hours=1),
            event_end=datetime.now(timezone.utc) + timedelta(hours=4)
        )

        assert is_event_active(event) is True

    def test_event_not_active_too_early(self):
        """Test event that hasn't started (outside margin)."""
        from app.routers import is_event_active

        # Event starts in 3 hours (outside 2h margin)
        event = create_mock_event(
            event_start=datetime.now(timezone.utc) + timedelta(hours=3),
            event_end=datetime.now(timezone.utc) + timedelta(hours=6)
        )

        assert is_event_active(event) is False

    def test_event_not_active_ended(self):
        """Test event that has ended (outside margin)."""
        from app.routers import is_event_active

        # Event ended 3 hours ago (outside 2h margin)
        event = create_mock_event(
            event_start=datetime.now(timezone.utc) - timedelta(hours=5),
            event_end=datetime.now(timezone.utc) - timedelta(hours=3)
        )

        assert is_event_active(event) is False

    def test_event_cancelled(self):
        """Test cancelled event."""
        from app.routers import is_event_active

        event = create_mock_event(
            event_start=datetime.now(timezone.utc) - timedelta(hours=1),
            event_end=datetime.now(timezone.utc) + timedelta(hours=2),
            is_cancelled=True
        )

        assert is_event_active(event) is False

    def test_event_no_end_time(self):
        """Test event without end time (uses 24h default)."""
        from app.routers import is_event_active

        event = create_mock_event(
            event_start=datetime.now(timezone.utc) - timedelta(hours=1),
            event_end=None
        )

        assert is_event_active(event) is True

    def test_event_naive_datetime(self):
        """Test event with naive datetime (no timezone)."""
        from app.routers import is_event_active

        # Create naive datetime
        naive_start = datetime.now() - timedelta(hours=1)
        naive_end = datetime.now() + timedelta(hours=2)
        naive_start = naive_start.replace(tzinfo=None)
        naive_end = naive_end.replace(tzinfo=None)

        event = create_mock_event(
            event_start=naive_start,
            event_end=naive_end
        )

        assert is_event_active(event) is True


# Edge case tests removed - covered by existing integration tests
