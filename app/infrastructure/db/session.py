"""
Database Session Utilities
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.infrastructure.db.base import get_async_session


async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async for session in get_async_session():
            result = await session.execute(text("SELECT 1"))
            await result.fetchone()
            return True
    except Exception:
        return False


async def get_db_session() -> AsyncSession:
    """Get database session for dependency injection"""
    async for session in get_async_session():
        yield session


async def get_db_session_sync() -> Optional[AsyncSession]:
    """Get database session synchronously (for testing)"""
    try:
        async for session in get_async_session():
            return session
    except Exception:
        return None
