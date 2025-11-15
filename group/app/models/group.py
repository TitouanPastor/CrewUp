"""
Pydantic models for Group & Chat Service request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID


# ==================== Group Models ====================

class GroupCreate(BaseModel):
    """Create group request model."""
    event_id: UUID = Field(..., description="Event this group is for")
    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: Optional[str] = Field(None, max_length=500, description="Group description")
    max_members: int = Field(10, ge=2, le=50, description="Maximum number of members")
    
    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        """Validate name is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class GroupResponse(BaseModel):
    """Group response model."""
    id: UUID
    event_id: UUID
    name: str
    description: Optional[str]
    max_members: int
    member_count: int = Field(..., description="Current number of members")
    is_full: bool = Field(..., description="Whether group is at capacity")
    is_private: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class GroupListResponse(BaseModel):
    """List of groups response."""
    groups: List[GroupResponse]
    total: int


# ==================== Member Models ====================

class MemberResponse(BaseModel):
    """Group member response model."""
    user_id: UUID
    keycloak_id: str | None = None  # Add keycloak_id for frontend matching
    joined_at: datetime
    is_admin: bool = False
    
    model_config = {"from_attributes": True}


class MemberListResponse(BaseModel):
    """List of members response."""
    members: List[MemberResponse]
    total: int


# ==================== Message Models ====================

class MessageCreate(BaseModel):
    """Create message request model (for REST API)."""
    content: str = Field(..., min_length=1, max_length=1000, description="Message content")
    
    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        """Validate content is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Message response model."""
    id: UUID
    group_id: UUID
    sender_id: UUID
    content: str
    is_edited: bool = False
    sent_at: datetime
    
    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    """List of messages response."""
    messages: List[MessageResponse]
    total: int
    limit: int
    offset: int


# ==================== WebSocket Models ====================

class WSMessageIn(BaseModel):
    """WebSocket message from client."""
    type: str = Field(..., pattern="^(message|typing)$", description="Message type")
    content: Optional[str] = Field(None, max_length=1000, description="Message content (for 'message' type)")
    is_typing: Optional[bool] = Field(None, description="Typing status (for 'typing' type)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("content")
    @classmethod
    def validate_content_for_message(cls, v: Optional[str], info) -> Optional[str]:
        """Validate content is provided for message type."""
        if info.data.get("type") == "message":
            if not v or not v.strip():
                raise ValueError("Message content is required for 'message' type")
            return v.strip()
        return v


class WSMessageOut(BaseModel):
    """WebSocket message to client."""
    type: str = Field(..., description="Message type: message, member_joined, member_left, typing, error")
    id: Optional[UUID] = Field(None, description="Message ID (for 'message' type)")
    user_id: Optional[UUID] = Field(None, description="User ID")
    username: Optional[str] = Field(None, description="Username")
    content: Optional[str] = Field(None, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_typing: Optional[bool] = Field(None, description="Typing status (for 'typing' type)")
    code: Optional[str] = Field(None, description="Error code (for 'error' type)")
    message: Optional[str] = Field(None, description="Error message (for 'error' type)")
    
    model_config = {"from_attributes": True}


class WSError(BaseModel):
    """WebSocket error response."""
    type: Literal["error"] = "error"
    code: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
