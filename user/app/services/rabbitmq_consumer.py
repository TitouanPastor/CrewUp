"""
RabbitMQ consumer for moderation commands.

Listens to the 'user.moderation' queue for ban/unban commands.
"""
import json
import pika
import logging
import threading
from typing import Callable
from sqlalchemy.orm import Session

from app.config import config
from app.db import SessionLocal, User

logger = logging.getLogger(__name__)


class ModerationConsumer:
    """
    RabbitMQ consumer for user moderation commands.

    Message format:
    {
        "action": "ban" | "unban",
        "user_id": "keycloak-user-id"
    }
    """

    def __init__(self, rabbitmq_url: str, queue_name: str = "user.moderation"):
        """
        Initialize the moderation consumer.

        Args:
            rabbitmq_url: RabbitMQ connection URL (e.g., amqp://user:pass@host:5672/)
            queue_name: Queue name to consume from
        """
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.consumer_thread = None
        self._is_running = False

    def connect(self):
        """Establish connection to RabbitMQ."""
        try:
            parameters = pika.URLParameters(self.rabbitmq_url)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queue (idempotent - creates if doesn't exist)
            self.channel.queue_declare(queue=self.queue_name, durable=True)

            logger.info(f"Connected to RabbitMQ, listening on queue: {self.queue_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def process_message(self, ch, method, properties, body):
        """
        Process incoming moderation command.

        Args:
            ch: Channel
            method: Delivery method
            properties: Message properties
            body: Message body (JSON)
        """
        db = SessionLocal()
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            action = message.get('action')
            user_id = message.get('user_id')

            if not action or not user_id:
                logger.error(f"Invalid message format: {message}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            if action not in ['ban', 'unban']:
                logger.error(f"Unknown action: {action}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Find user by keycloak_id
            user = db.query(User).filter(User.keycloak_id == user_id).first()

            if not user:
                logger.warning(f"User not found: {user_id}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Update ban status (with idempotency check)
            is_banned = (action == 'ban')

            # Check if user is already in the desired state
            if user.is_banned == is_banned:
                logger.warning(f"User {user_id} is already {'banned' if is_banned else 'unbanned'}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            user.is_banned = is_banned
            db.commit()

            logger.info(f"User {user_id} {'banned' if is_banned else 'unbanned'} successfully")

            # Acknowledge message
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject and requeue on unexpected errors
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            db.close()

    def start_consuming(self):
        """Start consuming messages from the queue."""
        if not self.channel:
            self.connect()

        self._is_running = True

        # Set up consumer
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=self.queue_name,
            on_message_callback=self.process_message
        )

        logger.info("Starting to consume messages...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming messages and close connection."""
        self._is_running = False

        if self.channel:
            self.channel.stop_consuming()

        if self.connection:
            self.connection.close()

        logger.info("Consumer stopped")

    def start_in_background(self):
        """Start the consumer in a background thread."""
        if self.consumer_thread and self.consumer_thread.is_alive():
            logger.warning("Consumer already running")
            return

        self.consumer_thread = threading.Thread(target=self.start_consuming, daemon=True)
        self.consumer_thread.start()
        logger.info("Consumer started in background thread")


# Singleton instance
_consumer = None


def get_consumer() -> ModerationConsumer:
    """Get or create the moderation consumer singleton."""
    global _consumer
    if _consumer is None:
        rabbitmq_url = config.RABBITMQ_URL
        _consumer = ModerationConsumer(rabbitmq_url)
    return _consumer


def start_consumer():
    """Start the RabbitMQ consumer in the background."""
    consumer = get_consumer()
    consumer.start_in_background()
