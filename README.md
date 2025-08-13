# IRIS Backend v2 - Clean Architecture Implementation

## 🚀 Overview
IRIS Backend v2 là phiên bản nâng cấp toàn diện của hệ thống IRIS, được xây dựng theo kiến trúc Domain-Driven Design (DDD) và Clean Architecture.

## 🎯 Mục tiêu

| Mục tiêu                             | Đáp ứng bởi                                  |
| ------------------------------------ | -------------------------------------------- |
| Dễ mở rộng từng module               | `domain-centric structure`                   |
| Không phụ thuộc framework            | `isolated domain layer`                      |
| Dễ tách từng phần thành microservice | `adapter/infrastructure boundaries`          |
| Phân quyền, theo dõi, tương tác      | `dedicated services` + `event/message queue` |
| Hỗ trợ nhiều client (Teams, Web...)  | `interface adapter layer`                    |
| Reuse logic giữa các API             | `service layer`                              |

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 15+ (với pgvector extension)
- Redis 7+

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd iris-backend-v2
```

2. **Setup environment**
```bash
cp .env.example .env
# Edit .env với configuration của bạn
```

3. **Install dependencies**
```bash
# Using pip
pip install -r requirements.txt

# Using poetry
poetry install
```

4. **Run with Docker**
```bash
# Development mode
docker-compose up

# With monitoring tools
docker-compose --profile tools up
```

5. **Access services**
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- pgAdmin: http://localhost:5050 (if tools profile enabled)
- RedisInsight: http://localhost:8001 (if tools profile enabled)

## 🏗️ Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────┐
│            Presentation Layer               │
│         (FastAPI Routes & DTOs)             │
├─────────────────────────────────────────────┤
│            Application Layer                │
│          (Use Cases & Services)             │
├─────────────────────────────────────────────┤
│             Domain Layer                    │
│      (Entities & Business Logic)            │
├─────────────────────────────────────────────┤
│          Infrastructure Layer               │
│    (Database, External APIs, Cache)         │
└─────────────────────────────────────────────┘
```

### Project Structure

```
iris-backend-v2/
├── app/
│   ├── api/                 # Presentation layer
│   │   └── v1/              # API version 1
│   │       ├── routers/     # API endpoints
│   │       └── dependencies.py
│   ├── domain/              # Business logic
│   │   ├── user/           # User domain
│   │   ├── document/       # Document domain
│   │   ├── chat/           # Chat domain
│   │   └── embedding/      # Embedding domain
│   ├── services/            # Application services
│   ├── adapters/            # External adapters
│   ├── infrastructure/      # Data persistence
│   │   ├── db/             # Database
│   │   ├── cache/          # Redis cache
│   │   └── vectordb/       # Vector database
│   └── core/                # Shared utilities
│       ├── config.py        # Configuration
│       ├── security.py      # Security utils
│       └── logger.py        # Logging setup
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── docker-compose.yml       # Docker setup
└── requirements.txt         # Dependencies
└── pyproject.toml         # Dependencies
```

## Sơ đồ Clean Architecture cho IRIS
```
                         [ UI / API Layer ]
                  ┌───────────────────────────┐
                  │  api/                      │
                  │  - routes (FastAPI)        │
                  │  - controllers             │
                  │  - request/response DTOs   │
                  └─────────────┬─────────────┘
                                │ gọi Application Layer
────────────────────────────────┼────────────────────────────────
                         [ Application Layer ]
                  ┌───────────────────────────┐
                  │  services/                 │
                  │  - orchestrate use cases   │
                  │  - dependency injection    │
                  │  - transaction handling    │
                  │                             │
                  │  Use Cases:                 │
                  │   - UploadDocumentUseCase   │
                  │   - ProcessChatUseCase      │
                  │   - GenerateEmbeddingUseCase│
                  └─────────────┬─────────────┘
                                │ gọi Domain Layer (business rules)
────────────────────────────────┼────────────────────────────────
                         [ Domain Layer ]
                  ┌───────────────────────────┐
                  │  domain/                   │
                  │  - entities (User, Document, Chat, Embedding...)│
                  │  - value objects           │
                  │  - domain events           │
                  │  - business rules          │
                  │  - repository interfaces   │
                  └─────────────┬─────────────┘
                                │ gọi Infrastructure Layer qua interface
────────────────────────────────┼────────────────────────────────
                         [ Infrastructure Layer ]
                  ┌───────────────────────────┐
                  │  infrastructure/           │
                  │  - database (Postgres repo) │
                  │  - vector DB (Pinecone/Weaviate)|
                  │  - cache (Redis)           │
                  │  - external API adapters   │
                  │    • OpenAIAdapter         │
                  │    • AzureADAdapter        │
                  │    • TeamsAdapter          │
                  │  - message queue           │
                  └───────────────────────────┘

```

