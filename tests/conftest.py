"""
Pytest Configuration and Fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.infrastructure.db.base import Base
from app.wiring import get_db_session, get_chat_repository, get_document_repository, get_embedding_repository
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5432/iris_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """Create test client"""
    with TestClient(app) as client:
        yield client


# Mock fixtures for external services
@pytest.fixture
def mock_openai_adapter():
    """Mock OpenAI adapter"""
    mock = AsyncMock()
    
    # Mock embedding response
    mock.generate_embedding.return_value = [0.1] * 1536
    
    # Mock chat completion response
    mock.generate_completion.return_value = {
        "content": "Test response",
        "model": "gpt-4",
        "usage": {"total_tokens": 100},
        "processing_time_ms": 500
    }
    
    # Mock health check
    mock.health_check.return_value = {"status": "healthy"}
    
    # Mock list models
    mock.list_models.return_value = [
        {"id": "gpt-4", "object": "model"},
        {"id": "text-embedding-ada-002", "object": "model"}
    ]
    
    return mock


@pytest.fixture
def mock_llm_service(mock_openai_adapter):
    """Mock LLM service"""
    from app.services.llm_service import LLMService
    
    service = LLMService(mock_openai_adapter)
    return service


@pytest.fixture
def mock_search_service():
    """Mock search service"""
    mock = AsyncMock()
    
    # Mock search results
    mock.search.return_value = [
        {
            "id": "test-doc-1",
            "title": "Test Document 1",
            "content": "This is test content 1",
            "score": 0.85,
            "source_type": "document",
            "source_id": "doc-1",
            "metadata": {}
        },
        {
            "id": "test-doc-2", 
            "title": "Test Document 2",
            "content": "This is test content 2",
            "score": 0.75,
            "source_type": "document",
            "source_id": "doc-2",
            "metadata": {}
        }
    ]
    
    return mock


# Repository fixtures
@pytest.fixture
async def chat_repository(test_session):
    """Get chat repository with test session"""
    return await get_chat_repository(test_session)


@pytest.fixture
async def document_repository(test_session):
    """Get document repository with test session"""
    return await get_document_repository(test_session)


@pytest.fixture
async def embedding_repository(test_session):
    """Get embedding repository with test session"""
    return await get_embedding_repository(test_session)


# Test data fixtures
@pytest.fixture
def sample_chat_session_data():
    """Sample chat session data for testing"""
    return {
        "id": "test-session-1",
        "user_id": "test-user-1",
        "title": "Test Chat Session",
        "metadata": {"test": True},
        "is_active": True,
        "max_messages": 100
    }


@pytest.fixture
def sample_chat_message_data():
    """Sample chat message data for testing"""
    return {
        "id": "test-message-1",
        "session_id": "test-session-1",
        "content": "Test message content",
        "role": "user",
        "status": "completed",
        "metadata": {"test": True},
        "sources": [],
        "tokens_used": 50,
        "model_used": "gpt-4",
        "response_time_ms": 200
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "id": "test-doc-1",
        "user_id": "test-user-1",
        "title": "Test Document",
        "content": "This is a test document content for testing purposes.",
        "file_metadata": {
            "filename": "test.pdf",
            "file_size": 1024,
            "content_type": "application/pdf",
            "checksum": "test-checksum"
        },
        "document_type": "pdf",
        "status": "completed",
        "metadata": {"test": True},
        "processing_config": {"chunk_size": 1000},
        "version": 1,
        "word_count": 10,
        "language": "vi"
    }


@pytest.fixture
def sample_embedding_data():
    """Sample embedding data for testing"""
    return {
        "id": "test-embedding-1",
        "vector": [0.1] * 1536,
        "metadata": {
            "source_type": "document_chunk",
            "source_id": "test-chunk-1",
            "content_preview": "Test content preview",
            "tokens_used": 50,
            "processing_time_ms": 100
        },
        "embedding_type": "text",
        "status": "completed",
        "tags": {"test": True},
        "version": 1,
        "dimension": 1536,
        "model": "text-embedding-ada-002"
    }


# Override dependencies for testing
def override_get_db_session():
    """Override database session dependency for testing"""
    async def _get_test_db_session():
        async_session = sessionmaker(
            create_async_engine(TEST_DATABASE_URL),
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session() as session:
            yield session
    
    return _get_test_db_session


# Test utilities
class TestUtils:
    """Utility functions for testing"""
    
    @staticmethod
    def create_test_user_id() -> str:
        """Create a test user ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def create_test_session_id() -> str:
        """Create a test session ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def create_test_document_id() -> str:
        """Create a test document ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def create_test_embedding_id() -> str:
        """Create a test embedding ID"""
        import uuid
        return str(uuid.uuid4())


@pytest.fixture
def test_utils():
    """Get test utilities"""
    return TestUtils
