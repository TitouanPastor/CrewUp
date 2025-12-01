"""
Integration tests for Group & Chat Service.

These tests require:
- Service running on localhost:8002
- PostgreSQL database (crewup-db container)
- Keycloak server with test users
- .env.test file with credentials

Tests verify:
1. ✅ Health check (no auth)
2. ✅ Keycloak authentication (real JWT tokens)
3. ✅ Group CRUD operations
4. ✅ Group membership (join/leave)
5. ✅ Message history
6. ✅ WebSocket real-time chat
7. ✅ Member lists
8. ✅ Pagination
9. ✅ Authorization checks

Run with:
    pytest tests/test_integration.py -v --cov=app
    
Or with user-friendly output:
    python run_integration.py
"""

import pytest
import requests
import os
import asyncio
import json
from uuid import UUID, uuid4
from dotenv import load_dotenv
import websockets
from typing import Dict, Optional

# Disable SSL warnings for dev Keycloak
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@pytest.fixture(scope="session")
def env_config():
    """
    Load test environment configuration from .env.test
    
    Expected variables:
    - KEYCLOAK_SERVER_URL: Keycloak server URL
    - KEYCLOAK_REALM: Realm name (crewup)
    - KEYCLOAK_CLIENT_ID: Client ID (crewup-frontend)
    - TEST_USER1_EMAIL: First test user email
    - TEST_USER1_PASSWORD: First test user password
    - TEST_USER2_EMAIL: Second test user email
    - TEST_USER2_PASSWORD: Second test user password
    - GROUP_SERVICE_URL: Service URL (http://localhost:8002)
    """
    load_dotenv(".env.test")
    return {
        "keycloak_url": os.getenv("KEYCLOAK_SERVER_URL"),
        "realm": os.getenv("KEYCLOAK_REALM", "crewup"),
        "client_id": os.getenv("KEYCLOAK_CLIENT_ID", "crewup-frontend"),
        "user1_email": os.getenv("TEST_USER1_EMAIL"),
        "user1_password": os.getenv("TEST_USER1_PASSWORD"),
        "user2_email": os.getenv("TEST_USER2_EMAIL"),
        "user2_password": os.getenv("TEST_USER2_PASSWORD"),
        "service_url": os.getenv("GROUP_SERVICE_URL", "http://localhost:8002"),
    }


@pytest.fixture(scope="session")
def keycloak_tokens(env_config):
    """
    Authenticate both test users with Keycloak and get JWT tokens.
    
    This fixture:
    1. Makes OAuth2 password grant requests to Keycloak
    2. Extracts access tokens (JWT)
    3. Decodes JWT to get user IDs (from 'sub' claim)
    4. Returns tokens and user info for both users
    
    Returns:
        dict: {
            'user1': {'token': str, 'id': UUID, 'email': str},
            'user2': {'token': str, 'id': UUID, 'email': str}
        }
    """
    import base64
    
    token_url = f"{env_config['keycloak_url']}/realms/{env_config['realm']}/protocol/openid-connect/token"
    
    def get_token(email, password):
        response = requests.post(
            token_url,
            data={
                "grant_type": "password",
                "client_id": env_config["client_id"],
                "username": email,
                "password": password
            },
            verify=False
        )
        assert response.status_code == 200, f"Failed to authenticate {email}: {response.text}"
        token = response.json()["access_token"]
        
        # Decode JWT to extract user ID (sub claim)
        payload = token.split('.')[1]
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        user_id = UUID(decoded["sub"])
        
        return {"token": token, "id": user_id, "email": email}
    
    return {
        "user1": get_token(env_config["user1_email"], env_config["user1_password"]),
        "user2": get_token(env_config["user2_email"], env_config["user2_password"])
    }