## Rules 
```
1. Quy tắc phụ thuộc (Dependency Rule)
Hướng phụ thuộc luôn từ ngoài vào trong:

java
Sao chép
Chỉnh sửa
UI/API  →  Application Layer  →  Domain Layer
                              ↑
                       Infrastructure Layer (implement interfaces)
Domain không phụ thuộc vào Application, Infrastructure, hay UI.

Application không phụ thuộc vào UI, không dùng code hạ tầng trực tiếp.

Infrastructure có thể phụ thuộc vào Application/Domain để implement interface.

2. Domain thuần nghiệp vụ
Domain Layer chỉ chứa:

Entities và Value Objects (có behavior, không chỉ dữ liệu).

Domain Services (nếu logic không thuộc entity nào).

Repository interfaces.

Domain Events.

Không chứa:

SQL, HTTP call, cache code.

Code framework (FastAPI, SQLAlchemy…).

Logging, config.

3. Application Layer chỉ orchestration
Application Layer = Use Case Orchestration:

Nhận input từ UI/API.

Gọi domain xử lý.

Gọi repository interface / external service adapter.

Trả output cho UI/API.

Không viết business rules ở đây (business rules nằm ở domain).

Không phụ thuộc vào implementation cụ thể (DB, API…).

4. Infrastructure Layer là nơi “nối dây”
Chứa implementation cụ thể:

Repository implement interface của domain.

Adapter kết nối external API, queue, cache…

Mapping data giữa domain object ↔ DB/DTO.

Không viết business rules.

Nếu đổi công nghệ (Postgres → Mongo), chỉ cần đổi ở đây.

5. UI/API Layer chỉ nhận request và trả response
Không viết logic nghiệp vụ ở controller/route.

Chuyển request thành DTO/input cho use case.

Gọi use case từ Application Layer.

Trả response từ output của use case.

6. Đặt tên theo Ubiquitous Language
Class, method, biến đặt tên đúng với thuật ngữ nghiệp vụ.

Tên trong code = tên bạn dùng khi nói chuyện với domain expert.

Ví dụ: Document, Chunk, UploadDocumentUseCase, ProcessChatQueryUseCase — không dùng process_data() chung chung.

7. Bounded Context rõ ràng
Mỗi domain module (vd: document, chat, user) là một bounded context riêng.

Không để entity từ module này bị dùng thẳng ở module khác → nếu cần thì mapping/adapter.

8. Test ở đúng layer
Domain: Unit test business rules (không cần DB).

Application: Test flow use case với mock repo/adapters.

Infrastructure: Integration test (DB, API thật).

UI/API: End-to-end test.

9. Cấm logic ngược dòng
Controller gọi thẳng repository → ❌.

Application gọi thẳng DB query → ❌.

Domain gọi thẳng HTTP API → ❌.

10. Chuẩn bị cho microservices
Giữ các bounded context ít phụ thuộc vào nhau.

Giao tiếp qua interface/event, không qua DB chung.

Nếu sau này tách, mỗi bounded context thành service riêng dễ dàng.
```

## 🔑 Key Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Email verification
- Password reset flow
- Rate limiting

### Document Management
- Upload and process various document formats (PDF, DOCX, TXT, MD)
- Intelligent chunking strategies
- Vector embeddings for semantic search
- Version control

### AI-Powered Chat
- RAG (Retrieval-Augmented Generation)
- Multi-turn conversations
- Context-aware responses
- Source attribution

### Search & Analytics
- Semantic search using vector embeddings
- Full-text search
- Analytics dashboard
- Usage metrics

## 🛠️ Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL + pgvector
- **Cache**: Redis
- **AI/ML**: OpenAI, Sentence Transformers
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic
- **ORM**: SQLAlchemy
- **Testing**: pytest
- **Logging**: structlog
- **Monitoring**: Prometheus

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | User login |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |
| POST | `/api/v1/auth/logout` | Logout user |

### Document Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/upload` | Upload document |
| GET | `/api/v1/documents` | List documents |
| GET | `/api/v1/documents/{id}` | Get document |
| DELETE | `/api/v1/documents/{id}` | Delete document |
| POST | `/api/v1/documents/search` | Search documents |

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/query` | Send chat query |
| GET | `/api/v1/chat/history` | Get chat history |
| DELETE | `/api/v1/chat/history` | Clear history |

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/domain/user/test_entities.py

# Run with verbose output
pytest -v
```

## 🚀 Deployment

### Production with Docker

```bash
# Build production image
docker build -t iris-backend:latest .

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables

Key environment variables (see `.env.example` for full list):

```env
# Application
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-api-key
```

## 📈 Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Metrics (Prometheus format)
```bash
curl http://localhost:8000/metrics
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- IRIS Development Team

## 📞 Support

For support, email support@iris.ai or create an issue in the repository.

---

**Version**: 2.0.0-alpha
**Status**: Active Development
**Last Updated**: 2025-08-07