"""
Event API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import logging

from app.db import get_db, User, Event, EventAttendee
from app.models import (
    EventCreate,
    EventUpdate,
    EventResponse,
    EventListResponse,
    JoinEventRequest,
    AttendeeResponse,
    AttendeeListResponse,
)
from app.middleware import get_current_user, get_optional_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


# ==================== Health Check ====================

@router.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint (no authentication required)."""
    return {"status": "healthy", "service": "event-service"}


# ==================== CRUD Operations ====================

@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new event.

    Requires authentication. The authenticated user becomes the event creator.
    Note: Creator is NOT automatically added as an attendee - they must join separately.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to create event")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Create event
        new_event = Event(
            creator_id=user.id,
            name=event_data.name,
            description=event_data.description,
            event_type=event_data.event_type or 'other',  # Default to 'other'
            address=event_data.address,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            event_start=event_data.event_start,
            event_end=event_data.event_end,
            max_attendees=event_data.max_attendees,
            is_public=True,  # All events public for now
            is_cancelled=False
        )

        db.add(new_event)
        db.commit()
        db.refresh(new_event)

        logger.info(f"Event created: {new_event.id} by user {user.id}")

        # 3. Build response with computed fields
        # Get participant counts (will be 0 since creator doesn't auto-join)
        going_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == new_event.id,
            EventAttendee.status == 'going'
        ).count()

        interested_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == new_event.id,
            EventAttendee.status == 'interested'
        ).count()

        # Calculate if event is full
        is_full = False
        if new_event.max_attendees is not None:
            is_full = going_count >= new_event.max_attendees

        # Build response with creator details
        response_data = {
            **new_event.__dict__,
            "creator_first_name": user.first_name,
            "creator_last_name": user.last_name,
            "creator_profile_picture": user.profile_picture_url,
            "participant_count": going_count,
            "interested_count": interested_count,
            "is_full": is_full,
            "user_status": None  # Creator hasn't joined yet
        }

        return EventResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create event: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event"
        )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get event details by ID.

    Requires authentication. Returns event with participant counts and creator details.
    For private events (when implemented), only participants can view.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # 2. Get event
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Privacy check (for when private events are implemented)
        # If event is private, check if user is creator or participant
        if not event.is_public:
            # Check if user is creator
            if event.creator_id != user.id:
                # Check if user is a participant
                is_participant = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event_id,
                    EventAttendee.user_id == user.id
                ).first() is not None

                if not is_participant:
                    # Return 404 to not reveal existence of private event
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Event {event_id} not found"
                    )

        # 4. Get participant counts
        going_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.status == 'going'
        ).count()

        interested_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.status == 'interested'
        ).count()

        # 5. Get current user's RSVP status
        user_attendance = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.user_id == user.id
        ).first()

        user_status = user_attendance.status if user_attendance else None

        # 6. Calculate if event is full
        is_full = False
        if event.max_attendees is not None:
            is_full = going_count >= event.max_attendees

        # 7. Get creator details
        creator = db.query(User).filter(User.id == event.creator_id).first()

        # 8. Build response
        response_data = {
            **event.__dict__,
            "creator_first_name": creator.first_name if creator else None,
            "creator_last_name": creator.last_name if creator else None,
            "creator_profile_picture": creator.profile_picture_url if creator else None,
            "participant_count": going_count,
            "interested_count": interested_count,
            "is_full": is_full,
            "user_status": user_status
        }

        return EventResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event"
        )


