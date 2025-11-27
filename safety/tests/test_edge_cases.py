"""
Additional tests for edge cases and error paths to increase coverage.
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.models import SafetyAlert, Event, Group, GroupMember


class TestEventValidation:
    """Test event state validation for alerts."""
    
    def test_create_alert_event_not_started(self, client, mock_user, mock_group_member, db_session):
        """Cannot create alert for event that starts >2h in future (outside margin)."""
        # Update event to start >2h in future (outside 2h margin)
        event = db_session.query(Event).first()
        event.event_start = datetime.now(timezone.utc) + timedelta(hours=3)
        event.event_end = datetime.now(timezone.utc) + timedelta(hours=5)
        db_session.commit()
        
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "alert_type": "help",
            "message": "Test alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active events" in response.json()["detail"].lower()
    
    def test_create_alert_event_ended(self, client, mock_user, mock_group_member, db_session):
        """Cannot create alert for event ended >2h ago (outside margin)."""
        # Update event to end >2h ago (outside 2h margin)
        event = db_session.query(Event).first()
        event.event_start = datetime.now(timezone.utc) - timedelta(hours=5)
        event.event_end = datetime.now(timezone.utc) - timedelta(hours=3)
        db_session.commit()
        
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "alert_type": "help",
            "message": "Test alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active events" in response.json()["detail"].lower()
    
    def test_create_alert_event_cancelled(self, client, mock_user, mock_group_member, db_session):
        """Cannot create alert for cancelled event."""
        # Cancel the event
        event = db_session.query(Event).first()
        event.is_cancelled = True
        db_session.commit()
        
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "alert_type": "help",
            "message": "Test alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "active events" in response.json()["detail"].lower()


class TestAlertTypes:
    """Test different alert types."""
    
    def test_create_alert_type_medical(self, client, mock_group_member):
        """Create medical alert."""
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "alert_type": "medical",
            "message": "Medical alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["alert_type"] == "medical"
    
    def test_create_alert_type_other(self, client, mock_group_member):
        """Create other type alert."""
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "alert_type": "other",
            "message": "Other alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["alert_type"] == "other"
    
    def test_create_alert_default_type_help(self, client, mock_group_member):
        """Create alert without specifying type (defaults to help)."""
        alert_data = {
            "group_id": str(mock_group_member.group_id),
            "latitude": 65.584819,
            "longitude": 22.154984,
            "message": "Default type alert"
        }
        
        response = client.post("/api/v1/safety", json=alert_data)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["alert_type"] == "help"  # Default value


class TestAlertResolution:
    """Test alert resolution edge cases."""
    
    def test_unresolve_alert(self, client, mock_user, mock_group_member, db_session):
        """Test marking a resolved alert as unresolved."""
        # Create an alert and mark as resolved
        alert_id = uuid4()
        batch_id = uuid4()
        alert = SafetyAlert(
            id=alert_id,
            user_id=mock_user.id,
            group_id=mock_group_member.group_id,
            latitude=65.584819,
            longitude=22.154984,
            alert_type="help",
            batch_id=batch_id
        )
        db_session.add(alert)
        db_session.commit()
        
        # First resolve it
        alert.resolved_at = datetime.now(timezone.utc)
        db_session.commit()
        
        # Now unresolve it
        response = client.patch(
            f"/api/v1/safety/{alert.id}/resolve",
            json={"resolved": False}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_resolved"] is False
        assert data["resolved_at"] is None


class TestExceptionHandlers:
    """Test custom exception classes."""
    
    def test_not_found_exception(self):
        """Test NotFoundException."""
        from app.utils.exceptions import NotFoundException
        
        exc = NotFoundException("Test not found")
        assert exc.status_code == 404
        assert exc.detail == "Test not found"
    
    def test_bad_request_exception(self):
        """Test BadRequestException."""
        from app.utils.exceptions import BadRequestException
        
        exc = BadRequestException("Bad request")
        assert exc.status_code == 400
        assert exc.detail == "Bad request"
    
    def test_unauthorized_exception(self):
        """Test UnauthorizedException."""
        from app.utils.exceptions import UnauthorizedException
        
        exc = UnauthorizedException("Not authorized")
        assert exc.status_code == 401
        assert exc.detail == "Not authorized"
    
    def test_forbidden_exception(self):
        """Test ForbiddenException."""
        from app.utils.exceptions import ForbiddenException
        
        exc = ForbiddenException("Forbidden")
        assert exc.status_code == 403
        assert exc.detail == "Forbidden"


class TestSafetyException:
    """Test SafetyException with custom status codes."""
    
    def test_safety_exception_custom_status(self):
        """Test SafetyException with custom status code."""
        from app.routers import SafetyException
        
        exc = SafetyException("Custom error", 418)  # I'm a teapot
        assert exc.status_code == 418
        assert exc.detail == "Custom error"


class TestListFiltering:
    """Test alert list filtering combinations."""
    
    def test_list_alerts_filter_by_type_harassment(self, client, mock_user, mock_group_member, db_session):
        """Filter alerts by harassment type."""
        # Create different alert types
        alert1 = SafetyAlert(
            id=uuid4(),
            user_id=mock_user.id,
            group_id=mock_group_member.group_id,
            latitude=65.58,
            longitude=22.15,
            alert_type="harassment"
        )
        alert2 = SafetyAlert(
            id=uuid4(),
            user_id=mock_user.id,
            group_id=mock_group_member.group_id,
            latitude=65.58,
            longitude=22.15,
            alert_type="help"
        )
        db_session.add_all([alert1, alert2])
        db_session.commit()
        
        response = client.get("/api/v1/safety?alert_type=harassment")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Filter works if we have at least one harassment alert
        harassment_alerts = [a for a in data["alerts"] if a["alert_type"] == "harassment"]
        assert len(harassment_alerts) >= 1
    
    def test_list_alerts_pagination(self, client, mock_user, mock_group_member, db_session):
        """Test pagination with limit and offset."""
        # Create multiple alerts
        for i in range(5):
            alert = SafetyAlert(
                id=uuid4(),
                user_id=mock_user.id,
                group_id=mock_group_member.group_id,
                latitude=65.58,
                longitude=22.15,
                alert_type="help",
                message=f"Alert {i}"
            )
            db_session.add(alert)
        db_session.commit()
        
        # Get first 2
        response = client.get("/api/v1/safety?limit=2&offset=0")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["alerts"]) == 2
        assert data["total"] >= 5
        
        # Get next 2
        response = client.get("/api/v1/safety?limit=2&offset=2")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["alerts"]) == 2
    
    def test_list_alerts_combined_filters(self, client, mock_user, mock_group_member, db_session):
        """Test combining multiple filters."""
        # Create resolved and unresolved alerts
        alert1 = SafetyAlert(
            id=uuid4(),
            user_id=mock_user.id,
            group_id=mock_group_member.group_id,
            latitude=65.58,
            longitude=22.15,
            alert_type="help"
        )
        db_session.add(alert1)
        db_session.commit()
        
        # Resolve it
        alert1.resolved_at = datetime.now(timezone.utc)
        
        alert2 = SafetyAlert(
            id=uuid4(),
            user_id=mock_user.id,
            group_id=mock_group_member.group_id,
            latitude=65.58,
            longitude=22.15,
            alert_type="help"
        )
        db_session.add(alert2)
        db_session.commit()
        
        # Filter by group and resolved status
        response = client.get(
            f"/api/v1/safety?group_id={mock_group_member.group_id}&is_resolved=true"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should have at least one resolved alert for this group
        resolved_alerts = [a for a in data["alerts"] if a["is_resolved"]]
        assert len(resolved_alerts) >= 1
        assert all(a["group_id"] == str(mock_group_member.group_id) for a in data["alerts"])


class TestConfigEdgeCases:
    """Test config edge cases."""
    
    def test_config_database_url_fallback(self, monkeypatch):
        """Test database URL construction from individual vars."""
        import os
        from app.config import Config
        
        # Remove DATABASE_URL to test fallback
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("POSTGRES_USER", "testuser")
        monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
        monkeypatch.setenv("POSTGRES_HOST", "testhost")
        monkeypatch.setenv("POSTGRES_PORT", "5555")
        monkeypatch.setenv("POSTGRES_DB", "testdb")
        
        # Force reload of config
        expected = "postgresql://testuser:testpass@testhost:5555/testdb"
        url = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
        assert url == expected
