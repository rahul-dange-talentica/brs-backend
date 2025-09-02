# Technical Product Requirement Document (Technical PRD)

## Book Review Platform (BRS) - Backend Service

**Owner**: Rahul Dange  
**Date**: January 2025  
**Version**: 1.0

---

## 1. Technical Overview

### 1.1 Architecture Approach
- **Pattern**: Microservice architecture with single backend service
- **API Style**: RESTful API with JSON responses
- **Authentication**: JWT token-based stateless authentication
- **Database**: Single PostgreSQL instance with normalized schema
- **Deployment**: Containerized deployment on AWS with Kubernetes

### 1.2 Technology Philosophy
- **Simplicity**: Keep architecture simple for single developer maintenance
- **Scalability**: Design for current needs (100 concurrent users) with growth potential
- **Reliability**: Focus on data consistency and service availability
- **Maintainability**: Clean code, comprehensive testing, clear documentation

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Load Balancer │    │   BRS Backend   │
│   (Separate)    │◄──►│   (AWS ALB)     │◄──►│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │   Database      │
                                              └─────────────────┘
```

### 2.2 Service Components

**BRS Backend Service Components:**
- **Authentication Module**: User registration, login, JWT management
- **User Management**: Profile management, preferences
- **Book Management**: Book catalog, search, filtering
- **Review Management**: CRUD operations for reviews and ratings
- **Recommendation Engine**: Basic recommendation logic
- **API Gateway**: Request routing, validation, response formatting

---

## 3. Technology Stack

### 3.1 Backend Framework
**Primary Choice: FastAPI**
- **Rationale**: 
  - High performance async framework
  - Automatic API documentation (OpenAPI/Swagger)
  - Built-in data validation with Pydantic
  - Excellent for REST API development
  - Strong typing support
- **Alternative**: Django REST Framework (if more rapid development needed)

### 3.2 Database & ORM
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy with Alembic for migrations
- **Connection Pool**: Built-in FastAPI database connection handling

### 3.3 Authentication & Security
- **JWT Library**: PyJWT or python-jose
- **Password Hashing**: bcrypt or argon2
- **CORS**: FastAPI built-in CORS middleware
- **Input Validation**: Pydantic models

### 3.4 Infrastructure & Deployment
- **Container**: Docker with multi-stage builds
- **Orchestration**: Amazon EKS (Elastic Kubernetes Service)
- **Load Balancer**: AWS Application Load Balancer (ALB)
- **Database Hosting**: Amazon RDS for PostgreSQL
- **Container Registry**: Amazon ECR

### 3.5 Development & Testing
- **Testing Framework**: pytest + pytest-asyncio
- **Code Coverage**: pytest-cov (target: 80%+)
- **Code Quality**: black (formatting), flake8 (linting), mypy (type checking)
- **API Testing**: httpx for async API testing
- **Database Testing**: pytest fixtures with test database

### 3.6 Development Tools
- **Dependency Management**: Poetry or pip-tools
- **Environment Management**: python-dotenv for configuration
- **API Documentation**: FastAPI automatic documentation
- **Database Migrations**: Alembic

---

## 4. Database Design

### 4.1 Core Entities

```sql
-- Users table
users (
    id: UUID PRIMARY KEY,
    email: VARCHAR(255) UNIQUE NOT NULL,
    password_hash: VARCHAR(255) NOT NULL,
    first_name: VARCHAR(100),
    last_name: VARCHAR(100),
    created_at: TIMESTAMP DEFAULT NOW(),
    updated_at: TIMESTAMP DEFAULT NOW(),
    is_active: BOOLEAN DEFAULT TRUE
)

-- Genres table
genres (
    id: UUID PRIMARY KEY,
    name: VARCHAR(100) UNIQUE NOT NULL,
    description: TEXT,
    created_at: TIMESTAMP DEFAULT NOW()
)

-- Books table
books (
    id: UUID PRIMARY KEY,
    title: VARCHAR(500) NOT NULL,
    author: VARCHAR(300) NOT NULL,
    isbn: VARCHAR(13) UNIQUE,
    description: TEXT,
    cover_image_url: VARCHAR(1000),
    publication_date: DATE,
    average_rating: DECIMAL(3,2) DEFAULT 0.00,
    total_reviews: INTEGER DEFAULT 0,
    created_at: TIMESTAMP DEFAULT NOW(),
    updated_at: TIMESTAMP DEFAULT NOW()
)

