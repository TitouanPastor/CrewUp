"""
Safety Service - Main application entry point.

Handles safety alerts and emergency notifications for events.
"""
import uvicorn
from app.main import app
from app.config import config

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug"
    )