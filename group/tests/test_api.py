"""
Unit tests for Group & Chat Service API.

These tests validate the API layer without requiring a database connection.
For full integration tests with database, see test_integration.py
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client: TestClient):
        """Health endpoint should return 200 OK."""
        response = client.get("/api/v1/groups/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "group-service"
    
    def test_root_endpoint(self, client: TestClient):
        """Root endpoint should return service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "group-service"
        assert "version" in data
        assert "docs" in data


class TestAuthentication:
    """Test authentication requirements."""
    
    def test_create_group_unauthorized(self, client: TestClient):
        """Creating group without auth should return 401."""
        response = client.post(
            "/api/v1/groups",
            json={
                "event_id": str(uuid4()),
                "name": "Test Group",
                "max_members": 10
            }
        )
        assert response.status_code == 401
    
    def test_list_groups_unauthorized(self, client: TestClient):
        """Listing groups without auth should return 401."""
        response = client.get("/api/v1/groups")
        assert response.status_code == 401
    
    def test_get_group_unauthorized(self, client: TestClient):
        """Getting group details without auth should return 401."""
        response = client.get(f"/api/v1/groups/{uuid4()}")
        assert response.status_code == 401
    
    def test_join_group_unauthorized(self, client: TestClient):
        """Joining group without auth should return 401."""
        response = client.post(f"/api/v1/groups/{uuid4()}/join")
        assert response.status_code == 401
    
    def test_leave_group_unauthorized(self, client: TestClient):
        """Leaving group without auth should return 401."""
        response = client.delete(f"/api/v1/groups/{uuid4()}/leave")
        assert response.status_code == 401
    
    def test_get_members_unauthorized(self, client: TestClient):
        """Getting members without auth should return 401."""
        response = client.get(f"/api/v1/groups/{uuid4()}/members")
        assert response.status_code == 401
    
    def test_get_messages_unauthorized(self, client: TestClient):
        """Getting messages without auth should return 401."""
        response = client.get(f"/api/v1/groups/{uuid4()}/messages")
        assert response.status_code == 401


class TestCreateGroupValidation:
    """Test Create Group validation (Pydantic layer)."""
    
    def get_valid_group_data(self):
        """Helper to get valid group data."""
        return {
            "event_id": str(uuid4()),
            "name": "Test Group",
            "description": "Test description",
            "max_members": 10
        }
    
    def test_create_group_missing_event_id(self, authed_client: TestClient):
        """Missing event_id should return 422."""
        data = self.get_valid_group_data()
        del data["event_id"]
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_invalid_event_id(self, authed_client: TestClient):
        """Invalid event_id UUID should return 422."""
        data = self.get_valid_group_data()
        data["event_id"] = "not-a-uuid"
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_missing_name(self, authed_client: TestClient):
        """Missing name should return 422."""
        data = self.get_valid_group_data()
        del data["name"]
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_empty_name(self, authed_client: TestClient):
        """Empty name should return 422."""
        data = self.get_valid_group_data()
        data["name"] = ""
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_whitespace_name(self, authed_client: TestClient):
        """Whitespace-only name should return 422."""
        data = self.get_valid_group_data()
        data["name"] = "   "
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_name_too_long(self, authed_client: TestClient):
        """Name over 200 characters should return 422."""
        data = self.get_valid_group_data()
        data["name"] = "x" * 201
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_description_too_long(self, authed_client: TestClient):
        """Description over 1000 characters should return 422."""
        data = self.get_valid_group_data()
        data["description"] = "x" * 1001
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_max_members_too_small(self, authed_client: TestClient):
        """Max members < 2 should return 422."""
        data = self.get_valid_group_data()
        data["max_members"] = 1
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_max_members_too_large(self, authed_client: TestClient):
        """Max members > 50 should return 422."""
        data = self.get_valid_group_data()
        data["max_members"] = 51
        response = authed_client.post("/api/v1/groups", json=data)
        assert response.status_code == 422
    
    def test_create_group_minimal_valid_data(self, authed_client: TestClient):
        """Group with minimal valid data should pass validation."""
        data = {
            "event_id": str(uuid4()),
            "name": "Test",
            "max_members": 2
        }
        # Will fail at DB layer but passes validation
        response = authed_client.post("/api/v1/groups", json=data)
        # Should not be 422 (validation error)
        assert response.status_code != 422


class TestMessagePagination:
    """Test message pagination parameters."""
    
    def test_get_messages_invalid_limit(self, authed_client: TestClient):
        """Limit > 100 should return 422."""
        response = authed_client.get(
            f"/api/v1/groups/{uuid4()}/messages",
            params={"limit": 101}
        )
        assert response.status_code == 422
    
    def test_get_messages_negative_limit(self, authed_client: TestClient):
        """Negative limit should return 422."""
        response = authed_client.get(
            f"/api/v1/groups/{uuid4()}/messages",
            params={"limit": -1}
        )
        assert response.status_code == 422
    
    def test_get_messages_negative_offset(self, authed_client: TestClient):
        """Negative offset should return 422."""
        response = authed_client.get(
            f"/api/v1/groups/{uuid4()}/messages",
            params={"offset": -1}
        )
        assert response.status_code == 422


class TestMemberPagination:
    """Test member pagination parameters."""
    
    # Note: These will return 404 since group doesn't exist
    # Parameter validation happens in Pydantic, tested in other tests
    
    def test_get_members_valid_pagination(self, authed_client: TestClient):
        """Test valid pagination parameters."""
        response = authed_client.get(
            f"/api/v1/groups/{uuid4()}/members",
            params={"limit": 50, "offset": 0}
        )
        # Will be 404 since group doesn't exist, but params are valid
        assert response.status_code == 404


class TestOpenAPI:
    """Test OpenAPI documentation."""
    
    def test_openapi_json_available(self, client: TestClient):
        """OpenAPI schema should be accessible."""
        response = client.get("/api/v1/groups/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "CrewUp Group & Chat Service"
        assert "paths" in data
        assert "components" in data
    
    def test_docs_ui_available(self, client: TestClient):
        """Swagger UI should be accessible."""
        response = client.get("/api/v1/groups/docs")
        assert response.status_code == 200
        assert b"swagger" in response.content.lower()
    
    def test_redoc_ui_available(self, client: TestClient):
        """ReDoc UI should be accessible."""
        response = client.get("/api/v1/groups/redoc")
        assert response.status_code == 200
        assert b"redoc" in response.content.lower()


class TestInvalidUUIDs:
    """Test invalid UUID handling."""
    
    def test_get_group_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.get("/api/v1/groups/not-a-uuid")
        assert response.status_code == 422
    
    def test_join_group_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.post("/api/v1/groups/not-a-uuid/join")
        assert response.status_code == 422
    
    def test_leave_group_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.delete("/api/v1/groups/not-a-uuid/leave")
        assert response.status_code == 422
    
    def test_get_members_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.get("/api/v1/groups/not-a-uuid/members")
        assert response.status_code == 422
    
    def test_get_messages_invalid_uuid(self, authed_client: TestClient):
        """Invalid UUID should return 422."""
        response = authed_client.get("/api/v1/groups/not-a-uuid/messages")
        assert response.status_code == 422


