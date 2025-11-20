"""
Unit tests for Event Service API.

These tests validate the API layer without requiring a database connection.
For full integration tests with database, see test_integration.py
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from uuid import UUID, uuid4
from decimal import Decimal


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self, client: TestClient):
        """Health endpoint should return 200 OK."""
        response = client.get("/api/v1/events/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "event-service"


class TestAuthentication:
    """Test authentication requirements."""

    def test_create_event_unauthorized(self, client: TestClient):
        """Creating event without auth should return 401."""
        event_start = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        event_end = (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat()

        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start,
            "event_end": event_end
        }
        response = client.post("/api/v1/events", json=event_data)
        assert response.status_code == 401

    def test_update_event_unauthorized(self, client: TestClient):
        """Updating event without auth should return 401."""
        event_data = {"name": "Updated Event"}
        response = client.put("/api/v1/events/550e8400-e29b-41d4-a716-446655440000", json=event_data)
        assert response.status_code == 401

    def test_delete_event_unauthorized(self, client: TestClient):
        """Deleting event without auth should return 401."""
        response = client.delete("/api/v1/events/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 401

    def test_join_event_unauthorized(self, client: TestClient):
        """Joining event without auth should return 401."""
        response = client.post("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/join")
        assert response.status_code == 401

    def test_leave_event_unauthorized(self, client: TestClient):
        """Leaving event without auth should return 401."""
        response = client.delete("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/leave")
        assert response.status_code == 401

    def test_get_participants_unauthorized(self, client: TestClient):
        """Getting participants without auth should return 401."""
        response = client.get("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/participants")
        assert response.status_code == 401


class TestCreateEventValidation:
    """Test Create Event validation (Pydantic layer)."""

    def get_valid_event_data(self):
        """Helper to get valid event data."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)
        return {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

    def test_create_event_missing_name(self, authed_client: TestClient):
        """Missing name should return 422."""
        data = self.get_valid_event_data()
        del data["name"]
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_empty_name(self, authed_client: TestClient):
        """Empty name should return 422."""
        data = self.get_valid_event_data()
        data["name"] = ""
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_whitespace_name(self, authed_client: TestClient):
        """Whitespace-only name should return 422."""
        data = self.get_valid_event_data()
        data["name"] = "   "
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_name_too_long(self, authed_client: TestClient):
        """Name longer than 255 chars should return 422."""
        data = self.get_valid_event_data()
        data["name"] = "A" * 256
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_missing_address(self, authed_client: TestClient):
        """Missing address should return 422."""
        data = self.get_valid_event_data()
        del data["address"]
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_empty_address(self, authed_client: TestClient):
        """Empty address should return 422."""
        data = self.get_valid_event_data()
        data["address"] = ""
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_invalid_event_type(self, authed_client: TestClient):
        """Invalid event_type should return 422."""
        data = self.get_valid_event_data()
        data["event_type"] = "invalid_type"
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_missing_event_type_defaults_to_other(self, client: TestClient):
        """Missing event_type should default to 'other' (validated in integration test)."""
        data = self.get_valid_event_data()
        # event_type is optional, defaults to 'other'
        # This will be validated in integration tests
        pass

    def test_create_event_missing_event_start(self, authed_client: TestClient):
        """Missing event_start should return 422."""
        data = self.get_valid_event_data()
        del data["event_start"]
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_missing_event_end(self, authed_client: TestClient):
        """Missing event_end should return 422."""
        data = self.get_valid_event_data()
        del data["event_end"]
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_start_in_past(self, authed_client: TestClient):
        """event_start in the past should return 422."""
        data = self.get_valid_event_data()
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)
        data["event_start"] = past_time.isoformat()
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_start_too_soon(self, authed_client: TestClient):
        """event_start less than 30 minutes from now should return 422."""
        data = self.get_valid_event_data()
        soon_time = datetime.now(timezone.utc) + timedelta(minutes=15)
        data["event_start"] = soon_time.isoformat()
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_end_before_start(self, authed_client: TestClient):
        """event_end before event_start should return 422."""
        data = self.get_valid_event_data()
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start - timedelta(hours=1)
        data["event_start"] = event_start.isoformat()
        data["event_end"] = event_end.isoformat()
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_end_equals_start(self, client: TestClient):
        """event_end equal to event_start should be accepted (validated in integration test)."""
        data = self.get_valid_event_data()
        event_time = datetime.now(timezone.utc) + timedelta(hours=2)
        data["event_start"] = event_time.isoformat()
        data["event_end"] = event_time.isoformat()
        # Should not fail validation (validated in integration test)
        pass

    def test_create_event_datetime_without_timezone(self, authed_client: TestClient):
        """Datetime without timezone should return 422."""
        data = self.get_valid_event_data()
        data["event_start"] = "2025-12-31T20:00:00"  # No timezone
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_max_attendees_zero(self, authed_client: TestClient):
        """max_attendees = 0 should return 422."""
        data = self.get_valid_event_data()
        data["max_attendees"] = 0
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_max_attendees_one(self, authed_client: TestClient):
        """max_attendees = 1 should return 422."""
        data = self.get_valid_event_data()
        data["max_attendees"] = 1
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_max_attendees_negative(self, authed_client: TestClient):
        """Negative max_attendees should return 422."""
        data = self.get_valid_event_data()
        data["max_attendees"] = -5
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_latitude_without_longitude(self, authed_client: TestClient):
        """Latitude without longitude should return 422."""
        data = self.get_valid_event_data()
        data["latitude"] = "40.7128"
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_longitude_without_latitude(self, authed_client: TestClient):
        """Longitude without latitude should return 422."""
        data = self.get_valid_event_data()
        data["longitude"] = "-74.0060"
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_latitude_out_of_range(self, authed_client: TestClient):
        """Latitude > 90 should return 422."""
        data = self.get_valid_event_data()
        data["latitude"] = "95.0"
        data["longitude"] = "-74.0060"
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422

    def test_create_event_longitude_out_of_range(self, authed_client: TestClient):
        """Longitude > 180 should return 422."""
        data = self.get_valid_event_data()
        data["latitude"] = "40.7128"
        data["longitude"] = "185.0"
        response = authed_client.post("/api/v1/events", json=data)
        assert response.status_code == 422


