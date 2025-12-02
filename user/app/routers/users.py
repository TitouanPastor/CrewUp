"""
User API endpoints.

Endpoints:
- POST /users - Create user profile from Keycloak token
- GET /users/me - Get current user profile
- PUT /users/me - Update current user profile
- GET /users/{user_id} - Get public user profile
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from app.db import get_db, User
from app.models import UserCreate, UserUpdate, UserResponse, UserPublicResponse
from app.middleware import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("", include_in_schema=False)
async def users_root():
    """Users API root - available endpoints."""
    return {
        "service": "user-service",
        "endpoints": {
            "POST /api/v1/users": "Create user profile from token",
            "GET /api/v1/users/me": "Get current user profile",
            "PUT /api/v1/users/me": "Update current user profile",
            "GET /api/v1/users/{user_id}": "Get public user profile",
            "GET /api/v1/users/health": "Health check"
        }
    }


@router.get("/health", include_in_schema=False, tags=["health"])
async def health_check():
    """Health check endpoint (no auth, no DB)."""
    return {
        "status": "healthy",
        "service": "user-service"
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    response: Response,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create user profile from Keycloak token (idempotent).
    
    This endpoint is called when a user logs in for the first time.
    User info is extracted from the JWT token (not from request body).
    
    If the user already exists, returns the existing profile (200 OK).
    If new user, creates profile and returns 201 Created.
    
    Args:
        response: FastAPI Response object to modify status code
        current_user: Extracted from JWT token by auth middleware
        db: Database session
    
    Returns:
        UserResponse: Created or existing user profile
    
    Raises:
        400: Invalid token data
        500: Database error
    """
    keycloak_id = current_user["keycloak_id"]
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    if existing_user:
        logger.info(f"User {keycloak_id} already exists, returning existing profile")
        response.status_code = status.HTTP_200_OK  # Override default 201
        return existing_user
    
    # Validate required fields from token
    if not current_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not found in token"
        )
    
    # Create new user
    try:
        new_user = User(
            keycloak_id=keycloak_id,
            email=current_user["email"],
            first_name=current_user.get("first_name", ""),
            last_name=current_user.get("last_name", ""),
            interests=[]
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"Created new user: {new_user.email} (keycloak_id={keycloak_id})")
        return new_user
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or keycloak_id already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile.
    
    Returns complete profile including email and keycloak_id.
    
    Args:
        current_user: Extracted from JWT token
        db: Database session
    
    Returns:
        UserResponse: Complete user profile
    
    Raises:
        403: Forbidden
        404: User profile not found (user needs to call POST /users first)
    """
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()

    if user and user.is_banned :
        logger.warning(f"User with keycloak_id={current_user['keycloak_id']} is banned")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have been banned from CrewUp."
        )
    
    if not user:
        logger.warning(f"User profile not found for keycloak_id={current_user['keycloak_id']}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please create your profile first by calling POST /users"
        )
    
    return user


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.
    
    Only bio and interests can be updated.
    Other fields (email, name, etc.) are managed by Keycloak.
    
    Args:
        user_update: Fields to update (bio, interests)
        current_user: Extracted from JWT token
        db: Database session
    
    Returns:
        UserResponse: Updated user profile
    
    Raises:
        403: Forbidden
        404: User not found
        422: Validation error (handled by Pydantic)
    """
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
    if user and user.is_banned :
        logger.warning(f"User with keycloak_id={current_user['keycloak_id']} is banned")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have been banned from CrewUp."
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Update fields (only if provided)
    update_data = user_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
        db.refresh(user)
        logger.info(f"Updated user {user.email}: {list(update_data.keys())}")
        return user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/search", response_model=dict)
async def search_users(
    query: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for users by name or email (Moderator only).

    This endpoint is restricted to users with the Moderator role.
    Searches first_name, last_name, and email fields.

    Args:
        query: Search query string (name or email)
        current_user: Authenticated user (must have Moderator role)
        db: Database session

    Returns:
        dict: List of users matching the search query with their ban status

    Raises:
        400: Empty query
    """

    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    # Search users by name or email (case-insensitive)
    search_pattern = f"%{query.strip()}%"
    users = db.query(User).filter(
        (User.first_name.ilike(search_pattern)) |
        (User.last_name.ilike(search_pattern)) |
        (User.email.ilike(search_pattern))
    ).limit(50).all()  # Limit to 50 results

    # Format response to include ban status
    result = {
        "users": [
            {
                "id": user.id,
                "keycloak_id": user.keycloak_id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_banned": user.is_banned,
                "is_active": user.is_active
            }
            for user in users
        ],
        "total": len(users)
    }

    logger.info(f"User {current_user['keycloak_id']} searched for '{query}', found {len(users)} users")
    return result


@router.get("/{user_id}", response_model=UserPublicResponse)
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get public profile of any user by ID.

    Returns limited profile (excludes email, keycloak_id).
    Requires authentication to prevent scraping.

    Args:
        user_id: UUID of the user to retrieve
        current_user: Authenticated user (prevents anonymous access)
        db: Database session

    Returns:
        UserPublicResponse: Public user profile

    Raises:
        404: User not found
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    return user

