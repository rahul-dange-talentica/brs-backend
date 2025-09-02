# Book Review System (BRS) Backend

A modern REST API backend for a book review platform built with FastAPI, PostgreSQL, and SQLAlchemy.

## 🚀 Features

- **FastAPI Framework**: High-performance async web framework with automatic OpenAPI documentation
- **PostgreSQL Database**: Robust relational database with full-text search capabilities  
- **JWT Authentication**: Secure user authentication and authorization
- **SQLAlchemy ORM**: Modern Python SQL toolkit and Object-Relational Mapping
- **Alembic Migrations**: Database schema version control
- **Docker Support**: Containerized development and deployment
- **Code Quality**: Pre-commit hooks, linting, formatting, and type checking
- **Comprehensive Testing**: Unit and integration tests with pytest

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- Docker and Docker Compose (for database)
- Git

## 🛠️ Development Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd brs-backend
```

### 2. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# DATABASE_URL=postgresql://brs_user:brs_password@localhost:5432/brs_dev
# SECRET_KEY=your-super-secret-key-change-in-production
```

### 4. Start Database Services

```bash
# Start PostgreSQL and Redis with Docker Compose
docker-compose up -d

# Verify database is running
docker-compose ps
```

### 5. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks on all files (optional)
poetry run pre-commit run --all-files
```

### 6. Run the Application

```bash
# Start the development server
poetry run uvicorn app.main:app --reload

# The API will be available at:
# - Application: http://127.0.0.1:8000
# - Interactive API docs: http://127.0.0.1:8000/docs
# - Alternative docs: http://127.0.0.1:8000/redoc
```

## 🔧 Development Commands

### Database Operations

```bash
# Initialize Alembic (first time only)
poetry run alembic init alembic

# Create a new migration
poetry run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
poetry run alembic upgrade head

# Downgrade migrations  
poetry run alembic downgrade -1
```

### Code Quality

```bash
# Format code with Black
poetry run black .

# Lint code with Flake8
poetry run flake8 .

# Type checking with MyPy
poetry run mypy app/

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_main.py

# Run tests in watch mode
poetry run pytest --watch
```

## 🐳 Docker Development

### Build and Run with Docker

```bash
# Build the application image
docker build -t brs-backend .

# Run the application container
docker run -p 8000:8000 --env-file .env brs-backend

# Or use docker-compose for full stack
docker-compose up --build
```

## 📁 Project Structure

```
brs-backend/
├── app/                     # Application source code
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Configuration management
│   ├── database.py         # Database connection setup
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas  
│   ├── api/                # API route handlers
│   ├── core/               # Core utilities
│   └── utils/              # Helper functions
├── tests/                  # Test files
├── alembic/                # Database migrations
├── docker-compose.yml      # Local development services
├── Dockerfile             # Application containerization
├── pyproject.toml         # Poetry configuration
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks
└── README.md             # Project documentation
```

## 🔑 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://brs_user:brs_password@localhost:5432/brs_dev` |
| `SECRET_KEY` | JWT secret key | Required for production |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `30` |
| `APP_NAME` | Application name | `Book Review System API` |
| `DEBUG` | Enable debug mode | `false` |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## 📖 API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc  
- **OpenAPI JSON**: http://127.0.0.1:8000/openapi.json

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

Response:
```json
{
  "status": "healthy",
  "message": "BRS Backend is running",
  "version": "1.0.0"
}
```

## 🧪 Testing Strategy

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and database interactions
- **Performance Tests**: Ensure API response times meet requirements
- **Security Tests**: Validate authentication and authorization

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- Security headers middleware

## 🚀 Deployment

### Production Environment Variables

```bash
# Essential production settings
SECRET_KEY=your-super-secure-secret-key
DEBUG=false
DATABASE_URL=postgresql://user:password@db-host:5432/database
BACKEND_CORS_ORIGINS=https://yourdomain.com
```

### Docker Production Build

```bash
# Build production image
docker build -t brs-backend:production .

# Run with production settings
docker run -p 8000:8000 --env-file .env.production brs-backend:production
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and commit: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages
- Ensure all pre-commit hooks pass

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions and support, please open an issue in the GitHub repository.

---

**Happy coding! 🎉**