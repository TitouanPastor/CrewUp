"""
Unit tests for RabbitMQ consumer.

Tests cover:
- Successful ban/unban message processing
- Invalid message formats (invalid JSON, missing fields)
- Unknown actions
- User not found cases
- Idempotency (already banned/unbanned)
- Database errors and retry logic
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.rabbitmq_consumer import ModerationConsumer
from app.db.database import Base
from app.db.models import User
import os

# Test database (PostgreSQL)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://crewup:crewup_dev_password@localhost:5432/crewup"
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a database session for testing."""
    # Create uuid extension if not exists
    with engine.connect() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        conn.commit()

    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session

    # Cleanup: Delete test users
    session.execute(text("DELETE FROM users WHERE keycloak_id LIKE 'test-rabbitmq-%'"))
    session.commit()
    session.close()


@pytest.fixture
def mock_channel():
    """Mock RabbitMQ channel."""
    channel = Mock()
    channel.basic_ack = Mock()
    channel.basic_nack = Mock()
    return channel


@pytest.fixture
def mock_method():
    """Mock delivery method with delivery tag."""
    method = Mock()
    method.delivery_tag = 123
    return method


@pytest.fixture
def consumer():
    """Create a ModerationConsumer instance for testing."""
    # We don't actually connect to RabbitMQ in unit tests
    consumer = ModerationConsumer("amqp://guest:guest@localhost:5672/")
    return consumer


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        keycloak_id="test-rabbitmq-user-123",
        email="testrabbit@example.com",
        first_name="Test",
        last_name="Rabbit",
        is_banned=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def banned_user(db_session):
    """Create a test user who is already banned."""
    user = User(
        keycloak_id="test-rabbitmq-banned-456",
        email="banned@example.com",
        first_name="Banned",
        last_name="User",
        is_banned=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_successful_ban_message(consumer, mock_channel, mock_method, test_user, db_session):
    """Test successful ban message processing."""
    message = {
        "action": "ban_user",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "moderator_keycloak_id": "moderator-123",
        "reason": "Test ban reason",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Verify user was banned
    db_session.expire_all()  # Refresh from database
    user = db_session.query(User).filter(User.keycloak_id == "test-rabbitmq-user-123").first()
    assert user.is_banned is True

    # Verify message was acknowledged
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_successful_unban_message(consumer, mock_channel, mock_method, banned_user, db_session):
    """Test successful unban message processing."""
    message = {
        "action": "unban_user",
        "user_keycloak_id": "test-rabbitmq-banned-456",
        "moderator_keycloak_id": "moderator-123",
        "reason": "Test unban reason",
        "ban": False
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Verify user was unbanned
    db_session.expire_all()  # Refresh from database
    user = db_session.query(User).filter(User.keycloak_id == "test-rabbitmq-banned-456").first()
    assert user.is_banned is False

    # Verify message was acknowledged
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_invalid_json_message(consumer, mock_channel, mock_method):
    """Test handling of invalid JSON message."""
    body = b"not valid json {["

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge (not requeue malformed messages)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_missing_action_field(consumer, mock_channel, mock_method):
    """Test handling of message missing 'action' field."""
    message = {
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge and skip
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_missing_user_id_field(consumer, mock_channel, mock_method):
    """Test handling of message missing 'user_keycloak_id' field."""
    message = {
        "action": "ban_user",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge and skip
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_unknown_action(consumer, mock_channel, mock_method):
    """Test handling of unknown action type."""
    message = {
        "action": "suspend",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge and skip
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_user_not_found(consumer, mock_channel, mock_method):
    """Test handling when user does not exist."""
    message = {
        "action": "ban_user",
        "user_keycloak_id": "non-existent-user-999",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge (user might have been deleted)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_ban_already_banned_user(consumer, mock_channel, mock_method, banned_user, db_session):
    """Test banning a user who is already banned (idempotency)."""
    message = {
        "action": "ban_user",
        "user_keycloak_id": "test-rabbitmq-banned-456",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # User should still be banned
    db_session.expire_all()
    user = db_session.query(User).filter(User.keycloak_id == "test-rabbitmq-banned-456").first()
    assert user.is_banned is True

    # Should acknowledge and skip update
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_unban_already_unbanned_user(consumer, mock_channel, mock_method, test_user, db_session):
    """Test unbanning a user who is not banned (idempotency)."""
    message = {
        "action": "unban_user",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": False
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # User should still be unbanned
    db_session.expire_all()
    user = db_session.query(User).filter(User.keycloak_id == "test-rabbitmq-user-123").first()
    assert user.is_banned is False

    # Should acknowledge and skip update
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


@patch('app.services.rabbitmq_consumer.SessionLocal')
def test_database_error_causes_requeue(mock_session_local, consumer, mock_channel, mock_method):
    """Test that database errors cause message to be requeued."""
    # Mock database session to raise an exception
    mock_db = Mock()
    mock_db.query.side_effect = Exception("Database connection error")
    mock_session_local.return_value = mock_db

    message = {
        "action": "ban_user",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should nack and requeue
    mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=True)
    mock_channel.basic_ack.assert_not_called()

    # Ensure session was closed
    mock_db.close.assert_called_once()


@patch('app.services.rabbitmq_consumer.SessionLocal')
def test_commit_error_causes_requeue(mock_session_local, consumer, mock_channel, mock_method):
    """Test that commit errors cause message to be requeued."""
    # Mock database session with commit error
    mock_db = Mock()
    mock_user = Mock()
    mock_user.keycloak_id = "test-rabbitmq-user-123"
    mock_user.is_banned = False

    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    mock_db.commit.side_effect = Exception("Commit failed")
    mock_session_local.return_value = mock_db

    message = {
        "action": "ban_user",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": True
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should nack and requeue
    mock_channel.basic_nack.assert_called_once_with(delivery_tag=123, requeue=True)
    mock_channel.basic_ack.assert_not_called()

    # Ensure session was closed
    mock_db.close.assert_called_once()


def test_empty_message(consumer, mock_channel, mock_method):
    """Test handling of empty message."""
    body = b""

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should acknowledge (malformed message, don't requeue)
    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()


def test_message_with_extra_fields(consumer, mock_channel, mock_method, test_user, db_session):
    """Test that extra fields in message are ignored."""
    message = {
        "action": "ban_user",
        "user_keycloak_id": "test-rabbitmq-user-123",
        "ban": True,
        "extra_field": "should be ignored",
        "another_field": "also ignored"
    }
    body = json.dumps(message).encode('utf-8')

    # Process message
    consumer.process_message(mock_channel, mock_method, None, body)

    # Should still process successfully
    db_session.expire_all()
    user = db_session.query(User).filter(User.keycloak_id == "test-rabbitmq-user-123").first()
    assert user.is_banned is True

    mock_channel.basic_ack.assert_called_once_with(delivery_tag=123)
    mock_channel.basic_nack.assert_not_called()
