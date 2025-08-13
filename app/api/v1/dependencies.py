from typing import Optional, Callable
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.token_service import TokenService
from app.domain.user.repository import UserRepository
from app.domain.user.entities.user import User, UserRole
from app.adapters.azure_ad_adapter import AzureADAdapter
from app.wiring import (
    provide_user_repository_with_session,
    provide_token_service,
    provide_password_service,
    provide_db_session,
    get_repository_mode,
)


async def get_token_service() -> TokenService:
    return provide_token_service()


async def get_user_repository() -> UserRepository:
    """Get UserRepository with automatic mode selection"""
    return await provide_user_repository_with_session()


async def get_azure_ad_adapter() -> AzureADAdapter:
    """Get Azure AD Adapter"""
    return AzureADAdapter()


async def get_db_session() -> AsyncSession:
    """Get database session"""
    async for session in provide_db_session():
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None),
    token_service: TokenService = Depends(get_token_service),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    token_data = await token_service.verify_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await user_repo.find_by_id(token_data["user_id"])  # type: ignore
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_roles(*roles: UserRole):
    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return _dependency


def require_permissions(*permissions: str):
    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        # Admin bypass
        if current_user.role == UserRole.ADMIN:
            return current_user
        missing = [p for p in permissions if p not in current_user.permissions]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Missing permissions: " + ", ".join(missing),
            )
        return current_user

    return _dependency


# Development helpers
async def get_repository_info():
    """Get repository mode for debugging"""
    return {
        "mode": get_repository_mode(),
        "database_url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden",
    }

