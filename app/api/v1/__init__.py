"""
API v1 Router
"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Test endpoint
@api_router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {"message": "API is working!"}

# Try to include routers one by one
try:
    from .routers import auth
    api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
    print("✅ Auth router included")
except Exception as e:
    print(f"❌ Error including auth router: {e}")

try:
    from .routers import chat
    api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
    print("✅ Chat router included")
except Exception as e:
    print(f"❌ Error including chat router: {e}")

try:
    from .routers import teams
    api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
    print("✅ Teams router included")
except Exception as e:
    print(f"❌ Error including teams router: {e}")

try:
    from .routers import upload
    api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
    print("✅ Upload router included")
except Exception as e:
    print(f"❌ Error including upload router: {e}")

try:
    from .routers import azure_ad
    api_router.include_router(azure_ad.router, tags=["Azure AD"])
    print("✅ Azure AD router included")
except Exception as e:
    print(f"❌ Error including azure_ad router: {e}")

__all__ = ["api_router"]
