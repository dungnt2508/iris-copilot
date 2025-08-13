"""
Dependency Injection Wiring
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import get_async_session
from app.infrastructure.db.repository_impl.chat_repository_impl import SQLAlchemyChatRepository
from app.infrastructure.db.repository_impl.document_repository_impl import SQLAlchemyDocumentRepository
from app.infrastructure.db.repository_impl.embedding_repository_impl import SQLAlchemyEmbeddingRepository
from app.adapters.openai_adapter import OpenAIAdapter
from app.services.llm_service import LLMService
from app.services.search_service import SearchService
from app.application.chat.use_cases.process_chat_query import ProcessChatQueryUseCase
from app.core.logger import get_logger

logger = get_logger(__name__)


# Database setup
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=300
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


# Repository dependencies
async def get_chat_repository(session: AsyncSession = None) -> SQLAlchemyChatRepository:
    """Get chat repository"""
    if session is None:
        async with AsyncSessionLocal() as session:
            return SQLAlchemyChatRepository(session)
    return SQLAlchemyChatRepository(session)


async def get_document_repository(session: AsyncSession = None) -> SQLAlchemyDocumentRepository:
    """Get document repository"""
    if session is None:
        async with AsyncSessionLocal() as session:
            return SQLAlchemyDocumentRepository(session)
    return SQLAlchemyDocumentRepository(session)


async def get_embedding_repository(session: AsyncSession = None) -> SQLAlchemyEmbeddingRepository:
    """Get embedding repository"""
    if session is None:
        async with AsyncSessionLocal() as session:
            return SQLAlchemyEmbeddingRepository(session)
    return SQLAlchemyEmbeddingRepository(session)


# Adapter dependencies
def get_openai_adapter() -> OpenAIAdapter:
    """Get OpenAI adapter"""
    return OpenAIAdapter(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url
    )


# Service dependencies
def get_llm_service() -> LLMService:
    """Get LLM service"""
    openai_adapter = get_openai_adapter()
    return LLMService(openai_adapter)


async def get_search_service() -> SearchService:
    """Get search service"""
    document_repo = await get_document_repository()
    embedding_repo = await get_embedding_repository()
    llm_service = get_llm_service()
    return SearchService(document_repo, embedding_repo, llm_service)


# Use case dependencies
async def get_process_chat_query_use_case() -> ProcessChatQueryUseCase:
    """Get process chat query use case"""
    chat_repo = await get_chat_repository()
    document_repo = await get_document_repository()
    embedding_repo = await get_embedding_repository()
    llm_service = get_llm_service()
    search_service = await get_search_service()
    
    return ProcessChatQueryUseCase(
        chat_repository=chat_repo,
        document_repository=document_repo,
        embedding_repository=embedding_repo,
        llm_service=llm_service,
        search_service=search_service
    )


# Database initialization
async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def close_database():
    """Close database connections"""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
        raise


