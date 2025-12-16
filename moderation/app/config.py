"""
Configuration management for Moderation Service.
Automatically detects environment (local dev vs k8s) and configures accordingly.
"""
import os
from typing import Optional


class Config:
    """Application configuration."""

    # Service info
    SERVICE_NAME: str = "moderation"

    # Database configuration
    @staticmethod
    def get_database_url() -> str:
        """
        Get PostgreSQL connection URL from environment variables.

        Priority:
        1. DATABASE_URL (full connection string)
        2. Individual POSTGRES_* variables

        Local dev: postgresql://crewup:crewup_dev_password@localhost:5432/crewup
        K8s: postgresql://crewup:<secret>@postgres:5432/crewup
        """
        # Check for full DATABASE_URL first (Docker Compose, some K8s configs)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url

        # Fall back to individual variables (K8s secrets)
        user = os.getenv("POSTGRES_USER", "crewup")
        password = os.getenv("POSTGRES_PASSWORD", "crewup_dev_password")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "crewup")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    # Keycloak configuration
    KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "https://keycloak.ltu-m7011e-3.se")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "crewup")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "crewup-backend")

    # API settings
    API_PREFIX: str = "/api/moderation"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Local Vite dev
        "http://localhost:3000",  # Alternative local
        "https://crewup.ltu-m7011e-3.se",  # Production
    ]

    # RabbitMQ configuration
    @staticmethod
    def get_rabbitmq_config() -> dict:
        """
        Get RabbitMQ connection parameters.

        Priority:
        1. RABBITMQ_URL (full connection string like amqp://user:pass@host:port/vhost)
        2. Individual RABBITMQ_* variables
        """
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if rabbitmq_url:
            # Parse RABBITMQ_URL: amqp://user:pass@host:port/vhost
            # Example: amqp://guest:guest@crewup-rabbitmq:5672/
            import re
            match = re.match(r'amqp://([^:]+):([^@]+)@([^:]+):(\d+)(/.*)?', rabbitmq_url)
            if match:
                user, password, host, port, vhost = match.groups()
                return {
                    'host': host,
                    'port': int(port),
                    'user': user,
                    'password': password,
                    'vhost': vhost or '/'
                }

        # Fall back to individual variables
        return {
            'host': os.getenv("RABBITMQ_HOST", "localhost"),
            'port': int(os.getenv("RABBITMQ_PORT", "5672")),
            'user': os.getenv("RABBITMQ_USER", "guest"),
            'password': os.getenv("RABBITMQ_PASSWORD", "guest"),
            'vhost': os.getenv("RABBITMQ_VHOST", "/")
        }

    # Get RabbitMQ config at startup
    _rabbitmq_config = get_rabbitmq_config.__func__()
    RABBITMQ_HOST: str = _rabbitmq_config['host']
    RABBITMQ_PORT: int = _rabbitmq_config['port']
    RABBITMQ_USER: str = _rabbitmq_config['user']
    RABBITMQ_PASSWORD: str = _rabbitmq_config['password']
    RABBITMQ_VHOST: str = _rabbitmq_config['vhost']

    # RabbitMQ exchanges and queues
    # Environment prefix to isolate queues between dev/staging/prod
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    USER_BAN_EXCHANGE: str = f"{ENVIRONMENT}.user.ban"
    USER_BAN_QUEUE: str = f"{ENVIRONMENT}.user.ban.queue"
    USER_BAN_ROUTING_KEY: str = f"{ENVIRONMENT}.user.ban"


# Create singleton instance
config = Config()
