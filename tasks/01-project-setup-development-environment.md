# Task 01: Project Setup & Development Environment

**Phase**: 1 - Foundation & Core Setup  
**Sequence**: 01  
**Priority**: Critical  
**Estimated Effort**: 6-8 hours  
**Dependencies**: None

---

## Objective

Set up the complete development environment with all necessary tools, dependencies, project structure, and basic FastAPI application for the BRS Backend.

## Scope

- Python development environment with Poetry
- FastAPI project structure and basic application
- PostgreSQL development database with Docker
- Code quality tools and pre-commit hooks
- Basic configuration management
- Development documentation

## Technical Requirements

### Development Stack
- **Python**: 3.11+ with Poetry for dependency management
- **Framework**: FastAPI with automatic OpenAPI documentation
- **Database**: PostgreSQL 15+ with Docker Compose
- **Code Quality**: black, flake8, mypy, pre-commit hooks
- **Testing**: pytest, pytest-asyncio, httpx

### Project Structure
```
brs-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection setup
│   ├── models/              # SQLAlchemy models (empty for now)
│   ├── schemas/             # Pydantic schemas (empty for now)
│   ├── api/                 # API routes (empty for now)
│   ├── core/                # Core utilities (empty for now)
│   └── utils/               # Helper functions (empty for now)
├── tests/                   # Test files
├── alembic/                 # Database migrations (setup only)
├── docker-compose.yml       # Local development services
├── Dockerfile              # Application containerization
├── pyproject.toml           # Poetry configuration
├── .env.example             # Environment variables template
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml  # Pre-commit hooks
└── README.md               # Project documentation
```

## Acceptance Criteria

### ✅ Environment Setup
- [ ] Python 3.11+ installed and working
- [ ] Poetry installed and configured
- [ ] PostgreSQL Docker container running locally (port 5432)
- [ ] All development dependencies installed via Poetry

### ✅ FastAPI Application
- [ ] Basic FastAPI app with health check endpoint
- [ ] Configuration management with environment variables
- [ ] Database connection setup (without models yet)
- [ ] CORS middleware configured
- [ ] Application starts successfully with uvicorn

### ✅ Development Tools
- [ ] Poetry `pyproject.toml` with all required dependencies
- [ ] Docker Compose for PostgreSQL development database
- [ ] Pre-commit hooks configured and working
- [ ] Code formatting (black), linting (flake8), type checking (mypy)

### ✅ Project Structure
- [ ] Complete directory structure as specified
- [ ] All `__init__.py` files created for proper packaging
- [ ] Basic configuration files in place
- [ ] Git repository initialized with proper .gitignore

### ✅ Documentation
- [ ] README with comprehensive setup instructions
- [ ] Environment variables documented
- [ ] Development workflow documented

## Implementation Details

### Key Dependencies
```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
sqlalchemy = "^2.0.0"
alembic = "^1.12.0"
psycopg2-binary = "^2.9.0"
pydantic = "^2.5.0"
python-jose = "^3.3.0"
bcrypt = "^4.1.0"
python-multipart = "^0.0.6"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.1.0"
httpx = "^0.25.0"
black = "^23.0.0"
flake8 = "^6.1.0"
mypy = "^1.7.0"
pre-commit = "^3.5.0"
```

### Basic FastAPI App (app/main.py)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Book Review System API",
    description="Backend API for Book Review Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "BRS Backend is running"}

@app.get("/")
async def root():
    return {"message": "Welcome to Book Review System API"}
```

### Configuration Management (app/config.py)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://brs_user:brs_password@localhost:5432/brs_dev"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Docker Compose (docker-compose.yml)
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: brs_dev
      POSTGRES_USER: brs_user
      POSTGRES_PASSWORD: brs_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U brs_user -d brs_dev"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Testing

### Manual Testing Steps
1. **Environment Verification**
   ```bash
   python --version  # Should be 3.11+
   poetry --version
   docker --version
   ```

2. **Application Startup**
   ```bash
   poetry run uvicorn app.main:app --reload
   # Should start without errors on http://127.0.0.1:8000
   ```

3. **API Endpoints**
   - Visit http://127.0.0.1:8000/health (should return healthy status)
   - Visit http://127.0.0.1:8000/docs (should show Swagger UI)

4. **Database Connection**
   ```bash
   docker-compose up -d
   # PostgreSQL should be accessible on localhost:5432
   ```

5. **Code Quality Tools**
   ```bash
   poetry run black --check .
   poetry run flake8 .
   poetry run mypy app/
   pre-commit run --all-files
   ```

## Definition of Done

- [ ] All acceptance criteria verified and tested
- [ ] FastAPI application starts successfully
- [ ] PostgreSQL database accessible via Docker
- [ ] All code quality tools configured and passing
- [ ] Pre-commit hooks working correctly
- [ ] Documentation complete and accurate
- [ ] Basic health check endpoint functional
- [ ] Project ready for next development phase

## Next Steps

After completion, this task enables:
- **Task 02**: Database Models & Migrations (database connection ready)
- **Task 03**: Authentication & Security System (FastAPI app ready)
- Development of all subsequent features

## Notes

- This task establishes the foundation for the entire project
- Ensure all environment variables are properly documented
- Test the complete setup before proceeding
- Any deviations from planned structure should be documented
