"""
Unit tests for the ban endpoint in moderation router.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException

from app.models import BanUserRequest


class TestBanEndpoint:
    """Tests for /moderation/ban endpoint."""

    def test_ban_user_success(
        self,
        client,
        db_session,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test successful user ban."""
        # Make the request
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Violated community guidelines repeatedly"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "banned successfully" in data["message"]
        assert data["moderation_action_id"] is not None

        # Verify RabbitMQ was called
        mock_rabbitmq_publisher_success.assert_called_once_with(
            user_keycloak_id=regular_user.keycloak_id,
            moderator_keycloak_id=moderator_user.keycloak_id,
            reason="Violated community guidelines repeatedly",
            ban=True
        )

    def test_unban_user_success(
        self,
        client,
        db_session,
        moderator_user,
        banned_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test successful user unban."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": banned_user.keycloak_id,
                "ban": False,
                "reason": "Ban appeal approved after review"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "unbanned successfully" in data["message"]
        assert data["moderation_action_id"] is not None

        # Verify RabbitMQ was called
        mock_rabbitmq_publisher_success.assert_called_once_with(
            user_keycloak_id=banned_user.keycloak_id,
            moderator_keycloak_id=moderator_user.keycloak_id,
            reason="Ban appeal approved after review",
            ban=False
        )

    def test_ban_user_moderator_not_in_db(
        self,
        client,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test ban fails when moderator doesn't exist in database."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test ban reason for moderator not in db"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 404
        assert "Moderator profile not found" in response.json()["detail"]

    def test_ban_user_self_ban_prevented(
        self,
        client,
        moderator_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that moderators cannot ban themselves."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": moderator_user.keycloak_id,
                "ban": True,
                "reason": "Trying to ban myself for testing"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 400
        assert "cannot ban yourself" in response.json()["detail"].lower()

    def test_ban_user_target_not_found(
        self,
        client,
        moderator_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test ban fails when target user doesn't exist."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": "nonexistent-user-id",
                "ban": True,
                "reason": "Test ban for nonexistent user"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_ban_user_already_banned(
        self,
        client,
        moderator_user,
        banned_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test banning a user who is already banned."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": banned_user.keycloak_id,
                "ban": True,
                "reason": "Trying to ban already banned user"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 400
        assert "already banned" in response.json()["detail"].lower()

    def test_unban_user_not_banned(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test unbanning a user who is not currently banned."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": False,
                "reason": "Trying to unban non-banned user"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 400
        assert "not currently banned" in response.json()["detail"].lower()

    def test_ban_user_rabbitmq_failure(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_failure
    ):
        """Test ban fails gracefully when RabbitMQ is unavailable."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test ban with RabbitMQ failure"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
        assert "try again later" in response.json()["detail"].lower()

    def test_ban_user_reason_too_short(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test ban fails with reason that's too short."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Short"  # Less than 10 characters
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 422
        # Just verify it's a validation error
        assert "detail" in response.json()

    def test_ban_user_reason_too_long(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test ban fails with reason that's too long."""
        long_reason = "a" * 256  # More than 255 characters

        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": long_reason
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 422
        # Just verify it's a validation error
        assert "detail" in response.json()

    def test_ban_user_missing_fields(
        self,
        client,
        moderator_user,
        mock_verify_token
    ):
        """Test ban fails when required fields are missing."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": "user-123",
                # Missing 'ban' and 'reason' fields
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 422

    @patch("app.routers.moderation.ModerationAction")
    def test_ban_user_partial_failure_logging(
        self,
        mock_moderation_action_class,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success,
        db_session
    ):
        """Test that partial failure is handled when RabbitMQ succeeds but DB logging fails."""
        # Make the ModerationAction constructor raise an exception
        mock_moderation_action_class.side_effect = Exception("Database error")

        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test partial failure scenario"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        # Should still return success since RabbitMQ published successfully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["moderation_action_id"] is None  # No action ID due to DB failure

    def test_ban_user_no_authentication(
        self,
        client,
        moderator_user,
        regular_user
    ):
        """Test ban fails without authentication."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test without auth token"
            }
            # No Authorization header
        )

        assert response.status_code == 403

    def test_ban_user_moderation_action_created(
        self,
        client,
        db_session,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that a moderation action is properly logged in the database."""
        from app.db import ModerationAction

        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test moderation action logging"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 200

        # Query the database for the moderation action
        action = db_session.query(ModerationAction).filter(
            ModerationAction.target_id == regular_user.keycloak_id
        ).first()

        assert action is not None
        assert action.moderator_id == moderator_user.keycloak_id
        assert action.action_type == "ban_user"
        assert action.target_type == "user"
        assert action.reason == "Test moderation action logging"
        assert regular_user.email in action.details

    def test_unban_user_moderation_action_created(
        self,
        client,
        db_session,
        moderator_user,
        banned_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that an unban moderation action is properly logged."""
        from app.db import ModerationAction

        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": banned_user.keycloak_id,
                "ban": False,
                "reason": "Test unban action logging"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 200

        # Query the database for the moderation action
        action = db_session.query(ModerationAction).filter(
            ModerationAction.target_id == banned_user.keycloak_id
        ).first()

        assert action is not None
        assert action.action_type == "unban_user"
        assert action.moderator_id == moderator_user.keycloak_id
