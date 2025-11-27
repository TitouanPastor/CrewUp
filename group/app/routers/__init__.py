"""
API routers package.
"""
from app.routers.groups import router as groups_router
from app.routers.chat import router as chat_router
from app.routers.internal import router as internal_router

__all__ = ["groups_router", "chat_router", "internal_router"]
