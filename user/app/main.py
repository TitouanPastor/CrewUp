"""
Main FastAPI application for User Service.

This service handles:
- User profile creation from Keycloak tokens
- User profile management (read, update)
- Public user profiles
- JWT authentication via Keycloak

Architecture:
- app/models/ - Pydantic validation models
- app/db/ - SQLAlchemy ORM and database connection
- app/routers/ - API endpoints
- app/middleware/ - JWT authentication
- app/utils/ - Logging and error handling
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import config
from app.routers import users_router
from app.services import start_consumer, get_consumer
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
    title="CrewUp User Service",
    description="User profile management service with Keycloak authentication",
    version="1.0.0",
    docs_url="/api/v1/users/docs",
    redoc_url="/api/v1/users/redoc",
    openapi_url="/api/v1/users/openapi.json"
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
app.include_router(users_router, prefix="/api/v1")


# Health check endpoint (no auth required)
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "user-service"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": "user-service",
        "version": "1.0.0",
        "docs": "/api/v1/users/docs"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup and start RabbitMQ consumer."""
    logger.info(f"User Service starting on {config.get_database_url().split('@')[1]}")
    logger.info(f"Keycloak server: {config.KEYCLOAK_SERVER_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")
    logger.info(f"RabbitMQ URL: {config.RABBITMQ_URL}")

    # Start RabbitMQ consumer for moderation commands
    try:
        start_consumer()
        logger.info("RabbitMQ consumer started successfully")
    except Exception as e:
        logger.error(f"Failed to start RabbitMQ consumer: {e}")
        logger.warning("User service will continue without moderation queue support")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown and stop RabbitMQ consumer."""
    logger.info("User Service shutting down")

    # Stop RabbitMQ consumer
    try:
        consumer = get_consumer()
        consumer.stop_consuming()
        logger.info("RabbitMQ consumer stopped")
    except Exception as e:
        logger.error(f"Error stopping RabbitMQ consumer: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
