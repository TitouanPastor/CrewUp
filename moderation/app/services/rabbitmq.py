"""
RabbitMQ service for publishing moderation events.
"""
import pika
import json
import logging
from typing import Dict, Any

from app.config import config

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """RabbitMQ publisher for sending moderation events."""

    def __init__(self):
        """Initialize RabbitMQ connection parameters."""
        self.credentials = pika.PlainCredentials(
            config.RABBITMQ_USER,
            config.RABBITMQ_PASSWORD
        )
        self.parameters = pika.ConnectionParameters(
            host=config.RABBITMQ_HOST,
            port=config.RABBITMQ_PORT,
            virtual_host=config.RABBITMQ_VHOST,
            credentials=self.credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )

    def publish_user_ban(self, user_keycloak_id: str, moderator_keycloak_id: str, reason: str, ban: bool = True) -> bool:
        """
        Publish a user ban/unban event to RabbitMQ.

        Args:
            user_keycloak_id: The Keycloak ID of the user to ban/unban
            moderator_keycloak_id: The Keycloak ID of the moderator performing the action
            reason: The reason for the action
            ban: True to ban, False to unban

        Returns:
            bool: True if published successfully, False otherwise
        """
        connection = None
        try:
            # Establish connection
            connection = pika.BlockingConnection(self.parameters)
            channel = connection.channel()

            # Declare exchange (idempotent)
            channel.exchange_declare(
                exchange=config.USER_BAN_EXCHANGE,
                exchange_type='direct',
                durable=True
            )

            # Declare queue (idempotent)
            channel.queue_declare(
                queue=config.USER_BAN_QUEUE,
                durable=True
            )

            # Bind queue to exchange
            channel.queue_bind(
                exchange=config.USER_BAN_EXCHANGE,
                queue=config.USER_BAN_QUEUE,
                routing_key=config.USER_BAN_ROUTING_KEY
            )

            # Prepare message
            action = "ban_user" if ban else "unban_user"
            message: Dict[str, Any] = {
                "user_keycloak_id": user_keycloak_id,
                "moderator_keycloak_id": moderator_keycloak_id,
                "reason": reason,
                "action": action,
                "ban": ban
            }

            # Publish message
            channel.basic_publish(
                exchange=config.USER_BAN_EXCHANGE,
                routing_key=config.USER_BAN_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type='application/json'
                )
            )

            action_text = "ban" if ban else "unban"
            logger.info(f"Published {action_text} event for user {user_keycloak_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish ban event: {e}")
            return False

        finally:
            if connection and not connection.is_closed:
                connection.close()


# Create singleton instance
rabbitmq_publisher = RabbitMQPublisher()
