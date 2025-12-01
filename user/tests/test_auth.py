"""Tests for authentication middleware."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from jose import jwt
from fastapi.security import HTTPAuthorizationCredentials


class TestGetKeycloakJwks:
    """Tests for get_keycloak_jwks function."""

    def test_jwks_fetch_success(self):
        """Test successful JWKS fetch."""
        from app.middleware.auth import get_keycloak_jwks

        # Clear cache before test
        get_keycloak_jwks.cache_clear()

        mock_jwks = {"keys": [{"kid": "test-key", "kty": "RSA"}]}

        with patch("app.middleware.auth.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            result = get_keycloak_jwks()

            assert result == mock_jwks
            mock_get.assert_called_once()

    def test_jwks_fetch_failure(self):
        """Test JWKS fetch failure raises 503."""
        from app.middleware.auth import get_keycloak_jwks

        # Clear cache before test
        get_keycloak_jwks.cache_clear()

        with patch("app.middleware.auth.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection failed")

            with pytest.raises(HTTPException) as exc_info:
                get_keycloak_jwks()

            assert exc_info.value.status_code == 503
            assert "Authentication service unavailable" in exc_info.value.detail


class TestVerifyToken:
    """Tests for verify_token function."""

    @pytest.mark.asyncio
    async def test_verify_token_no_credentials(self):
        """Test verify_token raises 401 when no credentials provided."""
        from app.middleware.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_valid_jwt(self):
        """Test verify_token with valid JWT."""
        from app.middleware.auth import verify_token, get_keycloak_jwks

        # Clear cache
        get_keycloak_jwks.cache_clear()

        # Mock JWKS response
        mock_jwks = {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB"
            }]
        }

        with patch("app.middleware.auth.requests.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode, \
             patch("app.middleware.auth.jwt.get_unverified_header") as mock_header:

            mock_response = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_header.return_value = {"kid": "test-kid", "alg": "RS256"}
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "test@example.com",
                "given_name": "Test",
                "family_name": "User"
            }

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")
            result = await verify_token(credentials=credentials)

            assert result["sub"] == "user-123"
            assert result["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_missing_signing_key(self):
        """Test verify_token raises 401 when signing key not found."""
        from app.middleware.auth import verify_token, get_keycloak_jwks

        get_keycloak_jwks.cache_clear()

        mock_jwks = {"keys": [{"kid": "different-kid", "kty": "RSA"}]}

        with patch("app.middleware.auth.requests.get") as mock_get, \
             patch("app.middleware.auth.jwt.get_unverified_header") as mock_header:

            mock_response = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_header.return_value = {"kid": "test-kid", "alg": "RS256"}

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")

            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials=credentials)

            assert exc_info.value.status_code == 401
            assert "Unable to find appropriate signing key" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_missing_claims(self):
        """Test verify_token raises 401 when required claims missing."""
        from app.middleware.auth import verify_token, get_keycloak_jwks

        get_keycloak_jwks.cache_clear()

        mock_jwks = {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB"
            }]
        }

        with patch("app.middleware.auth.requests.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode, \
             patch("app.middleware.auth.jwt.get_unverified_header") as mock_header:

            mock_response = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_header.return_value = {"kid": "test-kid", "alg": "RS256"}
            # Missing 'sub' and 'email' claims
            mock_decode.return_value = {"some_other_claim": "value"}

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")

            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials=credentials)

            assert exc_info.value.status_code == 401
            assert "missing required claims" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_jwt_error(self):
        """Test verify_token raises 401 on JWT validation error."""
        from app.middleware.auth import verify_token, get_keycloak_jwks
        from jose import JWTError

        get_keycloak_jwks.cache_clear()

        mock_jwks = {
            "keys": [{
                "kid": "test-kid",
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB"
            }]
        }

        with patch("app.middleware.auth.requests.get") as mock_get, \
             patch("app.middleware.auth.jwt.decode") as mock_decode, \
             patch("app.middleware.auth.jwt.get_unverified_header") as mock_header:

            mock_response = MagicMock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response

            mock_header.return_value = {"kid": "test-kid", "alg": "RS256"}
            mock_decode.side_effect = JWTError("Token expired")

            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake-token")

            with pytest.raises(HTTPException) as exc_info:
                await verify_token(credentials=credentials)

            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail


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
    async def test_get_current_user_handles_missing_optional_fields(self):
        """Test get_current_user handles missing optional fields."""
        from app.middleware.auth import get_current_user

        token_payload = {
            "sub": "keycloak-user-id",
            "email": "user@example.com"
            # Missing given_name, family_name, preferred_username
        }

        result = await get_current_user(token_payload=token_payload)

        assert result["keycloak_id"] == "keycloak-user-id"
        assert result["email"] == "user@example.com"
        assert result["first_name"] == ""
        assert result["last_name"] == ""
        assert result["username"] == ""
