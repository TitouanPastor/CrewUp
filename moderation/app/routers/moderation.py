"""
Moderation API endpoints.

ALL endpoints require:
1. Valid JWT authentication
2. "Moderator" role in Keycloak
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.middleware import get_current_moderator
from app.db import get_db, User, ModerationAction
from app.models import BanUserRequest, BanUserResponse
from app.services import rabbitmq_publisher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.post("/ban", response_model=BanUserResponse, status_code=status.HTTP_200_OK)
async def ban_user(
    ban_request: BanUserRequest,
    current_moderator: dict = Depends(get_current_moderator),
    db: Session = Depends(get_db)
):
    """
    Ban or unban a user from the platform.

    Workflow:
    1. Check if moderator exists in database
    2. Prevent self-banning (moderator cannot ban themselves)
    3. Check if moderator has the "Moderator" role (checked by middleware)
    4. Check if target user exists in database
    5. Check if user already has the requested ban status
    6. Publish ban/unban event to RabbitMQ for user service to process
    7. Log the moderation action (with partial failure handling)

    Edge cases handled:
    - Self-ban prevention: Moderators cannot ban themselves
    - Duplicate ban check: Cannot ban already banned users or unban non-banned users
    - RabbitMQ unavailable: Returns 503 with clear retry message
    - Partial failure: If RabbitMQ succeeds but database logging fails, still returns success
    - Reason validation: 10-255 characters enforced by Pydantic

    Args:
        ban_request: BanUserRequest with user_keycloak_id, ban (bool), and reason (10-255 chars)
        current_moderator: The authenticated moderator (injected by middleware)
        db: Database session

    Returns:
        BanUserResponse with success status and moderation action ID (may be None on partial failure)

    Raises:
        HTTPException 400: If moderator tries to ban themselves or user already has requested status
        HTTPException 404: If moderator or target user not found
        HTTPException 503: If RabbitMQ is unavailable
    """
    try:
        # Step 1: Check if moderator exists in database
        moderator = db.query(User).filter(
            User.keycloak_id == current_moderator["keycloak_id"]
        ).first()

        if not moderator:
            logger.error(f"Moderator {current_moderator['keycloak_id']} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Moderator profile not found. Please create your user profile first."
            )

        # Step 1.5: Prevent self-banning
        if current_moderator["keycloak_id"] == ban_request.user_keycloak_id:
            logger.warning(f"Moderator {current_moderator['keycloak_id']} attempted to ban themselves")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot ban yourself"
            )

        # Step 2: Check if target user exists in database
        target_user = db.query(User).filter(
            User.keycloak_id == ban_request.user_keycloak_id
        ).first()

        if not target_user:
            logger.warning(f"User {ban_request.user_keycloak_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with keycloak_id '{ban_request.user_keycloak_id}' not found"
            )

        # Step 3: Check if user already has the requested ban status
        if ban_request.ban and target_user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {target_user.email} is already banned"
            )

        if not ban_request.ban and not target_user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {target_user.email} is not currently banned"
            )

        # Step 4: Publish ban/unban event to RabbitMQ
        action_text = "ban" if ban_request.ban else "unban"
        logger.info(f"Publishing {action_text} event for user {ban_request.user_keycloak_id}")

        publish_success = rabbitmq_publisher.publish_user_ban(
            user_keycloak_id=ban_request.user_keycloak_id,
            moderator_keycloak_id=current_moderator["keycloak_id"],
            reason=ban_request.reason,
            ban=ban_request.ban
        )

        if not publish_success:
            logger.error(f"Failed to publish {action_text} event to RabbitMQ")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Message queue is currently unavailable. Please try again later."
            )

        # Step 5: Log moderation action
        action_type = "ban_user" if ban_request.ban else "unban_user"
        moderation_action_id = None

        try:
            moderation_action = ModerationAction(
                moderator_id=current_moderator["keycloak_id"],
                action_type=action_type,
                target_type="user",
                target_id=ban_request.user_keycloak_id,
                reason=ban_request.reason,
                details=f"{action_text.capitalize()}ned user {target_user.email} ({target_user.keycloak_id})"
            )
            db.add(moderation_action)
            db.commit()
            db.refresh(moderation_action)
            moderation_action_id = moderation_action.id

            logger.info(
                f"Moderator {current_moderator['email']} {action_text}ned user {target_user.email} "
                f"(action_id: {moderation_action.id})"
            )
        except Exception as e:
            # Log partial failure - RabbitMQ message was sent but database logging failed
            logger.error(
                f"PARTIAL FAILURE: {action_text.capitalize()} event published to RabbitMQ successfully, "
                f"but failed to log moderation action to database: {e}"
            )
            db.rollback()
            # Still return success since the ban was processed

        return BanUserResponse(
            success=True,
            message=f"User {target_user.email} has been {action_text}ned successfully.",
            moderation_action_id=moderation_action_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