@router.put("/{event_id}", response_model=EventResponse)
@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing event.

    Only the event creator can update the event.
    Cannot update events that have already started or ended.
    Can update cancelled events if uncancelling and event_start >= 30 min from now.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to update event")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Get event
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Authorization check - only creator can update
        if event.creator_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator can update this event"
            )

        # 4. Check if any fields are being updated
        update_dict = event_data.model_dump(exclude_unset=True)
        if not update_dict:
            # No fields to update - return current event (200 no-op)
            logger.info(f"No fields to update for event {event_id}")
            # Return current event state
            return await get_event(event_id, current_user, db)

        # 5. Event state validations
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Check if event has already started
        if event.event_start <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update an event that has already started"
            )

        # Check if event has already ended
        if event.event_end and event.event_end <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update an event that has already ended"
            )

        # 6. Validate event_start if being updated
        if "event_start" in update_dict:
            new_start = update_dict["event_start"]
            min_start_time = now + timedelta(minutes=30)

            if new_start.tzinfo is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="event_start must include timezone information"
                )

            if new_start < min_start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Event must start at least 30 minutes from now"
                )

        # 7. If uncancelling event, verify event_start is valid
        if "is_cancelled" in update_dict and update_dict["is_cancelled"] is False and event.is_cancelled:
            # Uncancelling event
            event_start_to_check = update_dict.get("event_start", event.event_start)
            min_start_time = now + timedelta(minutes=30)

            if event_start_to_check < min_start_time:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot uncancel event: event must start at least 30 minutes from now"
                )

        # 8. Validate event_end vs event_start
        if "event_end" in update_dict or "event_start" in update_dict:
            new_start = update_dict.get("event_start", event.event_start)
            new_end = update_dict.get("event_end", event.event_end)

            if new_end and new_start and new_end < new_start:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="event_end must be after or equal to event_start"
                )

        # 9. Validate lat/lng pair
        if "latitude" in update_dict or "longitude" in update_dict:
            new_lat = update_dict.get("latitude", event.latitude)
            new_lng = update_dict.get("longitude", event.longitude)

            has_lat = new_lat is not None
            has_lng = new_lng is not None

            if has_lat != has_lng:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Both latitude and longitude must be provided together, or neither"
                )

        # 10. Validate max_attendees vs current participants
        if "max_attendees" in update_dict:
            new_max = update_dict["max_attendees"]

            if new_max is not None:  # None means unlimited, which is always valid
                # Get current participant count
                current_going_count = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event_id,
                    EventAttendee.status == 'going'
                ).count()

                if new_max < current_going_count:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Cannot reduce max_attendees to {new_max}: event has {current_going_count} participants already"
                    )

        # 11. Apply updates
        for field, value in update_dict.items():
            setattr(event, field, value)

        db.commit()
        db.refresh(event)

        logger.info(f"Event {event_id} updated by user {user.id}")

        # 12. Return updated event (same structure as GET)
        return await get_event(event_id, current_user, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event"
        )


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
async def delete_event(
    event_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an event (soft delete).

    Only the event creator can delete the event.
    Sets is_cancelled=true to preserve data for legal/security reasons.
    Cannot delete events that have already started or ended.
    Idempotent - returns 200 if already deleted.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to delete event")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Get event
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Authorization check - only creator can delete
        if event.creator_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the event creator can delete this event"
            )

        # 4. Idempotency check - if already deleted (cancelled), return success
        if event.is_cancelled:
            logger.info(f"Event {event_id} already deleted (cancelled)")
            return {"message": "Event deleted successfully"}

        # 5. Event state validations
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Check if event has already started
        if event.event_start <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete an event that has already started"
            )

        # Check if event has already ended
        if event.event_end and event.event_end <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete an event that has already ended"
            )

        # 6. Soft delete - set is_cancelled to true
        event.is_cancelled = True
        db.commit()

        logger.info(f"Event {event_id} soft deleted (cancelled) by user {user.id}")

        return {"message": "Event deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event"
        )


# ==================== RSVP Operations ====================

@router.post("/{event_id}/join", status_code=status.HTTP_200_OK)
async def join_event(
    event_id: UUID,
    join_data: JoinEventRequest = JoinEventRequest(),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join an event (RSVP).

    User can set their status to 'going', 'interested', or 'not_going'.
    If already joined, updates the status and timestamp.
    Only 'going' status counts toward event capacity.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to join event")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Get event and validate it exists
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Event state validations
        if event.is_cancelled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join a cancelled event"
            )

        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        if event.event_start <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join an event that has already started"
            )

        if event.event_end and event.event_end <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot join an event that has already ended"
            )

        # Privacy check (for when private events are implemented)
        if not event.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This event is private"
            )

        # 4. Check if user already joined
        existing_attendee = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.user_id == user.id
        ).first()

        # 5. If changing status to 'going', check capacity
        if join_data.status == 'going':
            # Get current 'going' count
            going_count = db.query(EventAttendee).filter(
                EventAttendee.event_id == event_id,
                EventAttendee.status == 'going'
            ).count()

            # If user is changing from another status to 'going', don't count them in current total
            if existing_attendee and existing_attendee.status != 'going':
                # User switching to 'going', current count doesn't include them yet
                pass
            elif existing_attendee and existing_attendee.status == 'going':
                # Already 'going', this is idempotent - don't check capacity
                going_count -= 1  # Don't count the user in the capacity check

            # Check if event is full (only if max_attendees is set)
            if event.max_attendees is not None and going_count >= event.max_attendees:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Event is full"
                )

        # 6. Create or update attendee record
        if existing_attendee:
            # Update existing record (status and timestamp)
            existing_attendee.status = join_data.status
            # updated_at will be auto-updated by database trigger
            db.commit()
            logger.info(f"User {user.id} updated RSVP for event {event_id} to status '{join_data.status}'")
        else:
            # Create new attendee record
            new_attendee = EventAttendee(
                event_id=event_id,
                user_id=user.id,
                status=join_data.status
            )
            db.add(new_attendee)
            db.commit()
            logger.info(f"User {user.id} joined event {event_id} with status '{join_data.status}'")

        return {"message": "Successfully joined event"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to join event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to join event"
        )


