"""
Configuration management for Group Service.
Automatically detects environment (local dev vs k8s) and configures accordingly.
"""
import os


class Config:
    """Application configuration."""
    
    SERVICE_NAME: str = "group"
    
    @staticmethod
    def get_database_url() -> str:
        """Get PostgreSQL connection URL."""
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        user = os.getenv("POSTGRES_USER", "crewup")
        password = os.getenv("POSTGRES_PASSWORD", "crewup_dev_password")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "crewup")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    KEYCLOAK_SERVER_URL: str = os.getenv("KEYCLOAK_SERVER_URL", "https://keycloak.ltu-m7011e-3.se")
    KEYCLOAK_REALM: str = os.getenv("KEYCLOAK_REALM", "crewup")
    
    API_PREFIX: str = "/api/groups"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
