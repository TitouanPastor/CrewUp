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
        404: User profile not found (user needs to call POST /users first)
    """
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
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
        404: User not found
        422: Validation error (handled by Pydantic)
    """
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
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


@router.get("/health", status_code=status.HTTP_200_OK, include_in_schema=False)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Verifies database connectivity.
    Not included in OpenAPI docs (internal use).
    
    Returns:
        dict: Health status
    
    Raises:
        503: Database unreachable
    """
    try:
        # Simple query to check DB connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "service": "user-service",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable"
        )
