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
        Get PostgreSQL connection URL from individual environment variables.
        
        Local dev: postgresql://crewup:crewup_dev_password@localhost:5432/crewup
        K8s: postgresql://crewup:<secret>@postgres:5432/crewup
        """
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


# Create singleton instance
config = Config()
