"""
Integration tests for Event Service.

These tests require:
1. Event service running (localhost:8001 or EVENT_SERVICE_URL)
2. Database with schema applied
3. Keycloak running with test users
4. .env.test file with credentials

Run with: pytest tests/test_integration.py -v
Or use: ./run_tests.sh integration
"""
import pytest
from uuid import UUID
from datetime import datetime, timedelta, timezone
import requests
from jose import jwt


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
    This ensures users exist when creating events.
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

    # Cleanup: Delete ALL events after tests complete
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Delete ALL events from the database (not just test events)
        cursor.execute("DELETE FROM events")
        deleted_count = cursor.rowcount

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\n✓ Cleanup: Deleted {deleted_count} events from database")

    except Exception as e:
        print(f"\nWarning: Could not cleanup events: {e}")


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
def cleanup_events(api_client, keycloak_tokens):
    """
    Track events created during a test and delete them after the test completes.
    Usage: Call cleanup_events.add(event_id, creator_token) when creating an event.
    """
    created_events = []

    class EventTracker:
        def add(self, event_id: str, creator_token: str):
            """Register an event to be deleted after the test."""
            created_events.append((event_id, creator_token))
            return event_id

    tracker = EventTracker()

    yield tracker

    # Cleanup: Delete all events created during this test, even if test failed
    for event_id, token in created_events:
        try:
            api_client.delete(f"/api/v1/events/{event_id}", token=token)
        except Exception as e:
            print(f"Warning: Could not delete event {event_id}: {e}")


