"""
Configuration for Group & Chat Service.
Environment variables with defaults for local development.
"""
import os
from typing import List


class Config:
    """Application configuration."""
    
    SERVICE_NAME: str = "group"
    
    # Database
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "crewup")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "crewup_dev_password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "crewup")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    @staticmethod
    def get_database_url() -> str:
        """
        Construct database URL from environment variables.
        
        Priority:
        1. DATABASE_URL (full connection string)
        2. Individual POSTGRES_* variables
        """
        # Check for full DATABASE_URL first (Docker Compose, some K8s configs)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # Fall back to individual variables (K8s secrets)
        user = Config.POSTGRES_USER
        password = Config.POSTGRES_PASSWORD
        host = Config.POSTGRES_HOST
        port = Config.POSTGRES_PORT
        database = Config.POSTGRES_DB
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    # Keycloak
    KEYCLOAK_SERVER_URL: str = os.getenv(
        "KEYCLOAK_SERVER_URL",
        "https://keycloak.ltu-m7011e-3.se"
    )
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "crewup")
    KEYCLOAK_CLIENT_ID: str = os.getenv("KEYCLOAK_CLIENT_ID", "crewup-frontend")
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative frontend
        "https://crewup.ltu-m7011e-3.se",  # Production
    ]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Chat settings
    MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))
    MESSAGE_RATE_LIMIT: int = int(os.getenv("MESSAGE_RATE_LIMIT", "60"))  # per minute
    MAX_GROUP_MEMBERS: int = int(os.getenv("MAX_GROUP_MEMBERS", "50"))


config = Config()
