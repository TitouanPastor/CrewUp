"""
Integration tests for the moderation service.

These tests verify the full workflow from HTTP request to database changes.
"""
import pytest
from unittest.mock import patch, Mock
from app.db import ModerationAction


class TestBanWorkflowIntegration:
    """Integration tests for the complete ban workflow."""

    def test_full_ban_workflow(
        self,
        client,
        db_session,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """
        Test the complete ban workflow:
        1. Moderator is authenticated
        2. Target user exists
        3. RabbitMQ message is published
        4. Moderation action is logged
        5. Response is returned
        """
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Integration test ban reason"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "banned successfully" in data["message"].lower()
        assert data["moderation_action_id"] is not None

        # Verify RabbitMQ was called
        mock_rabbitmq_publisher_success.assert_called_once()
        call_args = mock_rabbitmq_publisher_success.call_args[1]
        assert call_args["user_keycloak_id"] == regular_user.keycloak_id
        assert call_args["moderator_keycloak_id"] == moderator_user.keycloak_id
        assert call_args["reason"] == "Integration test ban reason"
        assert call_args["ban"] is True

        # Verify moderation action was logged in database
        action = db_session.query(ModerationAction).filter(
            ModerationAction.id == data["moderation_action_id"]
        ).first()

        assert action is not None
        assert action.moderator_id == moderator_user.keycloak_id
        assert action.action_type == "ban_user"
        assert action.target_type == "user"
        assert action.target_id == regular_user.keycloak_id
        assert action.reason == "Integration test ban reason"
        assert regular_user.email in action.details
        assert action.created_at is not None

    def test_full_unban_workflow(
        self,
        client,
        db_session,
        moderator_user,
        banned_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test the complete unban workflow."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": banned_user.keycloak_id,
                "ban": False,
                "reason": "Integration test unban reason"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "unbanned successfully" in data["message"].lower()

        # Verify RabbitMQ was called with ban=False
        call_args = mock_rabbitmq_publisher_success.call_args[1]
        assert call_args["ban"] is False

        # Verify moderation action type is unban_user
        action = db_session.query(ModerationAction).filter(
            ModerationAction.id == data["moderation_action_id"]
        ).first()

        assert action.action_type == "unban_user"
        assert "unban" in action.details.lower()

    def test_multiple_moderation_actions_tracked(
        self,
        client,
        db_session,
        moderator_user,
        regular_user,
        banned_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that multiple moderation actions are properly tracked."""
        # First action: ban regular_user
        response1 = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "First ban action"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        # Second action: unban banned_user
        response2 = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": banned_user.keycloak_id,
                "ban": False,
                "reason": "First unban action"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both actions are in database
        actions = db_session.query(ModerationAction).all()
        assert len(actions) >= 2

        # Verify action details
        action1 = db_session.query(ModerationAction).filter(
            ModerationAction.id == response1.json()["moderation_action_id"]
        ).first()
        action2 = db_session.query(ModerationAction).filter(
            ModerationAction.id == response2.json()["moderation_action_id"]
        ).first()

        assert action1.action_type == "ban_user"
        assert action1.target_id == regular_user.keycloak_id
        assert action2.action_type == "unban_user"
        assert action2.target_id == banned_user.keycloak_id

    def test_workflow_with_authentication_failure(
        self,
        client,
        moderator_user,
        regular_user,
        mock_rabbitmq_publisher_success
    ):
        """Test that workflow fails properly with invalid authentication."""
        # Don't mock authentication - let it fail naturally with no token
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test with invalid auth"
            }
            # No Authorization header
        )

        assert response.status_code == 403

        # Verify no RabbitMQ message was published
        mock_rabbitmq_publisher_success.assert_not_called()

    def test_workflow_rollback_on_error(
        self,
        client,
        db_session,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that database changes are rolled back on unexpected errors."""
        initial_action_count = db_session.query(ModerationAction).count()

        # Simulate an error after RabbitMQ publish by making db.commit fail
        with patch.object(db_session, "commit") as mock_commit:
            mock_commit.side_effect = Exception("Database commit failed")

            response = client.post(
                "/api/v1/moderation/ban",
                json={
                    "user_keycloak_id": regular_user.keycloak_id,
                    "ban": True,
                    "reason": "Test rollback scenario"
                },
                headers={"Authorization": "Bearer mock-token"}
            )

            # Should still return success due to partial failure handling
            assert response.status_code == 200
            assert response.json()["moderation_action_id"] is None

        # Verify no new action was committed (due to the simulated failure)
        # Note: In real partial failure, RabbitMQ succeeds so we return success
        final_action_count = db_session.query(ModerationAction).count()
        assert final_action_count == initial_action_count


class TestAuthenticationIntegration:
    """Integration tests for authentication flow."""

    def test_unauthenticated_request_denied(
        self,
        client,
        regular_user
    ):
        """Test that unauthenticated requests are denied."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test without authentication"
            }
            # No Authorization header
        )

        assert response.status_code == 403


class TestModelsValidation:
    """Integration tests for Pydantic model validation."""

    def test_ban_request_validation_min_reason(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token
    ):
        """Test that reason must be at least 10 characters."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Short"  # 5 characters
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 422

    def test_ban_request_validation_max_reason(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token
    ):
        """Test that reason cannot exceed 255 characters."""
        long_reason = "a" * 256

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

    def test_ban_request_validation_missing_ban_field(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token
    ):
        """Test that ban field is required."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "reason": "Valid reason here"
                # Missing 'ban' field
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 422

    def test_ban_response_structure(
        self,
        client,
        moderator_user,
        regular_user,
        mock_verify_token,
        mock_rabbitmq_publisher_success
    ):
        """Test that the response matches the BanUserResponse model."""
        response = client.post(
            "/api/v1/moderation/ban",
            json={
                "user_keycloak_id": regular_user.keycloak_id,
                "ban": True,
                "reason": "Test response structure"
            },
            headers={"Authorization": "Bearer mock-token"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields are present
        assert "success" in data
        assert "message" in data
        assert "moderation_action_id" in data

        # Check field types
        assert isinstance(data["success"], bool)
        assert isinstance(data["message"], str)
        assert isinstance(data["moderation_action_id"], int) or data["moderation_action_id"] is None