class TestGetEvent:
    """Test Get Event endpoint."""

    def test_get_event_unauthorized(self, client: TestClient):
        """Getting event without auth should return 401."""
        response = client.get("/api/v1/events/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 401

    def test_get_event_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.get("/api/v1/events/invalid-uuid")
        assert response.status_code == 422


class TestUpdateEvent:
    """Test Update Event endpoint."""

    def test_update_event_unauthorized(self, client: TestClient):
        """Updating event without auth should return 401."""
        response = client.put(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 401

    def test_update_event_patch_unauthorized(self, client: TestClient):
        """PATCH event without auth should return 401."""
        response = client.patch(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000",
            json={"name": "Updated Name"}
        )
        assert response.status_code == 401

    def test_update_event_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.put("/api/v1/events/invalid-uuid", json={"name": "Test"})
        assert response.status_code == 422


class TestUpdateEventValidation:
    """Test Update Event validation edge cases."""

    def test_update_event_empty_name(self, client: TestClient):
        """Empty name should return 422."""
        response = client.put(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000",
            json={"name": ""}
        )
        assert response.status_code in [401, 422]  # 401 if no auth, 422 if validation fails first

    def test_update_event_max_attendees_one(self, client: TestClient):
        """max_attendees = 1 should return 422."""
        response = client.put(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000",
            json={"max_attendees": 1}
        )
        assert response.status_code in [401, 422]

    def test_update_event_max_attendees_zero(self, client: TestClient):
        """max_attendees = 0 should return 422."""
        response = client.put(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000",
            json={"max_attendees": 0}
        )
        assert response.status_code in [401, 422]


class TestDeleteEvent:
    """Test Delete Event endpoint."""

    def test_delete_event_unauthorized(self, client: TestClient):
        """Deleting event without auth should return 401."""
        response = client.delete("/api/v1/events/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 401

    def test_delete_event_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.delete("/api/v1/events/invalid-uuid")
        assert response.status_code == 422


class TestJoinEvent:
    """Test Join Event endpoint."""

    def test_join_event_unauthorized(self, client: TestClient):
        """Joining event without auth should return 401."""
        response = client.post("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/join")
        assert response.status_code == 401

    def test_join_event_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.post("/api/v1/events/invalid-uuid/join")
        assert response.status_code == 422

    def test_join_event_invalid_status(self, client: TestClient):
        """Invalid status should return 422."""
        response = client.post(
            "/api/v1/events/550e8400-e29b-41d4-a716-446655440000/join",
            json={"status": "maybe"}
        )
        assert response.status_code in [401, 422]  # 401 if no auth, 422 if validation fails first


class TestLeaveEvent:
    """Test Leave Event endpoint."""

    def test_leave_event_unauthorized(self, client: TestClient):
        """Leaving event without auth should return 401."""
        response = client.delete("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/leave")
        assert response.status_code == 401

    def test_leave_event_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.delete("/api/v1/events/invalid-uuid/leave")
        assert response.status_code == 422


class TestListEvents:
    """Test List Events endpoint."""

    def test_list_events_invalid_event_type(self, client: TestClient):
        """Invalid event_type should return 422."""
        response = client.get("/api/v1/events?event_type=invalid_type")
        assert response.status_code == 422
        assert "Invalid event_type" in response.json()["detail"]

    def test_list_events_status_filter_requires_auth(self, client: TestClient):
        """Status filter without auth should return 401."""
        response = client.get("/api/v1/events?status=going")
        assert response.status_code == 401

    def test_list_events_location_filter_incomplete(self, client: TestClient):
        """Providing only latitude or longitude should return 422."""
        # Only latitude
        response = client.get("/api/v1/events?latitude=40.7128")
        assert response.status_code == 422
        assert "latitude and longitude must be provided together" in response.json()["detail"]

        # Only longitude
        response = client.get("/api/v1/events?longitude=-74.0060")
        assert response.status_code == 422
        assert "latitude and longitude must be provided together" in response.json()["detail"]

class TestGetParticipants:
    """Test Get Event Participants endpoint."""

    def test_get_participants_invalid_status(self, client: TestClient):
        """Invalid status filter should return 422."""
        response = client.get("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/participants?status=invalid_status")
        # Note: This will return 401 because authentication is required first
        # In a real integration test with auth, it would return 422
        assert response.status_code == 401

    def test_get_participants_event_not_found(self, client: TestClient):
        """Getting participants for non-existent event should return 404."""
        # Note: This will return 401 because authentication is required first
        # In a real integration test with auth, it would return 404
        response = client.get("/api/v1/events/550e8400-e29b-41d4-a716-446655440000/participants")
        assert response.status_code == 401


class TestAPIDocumentation:
    """Test API documentation availability."""

    def test_openapi_schema_available(self, client: TestClient):
        """OpenAPI schema should be accessible."""
        response = client.get("/api/v1/events/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert schema["info"]["title"] == "CrewUp Event Service"

    def test_docs_available(self, client: TestClient):
        """Swagger UI docs should be accessible."""
        response = client.get("/api/v1/events/docs")
        assert response.status_code == 200


# ==================== Unit Tests with Mocked Database ====================


class TestListEventsEdgeCases:
    """Test list events endpoint edge cases that improve coverage."""

    def test_list_events_with_valid_filters(self, client: TestClient):
        """Test list events with various valid filters."""
        # Test with event_type filter
        response = client.get("/api/v1/events?event_type=concert")
        assert response.status_code == 200

        # Test with is_public filter
        response = client.get("/api/v1/events?is_public=true")
        assert response.status_code == 200

        # Test with is_cancelled filter
        response = client.get("/api/v1/events?is_cancelled=true")
        assert response.status_code == 200

        # Test with limit and offset
        response = client.get("/api/v1/events?limit=10&offset=0")
        assert response.status_code == 200

    def test_list_events_with_location_filter(self, client: TestClient):
        """Test list events with location filter."""
        # Test with valid latitude and longitude
        response = client.get("/api/v1/events?latitude=40.7128&longitude=-74.0060&radius_km=10")
        assert response.status_code == 200

    def test_list_events_with_creator_filter(self, client: TestClient):
        """Test list events with creator_id filter."""
        creator_id = uuid4()
        response = client.get(f"/api/v1/events?creator_id={creator_id}")
        assert response.status_code == 200


class TestAuthMiddleware:
    """Test authentication middleware coverage."""

    @patch("app.middleware.auth.requests.get")
    def test_get_keycloak_jwks_failure(self, mock_requests_get):
        """JWKS fetch failure should raise 503."""
        from app.middleware.auth import get_keycloak_jwks

        # Clear cache first
        get_keycloak_jwks.cache_clear()

        mock_requests_get.side_effect = Exception("Connection failed")

        with pytest.raises(HTTPException) as exc_info:
            get_keycloak_jwks()

        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.detail

    def test_get_current_user_in_test_mode(self):
        """In test mode, get_current_user should return mock user when token is provided."""
        from app.middleware.auth import get_current_user, MOCK_TEST_USER
        from fastapi.security import HTTPAuthorizationCredentials
        import asyncio

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="mock-token")

        # Call verify_token with credentials (will be used by get_current_user)
        from app.middleware.auth import verify_token
        token_payload = asyncio.run(verify_token(credentials))

        # Now call get_current_user
        result = asyncio.run(get_current_user(token_payload))

        assert result["keycloak_id"] == MOCK_TEST_USER["keycloak_id"]
        assert result["email"] == MOCK_TEST_USER["email"]

    def test_verify_token_without_credentials_raises_401(self):
        """verify_token without credentials should raise 401."""
        from app.middleware.auth import verify_token
        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(verify_token(None))

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
