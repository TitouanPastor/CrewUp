"""
Unit tests for authentication middleware.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from jose import jwt, JWTError

from app.middleware.auth import (
    get_keycloak_jwks,
    verify_token,
    check_moderator_role,
    get_current_moderator
)


class TestGetKeycloakJWKS:
    """Tests for get_keycloak_jwks function."""

    @patch("app.middleware.auth.requests.get")
    def test_get_keycloak_jwks_success(self, mock_get):
        """Test successful JWKS fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"keys": [{"kid": "test-key"}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Clear the cache first
        get_keycloak_jwks.cache_clear()

        result = get_keycloak_jwks()

        assert result == {"keys": [{"kid": "test-key"}]}
        mock_get.assert_called_once()

    @patch("app.middleware.auth.requests.get")
    def test_get_keycloak_jwks_failure(self, mock_get):
        """Test JWKS fetch failure."""
        mock_get.side_effect = Exception("Connection failed")

        # Clear the cache first
        get_keycloak_jwks.cache_clear()

        with pytest.raises(HTTPException) as exc_info:
            get_keycloak_jwks()

        assert exc_info.value.status_code == 503
        assert "unavailable" in exc_info.value.detail.lower()


class TestCheckModeratorRole:
    """Tests for check_moderator_role function."""

    def test_check_moderator_role_realm_level(self):
        """Test moderator role check at realm level."""
        payload = {
            "sub": "user-123",
            "realm_access": {
                "roles": ["Moderator", "user"]
            },
            "resource_access": {}
        }

        assert check_moderator_role(payload) is True

    def test_check_moderator_role_client_level(self):
        """Test moderator role check at client level."""
        with patch("app.middleware.auth.config.KEYCLOAK_CLIENT_ID", "test-client"):
            payload = {
                "sub": "user-123",
                "realm_access": {
                    "roles": ["user"]
                },
                "resource_access": {
                    "test-client": {
                        "roles": ["Moderator"]
                    }
                }
            }

            assert check_moderator_role(payload) is True

    def test_check_moderator_role_not_present(self):
        """Test when moderator role is not present."""
        payload = {
            "sub": "user-123",
            "realm_access": {
                "roles": ["user"]
            },
            "resource_access": {}
        }

        assert check_moderator_role(payload) is False

    def test_check_moderator_role_missing_fields(self):
        """Test with missing realm_access and resource_access."""
        payload = {
            "sub": "user-123"
        }

        assert check_moderator_role(payload) is False


class TestVerifyToken:
    """Tests for verify_token function."""

    @pytest.mark.asyncio
    @patch("app.middleware.auth.jwt.decode")
    @patch("app.middleware.auth.jwt.get_unverified_header")
    @patch("app.middleware.auth.get_keycloak_jwks")
    async def test_verify_token_success(self, mock_get_jwks, mock_get_header, mock_decode):
        """Test successful token verification."""
        # Mock the JWKS response
        mock_get_jwks.return_value = {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "n": "test-n",
                    "e": "AQAB"
                }
            ]
        }

        # Mock the unverified header
        mock_get_header.return_value = {"kid": "test-key-id"}

        # Mock the decoded payload
        mock_payload = {
            "sub": "user-123",
            "email": "test@example.com"
        }
        mock_decode.return_value = mock_payload

        # Create mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "mock.jwt.token"

        # Call the function
        with patch("jose.backends.RSAKey"):
            result = await verify_token(mock_credentials)

        assert result == mock_payload

    @pytest.mark.asyncio
    async def test_verify_token_no_credentials(self):
        """Test token verification with no credentials."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.middleware.auth.jwt.get_unverified_header")
    @patch("app.middleware.auth.get_keycloak_jwks")
    async def test_verify_token_invalid_kid(self, mock_get_jwks, mock_get_header):
        """Test token verification with invalid key ID."""
        mock_get_jwks.return_value = {
            "keys": [
                {
                    "kid": "different-key-id",
                    "kty": "RSA"
                }
            ]
        }

        mock_get_header.return_value = {"kid": "test-key-id"}

        mock_credentials = Mock()
        mock_credentials.credentials = "mock.jwt.token"

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "signing key" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch("app.middleware.auth.jwt.decode")
    @patch("app.middleware.auth.jwt.get_unverified_header")
    @patch("app.middleware.auth.get_keycloak_jwks")
    async def test_verify_token_missing_claims(self, mock_get_jwks, mock_get_header, mock_decode):
        """Test token verification with missing required claims."""
        mock_get_jwks.return_value = {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "n": "test-n",
                    "e": "AQAB"
                }
            ]
        }

        mock_get_header.return_value = {"kid": "test-key-id"}
        mock_decode.return_value = {"sub": "user-123"}  # Missing email

        mock_credentials = Mock()
        mock_credentials.credentials = "mock.jwt.token"

        with patch("jose.backends.RSAKey"):
            with pytest.raises(HTTPException) as exc_info:
                await verify_token(mock_credentials)

        assert exc_info.value.status_code == 401
        assert "missing required claims" in exc_info.value.detail.lower()


class TestGetCurrentModerator:
    """Tests for get_current_moderator function."""

    @pytest.mark.asyncio
    async def test_get_current_moderator_success(self):
        """Test successful moderator extraction."""
        token_payload = {
            "sub": "moderator-123",
            "email": "mod@test.com",
            "given_name": "Test",
            "family_name": "Moderator",
            "preferred_username": "testmod",
            "realm_access": {
                "roles": ["Moderator"]
            },
            "resource_access": {}
        }

        result = await get_current_moderator(token_payload)

        assert result["keycloak_id"] == "moderator-123"
        assert result["email"] == "mod@test.com"
        assert result["first_name"] == "Test"
        assert result["last_name"] == "Moderator"
        assert result["username"] == "testmod"
        assert "Moderator" in result["roles"]["realm"]

    @pytest.mark.asyncio
    async def test_get_current_moderator_no_role(self):
        """Test moderator extraction when user lacks Moderator role."""
        token_payload = {
            "sub": "user-123",
            "email": "user@test.com",
            "realm_access": {
                "roles": ["user"]
            },
            "resource_access": {}
        }

        with pytest.raises(HTTPException) as exc_info:
            await get_current_moderator(token_payload)

        assert exc_info.value.status_code == 403
        assert "Moderator role required" in exc_info.value.detail
