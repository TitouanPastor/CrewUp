"""
Unit tests for banned user restrictions in Safety Service.

Tests verify that banned users receive 403 Forbidden errors when trying
to perform actions on safety alerts.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_db, User, Event, Group, GroupMember, SafetyAlert
from app.middleware import get_current_user


@pytest.fixture
def banned_user(db_session):
    """Create a banned user."""
    user = User(
        id=uuid4(),
        keycloak_id="banned-user-123",
        email="banned@example.com",
        first_name="Banned",
        last_name="User",
        is_banned=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular (not banned) user."""
    user = User(
        id=uuid4(),
        keycloak_id="regular-user-456",
        email="regular@example.com",
        first_name="Regular",
        last_name="User",
        is_banned=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_event(db_session, regular_user):
    """Create a mock event that is currently active."""
    event = Event(
        id=uuid4(),
        creator_id=regular_user.id,
        name="Test Party",
        description="Test event description",
        event_type="party",
        address="123 Test Street",
        latitude=65.584819,
        longitude=22.154984,
        event_start=datetime.now(timezone.utc) - timedelta(hours=1),
        event_end=datetime.now(timezone.utc) + timedelta(hours=2),
        is_cancelled=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


@pytest.fixture
def mock_group(db_session, mock_event):
    """Create a mock group."""
    group = Group(
        id=uuid4(),
        event_id=mock_event.id,
        name="Test Group",
        description="Test group description",
        max_members=10,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(group)
    db_session.commit()
    db_session.refresh(group)
    return group


@pytest.fixture
def mock_group_member_banned(db_session, banned_user, mock_group):
    """Create group membership for banned user."""
    member = GroupMember(
        group_id=mock_group.id,
        user_id=banned_user.id,
        is_admin=False,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def mock_group_member_regular(db_session, regular_user, mock_group):
    """Create group membership for regular user."""
    member = GroupMember(
        group_id=mock_group.id,
        user_id=regular_user.id,
        is_admin=False,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(member)
    db_session.commit()
    return member


@pytest.fixture
def mock_alert(db_session, mock_group, regular_user):
    """Create a mock safety alert."""
    alert = SafetyAlert(
        id=uuid4(),
        group_id=mock_group.id,
        user_id=regular_user.id,
        alert_type="help",
        message="Test alert",
        latitude=65.584819,
        longitude=22.154984,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


@pytest.fixture(autouse=True)
def cleanup_overrides():
    """Automatically clean up dependency overrides after each test."""
    yield
    app.dependency_overrides.clear()


def test_banned_user_cannot_create_alert(db_session, banned_user, mock_group, mock_group_member_banned):
    """Banned user receives 403 when trying to create a safety alert."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": banned_user.keycloak_id,
            "email": banned_user.email,
            "first_name": banned_user.first_name,
            "last_name": banned_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    alert_data = {
        "group_id": str(mock_group.id),
        "alert_type": "help",
        "message": "Need help!",
        "latitude": 65.584819,
        "longitude": 22.154984
    }

    response = client.post(
        "/api/v1/safety",
        json=alert_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_list_alerts(db_session, banned_user, mock_alert):
    """Banned user receives 403 when trying to list alerts."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": banned_user.keycloak_id,
            "email": banned_user.email,
            "first_name": banned_user.first_name,
            "last_name": banned_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    response = client.get(
        "/api/v1/safety",
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_get_alert_details(db_session, banned_user, mock_alert):
    """Banned user receives 403 when trying to get alert details."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": banned_user.keycloak_id,
            "email": banned_user.email,
            "first_name": banned_user.first_name,
            "last_name": banned_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    response = client.get(
        f"/api/v1/safety/{mock_alert.id}",
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_resolve_alert(db_session, banned_user, mock_alert):
    """Banned user receives 403 when trying to resolve an alert."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": banned_user.keycloak_id,
            "email": banned_user.email,
            "first_name": banned_user.first_name,
            "last_name": banned_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    response = client.patch(
        f"/api/v1/safety/{mock_alert.id}/resolve",
        json={"resolved": True},
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_banned_user_cannot_get_my_alerts(db_session, banned_user):
    """Banned user receives 403 when trying to get their own alerts."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": banned_user.keycloak_id,
            "email": banned_user.email,
            "first_name": banned_user.first_name,
            "last_name": banned_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    response = client.get(
        "/api/v1/safety/my-alerts",
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 403
    assert "banned" in response.json()["detail"].lower()


def test_regular_user_can_create_alert(db_session, regular_user, mock_group, mock_group_member_regular):
    """Regular (non-banned) user can create safety alerts."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": regular_user.keycloak_id,
            "email": regular_user.email,
            "first_name": regular_user.first_name,
            "last_name": regular_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    alert_data = {
        "group_id": str(mock_group.id),
        "alert_type": "help",
        "message": "Need help!",
        "latitude": 65.584819,
        "longitude": 22.154984
    }

    response = client.post(
        "/api/v1/safety",
        json=alert_data,
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 201
    assert response.json()["alert_type"] == "help"


def test_regular_user_can_list_alerts(db_session, regular_user, mock_alert):
    """Regular (non-banned) user can list alerts."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return {
            "keycloak_id": regular_user.keycloak_id,
            "email": regular_user.email,
            "first_name": regular_user.first_name,
            "last_name": regular_user.last_name,
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    client = TestClient(app)

    response = client.get(
        "/api/v1/safety",
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 200
    assert "alerts" in response.json()
