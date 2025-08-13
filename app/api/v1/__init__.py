from fastapi import APIRouter

# Import routers
from .routers.auth import router as auth_router
from .routers.chat import router as chat_router
from .routers.upload import router as upload_router
from .routers.azure_ad import router as azure_ad_router
from .routers.calendar import router as calendar_router
from .routers.teams import router as teams_router


# Aggregate API v1 routers
api_router = APIRouter()

# Auth endpoints
api_router.include_router(auth_router, prefix="/auth")

# Chat endpoints
api_router.include_router(chat_router, prefix="/chat")

# Document endpoints
api_router.include_router(upload_router, prefix="/documents")

# Azure AD endpoints
api_router.include_router(azure_ad_router)

# Calendar endpoints
api_router.include_router(calendar_router)

# Teams endpoints
api_router.include_router(teams_router)

__all__ = ["api_router"]
