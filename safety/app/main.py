"""
FastAPI application setup and configuration.
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
    title="CrewUp Safety Service",
    description="Emergency alerts and safety features for events",
    version="1.0.0",
    docs_url="/api/v1/alerts/docs",
    redoc_url="/api/v1/alerts/redoc",
    openapi_url="/api/v1/alerts/openapi.json"
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
app.include_router(alerts_router, prefix="/api/v1")


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "safety",
        "version": "1.0.0"
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log application startup."""
    db_url = config.get_database_url()
    # Hide password in logs
    if '@' in db_url:
        db_info = db_url.split('@')[1]
    else:
        db_info = "in-memory" if "sqlite" in db_url else db_url
    logger.info(f"Safety Service starting on {db_info}")
    logger.info(f"Keycloak server: {config.KEYCLOAK_SERVER_URL}")
    logger.info(f"CORS origins: {config.CORS_ORIGINS}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Safety Service shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
