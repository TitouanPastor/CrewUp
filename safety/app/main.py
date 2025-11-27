"""
Safety Service - FastAPI application.
Emergency alert system for CrewUp events.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

from app.config import config
from app.routers import alerts_router
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
    title="Safety Service",
    description="Emergency alerts for CrewUp events",
    version="1.0.0",
    docs_url="/api/v1/safety/docs",
    redoc_url="/api/v1/safety/redoc",
    openapi_url="/api/v1/safety/openapi.json"
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

# Include routers WITHOUT additional prefix (router already has /safety)
app.include_router(alerts_router)


@app.get("/health", tags=["health"])
async def health_check():
    """Service health check."""
    return {"status": "healthy", "service": "safety", "version": "1.0.0"}


@app.on_event("startup")
async def startup_event():
    """Log startup info."""
    db_url = config.get_database_url()
    db_info = db_url.split('@')[1] if '@' in db_url else "in-memory"
    logger.info(f"Safety Service starting on {db_info}")
    logger.info(f"Keycloak: {config.KEYCLOAK_SERVER_URL}/realms/{config.KEYCLOAK_REALM}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log shutdown."""
    logger.info("Safety Service shutting down")

