"""
API v1 Router
"""
from fastapi import APIRouter

from .routers import auth, chat, teams, upload
from .routers.copilot import router as copilot_router

# Create main API router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])

# Include Copilot router
api_router.include_router(copilot_router, tags=["Copilot"])

__all__ = ["api_router"]
