"""
Tests for internal router logic in `app.routers.internal`.

Focus:
- `update_alert_in_messages` JSON update paths
- `broadcast_to_group` happy path and error paths
"""

import json
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from fastapi import HTTPException


# ========= update_alert_in_messages =========

@pytest.mark.asyncio
async def test_update_alert_in_messages_found_and_updated():
    """Alert exists in one message → content is updated and committed."""
    from app.routers.internal import update_alert_in_messages

    group_id = uuid4()
    alert_id = uuid4()

    original_content = {
        "type": "safety_alert",
        "alert_id": str(alert_id),
        "resolved": False,
    }

    msg = MagicMock()
    msg.content = json.dumps(original_content)

    db = MagicMock()
    db.query().filter().all.return_value = [msg]

    update_data = {"resolved": True, "resolved_at": "2025-12-01T12:00:00Z"}

    result = await update_alert_in_messages(
        group_id=group_id,
        alert_id=alert_id,
        update_data=update_data,
        db=db,
    )

    updated_payload = json.loads(msg.content)
    assert updated_payload["resolved"] is True
    assert updated_payload["resolved_at"] == "2025-12-01T12:00:00Z"
    db.commit.assert_called_once()

    assert result["success"] is True
    assert result["updated"] is True
    assert result["alert_id"] == str(alert_id)


@pytest.mark.asyncio
async def test_update_alert_in_messages_not_found():
    """No message contains the alert → no commit, updated=False."""
    from app.routers.internal import update_alert_in_messages

    group_id = uuid4()
    alert_id = uuid4()

    content = {
        "type": "safety_alert",
        "alert_id": str(uuid4()),
        "resolved": False,
    }
    msg = MagicMock()
    msg.content = json.dumps(content)

    db = MagicMock()
    db.query().filter().all.return_value = [msg]

    result = await update_alert_in_messages(
        group_id=group_id,
        alert_id=alert_id,
        update_data={"resolved": True},
        db=db,
    )

    db.commit.assert_not_called()
    assert result["success"] is True
    assert result["updated"] is False
    assert result["alert_id"] == str(alert_id)


@pytest.mark.asyncio
async def test_update_alert_in_messages_ignores_invalid_json():
    """Messages with invalid JSON are skipped, function still succeeds."""
    from app.routers.internal import update_alert_in_messages

    group_id = uuid4()
    alert_id = uuid4()

    bad_msg = MagicMock()
    bad_msg.content = "{not-valid-json"

    good_msg = MagicMock()
    good_msg.content = json.dumps(
        {
            "type": "safety_alert",
            "alert_id": str(uuid4()),
            "resolved": False,
        }
    )

    db = MagicMock()
    db.query().filter().all.return_value = [bad_msg, good_msg]

    result = await update_alert_in_messages(
        group_id=group_id,
        alert_id=alert_id,
        update_data={"resolved": True},
        db=db,
    )

    db.commit.assert_not_called()
    assert result["success"] is True
    assert result["updated"] is False
    assert result["alert_id"] == str(alert_id)


@pytest.mark.asyncio
async def test_update_alert_in_messages_db_exception_results_in_500():
    """Database error during processing → HTTP 500 is raised."""
    from app.routers.internal import update_alert_in_messages

    group_id = uuid4()
    alert_id = uuid4()

    db = MagicMock()
    db.query.side_effect = Exception("DB failure")

    with pytest.raises(HTTPException) as exc:
        await update_alert_in_messages(
            group_id=group_id,
            alert_id=alert_id,
            update_data={"resolved": True},
            db=db,
        )

    assert exc.value.status_code == 500
    assert "Failed to update alert message" in exc.value.detail


# ========= broadcast_to_group =========

@pytest.mark.asyncio
async def test_broadcast_to_group_happy_path():
    """Group exists, message saved, broadcast called → success response."""
    from app.routers.internal import broadcast_to_group
    from app.db import Group, Message

    group_id = uuid4()
    sender_id = uuid4()

    # Fake Group row
    group_row = MagicMock(spec=Group)

    # Fake DB session
    db = MagicMock()
    db.query().filter().first.return_value = group_row

    # Ensure commit/refresh are callable
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()

    payload = {
        "type": "safety_alert",
        "user_id": str(sender_id),
        "message": "Road closed",
    }

    with patch("app.routers.internal.chat_manager.broadcast_system_message", new=AsyncMock(return_value=3)):
        result = await broadcast_to_group(
            group_id=group_id,
            message=payload,
            db=db,
        )

    # DB should have stored a Message row
    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()

    assert result["success"] is True
    assert result["group_id"] == str(group_id)
    assert result["members_notified"] == 3
    assert result["message_type"] == "safety_alert"


@pytest.mark.asyncio
async def test_broadcast_to_group_group_not_found():
    """If group does not exist, a 404 HTTPException is raised."""
    from app.routers.internal import broadcast_to_group

    group_id = uuid4()
    db = MagicMock()
    db.query().filter().first.return_value = None

    with pytest.raises(HTTPException) as exc:
        await broadcast_to_group(
            group_id=group_id,
            message={"type": "safety_alert"},
            db=db,
        )

    assert exc.value.status_code == 404
    assert "Group not found" in exc.value.detail


@pytest.mark.asyncio
async def test_broadcast_to_group_db_error_results_in_500():
    """Any unexpected exception in broadcast_to_group → HTTP 500."""
    from app.routers.internal import broadcast_to_group

    group_id = uuid4()
    db = MagicMock()
    # Force an error when accessing the DB
    db.query.side_effect = Exception("DB connectivity issue")

    with pytest.raises(HTTPException) as exc:
        await broadcast_to_group(
            group_id=group_id,
            message={"type": "safety_alert"},
            db=db,
        )

    assert exc.value.status_code == 500
    assert "Failed to broadcast message" in exc.value.detail


