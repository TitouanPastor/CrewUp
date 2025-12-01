"""
Main FastAPI application for Group & Chat Service.

This service handles:
- Group creation and management for events
- Group membership (join/leave)
- Real-time WebSocket chat
- Message history
- Typing indicators
- Internal broadcast API for inter-service communication

Architecture:
- app/models/ - Pydantic validation models
- app/db/ - SQLAlchemy ORM and database connection
- app/routers/ - REST API endpoints + WebSocket + Internal API
- app/middleware/ - JWT authentication
- app/services/ - WebSocket connection manager
- app/utils/ - Logging and error handling
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import config
from app.routers import groups_router, chat_router, internal_router
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
    title="CrewUp Group & Chat Service",
    description="Group management and real-time chat service with WebSocket support",
    version="1.0.0",
    docs_url="/api/v1/groups/docs",
    redoc_url="/api/v1/groups/redoc",
    openapi_url="/api/v1/groups/openapi.json"
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
app.include_router(groups_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1/groups")  # Internal routes under /api/v1/groups


# Health check endpoint (no auth required)
@app.get("/api/v1/groups/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "group-service"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "group-service",
        "version": "1.0.0",
        "docs": "/api/v1/groups/docs"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(f"Group & Chat Service starting on {config.get_database_url().split('@')[1]}")
    logger.info(f"Keycloak server: {config.KEYCLOAK_SERVER_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")
    logger.info(f"Max message length: {config.MAX_MESSAGE_LENGTH}")
    logger.info(f"Message rate limit: {config.MESSAGE_RATE_LIMIT}/min")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Group & Chat Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