-- Book genres (many-to-many)
book_genres (
    book_id: UUID REFERENCES books(id) ON DELETE CASCADE,
    genre_id: UUID REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY(book_id, genre_id)
)

-- Reviews table
reviews (
    id: UUID PRIMARY KEY,
    user_id: UUID REFERENCES users(id) ON DELETE CASCADE,
    book_id: UUID REFERENCES books(id) ON DELETE CASCADE,
    rating: INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text: TEXT,
    created_at: TIMESTAMP DEFAULT NOW(),
    updated_at: TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, book_id)
)

-- User favorites table
user_favorites (
    id: UUID PRIMARY KEY,
    user_id: UUID REFERENCES users(id) ON DELETE CASCADE,
    book_id: UUID REFERENCES books(id) ON DELETE CASCADE,
    created_at: TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, book_id)
)
```

### 4.2 Indexes
```sql
-- Performance indexes
CREATE INDEX idx_books_average_rating ON books(average_rating DESC);
CREATE INDEX idx_book_genres_book ON book_genres(book_id);
CREATE INDEX idx_book_genres_genre ON book_genres(genre_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
```

---

## 5. API Design

### 5.1 API Structure
**Base URL**: `https://api.brs.example.com/v1`

### 5.2 Authentication Endpoints
```
POST /auth/register
POST /auth/login
POST /auth/refresh
DELETE /auth/logout
```

### 5.3 User Management
```
GET /users/profile
PUT /users/profile
GET /users/favorites
POST /users/favorites/{book_id}
DELETE /users/favorites/{book_id}
GET /users/reviews
```

### 5.4 Book Management
```
GET /books                    # List with pagination, filtering
GET /books/{book_id}         # Book details
GET /books/search            # Search books
GET /genres                  # List genres
```

### 5.5 Review Management
```
GET /books/{book_id}/reviews     # Book reviews with pagination
POST /books/{book_id}/reviews    # Create review
PUT /reviews/{review_id}         # Update own review
DELETE /reviews/{review_id}      # Delete own review
GET /reviews/{review_id}         # Review details
```

### 5.6 Recommendations
```
GET /recommendations/popular        # Top-rated books
GET /recommendations/genre/{id}     # Genre-based recommendations
GET /recommendations/personal       # User-based recommendations
```

### 5.7 Response Format
```json
{
    "success": true,
    "data": {...},
    "message": "Operation successful",
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "pages": 5
    }
}
```

---

## 6. Security Architecture

### 6.1 Authentication Flow
1. User registers/logs in with email/password
2. Server validates credentials and returns JWT access token
3. Client includes token in Authorization header for subsequent requests
4. Server validates JWT signature and expiration on each request

### 6.2 Security Measures
- **Password Security**: bcrypt hashing with salt rounds ≥ 12
- **JWT Security**: 
  - Short-lived access tokens (15 minutes)
  - Secure signing algorithm (RS256 or HS256)
  - Include user ID and permissions in payload
- **Input Validation**: Pydantic models for all request/response validation
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configured for frontend domain only

### 6.3 Data Protection
- **Sensitive Data**: Never log passwords or tokens
- **Database**: Use environment variables for database credentials
- **Secrets Management**: AWS Secrets Manager for production credentials

---

## 7. Development Strategy

### 7.1 Project Structure
```
brs-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection and session
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── genre.py
│   │   └── review.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── genre.py
│   │   └── review.py
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── books.py
│   │   ├── genres.py
│   │   └── reviews.py
│   ├── core/                # Core utilities
│   │   ├── __init__.py
│   │   ├── auth.py          # JWT handling
│   │   ├── security.py      # Password hashing
│   │   └── recommendations.py
│   └── utils/               # Helper functions
├── tests/                   # Test files
├── alembic/                 # Database migrations
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml           # Poetry configuration
└── README.md
```

### 7.2 Development Workflow
1. **Setup**: Use Poetry for dependency management
2. **Database**: Local PostgreSQL with Docker Compose
3. **Testing**: Write tests first (TDD approach)
4. **Code Quality**: Pre-commit hooks for black, flake8, mypy
5. **Documentation**: Maintain OpenAPI documentation through FastAPI

### 7.3 Testing Strategy
- **Unit Tests**: Test individual functions and methods (60% of coverage)
- **Integration Tests**: Test API endpoints and database operations (30% of coverage)
- **Test Database**: Separate test database with fixtures
- **Mocking**: Mock external services and complex dependencies
- **Coverage Target**: Minimum 80% code coverage

---

## 8. Deployment Architecture

### 8.1 AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS VPC                              │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │   Public Subnet │    │  Private Subnet │                │
│  │                 │    │                 │                │
│  │  ┌───────────┐  │    │  ┌───────────┐  │                │
│  │  │    ALB    │  │    │  │    EKS    │  │                │
│  │  │           │  │    │  │  Cluster  │  │                │
│  │  └───────────┘  │    │  └───────────┘  │                │
│  └─────────────────┘    └─────────────────┘                │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                 Private Subnet                          ││
│  │  ┌───────────┐              ┌───────────┐              ││
│  │  │    RDS    │              │    ECR    │              ││
│  │  │PostgreSQL │              │           │              ││
│  │  └───────────┘              └───────────┘              ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Kubernetes Configuration
- **Deployment**: Single pod deployment with resource limits
- **Service**: ClusterIP service for internal communication
- **Ingress**: ALB Ingress Controller for external access
- **ConfigMap**: Environment-specific configuration
- **Secrets**: Database credentials and JWT secrets

### 8.3 Deployment Process
1. **Build**: Docker image build with multi-stage build
2. **Push**: Push image to Amazon ECR
3. **Deploy**: Update Kubernetes deployment manually
4. **Verify**: Health check endpoints and smoke tests

---

## 9. Performance Considerations

### 9.1 Database Performance
- **Connection Pooling**: SQLAlchemy connection pool (5-20 connections)
- **Query Optimization**: Use database indexes for common queries
- **Pagination**: Implement cursor-based pagination for large datasets
- **N+1 Problem**: Use SQLAlchemy eager loading where appropriate

### 9.2 API Performance
- **Async Operations**: FastAPI async/await for I/O operations
- **Response Size**: Implement field selection for large objects
- **Rate Calculation**: Cache average ratings and update asynchronously
- **Database Queries**: Minimize database round trips

### 9.3 Monitoring & Health Checks
- **Health Endpoint**: `/health` for Kubernetes liveness probe
- **Metrics**: Basic application metrics (request count, response time)
- **Logging**: Structured logging with correlation IDs

---

## 10. Risk Assessment & Mitigation

### 10.1 Technical Risks
- **Single Point of Failure**: Database is single point of failure
  - *Mitigation*: Use RDS with automated backups and Multi-AZ deployment
- **Performance Degradation**: Rating calculations on large datasets
  - *Mitigation*: Implement background jobs for rating updates
- **Security Vulnerabilities**: JWT token management
  - *Mitigation*: Follow JWT best practices, short token expiration

### 10.2 Development Risks
- **Single Developer**: Knowledge concentration and development bottlenecks
  - *Mitigation*: Comprehensive documentation and clean code practices
- **Scope Creep**: Feature additions beyond initial scope
  - *Mitigation*: Stick to MVP features, maintain feature backlog

---

## 11. Success Criteria

### 11.1 Technical Metrics
- **Performance**: API response time < 500ms (95th percentile)
- **Availability**: 99% uptime during business hours
- **Code Quality**: 80%+ test coverage, zero critical security vulnerabilities
- **Scalability**: Support 100 concurrent users without degradation

### 11.2 Development Metrics
- **Delivery**: Complete MVP within 4 weeks
- **Documentation**: Complete API documentation available
- **Testing**: All core functionality covered by automated tests
- **Deployment**: Successful deployment to development environment

---

## 12. Next Steps

### 12.1 Immediate Actions (Week 1)
1. Set up development environment with Poetry and Docker Compose
2. Initialize FastAPI project structure
3. Set up PostgreSQL database with Alembic migrations
4. Implement user authentication endpoints
5. Set up testing framework and CI/CD pipeline

### 12.2 Implementation Phases
- **Phase 1** (Week 1-2): Authentication, user management, basic API structure
- **Phase 2** (Week 2-3): Book management, review CRUD, rating system
- **Phase 3** (Week 3-4): Recommendations, API optimization, deployment setup
- **Phase 4** (Week 4): Testing, documentation, production deployment

---

*This Technical PRD serves as the blueprint for implementing the Book Review Platform backend service. It should be reviewed and updated as development progresses and requirements evolve.*
