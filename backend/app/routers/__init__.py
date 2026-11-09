"""
FastAPI routers for PawFect backend.
"""

from app.routers.chat import router as chat_router
from app.routers.pets import router as pets_router
from app.routers.matches import router as matches_router
from app.routers.adoptions import router as adoptions_router
from app.routers.users import router as users_router

__all__ = [
    "chat_router",
    "pets_router",
    "matches_router",
    "adoptions_router",
    "users_router",
]
