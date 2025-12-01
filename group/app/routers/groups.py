"""
Group API endpoints.

Endpoints:
- POST /groups - Create group for event
- GET /groups - List groups (filter by event)
- GET /groups/{id} - Get group details
- POST /groups/{id}/join - Join group
- DELETE /groups/{id}/leave - Leave group
- GET /groups/{id}/members - List members
- GET /groups/{id}/messages - Message history
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import logging
from uuid import UUID

from app.db import get_db, Group, GroupMember, Message
from app.models import (
    GroupCreate,
    GroupResponse,
    GroupListResponse,
    MemberResponse,
    MemberListResponse,
    MessageResponse,
    MessageListResponse
)
from app.middleware import get_current_user
from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/groups", tags=["groups"])


@router.get("/health", include_in_schema=False, tags=["health"])
async def health_check():
    """Health check endpoint (no auth, no DB)."""
    return {
        "status": "healthy",
        "service": "group-service"
    }


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new group for an event.
    
    Creator is automatically added as the first member.
    """
    try:
        # Get user ID from database using keycloak_id
        from app.db.models import User
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please create your profile first."
            )
        
        # Create group
        new_group = Group(
            event_id=group_data.event_id,
            name=group_data.name,
            description=group_data.description,
            max_members=group_data.max_members
        )
        db.add(new_group)
        db.flush()  # Get the ID before committing
        
        # Add creator as first member
        creator_member = GroupMember(
            group_id=new_group.id,
            user_id=user.id
        )
        db.add(creator_member)
        db.commit()
        db.refresh(new_group)
        
        # Calculate member count
        member_count = db.query(func.count(GroupMember.user_id)).filter(
            GroupMember.group_id == new_group.id
        ).scalar()
        
        logger.info(f"Created group {new_group.id} by user {current_user['keycloak_id']}")
        
        return GroupResponse(
            id=new_group.id,
            event_id=new_group.event_id,
            name=new_group.name,
            description=new_group.description,
            max_members=new_group.max_members,
            member_count=member_count,
            is_full=member_count >= new_group.max_members,
            is_private=new_group.is_private,
            created_at=new_group.created_at
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create group"
        )


@router.get("", response_model=GroupListResponse)
async def list_groups(
    event_id: Optional[UUID] = Query(None, description="Filter by event ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List groups, optionally filtered by event."""
    query = db.query(Group)
    
    if event_id:
        query = query.filter(Group.event_id == event_id)
    
    groups = query.all()
    
    # Build responses with member counts
    group_responses = []
    for group in groups:
        member_count = db.query(func.count(GroupMember.user_id)).filter(
            GroupMember.group_id == group.id
        ).scalar()
        
        group_responses.append(GroupResponse(
            id=group.id,
            event_id=group.event_id,
            name=group.name,
            description=group.description,
            max_members=group.max_members,
            member_count=member_count,
            is_full=member_count >= group.max_members,
            is_private=group.is_private,
            created_at=group.created_at
        ))
    
    return GroupListResponse(groups=group_responses, total=len(group_responses))


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get group details."""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )
    
    member_count = db.query(func.count(GroupMember.user_id)).filter(
        GroupMember.group_id == group.id
    ).scalar()
    
    return GroupResponse(
        id=group.id,
        event_id=group.event_id,
        name=group.name,
        description=group.description,
        max_members=group.max_members,
        member_count=member_count,
        is_full=member_count >= group.max_members,
        is_private=group.is_private,
        created_at=group.created_at
    )


@router.post("/{group_id}/join", status_code=status.HTTP_200_OK)
async def join_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a group."""
    # Check if group exists and is active
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )
    
    keycloak_id = current_user["keycloak_id"]
    
    # Get user ID from database using keycloak_id
    from app.db.models import User
    user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Please create your profile first."
        )
    
    user_id = user.id
    
    # Check if already a member
    existing_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this group"
        )
    
    # Check if group is full
    member_count = db.query(func.count(GroupMember.user_id)).filter(
        GroupMember.group_id == group_id
    ).scalar()
    
    if member_count >= group.max_members:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Group is full"
        )
    
    # Add member
    try:
        new_member = GroupMember(
            group_id=group_id,
            user_id=user_id
        )
        db.add(new_member)
        db.commit()
        
        logger.info(f"User {user_id} joined group {group_id}")
        return {"message": "Successfully joined group"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error joining group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join group"
        )


@router.delete("/{group_id}/leave", status_code=status.HTTP_200_OK)
async def leave_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave a group."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )
    
    # Get user ID from database using keycloak_id
    from app.db.models import User
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Check if member
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this group"
        )
    
    # Remove member
    try:
        db.delete(member)
        db.commit()
        
        logger.info(f"User {user.id} left group {group_id}")
        return {"message": "Successfully left group"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error leaving group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave group"
        )


@router.get("/{group_id}/members", response_model=MemberListResponse)
async def list_members(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List group members."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )
    
    # Get user ID from database
    from app.db.models import User
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Check if requester is a member
    is_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member to view the member list"
        )
    
    # Get members with user info (JOIN with users table)
    from app.db.models import User
    members_with_users = db.query(GroupMember, User).join(
        User, GroupMember.user_id == User.id
    ).filter(GroupMember.group_id == group_id).all()
    
    # Build response with keycloak_id included
    member_responses = []
    for member, user_info in members_with_users:
        member_responses.append(MemberResponse(
            user_id=member.user_id,
            keycloak_id=user_info.keycloak_id,
            joined_at=member.joined_at,
            is_admin=False
        ))
    
    return MemberListResponse(
        members=member_responses,
        total=len(member_responses)
    )


@router.get("/{group_id}/messages", response_model=MessageListResponse)
async def list_messages(
    group_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get message history for a group (paginated)."""
    # Check if group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found"
        )
    
    # Get user ID from database
    from app.db.models import User
    user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Check if requester is a member
    is_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member to view messages"
        )
    
    # Get total count
    total = db.query(func.count(Message.id)).filter(Message.group_id == group_id).scalar()
    
    # Get messages with sender information (JOIN with User table)
    from app.db.models import User
    messages_query = db.query(
        Message,
        User.first_name,
        User.last_name
    ).outerjoin(
        User, Message.sender_id == User.id
    ).filter(
        Message.group_id == group_id
    ).order_by(
        Message.sent_at.desc()
    ).limit(limit).offset(offset).all()
    
    # Build response with sender names
    message_responses = []
    for msg, first_name, last_name in reversed(messages_query):
        msg_dict = {
            "id": msg.id,
            "group_id": msg.group_id,
            "sender_id": msg.sender_id,
            "sender_first_name": first_name,
            "sender_last_name": last_name,
            "content": msg.content,
            "is_edited": msg.is_edited,
            "sent_at": msg.sent_at,
        }
        message_responses.append(MessageResponse(**msg_dict))
    
    return MessageListResponse(
        messages=message_responses,
        total=total,
        limit=limit,
        offset=offset
    )
