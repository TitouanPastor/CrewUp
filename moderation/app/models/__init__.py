"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ModerationActionCreate(BaseModel):
    """Request model for creating a moderation action."""
    action_type: str = Field(..., description="Type of action (ban_user, delete_content, warn_user, etc.)")
    target_type: str = Field(..., description="Type of target (user, event, group, message)")
    target_id: str = Field(..., description="ID of the target entity")
    reason: str = Field(..., min_length=10, description="Reason for the action (min 10 characters)")
    details: Optional[str] = Field(None, description="Additional details")


class ModerationActionResponse(BaseModel):
    """Response model for moderation actions."""
    id: int
    moderator_id: str
    action_type: str
    target_type: str
    target_id: str
    reason: str
    details: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ModeratorInfo(BaseModel):
    """Response model for current moderator info."""
    keycloak_id: str
    email: str
    first_name: str
    last_name: str
    username: str
    roles: dict


class BanUserRequest(BaseModel):
    """Request model for banning or unbanning a user."""
    user_keycloak_id: str = Field(..., description="Keycloak ID of the user to ban/unban")
    ban: bool = Field(..., description="True to ban, False to unban")
    reason: str = Field(..., min_length=10, max_length=255, description="Reason for the action (10-255 characters)")


class BanUserResponse(BaseModel):
    """Response model for ban user action."""
    success: bool
    message: str
    moderation_action_id: Optional[int] = None


__all__ = [
    "ModerationActionCreate",
    "ModerationActionResponse",
    "ModeratorInfo",
    "BanUserRequest",
    "BanUserResponse"
]
