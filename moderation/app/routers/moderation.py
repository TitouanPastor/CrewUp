"""
Moderation API endpoints.

ALL endpoints require:
1. Valid JWT authentication
2. "Moderator" role in Keycloak
"""
from fastapi import APIRouter, Depends
import logging

from app.middleware import get_current_moderator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/ban")
async def ban_endpoint(
    current_moderator: dict = Depends(get_current_moderator)
):
    """
    Test endpoint that only checks if the user is a moderator.

    This endpoint verifies:
    1. JWT token is valid
    2. User has the "Moderator" role

    Returns the moderator's information if authorized.
    """
    return {
        "message": "Access granted - you are a moderator",
        "moderator_info": current_moderator
    }