@router.delete("/{event_id}/leave", status_code=status.HTTP_200_OK)
async def leave_event(
    event_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Leave an event (update RSVP to 'not_going').

    Sets the user's status to 'not_going' (soft delete).
    Allows leaving cancelled events.
    Cannot leave events that have already started or ended.
    Idempotent - returns 200 if user not joined or already left.
    Event creator can leave their own event.
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to leave event")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Get event and validate it exists
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Event state validations (block started/ended, allow cancelled)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # Cannot leave started events
        if event.event_start <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave an event that has already started"
            )

        # Cannot leave ended events
        if event.event_end and event.event_end <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot leave an event that has already ended"
            )

        # Note: Cancelled events are allowed (no check for is_cancelled)

        # 4. Check if user is currently joined
        existing_attendee = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.user_id == user.id
        ).first()

        # 5. Idempotent behavior - if not joined or already 'not_going', return success
        if not existing_attendee or existing_attendee.status == 'not_going':
            logger.info(f"User {user.id} not joined or already left event {event_id} (idempotent)")
            return {"message": "Successfully left event"}

        # 6. Update status to 'not_going' (soft delete)
        existing_attendee.status = 'not_going'
        # updated_at will be auto-updated by database trigger
        db.commit()

        logger.info(f"User {user.id} left event {event_id} (status set to 'not_going')")

        return {"message": "Successfully left event"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to leave event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave event"
        )


# ==================== List & Search Operations ====================

