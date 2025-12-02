"""
Main FastAPI application for Moderation Service.

This service handles:
- Moderation endpoints (requires Moderator role)
- JWT authentication via Keycloak
- Role-based access control (Moderator role required)

Architecture:
- app/models/ - Pydantic validation models
- app/db/ - SQLAlchemy ORM and database connection
- app/routers/ - API endpoints
- app/middleware/ - JWT authentication + role checking
- app/utils/ - Logging and error handling
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import config
from app.routers import moderation_router
from app.db import init_db
from app.utils import (
    setup_logging,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler
)

# Setup logging
logger = setup_logging(log_level=config.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="CrewUp Moderation Service",
    description="Moderation service with role-based access control (Moderator role required)",
    version="1.0.0",
    docs_url="/api/v1/moderation/docs",
    redoc_url="/api/v1/moderation/redoc",
    openapi_url="/api/v1/moderation/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include routers
app.include_router(moderation_router, prefix="/api/v1")


# Health check endpoint (no auth required)
@app.get("/api/v1/moderation/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "moderation-service"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "moderation-service",
        "version": "1.0.0",
        "docs": "/api/v1/moderation/docs",
        "note": "All endpoints require Moderator role"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and log application startup."""
    logger.info("Moderation Service starting...")
    init_db()
    logger.info(f"Database: {config.get_database_url().split('@')[1]}")
    logger.info(f"Keycloak server: {config.KEYCLOAK_SERVER_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Moderation Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