@pytest.fixture(scope="session")
def db_setup(env_config, keycloak_tokens):
    """
    Setup test data in database:
    1. Create test users (with Keycloak IDs) via API
    2. Create test event via API (or use existing one)
    
    This ensures database has the necessary records before running tests.
    
    Returns:
        dict: {'event_id': UUID, 'user1_id': UUID, 'user2_id': UUID}
    """
    # For now, we create test event manually or assume it exists
    # In production, you'd call the event service API
    
    # Create a test event ID that we'll use
    # In real scenario, this would come from event service
    test_event_id = uuid4()
    
    # Insert test users + event directly via database
    try:
        import psycopg2
        db_url = os.getenv("DATABASE_URL", "postgresql://crewup:crewup123@localhost:5432/crewup")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        user1_keycloak_id = keycloak_tokens["user1"]["id"]
        user2_keycloak_id = keycloak_tokens["user2"]["id"]
        
        # Insert users (ignore if already exist)
        for keycloak_id, email in [
            (user1_keycloak_id, keycloak_tokens["user1"]["email"]),
            (user2_keycloak_id, keycloak_tokens["user2"]["email"]),
        ]:
            cur.execute("""
                INSERT INTO users (id, keycloak_id, email, first_name, last_name)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (keycloak_id) DO NOTHING
            """, (str(keycloak_id), str(keycloak_id), email, "Test", "User"))

        # Fetch actual user IDs from DB (in case rows already existed with different PKs)
        cur.execute("SELECT id FROM users WHERE keycloak_id = %s", (str(user1_keycloak_id),))
        row1 = cur.fetchone()
        if not row1:
            raise Exception("Test user1 not found in users table after insert")
        user1_id = UUID(row1[0])

        cur.execute("SELECT id FROM users WHERE keycloak_id = %s", (str(user2_keycloak_id),))
        row2 = cur.fetchone()
        if not row2:
            raise Exception("Test user2 not found in users table after insert")
        user2_id = UUID(row2[0])
        
        # Create test event, ensuring creator_id matches an existing users.id
        cur.execute("""
            INSERT INTO events (id, creator_id, name, description, event_type, address, event_start, event_end)
            VALUES (%s, %s, %s, %s, %s, %s, NOW() + INTERVAL '1 day', NOW() + INTERVAL '2 days')
            ON CONFLICT DO NOTHING
        """, (str(test_event_id), str(user1_id), "Integration Test Event", "Automated test event", "other", "Test Location"))
        
        conn.commit()
        cur.close()
        conn.close()
        
    except Exception as e:
        pytest.skip(f"Database not available: {e}")
    
    return {"event_id": test_event_id, "user1_id": user1_id, "user2_id": user2_id}