@router.get("", response_model=EventListResponse)
async def list_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    is_public: Optional[bool] = Query(None, description="Filter by public/private"),
    creator_id: Optional[UUID] = Query(None, description="Filter by creator"),
    start_date_from: Optional[datetime] = Query(None, description="Events starting after this date"),
    start_date_to: Optional[datetime] = Query(None, description="Events starting before this date"),
    is_cancelled: bool = Query(False, description="Include cancelled events"),
    user_status: Optional[str] = Query(None, description="Filter by current user's RSVP status", alias="status"),
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="Filter by location latitude"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="Filter by location longitude"),
    radius_km: float = Query(10, gt=0, le=100, description="Search radius in kilometers (default: 10)"),
    include_past: bool = Query(False, description="Include past events (finished events)"),
    include_ongoing: bool = Query(True, description="Include ongoing events (currently happening)"),
    limit: int = Query(50, ge=1, le=100, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    List events with filters and pagination.

    By default, shows only public, non-cancelled, upcoming AND ongoing events sorted by event_start ASC.
    Authentication is optional - without auth, only public events are shown.
    If authenticated, can filter by user's RSVP status and see private events they're part of.
    
    Time filtering:
    - include_ongoing=True (default): Shows events currently happening (started but not finished)
    - include_past=False (default): Excludes finished events
    - include_past=True: Shows all events including finished ones (read-only)
    """
    try:
        from datetime import datetime, timezone, timedelta
        from math import radians, cos, sin, asin, sqrt
        from decimal import Decimal

        # 1. Validate event_type against valid values
        valid_event_types = ['bar', 'club', 'concert', 'party', 'restaurant', 'outdoor', 'sports', 'other']
        if event_type and event_type not in valid_event_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid event_type. Must be one of: {', '.join(valid_event_types)}"
            )

        # 2. Validate user_status filter requires authentication
        if user_status and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to filter by RSVP status"
            )

        # 3. Validate date range - if start_date_from > start_date_to, return empty results
        if start_date_from and start_date_to and start_date_from > start_date_to:
            # Return empty results
            return EventListResponse(events=[], total=0, limit=limit, offset=offset)

        # 4. Validate location filter - both latitude and longitude must be provided together
        has_lat = latitude is not None
        has_lng = longitude is not None
        if has_lat != has_lng:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Both latitude and longitude must be provided together for location filtering"
            )

        # 5. Get authenticated user if present
        user = None
        if current_user:
            user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()

        # 6. Build base query
        query = db.query(Event)

        # 7. Default time filters with 2-hour margin (for ongoing events detection)
        now = datetime.now(timezone.utc)
        margin = timedelta(hours=2)  # Same margin as safety service
        
        # Filter by event status (past/ongoing/upcoming)
        if not include_past:
            # Exclude finished events (event_end + margin < now)
            # This means: show events that haven't fully ended yet (including 2h after)
            query = query.filter(Event.event_end + margin > now)
        
        if not include_ongoing:
            # Exclude ongoing events (event_start - margin < now < event_end + margin)
            # This means: only show future events (not started yet, considering margin)
            query = query.filter(Event.event_start - margin > now)

        # Show only non-cancelled events unless is_cancelled=True
        if not is_cancelled:
            query = query.filter(Event.is_cancelled == False)

        # 8. Privacy filter
        if not current_user:
            # No authentication - only show public events
            query = query.filter(Event.is_public == True)
        else:
            # Authenticated - apply is_public filter if provided
            # Otherwise, show public events + private events user is part of
            if is_public is not None:
                query = query.filter(Event.is_public == is_public)
            # Note: We'll filter private events in post-processing to check participation

        # 9. Apply other filters
        if event_type:
            query = query.filter(Event.event_type == event_type)

        if creator_id:
            # Only show events by this creator
            # If unauthenticated, only public ones (already filtered above)
            query = query.filter(Event.creator_id == creator_id)

        if start_date_from:
            query = query.filter(Event.event_start >= start_date_from)

        if start_date_to:
            query = query.filter(Event.event_start <= start_date_to)

        # 10. Filter by user's RSVP status if requested
        if user_status and user:
            # Join with EventAttendee to filter by user's status
            query = query.join(EventAttendee, Event.id == EventAttendee.event_id)
            query = query.filter(EventAttendee.user_id == user.id)
            query = query.filter(EventAttendee.status == user_status)

        # 11. Order by event_start ASC (soonest first)
        query = query.order_by(Event.event_start.asc())

        # 12. Get total count before pagination
        total = query.count()

        # 13. Apply pagination
        events = query.limit(limit).offset(offset).all()

        # 14. Location filtering (post-processing with Haversine distance)
        if has_lat and has_lng:
            def haversine_distance(lat1, lon1, lat2, lon2):
                """Calculate distance between two points in kilometers using Haversine formula."""
                # Convert to radians
                lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

                # Haversine formula
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))

                # Earth radius in kilometers
                r = 6371
                return c * r

            # Filter events by distance
            filtered_events = []
            for event in events:
                # Skip events without coordinates
                if event.latitude is None or event.longitude is None:
                    continue

                # Calculate distance
                distance = haversine_distance(latitude, longitude, event.latitude, event.longitude)

                # Include if within radius
                if distance <= radius_km:
                    filtered_events.append(event)

            events = filtered_events
            total = len(filtered_events)  # Update total to match filtered count

        # 15. Build response with computed fields
        event_responses = []
        for event in events:
            # Skip private events if user is not authenticated or not a participant/creator
            if not event.is_public and current_user:
                # Check if user is creator or participant
                is_creator = event.creator_id == user.id
                is_participant = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event.id,
                    EventAttendee.user_id == user.id
                ).first() is not None

                if not is_creator and not is_participant:
                    # User should not see this private event
                    total -= 1  # Adjust total count
                    continue

            # Get participant counts
            going_count = db.query(EventAttendee).filter(
                EventAttendee.event_id == event.id,
                EventAttendee.status == 'going'
            ).count()

            interested_count = db.query(EventAttendee).filter(
                EventAttendee.event_id == event.id,
                EventAttendee.status == 'interested'
            ).count()

            # Calculate if event is full
            is_full = False
            if event.max_attendees is not None:
                is_full = going_count >= event.max_attendees

            # Get current user's RSVP status if authenticated
            user_status = None
            if user:
                user_attendance = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event.id,
                    EventAttendee.user_id == user.id
                ).first()
                user_status = user_attendance.status if user_attendance else None

            # Get creator details
            creator = db.query(User).filter(User.id == event.creator_id).first()

            # Build response
            response_data = {
                **event.__dict__,
                "creator_first_name": creator.first_name if creator else None,
                "creator_last_name": creator.last_name if creator else None,
                "creator_profile_picture": creator.profile_picture_url if creator else None,
                "participant_count": going_count,
                "interested_count": interested_count,
                "is_full": is_full,
                "user_status": user_status
            }

            event_responses.append(EventResponse(**response_data))

        return EventListResponse(events=event_responses, total=total, limit=limit, offset=offset)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list events: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list events"
        )


# ==================== Participants ====================

@router.get("/{event_id}/participants", response_model=AttendeeListResponse)
async def get_event_participants(
    event_id: UUID,
    attendee_status: Optional[str] = Query(None, description="Filter by status (going, interested, not_going)", alias="status"),
    include_details: bool = Query(False, description="Include full participant list"),
    limit: int = Query(50, ge=1, le=100, description="Number of participants to return"),
    offset: int = Query(0, ge=0, description="Number of participants to skip"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get event participant counts and optionally the list of participants.

    Authentication required for all requests.
    Returns counts for each status (going, interested).
    If include_details=true, returns full list of participants with public profile info (no email).
    """
    try:
        # 1. Validate user exists in database
        user = db.query(User).filter(User.keycloak_id == current_user["keycloak_id"]).first()
        if not user:
            logger.warning(f"User profile not found for keycloak_id: {current_user['keycloak_id']}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete your profile first."
            )

        # Check if user is banned
        if user.is_banned:
            logger.warning(f"Banned user {current_user['keycloak_id']} attempted to get participants")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have been banned from CrewUp."
            )

        # 2. Get event and validate it exists
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found"
            )

        # 3. Privacy check - for private events, only creator and participants can view
        if not event.is_public:
            # Check if user is creator
            if event.creator_id != user.id:
                # Check if user is a participant
                is_participant = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event_id,
                    EventAttendee.user_id == user.id
                ).first() is not None

                if not is_participant:
                    # Return 404 to not reveal existence of private event
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Event {event_id} not found"
                    )

        # 4. Validate attendee_status filter if provided
        valid_statuses = ['going', 'interested', 'not_going']
        if attendee_status and attendee_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )

        # 5. Get participant counts (always returned)
        going_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.status == 'going'
        ).count()

        interested_count = db.query(EventAttendee).filter(
            EventAttendee.event_id == event_id,
            EventAttendee.status == 'interested'
        ).count()

        # 6. Build response with counts
        response_data = {
            "event_id": event_id,
            "going_count": going_count,
            "interested_count": interested_count,
            "total_participants": 0,  # Will be set below
            "attendees": None
        }

        # 7. If include_details is true, fetch participant list
        if include_details:
            # Build query for attendees
            attendees_query = db.query(EventAttendee).filter(EventAttendee.event_id == event_id)

            # Apply attendee_status filter if provided
            if attendee_status:
                attendees_query = attendees_query.filter(EventAttendee.status == attendee_status)

            # Get total count (for pagination)
            total_participants = attendees_query.count()
            response_data["total_participants"] = total_participants

            # Apply pagination and order by created_at (first to join appears first)
            attendees = attendees_query.order_by(EventAttendee.created_at.asc()).limit(limit).offset(offset).all()

            # Build attendee list with public profile info
            attendee_list = []
            for attendee in attendees:
                # Get user details
                attendee_user = db.query(User).filter(User.id == attendee.user_id).first()

                attendee_data = {
                    "user_id": attendee.user_id,
                    "keycloak_id": attendee_user.keycloak_id if attendee_user else None,
                    "first_name": attendee_user.first_name if attendee_user else None,
                    "last_name": attendee_user.last_name if attendee_user else None,
                    "status": attendee.status,
                    "joined_at": attendee.created_at
                }

                attendee_list.append(AttendeeResponse(**attendee_data))

            response_data["attendees"] = attendee_list
        else:
            # If not including details, total_participants is the filtered count
            if attendee_status:
                # Count only the filtered status
                filtered_count = db.query(EventAttendee).filter(
                    EventAttendee.event_id == event_id,
                    EventAttendee.status == attendee_status
                ).count()
                response_data["total_participants"] = filtered_count
            else:
                # Total participants = going + interested (not_going doesn't count)
                response_data["total_participants"] = going_count + interested_count

        return AttendeeListResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get participants for event {event_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event participants"
        )
