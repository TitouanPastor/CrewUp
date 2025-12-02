"""
Keycloak JWT authentication middleware with role-based access control.

This middleware:
1. Extracts JWT token from Authorization header
2. Decodes and validates the token using Keycloak public key
3. Checks for "Moderator" role in realm_access or resource_access
4. Injects user info into request.state for downstream use
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
security = HTTPBearer(auto_error=True)  # Always require authentication


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
            - realm_access: realm roles
            - resource_access: client-specific roles

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )

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


def check_moderator_role(token_payload: dict) -> bool:
    """
    Check if the user has the "Moderator" role in Keycloak.

    Checks both:
    1. realm_access.roles (realm-level roles)
    2. resource_access.{client_id}.roles (client-level roles)

    Args:
        token_payload: Decoded JWT token payload

    Returns:
        bool: True if user has Moderator role, False otherwise
    """
    # Check realm-level roles
    realm_roles = token_payload.get("realm_access", {}).get("roles", [])
    if "Moderator" in realm_roles:
        logger.info(f"User {token_payload.get('sub')} has Moderator role (realm level)")
        return True

    # Check client-level roles
    client_roles = (
        token_payload.get("resource_access", {})
        .get(config.KEYCLOAK_CLIENT_ID, {})
        .get("roles", [])
    )
    if "Moderator" in client_roles:
        logger.info(f"User {token_payload.get('sub')} has Moderator role (client level)")
        return True

    logger.warning(f"User {token_payload.get('sub')} does not have Moderator role")
    return False


async def get_current_moderator(token_payload: dict = Depends(verify_token)) -> dict:
    """
    Extract user information from validated token and verify Moderator role.

    This is used as a FastAPI dependency in route handlers.
    It ensures that only users with the "Moderator" role can access protected endpoints.

    Usage:
        @router.get("/moderation/reports")
        async def get_reports(current_moderator: dict = Depends(get_current_moderator)):
            # Only moderators can reach this code
            keycloak_id = current_moderator["keycloak_id"]

    Raises:
        HTTPException: 403 if user does not have Moderator role
    """
    # Check for Moderator role
    if not check_moderator_role(token_payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Moderator role required"
        )

    return {
        "keycloak_id": token_payload["sub"],
        "email": token_payload.get("email"),
        "first_name": token_payload.get("given_name", ""),
        "last_name": token_payload.get("family_name", ""),
        "username": token_payload.get("preferred_username", ""),
        "roles": {
            "realm": token_payload.get("realm_access", {}).get("roles", []),
            "client": token_payload.get("resource_access", {}).get(config.KEYCLOAK_CLIENT_ID, {}).get("roles", [])
        }
    }
