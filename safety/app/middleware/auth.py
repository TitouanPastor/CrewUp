"""
Authentication middleware using Keycloak.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
import logging
from typing import Optional
from functools import lru_cache
import os

from app.config import config

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # Don't auto-raise 403, allow optional auth

# Test mode detection
TESTING = os.getenv("TESTING", "false").lower() == "true"

# Mock user for testing
MOCK_TEST_USER = {
    "keycloak_id": "test-keycloak-id",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "username": "testuser"
}


@lru_cache(maxsize=1)
def get_keycloak_public_key() -> str:
    """
    Fetch Keycloak public key for JWT verification.
    Cached to avoid repeated network calls.
    
    Returns:
        Public key in PEM format
        
    Raises:
        HTTPException: If unable to fetch public key
    """
    try:
        url = f"{config.KEYCLOAK_SERVER_URL}/realms/{config.KEYCLOAK_REALM}"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        realm_info = response.json()
        
        public_key = realm_info.get("public_key")
        if not public_key:
            raise ValueError("Public key not found in realm info")
        
        # Format as PEM
        pem_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
        logger.info("Keycloak public key fetched successfully")
        return pem_key
        
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to connect to authentication service"
        )


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    """
    Verify JWT token and return decoded payload.
    
    Args:
        credentials: HTTP bearer credentials
        
    Returns:
        Decoded JWT payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # In test mode, return mock user if credentials provided
    if TESTING:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return {
            "sub": MOCK_TEST_USER["keycloak_id"],
            "email": MOCK_TEST_USER["email"],
            "given_name": MOCK_TEST_USER["first_name"],
            "family_name": MOCK_TEST_USER["last_name"],
            "preferred_username": MOCK_TEST_USER["username"]
        }
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    try:
        public_key = get_keycloak_public_key()
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_aud": False}  # Keycloak uses different audience model
        )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed"
        )


async def get_current_user(token_payload: dict = Depends(verify_token)) -> dict:
    """
    Get current authenticated user from token.
    
    Args:
        token_payload: Decoded JWT payload
        
    Returns:
        User information from token
    """
    return {
        "keycloak_id": token_payload["sub"],
        "email": token_payload.get("email"),
        "first_name": token_payload.get("given_name"),
        "last_name": token_payload.get("family_name"),
        "username": token_payload.get("preferred_username"),
    }
