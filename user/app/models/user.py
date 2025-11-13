"""
Pydantic models for User entity.

These models handle:
- Request validation (UserCreate, UserUpdate)
- Response serialization (UserResponse, UserPublicResponse)
- Automatic OpenAPI documentation generation
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserCreate(BaseModel):
    """
    Model for creating a new user.
    Used when a user logs in for the first time via Keycloak.
    
    Most fields come from the Keycloak JWT token, not from the request body.
    """
    # These fields are extracted from Keycloak token automatically
    pass


class UserUpdate(BaseModel):
    """
    Model for updating user profile.
    Only bio and interests can be modified by the user.
    """
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    interests: Optional[list[str]] = Field(None, max_items=10, description="List of interests")
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v):
        """Ensure each interest is not empty and max 50 chars."""
        if v is not None:
            for interest in v:
                if not interest or len(interest.strip()) == 0:
                    raise ValueError("Interest cannot be empty")
                if len(interest) > 50:
                    raise ValueError("Each interest must be <= 50 characters")
        return v


class UserResponse(BaseModel):
    """
    Complete user profile response (for /users/me).
    Includes all fields including email.
    """
    id: UUID
    keycloak_id: str
    email: str
    first_name: str
    last_name: str
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    interests: list[str] = []
    reputation: float = 0.0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Enables ORM mode (SQLAlchemy compatibility)


class UserPublicResponse(BaseModel):
    """
    Public user profile response (for /users/{id}).
    Excludes sensitive fields like email and keycloak_id.
    """
    id: UUID
    first_name: str
    last_name: str
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None
    interests: list[str] = []
    reputation: float = 0.0
    created_at: datetime
    
    class Config:
        from_attributes = True
