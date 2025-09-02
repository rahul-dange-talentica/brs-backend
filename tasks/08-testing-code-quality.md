# Task 08: Testing & Code Quality

**Phase**: 3 - Quality & Deployment  
**Sequence**: 08  
**Priority**: High  
**Estimated Effort**: 10-12 hours  
**Dependencies**: All previous tasks (01-07)

---

## Objective

Implement comprehensive testing suite, code quality measures, and continuous integration setup to ensure 80%+ code coverage, maintainable code, and reliable application functionality.

## Scope

- Unit tests for all models, utilities, and business logic
- Integration tests for API endpoints and database operations
- Authentication and authorization testing
- Performance and load testing setup
- Code quality tools configuration and enforcement
- Test database setup and fixtures
- Mocking external dependencies
- Test documentation and reporting

## Technical Requirements

### Testing Strategy (from Technical PRD)
- **Unit Tests**: Test individual functions and methods (60% of coverage)
- **Integration Tests**: Test API endpoints and database operations (30% of coverage)  
- **Test Database**: Separate test database with fixtures
- **Mocking**: Mock external services and complex dependencies
- **Coverage Target**: Minimum 80% code coverage

### Code Quality Standards
- **Black**: Code formatting with consistent style
- **Flake8**: Linting for code quality and PEP8 compliance
- **Mypy**: Type checking for better code reliability
- **Pre-commit hooks**: Automated quality checks

## Acceptance Criteria

### ✅ Unit Testing
- [ ] Models testing (User, Book, Genre, Review, UserFavorite)
- [ ] Core utilities testing (auth, security, recommendations)
- [ ] Schema validation testing
- [ ] Business logic testing (rating calculations, user preferences)
- [ ] Edge cases and error conditions testing

### ✅ Integration Testing
- [ ] Authentication endpoints (register, login, token validation)
- [ ] User management API (profile, favorites, reviews)
- [ ] Book management API (listing, search, details)
- [ ] Review system API (CRUD operations, rating aggregation)
- [ ] Recommendation engine API (all recommendation types)

### ✅ Database Testing
- [ ] Database models and relationships
- [ ] Migration testing (up and down)
- [ ] Constraint validation (unique, check, foreign key)
- [ ] Database performance with large datasets
- [ ] Concurrent operations handling

### ✅ Authentication & Authorization Testing
- [ ] JWT token generation and validation
- [ ] Password security (hashing, verification)
- [ ] Protected endpoints access control
- [ ] User ownership validation
- [ ] Security vulnerability testing

### ✅ Code Coverage & Quality
- [ ] 80%+ code coverage across all modules
- [ ] Code quality metrics (complexity, maintainability)
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks established
- [ ] Documentation coverage

## Implementation Details

### Test Configuration (tests/conftest.py)
```python
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.book import Book
from app.models.genre import Genre
from app.core.security import hash_password

# Test database setup
SQLALCHEMY_DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/brs_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db_session):
    """Create async test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_book(db_session):
    """Create test book"""
    book = Book(
        title="Test Book",
        author="Test Author",
        isbn="1234567890123",
        description="A test book for testing",
        average_rating=4.5,
        total_reviews=10
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user"""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
```

### Model Unit Tests (tests/test_models/test_user.py)
```python
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import hash_password, verify_password

class TestUserModel:
    def test_create_user(self, db_session):
        """Test user creation with valid data"""
        user = User(
            email="newuser@example.com",
            password_hash=hash_password("password123"),
            first_name="New",
            last_name="User"
        )
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_email_unique_constraint(self, db_session, test_user):
        """Test email uniqueness constraint"""
        duplicate_user = User(
            email=test_user.email,
            password_hash=hash_password("password123"),
            first_name="Duplicate",
            last_name="User"
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "securepassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_user_relationships(self, db_session, test_user, test_book):
        """Test user model relationships"""
        # Test reviews relationship
        from app.models.review import Review
        review = Review(user_id=test_user.id, book_id=test_book.id, rating=5)
        db_session.add(review)
        db_session.commit()
        
        db_session.refresh(test_user)
        assert len(test_user.reviews) == 1
        assert test_user.reviews[0].rating == 5
```

### API Integration Tests (tests/test_api/test_auth.py)
```python
import pytest
from fastapi import status

class TestAuthAPI:
    def test_user_registration_success(self, client):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "first_name": "New",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_registration_duplicate_email(self, client, test_user):
        """Test registration with existing email"""
        user_data = {
            "email": test_user.email,
            "password": "SecurePass123",
            "first_name": "Duplicate",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    def test_user_login_success(self, client, test_user):
        """Test successful user login"""
        login_data = {
            "username": test_user.email,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/api/v1/users/profile")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_valid_token(self, client, auth_headers):
        """Test accessing protected endpoint with valid token"""
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
```

### Performance Tests (tests/test_performance/test_api_performance.py)
```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor

class TestAPIPerformance:
    def test_book_listing_performance(self, client):
        """Test book listing API performance"""
        start_time = time.time()
        response = client.get("/api/v1/books?limit=100")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # Should respond within 500ms

    def test_search_performance(self, client):
        """Test book search performance"""
        start_time = time.time()
        response = client.get("/api/v1/books/search?q=test&limit=50")
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_concurrent_requests(self, client):
        """Test handling concurrent requests"""
        def make_request():
            return client.get("/api/v1/books?limit=10")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in responses)
```

### Code Quality Configuration

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    slow: Slow tests
```

#### .flake8
```ini
[flake8]
max-line-length = 100
exclude = 
    .git,
    __pycache__,
    .venv,
    migrations,
    .pytest_cache
ignore = 
    E203,  # whitespace before ':'
    W503,  # line break before binary operator
per-file-ignores =
    __init__.py:F401
```

#### pyproject.toml (testing section)
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[tool.coverage.run]
source = ["app"]
omit = [
    "app/main.py",
    "*/tests/*",
    "*/__init__.py"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]
```

## Testing Commands

### Run All Tests
```bash
# Run all tests with coverage
poetry run pytest

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m performance

# Run tests with detailed output
poetry run pytest -v --tb=short

# Run tests and generate HTML coverage report
poetry run pytest --cov-report=html
```

### Code Quality Checks
```bash
# Format code
poetry run black app/ tests/

# Check linting
poetry run flake8 app/ tests/

# Type checking
poetry run mypy app/

# Run all quality checks
poetry run pre-commit run --all-files
```

## Definition of Done

- [ ] 80%+ code coverage achieved across all modules
- [ ] All unit tests passing for models and utilities
- [ ] All integration tests passing for API endpoints
- [ ] Authentication and authorization thoroughly tested
- [ ] Performance tests meeting response time requirements
- [ ] Code quality tools configured and enforcing standards
- [ ] Test database setup and fixtures working
- [ ] Pre-commit hooks preventing quality issues
- [ ] Test documentation and examples complete
- [ ] CI/CD pipeline ready for automated testing

## Next Steps

After completion, this task enables:
- **Task 09**: API Documentation & Validation
- **Task 10**: Deployment & Production Setup
- Reliable, maintainable production-ready code

## Notes

- Run tests frequently during development
- Monitor test performance and optimize slow tests
- Consider property-based testing for complex algorithms
- Document test scenarios and edge cases
- Set up test data seeding for manual testing
