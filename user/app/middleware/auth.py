"""
Keycloak JWT authentication middleware.

This middleware:
1. Extracts JWT token from Authorization header
2. Decodes and validates the token using Keycloak public key
3. Injects user info into request.state for downstream use
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
from functools import lru_cache
import logging
import urllib3

# Disable SSL warnings for development (self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from app.config import config

logger = logging.getLogger(__name__)
security = HTTPBearer()


@lru_cache(maxsize=1)
def get_keycloak_jwks() -> dict:
    """
    Fetch Keycloak's JWKS (JSON Web Key Set) for JWT verification.
    Cached to avoid repeated HTTP requests.
    
    Returns all public keys from Keycloak.
    """
    try:
        realm_url = f"{config.KEYCLOAK_SERVER_URL}/realms/{config.KEYCLOAK_REALM}"
        response = requests.get(f"{realm_url}/protocol/openid-connect/certs", timeout=5, verify=False)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to fetch Keycloak JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify and decode Keycloak JWT token.
    
    Returns:
        dict: Decoded token payload containing:
            - sub: keycloak user ID (UUID)
            - email: user email
            - given_name: first name
            - family_name: last name
            - preferred_username: username
    
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Get JWKS (all public keys)
        jwks = get_keycloak_jwks()
        
        # Decode header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Find the matching key
        rsa_key = None
        for key in jwks["keys"]:
            if key["kid"] == kid:
                from jose.backends import RSAKey
                rsa_key = RSAKey(key, algorithm="RS256")
                break
        
        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key"
            )
        
        # Decode and verify token with the correct key
        payload = jwt.decode(
            token,
            rsa_key.to_pem().decode('utf-8'),
            algorithms=["RS256"],
            audience=config.KEYCLOAK_CLIENT_ID,
            options={"verify_aud": False},  # Keycloak sometimes doesn't include aud claim
            issuer=f"{config.KEYCLOAK_SERVER_URL}/realms/{config.KEYCLOAK_REALM}"
        )
        
        # Validate required claims
        if "sub" not in payload or "email" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing required claims"
            )
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_current_user(token_payload: dict = Depends(verify_token)) -> dict:
    """
    Extract user information from validated token.
    
    This is used as a FastAPI dependency in route handlers.
    
    Usage:
        @router.get("/users/me")
        async def get_me(current_user: dict = Depends(get_current_user)):
            keycloak_id = current_user["keycloak_id"]
    """
    return {
        "keycloak_id": token_payload["sub"],
        "email": token_payload.get("email"),
        "first_name": token_payload.get("given_name", ""),
        "last_name": token_payload.get("family_name", ""),
        "username": token_payload.get("preferred_username", "")
    }
