# 🏠 HƯỚNG DẪN SETUP PROJECT Ở LOCAL

## 📥 Download Project

### Option 1: Download Archive
Project đã được nén thành file `iris-backend-v2.tar.gz` trong `/workspace/`

### Option 2: Clone từ Git (nếu đã push lên repository)
```bash
git clone <your-repository-url>
cd iris-backend-v2
```

## 🚀 Setup Local Development

### 1. System Requirements
- **Python 3.10+**
- **Docker Desktop** (Windows/Mac) hoặc Docker Engine (Linux)
- **Docker Compose**
- **Git**
- **Code Editor** (VSCode recommended)

### 2. Extract và Setup Project

#### Windows (PowerShell):
```powershell
# Extract archive
tar -xzf iris-backend-v2.tar.gz
cd iris-backend-v2

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

#### macOS/Linux:
```bash
# Extract archive
tar -xzf iris-backend-v2.tar.gz
cd iris-backend-v2

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file với text editor
# Thay đổi các giá trị sau:
# - SECRET_KEY=<generate-new-secret-key>
# - OPENAI_API_KEY=<your-openai-key>
# - Database credentials nếu cần
```

### 4. Run với Docker

#### Start all services:
```bash
# Build và run containers
docker-compose up --build

# Hoặc run in background
docker-compose up -d
```

#### Stop services:
```bash
docker-compose down

# Stop và xóa volumes (reset database)
docker-compose down -v
```

### 5. Run without Docker (Development)

#### Setup Database:
```bash
# Install PostgreSQL locally
# Create database
createdb iris_v2

# Install pgvector extension
psql -d iris_v2 -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### Setup Redis:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows
# Download từ: https://github.com/microsoftarchive/redis/releases
```

#### Run application:
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
.\venv\Scripts\Activate  # Windows

# Run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔗 Access Points

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **pgAdmin**: http://localhost:5050
  - Email: `admin@iris.ai`
  - Password: `admin`
- **RedisInsight**: http://localhost:8001

## 📁 Project Structure
```
iris-backend-v2/
├── app/                    # Application code
│   ├── domain/            # Business logic
│   ├── services/          # Application services
│   ├── api/               # API endpoints
│   └── infrastructure/    # Database, cache
├── tests/                 # Test files
├── docker-compose.yml     # Docker configuration
├── Dockerfile            # Container image
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
└── README.md           # Documentation
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## 🐛 Troubleshooting

### Port already in use
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in docker-compose.yml
```

### Docker issues
```bash
# Reset Docker
docker system prune -a
docker volume prune

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Database connection error
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -p 5432 -U postgres -d iris_v2
```

### Permission errors (Linux/Mac)
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod -R 755 .
```

## 💻 VSCode Setup (Recommended)

### Extensions to install:
- Python
- Pylance
- Docker
- PostgreSQL
- Thunder Client (API testing)
- GitLens

### .vscode/settings.json:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "[python]": {
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

### .vscode/launch.json:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## 🆘 Need Help?

1. Check logs:
```bash
docker-compose logs app
docker-compose logs postgres
docker-compose logs redis
```

2. Enable debug mode:
```bash
# In .env file
DEBUG=true
LOG_LEVEL=DEBUG
```

3. Contact support or create issue on GitHub

---

**Happy Coding! 🚀**