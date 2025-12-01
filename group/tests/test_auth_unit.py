"""
Unit tests for auth.py middleware.
Tests Keycloak JWT authentication with mocked external dependencies.
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from fastapi import HTTPException
from jose import jwt
import json

# Don't set TESTING mode for these tests - we want to test real auth logic
import os
# Temporarily unset TESTING to test real auth paths
original_testing = os.environ.get("TESTING")


class TestGetKeycloakJwks:
    """Test JWKS fetching from Keycloak."""
    
    def test_get_jwks_success(self):
        """Test successful JWKS fetch."""
        # Need to reimport with TESTING=false
        os.environ["TESTING"] = "false"
        
        # Clear the lru_cache
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        auth_module.get_keycloak_jwks.cache_clear()
        
        mock_jwks = {
            "keys": [
                {
                    "kid": "test-key-id",
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "n": "test-n-value",
                    "e": "AQAB"
                }
            ]
        }
        
        with patch('app.middleware.auth.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            result = auth_module.get_keycloak_jwks()
            
            assert result == mock_jwks
            assert "keys" in result
        
        # Restore TESTING
        if original_testing:
            os.environ["TESTING"] = original_testing
    
    def test_get_jwks_failure(self):
        """Test JWKS fetch failure."""
        os.environ["TESTING"] = "false"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        auth_module.get_keycloak_jwks.cache_clear()
        
        with patch('app.middleware.auth.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            with pytest.raises(HTTPException) as exc_info:
                auth_module.get_keycloak_jwks()
            
            assert exc_info.value.status_code == 503
            assert "Authentication service unavailable" in exc_info.value.detail
        
        if original_testing:
            os.environ["TESTING"] = original_testing


class TestVerifyToken:
    """Test token verification."""
    
    @pytest.mark.asyncio
    async def test_verify_token_no_credentials(self):
        """Test verify_token with no credentials."""
        os.environ["TESTING"] = "false"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_module.verify_token(None)
        
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail
        
        if original_testing:
            os.environ["TESTING"] = original_testing
    
    @pytest.mark.asyncio
    async def test_verify_token_testing_mode(self):
        """Test verify_token in testing mode returns mock user."""
        os.environ["TESTING"] = "true"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        
        # Create mock credentials
        mock_credentials = Mock()
        mock_credentials.credentials = "fake-token"
        
        result = await auth_module.verify_token(mock_credentials)
        
        assert result["sub"] == auth_module.MOCK_TEST_USER["keycloak_id"]
        assert result["email"] == auth_module.MOCK_TEST_USER["email"]
        
        if original_testing:
            os.environ["TESTING"] = original_testing
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid_jwt(self):
        """Test verify_token with invalid JWT."""
        os.environ["TESTING"] = "false"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        auth_module.get_keycloak_jwks.cache_clear()
        
        mock_jwks = {"keys": [{"kid": "key1", "kty": "RSA", "n": "test", "e": "AQAB"}]}
        
        with patch('app.middleware.auth.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            with patch('app.middleware.auth.jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {"kid": "different-key"}
                
                mock_credentials = Mock()
                mock_credentials.credentials = "fake-token"
                
                with pytest.raises(HTTPException) as exc_info:
                    await auth_module.verify_token(mock_credentials)
                
                assert exc_info.value.status_code == 401
        
        if original_testing:
            os.environ["TESTING"] = original_testing


class TestVerifyTokenWs:
    """Test WebSocket token verification."""
    
    @pytest.mark.asyncio
    async def test_verify_token_ws_invalid(self):
        """Test WebSocket token verification with invalid token."""
        os.environ["TESTING"] = "false"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        auth_module.get_keycloak_jwks.cache_clear()
        
        mock_jwks = {"keys": [{"kid": "key1", "kty": "RSA", "n": "test", "e": "AQAB"}]}
        
        with patch('app.middleware.auth.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = mock_jwks
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            with patch('app.middleware.auth.jwt.get_unverified_header') as mock_header:
                mock_header.return_value = {"kid": "wrong-key"}
                
                with pytest.raises(Exception) as exc_info:
                    await auth_module.verify_token_ws("fake-token")
                
                assert "Unable to find appropriate signing key" in str(exc_info.value)
        
        if original_testing:
            os.environ["TESTING"] = original_testing


class TestGetCurrentUser:
    """Test get_current_user function."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_extracts_info(self):
        """Test that get_current_user correctly extracts user info."""
        os.environ["TESTING"] = "true"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        
        token_payload = {
            "sub": "user-123",
            "email": "user@example.com",
            "given_name": "John",
            "family_name": "Doe",
            "preferred_username": "johndoe"
        }
        
        result = await auth_module.get_current_user(token_payload)
        
        assert result["keycloak_id"] == "user-123"
        assert result["email"] == "user@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["username"] == "johndoe"
        
        if original_testing:
            os.environ["TESTING"] = original_testing
    
    @pytest.mark.asyncio
    async def test_get_current_user_handles_missing_fields(self):
        """Test that get_current_user handles missing optional fields."""
        os.environ["TESTING"] = "true"
        
        from importlib import reload
        import app.middleware.auth as auth_module
        reload(auth_module)
        
        token_payload = {
            "sub": "user-123"
            # Missing other fields
        }
        
        result = await auth_module.get_current_user(token_payload)
        
        assert result["keycloak_id"] == "user-123"
        assert result["email"] is None
        assert result["first_name"] == ""
        assert result["last_name"] == ""
        assert result["username"] == ""
        
        if original_testing:
            os.environ["TESTING"] = original_testing
