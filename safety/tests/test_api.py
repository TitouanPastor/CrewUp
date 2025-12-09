"""
Unit tests for Safety Alert Service API.
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, timezone


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/api/v1/safety/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "safety-service"


class TestAuthentication:
    """Test authentication requirements."""

    def test_create_alert_unauthorized(self, unauth_client):
        """Creating alert without auth should return 401."""
        response = unauth_client.post(
            "/api/v1/safety",
            json={
                "group_id": str(uuid4()),
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "help",
                "message": "Test"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_alerts_unauthorized(self, unauth_client):
        """Listing alerts without auth should return 401."""
        response = unauth_client.get("/api/v1/safety")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_alert_unauthorized(self, unauth_client):
        """Getting alert without auth should return 401."""
        response = unauth_client.get(f"/api/v1/safety/{uuid4()}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_resolve_alert_unauthorized(self, unauth_client):
        """Resolving alert without auth should return 401."""
        response = unauth_client.patch(f"/api/v1/safety/{uuid4()}/resolve")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateAlert:
    """Test alert creation."""

    def test_create_alert_success(self, client, mock_user, mock_group, mock_group_member, mock_current_user):
        """Test successful alert creation."""
        response = client.post(
            "/api/v1/safety",
            json={
                "group_id": str(mock_group.id),
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "help",
                "message": "Need assistance"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(mock_user.id)
        assert data["group_id"] == str(mock_group.id)
        assert data["latitude"] == 65.584819
        assert data["longitude"] == 22.154984
        assert data["alert_type"] == "help"
        assert data["message"] == "Need assistance"
        assert data["is_resolved"] is False

    def test_create_alert_invalid_group(self, client, mock_user, mock_current_user):
        """Test creating alert with non-existent group."""
        fake_group_id = uuid4()
        response = client.post(
            "/api/v1/safety",
            json={
                "group_id": str(fake_group_id),
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "help"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Group not found" in response.json()["detail"]

    def test_create_alert_not_group_member(self, client, mock_user, mock_group, mock_current_user):
        """Test creating alert when user is not a group member."""
        # Don't create mock_group_member, so user is not in group
        response = client.post(
            "/api/v1/safety",
            json={
                "group_id": str(mock_group.id),
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "help"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "member" in response.json()["detail"].lower()

    def test_create_alert_invalid_type(self, client, mock_user, mock_group, mock_group_member, mock_current_user):
        """Test creating alert with invalid alert type."""
        response = client.post(
            "/api/v1/safety",
            json={
                "group_id": str(mock_group.id),
                "latitude": 65.584819,
                "longitude": 22.154984,
                "alert_type": "invalid_type"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        # Pydantic validation error returns 422
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_alert_invalid_coordinates(self, client, mock_user, mock_group, mock_group_member, mock_current_user):
        """Test creating alert with invalid coordinates."""
        response = client.post(
            "/api/v1/safety",
            json={
                "group_id": str(mock_group.id),
                "latitude": 95.0,  # Invalid latitude
                "longitude": 22.154984,
                "alert_type": "help"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestListAlerts:
    """Test alert listing."""

    def test_list_alerts_success(self, client, mock_user, mock_group, mock_group_member, mock_current_user):
        """Test listing all alerts."""
        response = client.get(
            "/api/v1/safety",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert isinstance(data["alerts"], list)

    def test_list_alerts_filter_by_group(self, client, mock_user, mock_group, mock_group_member, mock_current_user):
        """Test filtering alerts by group."""
        response = client.get(
            f"/api/v1/safety?group_id={mock_group.id}",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_list_alerts_filter_by_resolved(self, client, mock_user, mock_current_user):
        """Test filtering alerts by resolved status."""
        response = client.get(
            "/api/v1/safety?is_resolved=true",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)

    def test_list_alerts_filter_by_alert_type(self, client, mock_user, mock_current_user):
        """Test filtering alerts by type."""
        response = client.get(
            "/api/v1/safety?alert_type=help",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)


class TestGetAlert:
    """Test getting specific alerts."""

    def test_get_alert_success(self, client, mock_user, mock_group, mock_group_member, mock_current_user, db_session):
        """Test getting a specific alert."""
        # First create an alert
        from app.db import SafetyAlert
        alert = SafetyAlert(
            user_id=mock_user.id,
            group_id=mock_group.id,
            latitude=65.584819,
            longitude=22.154984,
            alert_type="help",
            message="Test alert"
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        response = client.get(
            f"/api/v1/safety/{alert.id}",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(alert.id)
        assert data["user_id"] == str(mock_user.id)
        assert data["group_id"] == str(mock_group.id)

    def test_get_alert_not_found(self, client, mock_current_user):
        """Test getting non-existent alert."""
        fake_id = uuid4()
        response = client.get(
            f"/api/v1/safety/{fake_id}",
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResolveAlert:
    """Test alert resolution."""

    def test_resolve_alert_success(self, client, mock_user, mock_group, mock_group_member, mock_current_user, db_session):
        """Test resolving an alert."""
        from app.db import SafetyAlert
        from uuid import uuid4
        batch_id = uuid4()
        alert = SafetyAlert(
            user_id=mock_user.id,
            group_id=mock_group.id,
            latitude=65.584819,
            longitude=22.154984,
            alert_type="help",
            batch_id=batch_id
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        response = client.patch(
            f"/api/v1/safety/{alert.id}/resolve",
            json={"resolved": True},
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_resolved"] is True
        assert data["resolved_at"] is not None

    def test_resolve_alert_already_resolved(self, client, mock_user, mock_group, mock_group_member, mock_current_user, db_session):
        """Test resolving an already resolved alert."""
        from app.db import SafetyAlert
        alert = SafetyAlert(
            user_id=mock_user.id,
            group_id=mock_group.id,
            latitude=65.584819,
            longitude=22.154984,
            alert_type="help",
            resolved_at=datetime.now(timezone.utc)
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        response = client.patch(
            f"/api/v1/safety/{alert.id}/resolve",
            json={"resolved": True},
            headers={"Authorization": "Bearer mock-token"}
        )

        # Endpoint allows re-resolving, so it returns 200
        assert response.status_code == status.HTTP_200_OK

    def test_resolve_alert_not_found(self, client, mock_current_user):
        """Test resolving non-existent alert."""
        fake_id = uuid4()
        response = client.patch(
            f"/api/v1/safety/{fake_id}/resolve",
            json={"resolved": True},
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

