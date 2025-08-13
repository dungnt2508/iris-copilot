# Testing Guide - IRIS Backend

## 📋 Tổng quan

Testing suite được thiết kế theo Clean Architecture và Domain-Driven Design, bao gồm:

- **Unit Tests**: Test các domain entities, value objects, và business logic
- **Integration Tests**: Test use cases và service interactions
- **End-to-End Tests**: Test API endpoints và Copilot integration
- **Test Coverage**: Đảm bảo coverage > 80%

## 🏗️ Test Structure

```
tests/
├── conftest.py                 # Pytest configuration và fixtures
├── test_runner.py             # Test runner script
├── unit/                      # Unit tests
│   ├── test_chat_entities.py  # Chat domain tests
│   └── test_services.py       # Service layer tests
├── integration/               # Integration tests
│   └── test_use_cases.py      # Use case tests
└── e2e/                       # End-to-end tests
    └── test_copilot_api.py    # API endpoint tests
```

## 🚀 Chạy Tests

### 1. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 2. Chạy tất cả tests
```bash
python tests/test_runner.py
```

### 3. Chạy theo loại test
```bash
# Unit tests only
python tests/test_runner.py --type unit

# Integration tests only
python tests/test_runner.py --type integration

# E2E tests only
python tests/test_runner.py --type e2e
```

### 4. Chạy với coverage
```bash
python tests/test_runner.py --coverage
```

### 5. Chạy với verbose output
```bash
python tests/test_runner.py --verbose
```

### 6. Chạy fast tests (skip slow markers)
```bash
python tests/test_runner.py --fast
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)

**Mục đích**: Test các domain entities, value objects, và business logic độc lập

**Coverage**:
- ✅ Chat domain entities (ChatSession, ChatMessage)
- ✅ Value objects (MessageContent, ChatContext)
- ✅ Service layer (LLMService, SearchService)
- ✅ Adapters (OpenAIAdapter)

**Ví dụ**:
```python
def test_create_user_message(self):
    """Test creating user message"""
    message = ChatMessage.create_user_message(
        session_id="test-session",
        content="Test user message"
    )
    
    assert message.role == MessageRole.USER
    assert message.content.text == "Test user message"
    assert message.status == MessageStatus.PENDING
```

### Integration Tests (`tests/integration/`)

**Mục đích**: Test use cases và service interactions

**Coverage**:
- ✅ ProcessChatQueryUseCase
- ✅ Service orchestration
- ✅ Repository interactions
- ✅ Error handling

**Ví dụ**:
```python
@pytest.mark.asyncio
async def test_execute_rag_query(self, use_case, mock_llm_service):
    """Test executing RAG query"""
    request = ProcessChatQueryRequest(
        user_id="test-user",
        query="What is AI?",
        use_rag=True,
        max_sources=3
    )
    
    response = await use_case.execute(request)
    
    assert response.answer == "Test RAG response"
    assert len(response.sources) == 1
    assert response.confidence > 0.0