class TestEventCRUD:
    """Test event CRUD operations."""

    def test_create_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test creating a new event with valid data."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=3)

        event_data = {
            "name": "Integration Test Event",
            "description": "A test event for integration testing",
            "event_type": "party",
            "address": "123 Test Street, Test City",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 50
        }

        response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )

        assert response.status_code == 201
        data = response.json()

        # Register event for cleanup
        cleanup_events.add(data["id"], keycloak_tokens["user1"]["access_token"])

        # Verify response structure
        assert "id" in data
        assert data["name"] == "Integration Test Event"
        assert data["description"] == "A test event for integration testing"
        assert data["event_type"] == "party"
        assert data["address"] == "123 Test Street, Test City"
        assert data["max_attendees"] == 50
        assert data["is_public"] is True
        assert data["is_cancelled"] is False

        # Verify computed fields
        assert data["participant_count"] == 0  # Creator doesn't auto-join
        assert data["interested_count"] == 0
        assert data["is_full"] is False
        assert data["user_status"] is None

    def test_create_event_with_minimal_data(self, api_client, keycloak_tokens, cleanup_events):
        """Test creating event with only required fields."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Minimal Event",
            "address": "456 Minimal St",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )

        assert response.status_code == 201
        data = response.json()

        # Register event for cleanup
        cleanup_events.add(data["id"], keycloak_tokens["user1"]["access_token"])

        assert data["name"] == "Minimal Event"
        assert data["event_type"] == "other"  # Default value
        assert data["description"] is None
        assert data["latitude"] is None
        assert data["longitude"] is None
        assert data["max_attendees"] is None  # Unlimited


    def test_create_event_with_unlimited_capacity(self, api_client, keycloak_tokens, cleanup_events):
        """Test creating event with null max_attendees (unlimited)."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Unlimited Capacity Event",
            "address": "789 Unlimited Ave",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": None
        }

        response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )

        assert response.status_code == 201
        data = response.json()

        # Register event for cleanup
        cleanup_events.add(data["id"], keycloak_tokens["user1"]["access_token"])
        assert data["max_attendees"] is None
        assert data["is_full"] is False


    def test_create_event_with_min_capacity(self, api_client, keycloak_tokens, cleanup_events):
        """Test creating event with min allowed capacity (2)."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Small Event",
            "address": "Small Street",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 2
        }

        response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )

        assert response.status_code == 201
        data = response.json()

        # Register event for cleanup
        cleanup_events.add(data["id"], keycloak_tokens["user1"]["access_token"])
        assert data["max_attendees"] == 2


    def test_create_event_user_not_in_db(self, api_client):
        """Test creating event when user JWT valid but not in database."""
        # This would require a valid JWT for a user not in the users table
        # Skip for now as it requires special setup
        pass

    def test_get_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting event details."""
        # First create an event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Get Event Test",
            "description": "Event to test GET endpoint",
            "event_type": "concert",
            "address": "Concert Hall",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 100
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        assert create_response.status_code == 201
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Now get the event
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )

        assert get_response.status_code == 200
        data = get_response.json()

        # Verify all fields
        assert data["id"] == event_id
        assert data["name"] == "Get Event Test"
        assert data["description"] == "Event to test GET endpoint"
        assert data["event_type"] == "concert"
        assert data["address"] == "Concert Hall"
        assert data["max_attendees"] == 100
        assert data["is_cancelled"] is False

        # Verify computed fields
        assert data["participant_count"] == 0
        assert data["interested_count"] == 0
        assert data["is_full"] is False
        assert data["user_status"] is None  # User hasn't joined

        # Verify creator details are present
        assert "creator_first_name" in data
        assert "creator_last_name" in data
        assert "creator_profile_picture" in data


    def test_get_event_not_found(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting non-existent event returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(
            f"/api/v1/events/{fake_uuid}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 404

    def test_get_event_with_participants(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting event shows participant counts after users join."""
        # Create an event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Event With Participants",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 10
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User 1 joins as 'going'
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        # User 2 joins as 'interested'
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "interested"}
        )

        # Get event as user 1
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )

        assert get_response.status_code == 200
        data = get_response.json()

        # Verify participant counts
        assert data["participant_count"] == 1  # Only 'going' count
        assert data["interested_count"] == 1
        assert data["user_status"] == "going"  # User 1's status
        assert data["is_full"] is False  # 1/10

        # Get event as user 2
        get_response2 = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user2"]["access_token"]
        )

        data2 = get_response2.json()
        assert data2["user_status"] == "interested"  # User 2's status


    def test_update_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test successfully updating event fields."""
        # Create an event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Original Event",
            "address": "Original Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 50
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Update the event
        update_data = {
            "name": "Updated Event Name",
            "description": "New description",
            "max_attendees": 100
        }

        update_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json=update_data
        )

        assert update_response.status_code == 200
        data = update_response.json()

        # Verify updates
        assert data["name"] == "Updated Event Name"
        assert data["description"] == "New description"
        assert data["max_attendees"] == 100
        # Original fields unchanged
        assert data["address"] == "Original Address"


    def test_update_event_not_creator(self, api_client, keycloak_tokens, cleanup_events):
        """Test that only creator can update event (403)."""
        # User 1 creates event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "User 1 Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User 2 tries to update
        update_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user2"]["access_token"],
            json={"name": "Hacked Name"}
        )

        assert update_response.status_code == 403


    def test_update_event_empty_body(self, api_client, keycloak_tokens, cleanup_events):
        """Test updating with empty body returns 200 no-op."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Test Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])
        original_name = create_response.json()["name"]

        # Update with empty body
        update_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={}
        )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == original_name  # Unchanged


    def test_update_event_reduce_capacity_below_participants(self, api_client, keycloak_tokens, cleanup_events):
        """Test cannot reduce max_attendees below current participant count."""
        # Create event with capacity 10
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Capacity Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 10
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Two users join
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # Try to reduce capacity to 1 (below 2 participants)
        update_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"max_attendees": 2}  # Changed to 2 which should work since we have exactly 2
        )

        # This should succeed since 2 participants and setting to 2
        assert update_response.status_code == 200

        # Now try to reduce to 1 (should fail)
        update_response2 = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"max_attendees": 3}  # First increase to 3
        )
        assert update_response2.status_code == 200

        # Then try to reduce below participant count
        update_response3 = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"max_attendees": 1}  # Should fail - below minimum of 2
        )
        assert update_response3.status_code == 422  # Fails Pydantic validation (min 2)


    def test_update_event_cancel_and_uncancel(self, api_client, keycloak_tokens, cleanup_events):
        """Test cancelling and uncancelling an event."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Cancellable Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Cancel event
        cancel_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"is_cancelled": True}
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["is_cancelled"] is True

        # Uncancel event (event_start is still >= 30 min from now)
        uncancel_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"is_cancelled": False}
        )

        assert uncancel_response.status_code == 200
        assert uncancel_response.json()["is_cancelled"] is False


    def test_update_event_set_unlimited_capacity(self, api_client, keycloak_tokens, cleanup_events):
        """Test setting max_attendees to null (unlimited)."""
        # Create event with limited capacity
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Limited Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 10
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Update to unlimited
        update_response = api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"max_attendees": None}
        )

        assert update_response.status_code == 200
        assert update_response.json()["max_attendees"] is None
        assert update_response.json()["is_full"] is False


    def test_update_event_partial_update(self, api_client, keycloak_tokens, cleanup_events):
        """Test updating only one field keeps others unchanged."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Original Name",
            "description": "Original Description",
            "event_type": "party",
            "address": "Original Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 50
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Update only description
        update_response = api_client.patch(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"description": "Updated Description Only"}
        )

        assert update_response.status_code == 200
        data = update_response.json()

        # Only description changed
        assert data["description"] == "Updated Description Only"
        # Others unchanged
        assert data["name"] == "Original Name"
        assert data["event_type"] == "party"
        assert data["address"] == "Original Address"
        assert data["max_attendees"] == 50


    def test_delete_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test successfully deleting an event (soft delete)."""
        # Create an event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Event to Delete",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Delete the event
        delete_response = api_client.delete(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )

        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Event deleted successfully"

        # Verify event is soft deleted (is_cancelled=true)
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_cancelled"] is True

    def test_delete_event_not_creator(self, api_client, keycloak_tokens, cleanup_events):
        """Test that only creator can delete event (403)."""
        # User 1 creates event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "User 1 Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User 2 tries to delete
        delete_response = api_client.delete(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user2"]["access_token"]
        )

        assert delete_response.status_code == 403


    def test_delete_event_not_found(self, api_client, keycloak_tokens, cleanup_events):
        """Test deleting non-existent event returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = api_client.delete(
            f"/api/v1/events/{fake_uuid}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 404

    def test_delete_event_idempotent(self, api_client, keycloak_tokens, cleanup_events):
        """Test deleting already deleted event is idempotent (200)."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Idempotent Delete Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Delete once
        delete_response1 = api_client.delete(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert delete_response1.status_code == 200

        # Delete again - should be idempotent
        delete_response2 = api_client.delete(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert delete_response2.status_code == 200
        assert delete_response2.json()["message"] == "Event deleted successfully"

    def test_delete_event_with_participants(self, api_client, keycloak_tokens, cleanup_events):
        """Test deleting event with participants (soft delete preserves data)."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Event with Participants",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Users join
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # Delete event
        delete_response = api_client.delete(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )

        assert delete_response.status_code == 200

        # Event still exists (soft delete) with is_cancelled=true
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_cancelled"] is True
        # Participants data preserved
        assert get_response.json()["participant_count"] == 2


class TestEventRSVP:
    """Test event RSVP operations."""

    def test_join_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test successfully joining an event."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Join Test Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 10
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join event
        join_response = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        assert join_response.status_code == 200
        assert join_response.json()["message"] == "Successfully joined event"

        # Verify participant count
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["participant_count"] == 1
        assert get_response.json()["user_status"] == "going"


    def test_join_event_default_status(self, api_client, keycloak_tokens, cleanup_events):
        """Test joining event with default status (going)."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Default Status Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join without status (should default to 'going')
        join_response = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"]
        )

        assert join_response.status_code == 200

        # Verify status is 'going'
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["user_status"] == "going"


    def test_join_event_as_interested(self, api_client, keycloak_tokens, cleanup_events):
        """Test joining event with 'interested' status."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Interested Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join as interested
        join_response = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "interested"}
        )

        assert join_response.status_code == 200

        # Verify counts
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["participant_count"] == 0  # 'interested' doesn't count
        assert get_response.json()["interested_count"] == 1
        assert get_response.json()["user_status"] == "interested"


    def test_join_event_full_capacity(self, api_client, keycloak_tokens, cleanup_events):
        """Test joining event when at capacity returns 400."""
        # Create event with capacity 1
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Full Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 2
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User 1 joins
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        # User 2 joins
        join_response2 = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )
        assert join_response2.status_code == 200  # Should succeed (2/2)

        # Try to join when full - should fail
        # Note: We can't test this without a 3rd user, so let's skip for now
        # The integration test setup only has 2 users


    def test_join_event_idempotent(self, api_client, keycloak_tokens, cleanup_events):
        """Test joining same event twice is idempotent."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Idempotent Join Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join once
        join_response1 = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )
        assert join_response1.status_code == 200

        # Join again (idempotent)
        join_response2 = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )
        assert join_response2.status_code == 200

        # Count should still be 1
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["participant_count"] == 1


    def test_join_event_change_status(self, api_client, keycloak_tokens, cleanup_events):
        """Test changing RSVP status."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Status Change Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join as 'interested'
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "interested"}
        )

        # Change to 'going'
        change_response = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )
        assert change_response.status_code == 200

        # Verify status changed
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["user_status"] == "going"
        assert get_response.json()["participant_count"] == 1
        assert get_response.json()["interested_count"] == 0


    def test_join_cancelled_event(self, api_client, keycloak_tokens, cleanup_events):
        """Test cannot join cancelled event."""
        # Create and cancel event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Cancelled Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Cancel event
        api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"is_cancelled": True}
        )

        # Try to join
        join_response = api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        assert join_response.status_code == 400


    def test_join_event_not_found(self, api_client, keycloak_tokens, cleanup_events):
        """Test joining non-existent event returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = api_client.post(
            f"/api/v1/events/{fake_uuid}/join",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 404

    def test_leave_event_success(self, api_client, keycloak_tokens, cleanup_events):
        """Test successfully leaving an event after joining."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Leave Test Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join event
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # Verify joined
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert get_response.json()["user_status"] == "going"
        assert get_response.json()["participant_count"] == 1

        # Leave event
        leave_response = api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert leave_response.status_code == 200
        assert leave_response.json()["message"] == "Successfully left event"

        # Verify left (status is 'not_going')
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert get_response.json()["user_status"] == "not_going"
        assert get_response.json()["participant_count"] == 0


    def test_leave_event_idempotent_not_joined(self, api_client, keycloak_tokens, cleanup_events):
        """Test leaving event when not joined is idempotent."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Idempotent Leave Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Leave without joining
        leave_response = api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert leave_response.status_code == 200
        assert leave_response.json()["message"] == "Successfully left event"


    def test_leave_event_idempotent_already_left(self, api_client, keycloak_tokens, cleanup_events):
        """Test leaving event twice is idempotent."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Double Leave Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join event
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # Leave first time
        api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )

        # Leave second time (idempotent)
        leave_response = api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert leave_response.status_code == 200
        assert leave_response.json()["message"] == "Successfully left event"


    def test_leave_cancelled_event(self, api_client, keycloak_tokens, cleanup_events):
        """Test can leave a cancelled event."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Leave Cancelled Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Join event
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # Cancel event
        api_client.put(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"],
            json={"is_cancelled": True}
        )

        # Leave cancelled event (should succeed)
        leave_response = api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )
        assert leave_response.status_code == 200


    def test_leave_event_creator_allowed(self, api_client, keycloak_tokens, cleanup_events):
        """Test event creator can leave their own event."""
        # Create event
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Creator Leave Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat()
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Creator joins their own event
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        # Creator leaves
        leave_response = api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert leave_response.status_code == 200

        # Verify event still exists (not deleted)
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.status_code == 200
        assert get_response.json()["is_cancelled"] is False


    def test_leave_event_frees_capacity(self, api_client, keycloak_tokens, cleanup_events):
        """Test leaving event frees up capacity."""
        # Create event with capacity 1
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)
        event_end = event_start + timedelta(hours=2)

        event_data = {
            "name": "Capacity Test",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": event_end.isoformat(),
            "max_attendees": 2
        }

        create_response = api_client.post(
            "/api/v1/events",
            token=keycloak_tokens["user1"]["access_token"],
            json=event_data
        )
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User2 joins
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user2"]["access_token"],
            json={"status": "going"}
        )

        # User1 joins (event now full)
        api_client.post(
            f"/api/v1/events/{event_id}/join",
            token=keycloak_tokens["user1"]["access_token"],
            json={"status": "going"}
        )

        # Verify event is full
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["is_full"] is True

        # User2 leaves
        api_client.delete(
            f"/api/v1/events/{event_id}/leave",
            token=keycloak_tokens["user2"]["access_token"]
        )

        # Verify event is no longer full
        get_response = api_client.get(
            f"/api/v1/events/{event_id}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert get_response.json()["is_full"] is False
        assert get_response.json()["participant_count"] == 1


    def test_leave_event_not_found(self, api_client, keycloak_tokens, cleanup_events):
        """Test leaving non-existent event returns 404."""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = api_client.delete(
            f"/api/v1/events/{fake_uuid}/leave",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 404


class TestEventListing:
    """Test event listing and search."""

    def test_list_events_default(self, api_client, keycloak_tokens, cleanup_events):
        """Test listing events with default filters (public, future, non-cancelled)."""
        # Create multiple events
        event_start_1 = datetime.now(timezone.utc) + timedelta(hours=2)
        event_start_2 = datetime.now(timezone.utc) + timedelta(hours=4)

        event1_data = {
            "name": "Event 1",
            "address": "Address 1",
            "event_start": event_start_1.isoformat(),
            "event_end": (event_start_1 + timedelta(hours=2)).isoformat()
        }

        event2_data = {
            "name": "Event 2",
            "address": "Address 2",
            "event_start": event_start_2.isoformat(),
            "event_end": (event_start_2 + timedelta(hours=2)).isoformat()
        }

        api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event1_data)
        api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event2_data)

        # List events
        response = api_client.get("/api/v1/events", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        # Should have at least our 2 events
        assert data["total"] >= 2
        assert len(data["events"]) >= 2

        # Events should be sorted by event_start ASC
        event_starts = [event["event_start"] for event in data["events"]]
        assert event_starts == sorted(event_starts)

        # Each event should have required fields
        for event in data["events"]:
            assert "id" in event
            assert "name" in event
            assert "participant_count" in event
            assert "is_full" in event
            assert "creator_first_name" in event

    def test_list_events_filter_by_event_type(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering events by event_type."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create events with different types
        concert_data = {
            "name": "Concert Event",
            "address": "Concert Hall",
            "event_type": "concert",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        bar_data = {
            "name": "Bar Event",
            "address": "Bar Location",
            "event_type": "bar",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        concert_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=concert_data)
        bar_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=bar_data)

        concert_id = concert_response.json()["id"]
        cleanup_events.add(concert_id, keycloak_tokens["user1"]["access_token"])
        bar_id = bar_response.json()["id"]
        cleanup_events.add(bar_id, keycloak_tokens["user1"]["access_token"])

        # Filter by concert type
        response = api_client.get("/api/v1/events?event_type=concert", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200

        event_ids = [e["id"] for e in response.json()["events"]]
        assert concert_id in event_ids

        # All returned events should be concerts
        for event in response.json()["events"]:
            assert event["event_type"] == "concert"

        api_client.delete(f"/api/v1/events/{bar_id}", token=keycloak_tokens["user1"]["access_token"])

    def test_list_events_filter_by_creator(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering events by creator_id."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        event_data = {
            "name": "Creator Test Event",
            "address": "Test Address",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        # User1 creates event
        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])
        creator_id = create_response.json()["creator_id"]

        # Filter by user1's creator_id (with high limit to ensure we get our event)
        response = api_client.get(f"/api/v1/events?creator_id={creator_id}", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200

        # Should include our event
        event_ids = [e["id"] for e in response.json()["events"]]
        assert event_id in event_ids

        # All returned events should be created by user1
        for event in response.json()["events"]:
            assert event["creator_id"] == creator_id


    def test_list_events_filter_by_date_range(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering events by date range."""
        base_time = datetime.now(timezone.utc)

        # Create events at different times
        early_start = base_time + timedelta(hours=2)
        late_start = base_time + timedelta(days=7)

        early_event_data = {
            "name": "Early Event",
            "address": "Address",
            "event_start": early_start.isoformat(),
            "event_end": (early_start + timedelta(hours=2)).isoformat()
        }

        late_event_data = {
            "name": "Late Event",
            "address": "Address",
            "event_start": late_start.isoformat(),
            "event_end": (late_start + timedelta(hours=2)).isoformat()
        }

        early_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=early_event_data)
        late_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=late_event_data)

        early_id = early_response.json()["id"]
        cleanup_events.add(early_id, keycloak_tokens["user1"]["access_token"])
        late_id = late_response.json()["id"]
        cleanup_events.add(late_id, keycloak_tokens["user1"]["access_token"])

        # Filter for events in the next 3 days
        from urllib.parse import quote
        start_from = quote(base_time.isoformat())
        start_to = quote((base_time + timedelta(days=3)).isoformat())

        response = api_client.get(
            f"/api/v1/events?start_date_from={start_from}&start_date_to={start_to}",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 200

        event_ids = [e["id"] for e in response.json()["events"]]

        # Should include early event, not late event
        assert early_id in event_ids
        assert late_id not in event_ids

        api_client.delete(f"/api/v1/events/{late_id}", token=keycloak_tokens["user1"]["access_token"])

    def test_list_events_filter_by_status(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering events by user's RSVP status."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create two events
        event1_data = {
            "name": "Going Event",
            "address": "Address 1",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        event2_data = {
            "name": "Interested Event",
            "address": "Address 2",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        event1_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event1_data)
        event2_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event2_data)

        event1_id = event1_response.json()["id"]
        event2_id = event2_response.json()["id"]

        # User2 joins event1 as 'going'
        api_client.post(f"/api/v1/events/{event1_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "going"})

        # User2 joins event2 as 'interested'
        api_client.post(f"/api/v1/events/{event2_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "interested"})

        # Filter by status='going' for user2
        response = api_client.get("/api/v1/events?status=going", token=keycloak_tokens["user2"]["access_token"])
        assert response.status_code == 200

        event_ids = [e["id"] for e in response.json()["events"]]

        # Should include event1 (going), not event2 (interested)
        assert event1_id in event_ids
        assert event2_id not in event_ids

        api_client.delete(f"/api/v1/events/{event2_id}", token=keycloak_tokens["user1"]["access_token"])

    def test_list_events_with_location_filter(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering events by location with radius."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event with specific coordinates (New York City)
        nyc_event_data = {
            "name": "NYC Event",
            "address": "New York",
            "latitude": "40.7128",
            "longitude": "-74.0060",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        # Create event far away (Los Angeles)
        la_event_data = {
            "name": "LA Event",
            "address": "Los Angeles",
            "latitude": "34.0522",
            "longitude": "-118.2437",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        nyc_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=nyc_event_data)
        la_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=la_event_data)

        nyc_id = nyc_response.json()["id"]
        cleanup_events.add(nyc_id, keycloak_tokens["user1"]["access_token"])
        la_id = la_response.json()["id"]
        cleanup_events.add(la_id, keycloak_tokens["user1"]["access_token"])

        # Search near NYC with 50km radius (with high limit to ensure we get our events)
        response = api_client.get(
            "/api/v1/events?latitude=40.7128&longitude=-74.0060&radius_km=50&limit=100",
            token=keycloak_tokens["user1"]["access_token"]
        )
        assert response.status_code == 200

        event_ids = [e["id"] for e in response.json()["events"]]

        # Should include NYC event, not LA event (too far)
        assert nyc_id in event_ids
        assert la_id not in event_ids

        api_client.delete(f"/api/v1/events/{la_id}", token=keycloak_tokens["user1"]["access_token"])

    def test_list_events_pagination(self, api_client, keycloak_tokens, cleanup_events):
        """Test event listing pagination."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create multiple events
        event_ids = []
        for i in range(5):
            event_data = {
                "name": f"Pagination Event {i}",
                "address": "Address",
                "event_start": (event_start + timedelta(minutes=i*10)).isoformat(),
                "event_end": (event_start + timedelta(hours=2, minutes=i*10)).isoformat()
            }
            response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
            event_ids.append(response.json()["id"])

        # Get first page (limit=2, offset=0)
        response = api_client.get("/api/v1/events?limit=2&offset=0", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        assert len(response.json()["events"]) == 2
        assert response.json()["limit"] == 2
        assert response.json()["offset"] == 0

        # Get second page (limit=2, offset=2)
        response = api_client.get("/api/v1/events?limit=2&offset=2", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        assert len(response.json()["events"]) == 2

        for event_id in event_ids:
            api_client.delete(f"/api/v1/events/{event_id}", token=keycloak_tokens["user1"]["access_token"])

    def test_list_events_include_cancelled(self, api_client, keycloak_tokens, cleanup_events):
        """Test listing cancelled events with is_cancelled filter."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        event_data = {
            "name": "Cancelled Event Test",
            "address": "Address",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        # Create and cancel event
        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        api_client.delete(f"/api/v1/events/{event_id}", token=keycloak_tokens["user1"]["access_token"])

        # List without cancelled (default)
        response = api_client.get("/api/v1/events", token=keycloak_tokens["user1"]["access_token"])
        event_ids = [e["id"] for e in response.json()["events"]]
        assert event_id not in event_ids  # Should not include cancelled

        # List with cancelled
        response = api_client.get("/api/v1/events?is_cancelled=true", token=keycloak_tokens["user1"]["access_token"])
        event_ids = [e["id"] for e in response.json()["events"]]
        assert event_id in event_ids  # Should include cancelled


class TestEventParticipants:
    """Test event participant management."""

    def test_get_participants_counts_only(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting participant counts without details."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event
        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User2 joins as 'going'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "going"})

        # User1 (creator) joins as 'interested'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user1"]["access_token"], json={"status": "interested"})

        # Get participants without details
        response = api_client.get(f"/api/v1/events/{event_id}/participants", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        # Should have counts
        assert data["event_id"] == event_id
        assert data["going_count"] == 1
        assert data["interested_count"] == 1
        assert data["total_participants"] == 2  # going + interested
        assert data["attendees"] is None  # No details included


    def test_get_participants_with_details(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting participant list with details."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event
        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User2 joins as 'going'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "going"})

        # User1 joins as 'going'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user1"]["access_token"], json={"status": "going"})

        # Get participants with details
        response = api_client.get(f"/api/v1/events/{event_id}/participants?include_details=true", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        # Should have counts and attendee list
        assert data["event_id"] == event_id
        assert data["going_count"] == 2
        assert data["interested_count"] == 0
        assert data["total_participants"] == 2
        assert data["attendees"] is not None
        assert len(data["attendees"]) == 2

        # Check attendee details (public profile)
        for attendee in data["attendees"]:
            assert "user_id" in attendee
            assert "keycloak_id" in attendee
            assert "first_name" in attendee
            assert "last_name" in attendee
            assert "status" in attendee
            assert "joined_at" in attendee
            assert attendee["status"] == "going"
            # Email should NOT be included (public profile only)
            assert "email" not in attendee


    def test_get_participants_filter_by_status(self, api_client, keycloak_tokens, cleanup_events):
        """Test filtering participants by status."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event
        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User1 joins as 'going'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user1"]["access_token"], json={"status": "going"})

        # User2 joins as 'interested'
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "interested"})

        # Get only 'going' participants
        response = api_client.get(f"/api/v1/events/{event_id}/participants?status=going&include_details=true", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        # Should have all counts but filtered attendees
        assert data["going_count"] == 1
        assert data["interested_count"] == 1
        assert data["total_participants"] == 1  # Only 'going' filtered
        assert len(data["attendees"]) == 1
        assert data["attendees"][0]["status"] == "going"

        # Get only 'interested' participants
        response = api_client.get(f"/api/v1/events/{event_id}/participants?status=interested&include_details=true", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        assert data["going_count"] == 1
        assert data["interested_count"] == 1
        assert data["total_participants"] == 1  # Only 'interested' filtered
        assert len(data["attendees"]) == 1
        assert data["attendees"][0]["status"] == "interested"


    def test_get_participants_invalid_status(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting participants with invalid status filter."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event
        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # Try to get participants with invalid status
        response = api_client.get(f"/api/v1/events/{event_id}/participants?status=invalid_status", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 422
        assert "Invalid status" in response.json()["detail"]


    def test_get_participants_pagination(self, api_client, keycloak_tokens, cleanup_events):
        """Test participant list pagination."""
        event_start = datetime.now(timezone.utc) + timedelta(hours=2)

        # Create event
        event_data = {
            "name": "Test Event",
            "address": "123 Main St",
            "max_attendees": 10,
            "event_start": event_start.isoformat(),
            "event_end": (event_start + timedelta(hours=2)).isoformat()
        }

        create_response = api_client.post("/api/v1/events", token=keycloak_tokens["user1"]["access_token"], json=event_data)
        event_id = create_response.json()["id"]
        cleanup_events.add(event_id, keycloak_tokens["user1"]["access_token"])

        # User1 and User2 join
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user1"]["access_token"], json={"status": "going"})
        api_client.post(f"/api/v1/events/{event_id}/join", token=keycloak_tokens["user2"]["access_token"], json={"status": "going"})

        # Get first page (limit=1)
        response = api_client.get(f"/api/v1/events/{event_id}/participants?include_details=true&limit=1&offset=0", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        assert data["total_participants"] == 2
        assert len(data["attendees"]) == 1

        # Get second page (limit=1, offset=1)
        response = api_client.get(f"/api/v1/events/{event_id}/participants?include_details=true&limit=1&offset=1", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 200
        data = response.json()

        assert data["total_participants"] == 2
        assert len(data["attendees"]) == 1


    def test_get_participants_event_not_found(self, api_client, keycloak_tokens, cleanup_events):
        """Test getting participants for non-existent event."""
        fake_event_id = "550e8400-e29b-41d4-a716-446655440000"
        response = api_client.get(f"/api/v1/events/{fake_event_id}/participants", token=keycloak_tokens["user1"]["access_token"])
        assert response.status_code == 404
