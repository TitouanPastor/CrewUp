"""
Integration tests for Safety Service with real Keycloak authentication.

These tests require:
1. Safety service running (localhost:8003 or SAFETY_SERVICE_URL)
2. Database with schema applied
3. Keycloak running with test users
4. .env.test file with credentials

Run with: pytest tests/test_integration_auth.py -v
Or use: ./run_tests.sh integration

Note: These tests are marked as integration tests and will be skipped
if the environment is not properly configured (missing KEYCLOAK_SERVER_URL).
"""
import pytest
import os
from uuid import UUID
from datetime import datetime, timedelta, timezone
import requests
from jose import jwt


# Skip all tests in this module if Keycloak is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("KEYCLOAK_SERVER_URL"),
    reason="Integration tests require KEYCLOAK_SERVER_URL environment variable"
)


@pytest.fixture(scope="session")
def keycloak_tokens(integration_env):
    """
    Authenticate with Keycloak and get JWT tokens for test users.
    Returns decoded tokens with user info.
    """
    def get_token(username: str, password: str) -> dict:
        """Get access token from Keycloak."""
        token_url = f"{integration_env['keycloak_url']}/realms/{integration_env['keycloak_realm']}/protocol/openid-connect/token"

        response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": integration_env["keycloak_client_id"],
                "username": username,
                "password": password,
            },
            verify=False
        )

        assert response.status_code == 200, f"Failed to get token for {username}: {response.text}"
        token_data = response.json()

        # Decode token to get user info
        decoded = jwt.get_unverified_claims(token_data["access_token"])

        return {
            "access_token": token_data["access_token"],
            "keycloak_id": decoded["sub"],
            "email": decoded.get("email"),
            "first_name": decoded.get("given_name", "Test"),
            "last_name": decoded.get("family_name", "User"),
        }

    return {
        "user1": get_token(integration_env["user1_email"], integration_env["user1_password"]),
        "user2": get_token(integration_env["user2_email"], integration_env["user2_password"]),
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_users(integration_env, keycloak_tokens):
    """
    Create test user profiles in the database before running tests.
    This ensures users exist when creating safety alerts.
    """
    import psycopg2

    # Parse DATABASE_URL from .env.test
    db_url = integration_env.get("database_url", "postgresql://crewup:crewup_dev_password@localhost:5432/crewup")

    # Connect to database
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Insert user1
        user1 = keycloak_tokens["user1"]
        cursor.execute(
            """
            INSERT INTO users (id, keycloak_id, email, first_name, last_name, bio, interests, reputation, is_active)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 0.00, true)
            ON CONFLICT (keycloak_id) DO NOTHING
            """,
            (
                user1["keycloak_id"],
                user1["email"],
                user1.get("first_name", "Test"),
                user1.get("last_name", "User1"),
                "Test user 1 for integration tests",
                []
            )
        )

        # Insert user2
        user2 = keycloak_tokens["user2"]
        cursor.execute(
            """
            INSERT INTO users (id, keycloak_id, email, first_name, last_name, bio, interests, reputation, is_active)
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, 0.00, true)
            ON CONFLICT (keycloak_id) DO NOTHING
            """,
            (
                user2["keycloak_id"],
                user2["email"],
                user2.get("first_name", "Test"),
                user2.get("last_name", "User2"),
                "Test user 2 for integration tests",
                []
            )
        )

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n✓ Test users created in database")

    except Exception as e:
        print(f"\nWarning: Could not create test users in database: {e}")
        print("Tests may fail if users don't exist")

    yield

    # Cleanup: Delete ALL safety alerts after tests complete
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Delete ALL safety alerts from the database (not just test alerts)
        cursor.execute("DELETE FROM safety_alerts")
        deleted_count = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n✓ Cleanup: Deleted {deleted_count} safety alerts from database")

    except Exception as e:
        print(f"\nWarning: Could not cleanup safety alerts: {e}")


@pytest.fixture(scope="session")
def api_client(integration_env):
    """HTTP client for API calls."""
    class APIClient:
        def __init__(self, base_url: str):
            self.base_url = base_url

        def get(self, path: str, token: str = None, **kwargs):
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return requests.get(f"{self.base_url}{path}", headers=headers, **kwargs)

        def post(self, path: str, token: str = None, **kwargs):
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return requests.post(f"{self.base_url}{path}", headers=headers, **kwargs)

        def put(self, path: str, token: str = None, **kwargs):
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return requests.put(f"{self.base_url}{path}", headers=headers, **kwargs)

        def patch(self, path: str, token: str = None, **kwargs):
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return requests.patch(f"{self.base_url}{path}", headers=headers, **kwargs)

        def delete(self, path: str, token: str = None, **kwargs):
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            return requests.delete(f"{self.base_url}{path}", headers=headers, **kwargs)

    return APIClient(integration_env["service_url"])


@pytest.fixture(scope="function")
def cleanup_alerts(api_client, keycloak_tokens):
    """
    Track alerts created during a test and delete them after the test completes.
    Usage: Call cleanup_alerts.add(alert_id, creator_token) when creating an alert.
    """
    created_alerts = []

    class AlertTracker:
        def add(self, alert_id: str, creator_token: str):
            """Register an alert to be deleted after the test."""
            created_alerts.append((alert_id, creator_token))
            return alert_id

    tracker = AlertTracker()

    yield tracker

    # Cleanup: Delete all alerts created during this test, even if test failed
    for alert_id, token in created_alerts:
        try:
            # Resolve the alert first (safety alerts are resolved, not deleted)
            api_client.patch(f"/api/v1/safety/{alert_id}/resolve", token=token)
        except Exception as e:
            print(f"Warning: Could not resolve alert {alert_id}: {e}")


class TestHealthCheck:
    """Test health check endpoint (no auth required)."""

    def test_health_check(self, api_client):
        """Health check should return 200 without authentication."""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "safety"


class TestAuthentication:
    """Test authentication requirements."""

    def test_list_alerts_without_token(self, api_client):
        """Listing alerts without token should return 401."""
        response = api_client.get("/api/v1/safety")
        assert response.status_code == 401

    def test_list_alerts_with_invalid_token(self, api_client):
        """Listing alerts with invalid token should return 401."""
        response = api_client.get("/api/v1/safety", token="invalid-token")
        assert response.status_code == 401

    def test_list_alerts_with_valid_token(self, api_client, keycloak_tokens):
        """Listing alerts with valid Keycloak token should return 200."""
        response = api_client.get("/api/v1/safety", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert "total" in data


class TestAlertCRUD:
    """Test safety alert CRUD operations with real authentication."""

    def test_create_alert_with_valid_token(self, api_client, keycloak_tokens, cleanup_alerts, integration_env):
        """Create a safety alert with valid Keycloak token."""
        import psycopg2
        from datetime import datetime, timedelta
        
        # Setup: Create event and group in DB
        db_url = integration_env.get("database_url", "postgresql://crewup:crewup_dev_password@localhost:5432/crewup")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Initialize variables for cleanup
        event_id = None
        group_id = None
        
        try:
            # Get user1 ID
            user1 = keycloak_tokens["user1"]
            cursor.execute("SELECT id FROM users WHERE keycloak_id = %s", (user1["keycloak_id"],))
            user_id = cursor.fetchone()[0]
            
            # Create event with explicit created_at in the past so event can start "now"
            now = datetime.now(timezone.utc)
            created_at = now - timedelta(hours=2)  # Created 2h ago
            event_start = now - timedelta(minutes=30)  # Started 30 min ago (active now)
            event_end = now + timedelta(hours=1)  # Ends in 1h
            
            cursor.execute(
                """
                INSERT INTO events (id, creator_id, name, description, event_type, address, 
                                    latitude, longitude, event_start, event_end, is_cancelled, created_at)
                VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, false, %s)
                RETURNING id
                """,
                (
                    user_id,
                    "Test Safety Event",
                    "Event for testing safety alerts",
                    "party",
                    "Test Street 123",
                    65.584819,
                    22.154984,
                    event_start,
                    event_end,
                    created_at
                )
            )
            event_id = cursor.fetchone()[0]
            
            # Create a group for this event
            cursor.execute(
                """
                INSERT INTO groups (id, event_id, name, description, max_members, created_at)
                VALUES (gen_random_uuid(), %s, %s, %s, 10, NOW())
                RETURNING id
                """,
                (event_id, "Test Safety Group", "Group for testing")
            )
            group_id = cursor.fetchone()[0]
            
            # Add user1 as member of the group
            cursor.execute(
                """
                INSERT INTO group_members (group_id, user_id, is_admin, joined_at)
                VALUES (%s, %s, true, NOW())
                """,
                (group_id, user_id)
            )
            
            conn.commit()
            
            # Now test creating a safety alert
            alert_data = {
                "group_id": str(group_id),
                "latitude": 65.585,
                "longitude": 22.155,
                "alert_type": "help",
                "message": "Integration test alert"
            }
            
            response = api_client.post(
                "/api/v1/safety",
                token=user1["access_token"],
                json=alert_data
            )
            
            assert response.status_code == 201, f"Failed to create alert: {response.text}"
            data = response.json()
            
            assert "id" in data
            assert data["group_id"] == str(group_id)
            assert data["alert_type"] == "help"
            assert data["message"] == "Integration test alert"
            assert data["latitude"] == 65.585
            assert data["longitude"] == 22.155
            assert data["is_resolved"] is False
            
            # Track for cleanup
            cleanup_alerts.add(data["id"], user1["access_token"])
            
        finally:
            # Cleanup: Delete test data
            if group_id:
                cursor.execute("DELETE FROM safety_alerts WHERE group_id = %s", (group_id,))
                cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
                cursor.execute("DELETE FROM groups WHERE id = %s", (group_id,))
            if event_id:
                cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()
            cursor.close()
            conn.close()

    def test_list_alerts(self, api_client, keycloak_tokens):
        """List all alerts for authenticated user."""
        response = api_client.get("/api/v1/safety", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)
        assert "total" in data
    
    def test_resolve_alert(self, api_client, keycloak_tokens, cleanup_alerts, integration_env):
        """Test resolving a safety alert."""
        import psycopg2
        from datetime import datetime, timedelta
        
        # Setup: Create event, group, and alert in DB
        db_url = integration_env.get("database_url", "postgresql://crewup:crewup_dev_password@localhost:5432/crewup")
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Initialize variables for cleanup
        event_id = None
        group_id = None
        
        try:
            # Get user1 ID
            user1 = keycloak_tokens["user1"]
            cursor.execute("SELECT id FROM users WHERE keycloak_id = %s", (user1["keycloak_id"],))
            user_id = cursor.fetchone()[0]
            
            # Create event with explicit created_at in the past
            now = datetime.now(timezone.utc)
            created_at = now - timedelta(hours=2)
            event_start = now - timedelta(minutes=30)
            event_end = now + timedelta(hours=1)
            
            cursor.execute(
                """
                INSERT INTO events (id, creator_id, name, description, event_type, address, 
                                    latitude, longitude, event_start, event_end, is_cancelled, created_at)
                VALUES (gen_random_uuid(), %s, 'Resolve Test Event', 'Event for resolve test', 
                        'party', 'Test St', 65.58, 22.15, %s, %s, false, %s)
                RETURNING id
                """,
                (user_id, event_start, event_end, created_at)
            )
            event_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO groups (id, event_id, name, max_members, created_at) VALUES (gen_random_uuid(), %s, 'Test Group', 10, NOW()) RETURNING id",
                (event_id,)
            )
            group_id = cursor.fetchone()[0]
            
            cursor.execute(
                "INSERT INTO group_members (group_id, user_id, is_admin, joined_at) VALUES (%s, %s, true, NOW())",
                (group_id, user_id)
            )
            
            # Create an alert
            cursor.execute(
                """
                INSERT INTO safety_alerts (id, user_id, group_id, latitude, longitude, 
                                          alert_type, message, batch_id, created_at)
                VALUES (gen_random_uuid(), %s, %s, 65.58, 22.15, 'help', 'Test alert', gen_random_uuid(), NOW())
                RETURNING id
                """,
                (user_id, group_id)
            )
            alert_id = cursor.fetchone()[0]
            conn.commit()
            
            # Test resolving the alert
            response = api_client.patch(
                f"/api/v1/safety/{alert_id}/resolve",
                token=user1["access_token"],
                json={"resolved": True}
            )
            
            assert response.status_code == 200, f"Failed to resolve alert: {response.text}"
            data = response.json()
            
            assert data["is_resolved"] is True
            assert data["resolved_at"] is not None
            
        finally:
            # Cleanup
            if group_id:
                cursor.execute("DELETE FROM safety_alerts WHERE group_id = %s", (group_id,))
                cursor.execute("DELETE FROM group_members WHERE group_id = %s", (group_id,))
                cursor.execute("DELETE FROM groups WHERE id = %s", (group_id,))
            if event_id:
                cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()
            cursor.close()
            conn.close()

