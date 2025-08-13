# KẾ HOẠCH NÂNG CẤP DỰ ÁN IRIS THEO KIẾN TRÚC DOMAIN-DRIVEN DESIGN

## 📋 Tổng quan
Kế hoạch nâng cấp dự án IRIS từ kiến trúc monolithic hiện tại sang kiến trúc Domain-Driven Design (DDD) theo chuẩn Clean Architecture.

## 🎯 Mục tiêu nâng cấp

| Mục tiêu | Lợi ích | Phương pháp |
|----------|---------|-------------|
| **Tách biệt business logic** | Dễ kiểm thử, tái sử dụng | Domain layer độc lập |
| **Không phụ thuộc framework** | Linh hoạt thay đổi công nghệ | Interface & Adapter pattern |
| **Dễ chuyển sang microservices** | Scale từng phần độc lập | Module boundaries rõ ràng |
| **Quản lý phức tạp tốt hơn** | Maintainability cao | Use case driven |
| **Hỗ trợ nhiều client** | Teams, Web, Mobile | Adapter layer |

## 🏗️ So sánh kiến trúc

### Kiến trúc hiện tại (Monolithic)
```
backend/
├── api/v1/
│   ├── main.py              # Entry point + routes
│   ├── routers/             # API endpoints  
│   └── services/            # 23+ services (mixed logic)
│       ├── auth.py
│       ├── chat_service.py
│       ├── document_service.py (1485 lines!)
│       ├── embedding_service.py
│       ├── openai_service.py
│       └── ... (18 services khác)
```

**Vấn đề:**
- ❌ Business logic trộn lẫn với infrastructure
- ❌ Service files quá lớn (document_service.py: 1485 dòng)
- ❌ Khó test và mock dependencies
- ❌ Tight coupling giữa các layers

### Kiến trúc mới (Domain-Driven Design)
```
iris-backend-v2/
├── app/
│   ├── domain/              # Pure business logic
│   ├── services/            # Orchestration layer
│   ├── adapters/            # External integrations
│   ├── infrastructure/      # Data persistence
│   └── api/                 # Presentation layer
```

## 📊 Phân tích & Mapping

### 1. Mapping Services sang Domain

| Service hiện tại | Domain mới | Use Cases |
|-----------------|------------|-----------|
| `auth.py` + `role_service.py` | `domain/user/` | Login, Register, UpdateRole |
| `chat_service.py` | `domain/chat/` | ProcessQuery, GetHistory |
| `document_service.py` + `enhanced_document_service.py` | `domain/document/` | Upload, Search, Update |
| `embedding_service.py` + `centralized_embedding_service.py` | `domain/embedding/` | GenerateEmbedding, UpdateEmbedding |
| `content_generation_service.py` | `domain/generation/` | GenerateContent, GenerateImage |
| `analytics_service.py` | `domain/analytics/` | GetMetrics, GenerateReport |
| `versioning_service.py` | `domain/versioning/` | CreateVersion, Rollback |

### 2. Tách Service Layer

| Service hiện tại | Service mới | Vai trò |
|-----------------|-------------|---------|
| `openai_service.py` | `services/llm_service.py` | Orchestrate AI calls |
| `database_service.py` | Infrastructure layer | Data persistence |
| `cache_service.py` | Infrastructure layer | Caching |
| `search_service.py` + `semantic_search.py` | `services/search_service.py` | Search orchestration |
| `quality_monitoring_service.py` | `services/monitoring_service.py` | Quality checks |

### 3. Thiết kế Adapter Layer

| Integration | Adapter | Mục đích |
|------------|---------|----------|
| OpenAI API | `adapters/openai_adapter.py` | Wrap OpenAI calls |
| Azure AD | `adapters/azure_ad_adapter.py` | Authentication |
| Teams/Web | `adapters/teams_adapter.py` | Client communication |
| Frontend | `adapters/frontend_adapter.py` | Web interface |

## 🚀 Lộ trình di chuyển (Migration Roadmap)

### Phase 1: Chuẩn bị (2 tuần)
**Mục tiêu:** Thiết lập cấu trúc mới song song với cấu trúc cũ

#### Tuần 1: Setup cấu trúc
- [ ] Tạo cấu trúc thư mục iris-backend-v2
- [ ] Setup domain layer với entities cơ bản
- [ ] Định nghĩa interfaces cho repositories
- [ ] Setup testing framework

#### Tuần 2: Core domains
- [ ] Implement User domain (auth, roles)
- [ ] Implement Document domain (upload, search)
- [ ] Implement Chat domain (query processing)
- [ ] Unit tests cho domain layer

### Phase 2: Di chuyển Business Logic (3 tuần)

#### Tuần 3-4: Domain Implementation
- [ ] Migrate authentication logic → `domain/user/`
- [ ] Migrate document processing → `domain/document/`
- [ ] Migrate chat logic → `domain/chat/`
- [ ] Migrate embedding logic → `domain/embedding/`

#### Tuần 5: Service Layer
- [ ] Implement orchestration services
- [ ] Connect domain với external services
- [ ] Implement caching strategies
- [ ] Integration tests

### Phase 3: Infrastructure & Adapters (2 tuần)

#### Tuần 6: Infrastructure
- [ ] Setup PostgreSQL repositories
- [ ] Implement vector database layer
- [ ] Setup Redis caching
- [ ] Message queue implementation

#### Tuần 7: Adapters
- [ ] OpenAI/Azure OpenAI adapter
- [ ] Teams/Telegram adapters
- [ ] Frontend adapter
- [ ] External API adapters

### Phase 4: API Migration (2 tuần)

