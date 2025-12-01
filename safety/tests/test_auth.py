"""Tests for authentication middleware."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from fastapi.security import HTTPAuthorizationCredentials


class TestGetKeycloakPublicKey:
    """Tests for get_keycloak_public_key function."""

    def test_public_key_fetch_success(self):
        """Test successful public key fetch."""
        from app.middleware.auth import get_keycloak_public_key

        # Clear cache before test
        get_keycloak_public_key.cache_clear()

        mock_realm_data = {"public_key": "MOCK_PUBLIC_KEY_DATA"}

        with patch("app.middleware.auth.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_realm_data
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = get_keycloak_public_key()

            assert "BEGIN PUBLIC KEY" in result
            assert "MOCK_PUBLIC_KEY_DATA" in result
            assert "END PUBLIC KEY" in result

    def test_public_key_fetch_missing_key(self):
        """Test public key fetch when key not in response."""
        from app.middleware.auth import get_keycloak_public_key

        get_keycloak_public_key.cache_clear()

        with patch("app.middleware.auth.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {}  # No public_key
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            with pytest.raises(HTTPException) as exc_info:
                get_keycloak_public_key()

            assert exc_info.value.status_code == 503

    def test_public_key_fetch_connection_error(self):
        """Test public key fetch with connection error."""
        from app.middleware.auth import get_keycloak_public_key

        get_keycloak_public_key.cache_clear()

        with patch("app.middleware.auth.httpx.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            with pytest.raises(HTTPException) as exc_info:
                get_keycloak_public_key()

            assert exc_info.value.status_code == 503
            assert "Unable to connect" in exc_info.value.detail


class TestVerifyToken:
    """Tests for verify_token function."""

    def test_verify_token_no_credentials(self):
        """Test verify_token raises 401 when no credentials."""
        from app.middleware.auth import verify_token

        with patch("app.middleware.auth.TESTING", False):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(credentials=None)

            assert exc_info.value.status_code == 401
            assert "Not authenticated" in exc_info.value.detail

    def test_verify_token_testing_mode_with_credentials(self):
        """Test verify_token in testing mode with credentials."""
        from app.middleware.auth import verify_token, MOCK_TEST_USER

        with patch("app.middleware.auth.TESTING", True):
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
            result = verify_token(credentials=credentials)

            assert result["sub"] == MOCK_TEST_USER["keycloak_id"]
            assert result["email"] == MOCK_TEST_USER["email"]

    def test_verify_token_testing_mode_no_credentials(self):
        """Test verify_token in testing mode without credentials."""
        from app.middleware.auth import verify_token

        with patch("app.middleware.auth.TESTING", True):
            with pytest.raises(HTTPException) as exc_info:
                verify_token(credentials=None)

            assert exc_info.value.status_code == 401

    def test_verify_token_valid_jwt(self):
        """Test verify_token with valid JWT."""
        from app.middleware.auth import verify_token, get_keycloak_public_key

        get_keycloak_public_key.cache_clear()

        mock_public_key = "-----BEGIN PUBLIC KEY-----\nMOCK_KEY\n-----END PUBLIC KEY-----"

        with patch("app.middleware.auth.TESTING", False), \
             patch("app.middleware.auth.httpx.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode:

            mock_response = MagicMock()
            mock_response.json.return_value = {"public_key": "MOCK_KEY"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_decode.return_value = {
                "sub": "user-123",
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User"
            }

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
            result = verify_token(credentials=credentials)

            assert result["sub"] == "user-123"
            assert result["email"] == "test@example.com"

    def test_verify_token_jwt_error(self):
        """Test verify_token with JWT validation error."""
        from app.middleware.auth import verify_token, get_keycloak_public_key
        from jose import JWTError

        get_keycloak_public_key.cache_clear()

        with patch("app.middleware.auth.TESTING", False), \
             patch("app.middleware.auth.httpx.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode:

            mock_response = MagicMock()
            mock_response.json.return_value = {"public_key": "MOCK_KEY"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_decode.side_effect = JWTError("Token expired")

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")

            with pytest.raises(HTTPException) as exc_info:
                verify_token(credentials=credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail

    def test_verify_token_generic_exception(self):
        """Test verify_token with generic exception."""
        from app.middleware.auth import verify_token, get_keycloak_public_key

        get_keycloak_public_key.cache_clear()

        with patch("app.middleware.auth.TESTING", False), \
             patch("app.middleware.auth.httpx.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode:

            mock_response = MagicMock()
            mock_response.json.return_value = {"public_key": "MOCK_KEY"}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_decode.side_effect = Exception("Unexpected error")

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")

            with pytest.raises(HTTPException) as exc_info:
                verify_token(credentials=credentials)

            assert exc_info.value.status_code == 500
            assert "Token verification failed" in exc_info.value.detail


class TestGetCurrentUser:
    """Tests for get_current_user function."""

    @pytest.mark.asyncio
    async def test_get_current_user_extracts_info(self):
        """Test get_current_user extracts user info from token payload."""
        from app.middleware.auth import get_current_user

        token_payload = {
            "sub": "keycloak-user-id",
            "email": "user@example.com",
            "given_name": "John",
            "family_name": "Doe",
            "preferred_username": "johndoe"
        }

        result = await get_current_user(token_payload=token_payload)

        assert result["keycloak_id"] == "keycloak-user-id"
        assert result["email"] == "user@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["username"] == "johndoe"

    @pytest.mark.asyncio
    async def test_get_current_user_handles_missing_fields(self):
        """Test get_current_user handles missing optional fields."""
        from app.middleware.auth import get_current_user

        token_payload = {
            "sub": "keycloak-user-id"
            # Missing all optional fields
        }

        result = await get_current_user(token_payload=token_payload)

        assert result["keycloak_id"] == "keycloak-user-id"
        assert result["email"] is None
        assert result["first_name"] is None
        assert result["last_name"] is None
        assert result["username"] is None
