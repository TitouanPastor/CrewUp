"""
Unit tests for RabbitMQ service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pika

from app.services.rabbitmq import RabbitMQPublisher


class TestRabbitMQPublisher:
    """Tests for RabbitMQPublisher class."""

    def test_init(self):
        """Test RabbitMQPublisher initialization."""
        publisher = RabbitMQPublisher()

        assert publisher.credentials is not None
        assert publisher.parameters is not None
        assert isinstance(publisher.parameters, pika.ConnectionParameters)

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_success(self, mock_connection):
        """Test successful ban event publishing."""
        # Setup mocks
        mock_channel = Mock()
        mock_conn_instance = Mock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        # Call the method
        result = publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test ban reason",
            ban=True
        )

        # Assertions
        assert result is True
        mock_channel.exchange_declare.assert_called_once()
        mock_channel.queue_declare.assert_called_once()
        mock_channel.queue_bind.assert_called_once()
        mock_channel.basic_publish.assert_called_once()

        # Check the message content
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]["routing_key"] is not None
        assert "user-123" in call_args[1]["body"]
        assert "mod-456" in call_args[1]["body"]
        assert "Test ban reason" in call_args[1]["body"]

        mock_conn_instance.close.assert_called_once()

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_unban_success(self, mock_connection):
        """Test successful unban event publishing."""
        # Setup mocks
        mock_channel = Mock()
        mock_conn_instance = Mock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        # Call the method with ban=False
        result = publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test unban reason",
            ban=False
        )

        # Assertions
        assert result is True

        # Check the message includes unban action
        call_args = mock_channel.basic_publish.call_args
        message_body = call_args[1]["body"]
        assert "unban_user" in message_body
        assert '"ban": false' in message_body.lower()

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_connection_failure(self, mock_connection):
        """Test ban event publishing when connection fails."""
        # Simulate connection failure
        mock_connection.side_effect = pika.exceptions.AMQPConnectionError("Connection failed")

        publisher = RabbitMQPublisher()

        result = publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test ban reason",
            ban=True
        )

        assert result is False

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_channel_error(self, mock_connection):
        """Test ban event publishing when channel operations fail."""
        # Setup mocks
        mock_conn_instance = Mock()
        mock_conn_instance.channel.side_effect = pika.exceptions.AMQPChannelError("Channel error")
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        result = publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test ban reason",
            ban=True
        )

        assert result is False
        mock_conn_instance.close.assert_called_once()

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_publish_error(self, mock_connection):
        """Test ban event publishing when basic_publish fails."""
        # Setup mocks
        mock_channel = Mock()
        mock_channel.basic_publish.side_effect = Exception("Publish failed")
        mock_conn_instance = Mock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        result = publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test ban reason",
            ban=True
        )

        assert result is False
        mock_conn_instance.close.assert_called_once()

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_closes_connection_on_success(self, mock_connection):
        """Test that connection is closed after successful publish."""
        # Setup mocks
        mock_channel = Mock()
        mock_conn_instance = Mock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test ban reason",
            ban=True
        )

        mock_conn_instance.close.assert_called_once()

    @patch("app.services.rabbitmq.pika.BlockingConnection")
    def test_publish_user_ban_message_format(self, mock_connection):
        """Test that the published message has correct format."""
        # Setup mocks
        mock_channel = Mock()
        mock_conn_instance = Mock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        publisher = RabbitMQPublisher()

        publisher.publish_user_ban(
            user_keycloak_id="user-123",
            moderator_keycloak_id="mod-456",
            reason="Test reason",
            ban=True
        )

        # Get the call arguments
        call_args = mock_channel.basic_publish.call_args
        message_body = call_args[1]["body"]

        # Check message contains all required fields
        assert "user_keycloak_id" in message_body
        assert "moderator_keycloak_id" in message_body
        assert "reason" in message_body
        assert "action" in message_body
        assert "ban" in message_body

        # Check properties
        properties = call_args[1]["properties"]
        assert properties.delivery_mode == 2  # Persistent
        assert properties.content_type == "application/json"
