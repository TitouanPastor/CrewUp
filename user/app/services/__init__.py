"""
Services package.
"""
from app.services.rabbitmq_consumer import start_consumer, get_consumer

__all__ = ["start_consumer", "get_consumer"]
