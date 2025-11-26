"""
Simple tests for Safety Alert API - with dependency overrides.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from datetime import datetime

from app.db import SafetyAlert


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "safety"


def test_create_safety_alert_success(client, db_session, mock_user, mock_group, mock_group_member, mock_current_user):
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
    assert data["alert_type"] == "help"
    assert data["message"] == "Need assistance"


def test_list_alerts_success(client, db_session, mock_user, mock_group, mock_group_member):
    """Test listing alerts."""
    # Create some alerts
    alert1 = SafetyAlert(
    user_id=mock_user.id,
    group_id=mock_group.id,
    alert_type="help",
    message="Test alert 1"
    )
    alert2 = SafetyAlert(
    user_id=mock_user.id,
    group_id=mock_group.id,
    alert_type="emergency",
    message="Test alert 2"
    )
    db_session.add_all([alert1, alert2])
    db_session.commit()

    response = client.get(
    "/api/v1/safety",
    headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] >= 2
    assert len(data["alerts"]) >= 2


def test_get_alert_success(client, db_session, mock_user, mock_group, mock_group_member):
    """Test getting a specific alert."""
    alert = SafetyAlert(
    user_id=mock_user.id,
    group_id=mock_group.id,
    alert_type="help",
    message="Test alert",
    latitude=65.5,
    longitude=22.1
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
    assert data["alert_type"] == "help"


def test_resolve_alert(client, db_session, mock_user, mock_group, mock_group_member):
    """Test resolving an alert."""
    alert = SafetyAlert(
    user_id=mock_user.id,
    group_id=mock_group.id,
    alert_type="help"
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
    assert data["resolved_at"] is not None