#### Tuần 8: API Routes
- [ ] Migrate existing routes sang cấu trúc mới
- [ ] Implement dependency injection
- [ ] Setup middleware và security
- [ ] API documentation (OpenAPI)

#### Tuần 9: Testing & Validation
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Security audit
- [ ] Load testing

### Phase 5: Deployment & Cutover (1 tuần)

#### Tuần 10: Production Ready
- [ ] Docker configuration mới
- [ ] CI/CD pipeline update
- [ ] Monitoring & logging setup
- [ ] Rollback plan
- [ ] Production deployment

## 📝 Chi tiết Implementation

### 1. Domain Layer Example

```python
# domain/document/entities.py
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Document:
    id: str
    title: str
    content: str
    chunks: List['Chunk']
    metadata: dict
    created_at: datetime
    updated_at: datetime
    version: int

@dataclass
class Chunk:
    id: str
    document_id: str
    content: str
    embedding: Optional[List[float]]
    position: int
```

```python
# domain/document/use_cases.py
class UploadDocumentUseCase:
    def __init__(self, repo: DocumentRepository, 
                 chunking_service: ChunkingService):
        self.repo = repo
        self.chunking_service = chunking_service
    
    async def execute(self, file_content: bytes, 
                     metadata: dict) -> Document:
        # Pure business logic
        chunks = await self.chunking_service.chunk(file_content)
        document = Document(...)
        return await self.repo.save(document)
```

### 2. Service Layer Example

```python
# services/document_service.py
class DocumentService:
    def __init__(self, 
                 upload_use_case: UploadDocumentUseCase,
                 embedding_service: EmbeddingService,
                 cache_service: CacheService):
        self.upload_use_case = upload_use_case
        self.embedding_service = embedding_service
        self.cache_service = cache_service
    
    async def process_document(self, file) -> dict:
        # Orchestration logic
        document = await self.upload_use_case.execute(file)
        embeddings = await self.embedding_service.generate(document)
        await self.cache_service.invalidate(f"doc_{document.id}")
        return document.to_dict()
```

### 3. Adapter Example

```python
# adapters/openai_adapter.py
class OpenAIAdapter:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    async def generate_completion(self, prompt: str, 
                                 model: str = "gpt-3.5-turbo") -> str:
        # Wrap external API
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

## 🔄 Migration Strategy

### Incremental Migration
1. **Strangler Fig Pattern**: Xây dựng hệ thống mới song song
2. **Feature Toggle**: Switch từng feature sang hệ thống mới
3. **Dual Write**: Ghi data vào cả 2 hệ thống trong transition
4. **Gradual Cutover**: Chuyển traffic từ từ

### Risk Mitigation
| Rủi ro | Biện pháp |
|--------|-----------|
| Data inconsistency | Dual write + validation |
| Performance degradation | Benchmark & monitoring |
| Breaking changes | API versioning |
| Rollback complexity | Feature flags |

## 📊 Success Metrics

### Technical Metrics
- [ ] Test coverage > 80%
- [ ] Response time < 200ms (p95)
- [ ] Zero downtime migration
- [ ] Code complexity reduction 40%

### Business Metrics
- [ ] Development velocity +30%
- [ ] Bug rate -50%
- [ ] Time to market new features -40%
- [ ] Maintenance cost -35%

## 🛠️ Tools & Technologies

### Development
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Linting**: ruff, mypy, black
- **Documentation**: mkdocs, swagger
- **CI/CD**: GitHub Actions, Docker

### Monitoring
- **APM**: Azure Application Insights
- **Logging**: structlog + Azure Log Analytics
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry

## 📚 Training & Documentation

### Team Training
1. **Week 1**: DDD concepts & principles
2. **Week 2**: Clean Architecture patterns
3. **Week 3**: New codebase walkthrough
4. **Week 4**: Testing strategies

### Documentation
- [ ] Architecture Decision Records (ADRs)
- [ ] API documentation
- [ ] Domain model documentation
- [ ] Deployment guides
- [ ] Troubleshooting guides

## ✅ Checklist Pre-Migration

### Technical Readiness
- [ ] All tests passing in current system
- [ ] Database backup strategy
- [ ] Rollback procedures documented
- [ ] Performance baselines established

### Team Readiness
- [ ] Team trained on new architecture
- [ ] Code review guidelines updated
- [ ] Support procedures defined
- [ ] Communication plan established

## 🎯 Expected Outcomes

### Short-term (3 months)
- Clean separation of concerns
- Improved testability
- Better code organization
- Reduced technical debt

### Long-term (6-12 months)
- Microservices ready architecture
- Multi-client support (Teams, Web, Mobile)
- Improved scalability
- Faster feature development
- Lower maintenance cost

## 📞 Support & Resources

### Internal Resources
- Architecture team consultation
- DevOps support for CI/CD
- QA team for testing

### External Resources
- DDD community forums
- Clean Architecture documentation
- Azure architecture guidance

## 🔄 Review & Iteration

### Checkpoints
- **Week 2**: Architecture review
- **Week 5**: Domain implementation review
- **Week 8**: API design review
- **Week 10**: Go-live readiness review

### Success Criteria
✅ All domains implemented with > 80% test coverage
✅ Zero breaking changes for existing APIs
✅ Performance metrics maintained or improved
✅ Team confidence in new architecture
✅ Documentation complete and reviewed

---

## 📝 Notes

- Ưu tiên migration các core features trước (auth, document, chat)
- Giữ backward compatibility trong suốt quá trình migration
- Regular sync meetings với stakeholders
- Continuous monitoring và feedback collection

**Last Updated:** [Current Date]
**Author:** IRIS Development Team
**Status:** PLANNING