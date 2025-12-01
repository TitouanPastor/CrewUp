"""
Configuration management for User Service.
Automatically detects environment (local dev vs k8s) and configures accordingly.
"""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Service info
    SERVICE_NAME: str = "user"
    
    # Database configuration
    # Database configuration - constructed from environment variables
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
    API_PREFIX: str = "/api/users"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS settings
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Local Vite dev
        "http://localhost:3000",  # Alternative local
        "https://crewup.ltu-m7011e-3.se",  # Production
    ]

    # RabbitMQ configuration
    RABBITMQ_URL: str = os.getenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/"
    )


# Create singleton instance
config = Config()