```

### End-to-End Tests (`tests/e2e/`)

**Mục đích**: Test API endpoints và Copilot integration

**Coverage**:
- ✅ Copilot chat endpoint
- ✅ Copilot search endpoint
- ✅ Health check endpoint
- ✅ Error handling
- ✅ Response format validation

**Ví dụ**:
```python
def test_copilot_chat_endpoint(self, test_client, mock_use_case):
    """Test copilot chat endpoint"""
    with patch("app.api.v1.routers.copilot.get_process_chat_query_use_case", return_value=mock_use_case):
        response = test_client.post(
            "/api/v1/copilot/chat",
            json={
                "query": "Hello, how are you?",
                "use_rag": True
            }
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Test assistant response"
```

## 🔧 Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    database: Tests that require database
    external: Tests that require external services

addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
```

### Test Fixtures (`tests/conftest.py`)

**Database Fixtures**:
- `test_engine`: Test database engine
- `test_session`: Test database session
- `chat_repository`: Chat repository with test session
- `document_repository`: Document repository with test session
- `embedding_repository`: Embedding repository with test session

**Mock Fixtures**:
- `mock_openai_adapter`: Mock OpenAI adapter
- `mock_llm_service`: Mock LLM service
- `mock_search_service`: Mock search service

**Test Data Fixtures**:
- `sample_chat_session_data`: Sample chat session data
- `sample_chat_message_data`: Sample chat message data
- `sample_document_data`: Sample document data
- `sample_embedding_data`: Sample embedding data

## 📊 Coverage Reports

### HTML Coverage Report
```bash
# Generate HTML coverage report
python tests/test_runner.py --coverage

# Open in browser
open htmlcov/index.html
```

### Coverage Targets
- **Overall Coverage**: > 80%
- **Domain Layer**: > 90%
- **Service Layer**: > 85%
- **API Layer**: > 80%

## 🏷️ Test Markers

### Markers Usage
```python
import pytest

@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_function():
    pass

@pytest.mark.e2e
def test_e2e_function():
    pass

@pytest.mark.slow
def test_slow_function():
    pass

@pytest.mark.database
def test_database_function():
    pass

@pytest.mark.external
def test_external_service():
    pass
```

### Running Tests by Markers
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only e2e tests
pytest -m e2e

# Skip slow tests
pytest -m "not slow"

# Run tests that require database
pytest -m database

# Run tests that require external services
pytest -m external
```

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest -v -s
```

### Debug Specific Test
```bash
pytest tests/unit/test_chat_entities.py::TestChatMessage::test_create_user_message -v -s
```

### Debug with PDB
```bash
pytest --pdb
```

### Debug with IPDB (if installed)
```bash
pytest --ipdb
```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/test_runner.py --coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## 📝 Best Practices

### 1. Test Naming
```python
# Good
def test_create_user_message_with_valid_content():
    pass

def test_create_user_message_with_empty_content_raises_error():
    pass

# Bad
def test_1():
    pass

def test_something():
    pass
```

### 2. Test Organization
```python
class TestChatMessage:
    """Test ChatMessage entity"""
    
    def test_create_user_message(self):
        """Test creating user message"""
        pass
    
    def test_create_assistant_message(self):
        """Test creating assistant message"""
        pass
    
    def test_mark_completed(self):
        """Test marking message as completed"""
        pass
```

### 3. Mock Usage
```python
@pytest.fixture
def mock_openai_adapter(self):
    """Mock OpenAI adapter"""
    mock = AsyncMock()
    mock.generate_embedding.return_value = [0.1] * 1536
    return mock

def test_with_mock(self, mock_openai_adapter):
    """Test with mock"""
    # Use mock
    result = mock_openai_adapter.generate_embedding("test")
    assert len(result) == 1536
```

### 4. Async Test Handling
```python
@pytest.mark.asyncio
async def test_async_function(self):
    """Test async function"""
    result = await some_async_function()
    assert result == expected_value
```

### 5. Database Test Isolation
```python
@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # Cleanup
```

## 🚨 Common Issues

### 1. Async Test Issues
```python
# Problem: Test not running async
def test_async_function():  # Missing @pytest.mark.asyncio
    result = await some_async_function()  # Will fail

# Solution
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
```

### 2. Mock Not Working
```python
# Problem: Mock not being used
def test_with_mock(self):
    result = real_function()  # Calls real function

# Solution: Use dependency injection
def test_with_mock(self, mock_dependency):
    result = mock_dependency.function()
```

### 3. Database Test Pollution
```python
# Problem: Tests affecting each other
def test_1(self):
    create_data()  # Affects other tests

# Solution: Use transaction rollback
@pytest.fixture
async def test_session():
    async with session() as s:
        yield s
        await s.rollback()  # Cleanup
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-Cov](https://pytest-cov.readthedocs.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Faker](https://faker.readthedocs.io/)


Next Steps:
Bây giờ chúng ta đã hoàn thiện:
✅ Domain Layer - Entities, Value Objects, Repositories
✅ Infrastructure Layer - SQLAlchemy models, Repository implementations
✅ Service Layer - LLMService, SearchService, OpenAIAdapter
✅ Application Layer - Use cases, ProcessChatQueryUseCase
✅ API Layer - Copilot endpoints, FastAPI integration
✅ Testing Layer - Unit, Integration, E2E tests
Phase 1 đã hoàn thiện! 🎉
Bước tiếp theo có thể là:
Deployment & DevOps - Docker, CI/CD, monitoring
Performance Optimization - Caching, async processing
Security Hardening - Authentication, authorization
Documentation - API docs, user guides
Production Readiness - Error handling, logging, monitoring
Bạn muốn tiếp tục với bước nào tiếp theo?