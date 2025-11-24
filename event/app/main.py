"""
Main FastAPI application for Event Service.

This service handles:
- Event creation and management
- Event RSVP (join/leave)
- Event search and filtering
- Participant management

Architecture:
- app/models/ - Pydantic validation models
- app/db/ - SQLAlchemy ORM and database connection
- app/routers/ - REST API endpoints
- app/middleware/ - JWT authentication
- app/utils/ - Logging and error handling
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import config
from app.routers import events_router
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
    title="CrewUp Event Service",
    description="Event management service with RSVP, search, and participant tracking",
    version="1.0.0",
    docs_url="/api/v1/events/docs",
    redoc_url="/api/v1/events/redoc",
    openapi_url="/api/v1/events/openapi.json"
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
app.include_router(events_router, prefix="/api/v1")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    logger.info(f"Event Service starting on {config.get_database_url().split('@')[1]}")
    logger.info(f"Keycloak server: {config.KEYCLOAK_SERVER_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Event Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
