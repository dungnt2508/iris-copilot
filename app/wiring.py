"""
Composition Root / Wiring module

Centralizes dependency wiring to keep API layer clean.
Replace InMemory implementations here with real infra when ready.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user.repository import UserRepository, UserEntityRepository
from app.domain.user.aggregates import UserAggregate, UserAggregateRepository
from app.infrastructure.db.repository_impl.user_repository_impl import (
    InMemoryUserRepository,
)
from app.infrastructure.db.repository_impl.sqlalchemy_user_repository import (
    SQLAlchemyUserRepository,
)
from app.infrastructure.db.repository_impl.sqlalchemy_user_aggregate_repository import (
    SQLAlchemyUserAggregateRepository,
)
from app.infrastructure.db.session import get_db_session
from app.core.config import settings


async def provide_db_session() -> AsyncSession:
    """Provide database session for dependency injection"""
    async for session in get_db_session():
        yield session


def provide_user_repository(session: Optional[AsyncSession] = None) -> UserRepository:
    """
    Provide UserRepository implementation (legacy)
    
    Args:
        session: SQLAlchemy session for DB operations. If None, uses InMemory.
    
    Returns:
        UserRepository implementation
    """
    if session and settings.database_url != "sqlite:///:memory:":
        # Use SQLAlchemy implementation with DB session
        return SQLAlchemyUserRepository(session)
    else:
        # Use InMemory implementation for development/testing
        return InMemoryUserRepository()


async def provide_user_repository_with_session() -> UserRepository:
    """Provide UserRepository with automatic session injection (legacy)"""
    async for session in get_db_session():
        if settings.database_url != "sqlite:///:memory:":
            return SQLAlchemyUserRepository(session)
        else:
            return InMemoryUserRepository()


# New Aggregate-based providers
def provide_user_aggregate_repository(session: Optional[AsyncSession] = None) -> UserAggregateRepository:
    """
    Provide UserAggregateRepository implementation
    
    Args:
        session: SQLAlchemy session for DB operations. If None, uses InMemory.
    
    Returns:
        UserAggregateRepository implementation
    """
    if session and settings.database_url != "sqlite:///:memory:":
        # Use SQLAlchemy implementation with DB session
        return SQLAlchemyUserAggregateRepository(session)
    else:
        # Use InMemory implementation for development/testing
        # Note: InMemoryUserAggregateRepository would need to be implemented
        raise NotImplementedError("InMemoryUserAggregateRepository not implemented yet")


async def provide_user_aggregate_repository_with_session() -> UserAggregateRepository:
    """Provide UserAggregateRepository with automatic session injection"""
    async for session in get_db_session():
        if settings.database_url != "sqlite:///:memory:":
            return SQLAlchemyUserAggregateRepository(session)
        else:
            # Use InMemory implementation for development/testing
            raise NotImplementedError("InMemoryUserAggregateRepository not implemented yet")


# Service providers
def provide_token_service():
    """Provide TokenService with configuration"""
    from app.services.token_service import TokenService
    return TokenService(
        secret_key=settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


def provide_password_service():
    """Provide PasswordService"""
    from app.services.password_service import PasswordService
    return PasswordService()


# Development helpers
def get_repository_mode() -> str:
    """Get current repository mode (in_memory or database)"""
    if settings.database_url == "sqlite:///:memory:" or not settings.database_url:
        return "in_memory"
    return "database"


def get_aggregate_mode() -> str:
    """Get current aggregate mode (legacy or aggregate)"""
    return "aggregate"  # Always use aggregate mode for new features


