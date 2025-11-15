"""
Unit tests for Group & Chat Service API endpoints.

These are simple tests without database dependency.
For comprehensive testing with real database, see test_integration.py

Run with: pytest tests/test_api.py -v
"""
import pytest
from fastapi import status


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Health endpoint should return 200 without authentication."""
        response = client.get("/api/v1/groups/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "group-service"


class TestAuthentication:
    """Test authentication requirements."""
    
    def test_create_group_unauthorized(self, client):
        """Test creating group without auth returns 401."""
        from uuid import uuid4
        
        response = client.post(
            "/api/v1/groups",
            json={
                "event_id": str(uuid4()),
                "name": "Test Group",
                "max_members": 10
            }
        )
        assert response.status_code == 401
    
    def test_list_groups_unauthorized(self, client):
        """Test listing groups without auth returns 401."""
        response = client.get("/api/v1/groups")
        assert response.status_code == 401
    
    def test_join_group_unauthorized(self, client):
        """Test joining group without auth returns 401."""
        from uuid import uuid4
        
        response = client.post(f"/api/v1/groups/{uuid4()}/join")
        assert response.status_code == 401


class TestOpenAPI:
    """Test OpenAPI documentation."""
    
    def test_openapi_json_available(self, client):
        """Test OpenAPI schema is accessible."""
        response = client.get("/api/v1/groups/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "CrewUp Group & Chat Service"
        assert "paths" in data
    
    def test_docs_ui_available(self, client):
        """Test Swagger UI is accessible."""
        response = client.get("/api/v1/groups/docs")
        assert response.status_code == 200