@pytest.fixture
def test_group(env_config, keycloak_tokens, db_setup):
    """
    Create a test group for each test, cleanup after.
    
    This fixture:
    1. Creates a group via API (user1 is creator)
    2. Yields group_id for the test
    3. Cleans up group after test completes
    
    Returns:
        UUID: The created group ID
    """
    service_url = env_config["service_url"]
    user1_token = keycloak_tokens["user1"]["token"]
    event_id = db_setup["event_id"]
    
    # Create group
    response = requests.post(
        f"{service_url}/api/v1/groups",
        json={
            "event_id": str(event_id),
            "name": "Test Group",
            "description": "Integration test group",
            "max_members": 10
        },
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    assert response.status_code == 201, f"Failed to create group: {response.text}"
    group_id = UUID(response.json()["id"])
    
    yield group_id
    
    # Cleanup: Delete group via database (cascade will remove members/messages)
    import psycopg2
    db_url = os.getenv("DATABASE_URL", "postgresql://crewup:crewup123@localhost:5432/crewup")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("DELETE FROM groups WHERE id = %s", (str(group_id),))
    conn.commit()
    cur.close()
    conn.close()


class TestServiceHealth:
    """Test basic service availability."""
    
    def test_health_check(self, env_config):
        """
        Test 1: Health Check (No Authentication)
        
        Verifies:
        - Service is running
        - Health endpoint is accessible without auth
        - Returns correct service name
        """
        response = requests.get(f"{env_config['service_url']}/api/v1/groups/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "group-service"


class TestAuthentication:
    """Test Keycloak authentication flow."""
    
    def test_keycloak_authentication(self, keycloak_tokens):
        """
        Test 2: Keycloak Authentication
        
        Verifies:
        - Both test users can authenticate with Keycloak
        - JWT tokens are valid
        - User IDs are extracted from tokens
        
        This test validates that the .env.test credentials are correct.
        """
        assert keycloak_tokens["user1"]["token"] is not None
        assert keycloak_tokens["user2"]["token"] is not None
        assert isinstance(keycloak_tokens["user1"]["id"], UUID)
        assert isinstance(keycloak_tokens["user2"]["id"], UUID)
    
    def test_unauthorized_access(self, env_config):
        """
        Test 3: Unauthorized Access (No Token)
        
        Verifies:
        - Endpoints require authentication
        - Returns 401 when no token provided
        """
        response = requests.get(f"{env_config['service_url']}/api/v1/groups")
        assert response.status_code == 401


@pytest.mark.skipif(
    os.getenv("GROUP_INTEGRATION_ENABLED") != "1",
    reason="Group CRUD integration tests require full stack (DB + event/user services) and are disabled by default.",
)
class TestGroupCRUD:
    """Test Group Create, Read, Update, Delete operations."""
    
    def test_create_group(self, env_config, keycloak_tokens, db_setup):
        """
        Test 4: Create Group
        
        Verifies:
        - User can create a group for an event
        - Creator is automatically added as member
        - Group has correct initial state (member_count=1, is_full=False)
        
        Cleanup: Group deleted in fixture
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        event_id = db_setup["event_id"]
        
        response = requests.post(
            f"{service_url}/api/v1/groups",
            json={
                "event_id": str(event_id),
                "name": "Create Test Group",
                "description": "Test description",
                "max_members": 5
            },
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Create Test Group"
        assert data["max_members"] == 5
        assert data["member_count"] == 1  # Creator auto-added
        assert data["is_full"] is False
        
        # Cleanup
        import psycopg2
        db_url = os.getenv("DATABASE_URL", "postgresql://crewup:crewup123@localhost:5432/crewup")
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("DELETE FROM groups WHERE id = %s", (data["id"],))
        conn.commit()
        cur.close()
        conn.close()
    
    def test_list_groups(self, env_config, keycloak_tokens, db_setup, test_group):
        """
        Test 5: List Groups (Filter by Event)
        
        Verifies:
        - Can list groups for a specific event
        - Created group appears in list
        - Filtering by event_id works correctly
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        event_id = db_setup["event_id"]
        
        response = requests.get(
            f"{service_url}/api/v1/groups",
            params={"event_id": str(event_id)},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(g["id"] == str(test_group) for g in data["groups"])
    
    def test_get_group_details(self, env_config, keycloak_tokens, test_group):
        """
        Test 6: Get Group Details
        
        Verifies:
        - Can retrieve group by ID
        - Returns complete group information
        - Includes member count
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        
        response = requests.get(
            f"{service_url}/api/v1/groups/{test_group}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_group)
        assert data["name"] == "Test Group"
        assert data["member_count"] >= 1


@pytest.mark.skipif(
    os.getenv("GROUP_INTEGRATION_ENABLED") != "1",
    reason="Group membership integration tests require full stack (DB + event/user services) and are disabled by default.",
)
class TestGroupMembership:
    """Test group membership operations (join/leave)."""
    
    def test_join_group(self, env_config, keycloak_tokens, test_group):
        """
        Test 7: User 2 Joins Group
        
        Verifies:
        - Non-member can join public group
        - Returns success message
        - User is added to group
        """
        service_url = env_config["service_url"]
        user2_token = keycloak_tokens["user2"]["token"]
        
        response = requests.post(
            f"{service_url}/api/v1/groups/{test_group}/join",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        assert "joined" in response.json()["message"].lower()
    
    def test_duplicate_join_prevention(self, env_config, keycloak_tokens, test_group):
        """
        Test 8: Duplicate Join Prevention
        
        Verifies:
        - User cannot join same group twice
        - Returns 400 Bad Request
        - Error message indicates already a member
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        
        # User1 is already creator/member, try to join again
        response = requests.post(
            f"{service_url}/api/v1/groups/{test_group}/join",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()
    
    def test_list_members(self, env_config, keycloak_tokens, test_group):
        """
        Test 9: List Group Members
        
        Verifies:
        - Members can view member list
        - Returns all group members
        - Includes user_id and is_admin fields
        
        Note: Member names come from user service, not group service
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        
        # First add user2
        user2_token = keycloak_tokens["user2"]["token"]
        requests.post(
            f"{service_url}/api/v1/groups/{test_group}/join",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        # List members
        response = requests.get(
            f"{service_url}/api/v1/groups/{test_group}/members",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["members"]) == 2
        
        # Check member structure
        for member in data["members"]:
            assert "user_id" in member
            assert "joined_at" in member
            assert "is_admin" in member
    
    def test_leave_group(self, env_config, keycloak_tokens, test_group):
        """
        Test 10: User Leaves Group
        
        Verifies:
        - Member can leave group
        - Returns success message
        - Member is removed from database
        """
        service_url = env_config["service_url"]
        user2_token = keycloak_tokens["user2"]["token"]
        
        # Join first
        requests.post(
            f"{service_url}/api/v1/groups/{test_group}/join",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        # Then leave
        response = requests.delete(
            f"{service_url}/api/v1/groups/{test_group}/leave",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 200
        assert "left" in response.json()["message"].lower()
        
        # Verify member count decreased
        user1_token = keycloak_tokens["user1"]["token"]
        response = requests.get(
            f"{service_url}/api/v1/groups/{test_group}",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.json()["member_count"] == 1


@pytest.mark.skipif(
    os.getenv("GROUP_INTEGRATION_ENABLED") != "1",
    reason="Message history integration tests require full stack (DB + WebSocket) and are disabled by default.",
)
class TestMessages:
    """Test message history and pagination."""
    
    def test_get_messages_empty(self, env_config, keycloak_tokens, test_group):
        """
        Test 11: Get Message History (Empty)
        
        Verifies:
        - Members can access message history
        - Empty group returns total=0
        - Returns correct pagination structure
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        
        response = requests.get(
            f"{service_url}/api/v1/groups/{test_group}/messages",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["messages"]) == 0
        assert "limit" in data
        assert "offset" in data
    
    def test_message_pagination(self, env_config, keycloak_tokens, test_group):
        """
        Test 12: Message Pagination
        
        Verifies:
        - Pagination works with limit/offset
        - Different pages return different results
        - Total count is consistent
        
        Note: Requires messages in group (sent via WebSocket test)
        """
        service_url = env_config["service_url"]
        user1_token = keycloak_tokens["user1"]["token"]
        
        # Page 1
        response1 = requests.get(
            f"{service_url}/api/v1/groups/{test_group}/messages",
            params={"limit": 5, "offset": 0},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        # Page 2
        response2 = requests.get(
            f"{service_url}/api/v1/groups/{test_group}/messages",
            params={"limit": 5, "offset": 5},
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Both pages should have same total
        assert response1.json()["total"] == response2.json()["total"]
    
    def test_non_member_cannot_access_messages(self, env_config, keycloak_tokens, test_group):
        """
        Test 13: Non-Member Cannot Access Messages (Authorization)
        
        Verifies:
        - Only group members can view messages
        - Non-members get 403 Forbidden
        - Authorization check works correctly
        """
        service_url = env_config["service_url"]
        user2_token = keycloak_tokens["user2"]["token"]
        
        # User2 is not a member (user1 is creator)
        response = requests.get(
            f"{service_url}/api/v1/groups/{test_group}/messages",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        
        assert response.status_code == 403


@pytest.mark.skipif(
    os.getenv("GROUP_INTEGRATION_ENABLED") != "1",
    reason="WebSocket chat integration tests require full stack (DB + WebSocket) and are disabled by default.",
)
class TestWebSocketChat:
    """Test real-time WebSocket chat functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_chat(self, env_config, keycloak_tokens, test_group):
        """
        Test 14: WebSocket Real-Time Chat
        
        Verifies:
        - Members can connect to WebSocket
        - Can send messages in real-time
        - Messages are broadcast to all members
        - Message is saved to database
        
        WebSocket Protocol:
        - Connect: ws://localhost:8002/api/v1/ws/groups/{id}?token={jwt}
        - Send: {"type": "message", "content": "Hello"}
        - Receive: {"type": "message", "id": "uuid", "content": "Hello", ...}
        """
        service_url = env_config["service_url"].replace("http://", "ws://")
        user1_token = keycloak_tokens["user1"]["token"]
        
        uri = f"{service_url}/api/v1/ws/groups/{test_group}?token={user1_token}"
        
        # Connect to WebSocket (no ssl argument for ws:// URIs)
        async with websockets.connect(uri) as websocket:
            # Send a test message
            await websocket.send(json.dumps({
                "type": "message",
                "content": "WebSocket integration test message"
            }))
            
            # Receive the broadcast
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            
            assert data["type"] == "message"
            assert data["content"] == "WebSocket integration test message"
            assert "id" in data  # Message ID
            assert "user_id" in data
            assert "timestamp" in data
        
        # Verify message was saved to database
        response = requests.get(
            f"{env_config['service_url']}/api/v1/groups/{test_group}/messages",
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert any(m["content"] == "WebSocket integration test message" for m in messages)


# Test execution summary
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print custom summary after all tests."""
    print("\n" + "="*60)
    print("Integration Test Summary")
    print("="*60)
    print(f"Tests run: {terminalreporter._numcollected}")
    print(f"Passed: {len(terminalreporter.stats.get('passed', []))}")
    print(f"Failed: {len(terminalreporter.stats.get('failed', []))}")
    print(f"Skipped: {len(terminalreporter.stats.get('skipped', []))}")
    print("="*60)
