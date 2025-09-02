# Task 09: API Documentation & Validation

**Phase**: 3 - Quality & Deployment  
**Sequence**: 09  
**Priority**: Medium  
**Estimated Effort**: 6-8 hours  
**Dependencies**: All API tasks (03-07), Task 08 (Testing)

---

## Objective

Create comprehensive API documentation, enhance input validation, implement proper error handling, and ensure API consistency according to technical PRD specifications for production readiness.

## Scope

- Complete OpenAPI/Swagger documentation
- Enhanced input validation with detailed error messages
- Standardized error response format
- API versioning and deprecation handling
- Request/response examples and schemas
- API rate limiting and throttling
- Health checks and monitoring endpoints
- API usage documentation and guides

## Technical Requirements

### Documentation Standards
- **OpenAPI/Swagger**: Automatic documentation generation via FastAPI
- **Response Format**: Consistent JSON responses with metadata (from Technical PRD)
- **Error Handling**: Standardized error responses with appropriate HTTP codes
- **Validation**: Comprehensive input validation with informative messages

### API Response Format (from Technical PRD)
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

## Acceptance Criteria

### ✅ API Documentation
- [ ] Complete OpenAPI 3.0 specification generated
- [ ] All endpoints documented with descriptions and examples
- [ ] Request/response schemas fully defined
- [ ] Authentication requirements clearly specified
- [ ] Error responses documented with status codes

### ✅ Input Validation Enhancement
- [ ] Comprehensive Pydantic model validation
- [ ] Custom validators for business rules
- [ ] Detailed validation error messages
- [ ] Input sanitization for security
- [ ] File upload validation (if applicable)

### ✅ Standardized Response Format
- [ ] Consistent JSON response structure across all endpoints
- [ ] Standardized error response format
- [ ] Proper HTTP status codes for all scenarios
- [ ] Pagination metadata where applicable
- [ ] Success/error message consistency

### ✅ API Versioning & Health
- [ ] API versioning strategy implemented
- [ ] Health check endpoints functional
- [ ] API metrics and monitoring endpoints
- [ ] Deprecation warnings and migration guides
- [ ] API rate limiting configured

### ✅ Documentation Quality
- [ ] Interactive API documentation (Swagger UI)
- [ ] API usage examples and tutorials
- [ ] Authentication flow documentation
- [ ] Error handling guide
- [ ] Performance and rate limit documentation

## Implementation Details

### Enhanced Response Models (app/schemas/common.py)
```python
from pydantic import BaseModel
from typing import Optional, Any, Dict
from enum import Enum

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool

class APIResponse(BaseModel):
    status: ResponseStatus
    message: str
    data: Optional[Any] = None
    pagination: Optional[PaginationMeta] = None
    errors: Optional[Dict[str, Any]] = None

class ErrorDetail(BaseModel):
    field: str
    message: str
    code: str

class ErrorResponse(BaseModel):
    status: ResponseStatus = ResponseStatus.ERROR
    message: str
    errors: Optional[Dict[str, Any]] = None
    timestamp: str
    request_id: Optional[str] = None
```

### Enhanced Error Handling (app/core/exceptions.py)
```python
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback
import uuid
from datetime import datetime

from app.schemas.common import ErrorResponse

class BRSException(Exception):
    """Base exception for BRS application"""
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class BookNotFoundError(BRSException):
    def __init__(self, book_id: str):
        super().__init__(
            message=f"Book with ID '{book_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

class ReviewNotFoundError(BRSException):
    def __init__(self, review_id: str):
        super().__init__(
            message=f"Review with ID '{review_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )

class DuplicateReviewError(BRSException):
    def __init__(self):
        super().__init__(
            message="You have already reviewed this book",
            status_code=status.HTTP_400_BAD_REQUEST
        )

async def brs_exception_handler(request: Request, exc: BRSException):
    """Handle custom BRS exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.message,
            errors=exc.details,
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip 'body'
        errors[field] = {
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            message="Validation error",
            errors=errors,
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4())
        ).dict()
    )

async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=exc.detail,
            timestamp=datetime.utcnow().isoformat(),
            request_id=str(uuid.uuid4())
        ).dict()
    )
```

### Enhanced Validation Models (app/schemas/validation.py)
```python
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
import re
from datetime import date

class EnhancedUserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > 50:
            raise ValueError('Name cannot exceed 50 characters')
        if not re.match(r'^[a-zA-Z\s\-\']+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        return v.strip()

class EnhancedBookCreate(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    publication_date: Optional[date] = None
    genre_ids: List[str] = []
    
    @validator('title', 'author')
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('This field is required')
        if len(v) > 500:
            raise ValueError('Field cannot exceed 500 characters')
        return v.strip()
    
    @validator('isbn')
    def validate_isbn(cls, v):
        if v:
            # Remove hyphens and spaces
            isbn = re.sub(r'[-\s]', '', v)
            if not re.match(r'^\d{10}$|^\d{13}$', isbn):
                raise ValueError('ISBN must be 10 or 13 digits')
            return isbn
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v and len(v) > 2000:
            raise ValueError('Description cannot exceed 2000 characters')
        return v
    
    @validator('cover_image_url')
    def validate_image_url(cls, v):
        if v:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError('Invalid URL format')
        return v

class EnhancedReviewCreate(BaseModel):
    rating: int
    review_text: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None:
            if len(v.strip()) == 0:
                return None  # Convert empty string to None
            if len(v) > 2000:
                raise ValueError('Review text cannot exceed 2000 characters')
            if len(v.strip()) < 10:
                raise ValueError('Review text must be at least 10 characters long')
        return v
```

### API Documentation Configuration (app/main.py)
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi

from app.config import settings
from app.core.exceptions import (
    brs_exception_handler, 
    validation_exception_handler, 
    http_exception_handler,
    BRSException
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Book Review System API",
        description="""
        ## Book Review System Backend API
        
        A comprehensive REST API for managing books, reviews, and user recommendations.
        
        ### Features
        - **User Management**: Registration, authentication, profile management
        - **Book Catalog**: Browse, search, and discover books
        - **Review System**: Create, update, and manage book reviews
        - **Recommendations**: Personalized book recommendations
        - **Favorites**: Manage personal book collections
        
        ### Authentication
        This API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:
        ```
        Authorization: Bearer <your-token>
        ```
        
        ### Rate Limiting
        API requests are limited to 100 requests per minute per user.
        
        ### Error Handling
        All API responses follow a consistent format with appropriate HTTP status codes.
        """,
        version="1.0.0",
        terms_of_service="https://brs.example.com/terms",
        contact={
            "name": "BRS API Support",
            "url": "https://brs.example.com/support",
            "email": "support@brs.example.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Exception handlers
    app.add_exception_handler(BRSException, brs_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    return app

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Book Review System API",
        version="1.0.0",
        description="A comprehensive REST API for managing books, reviews, and recommendations",
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add examples to schemas
    openapi_schema["components"]["examples"] = {
        "UserCreateExample": {
            "summary": "User Registration Example",
            "value": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        },
        "BookCreateExample": {
            "summary": "Book Creation Example",
            "value": {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "isbn": "9780743273565",
                "description": "A classic American novel",
                "publication_date": "1925-04-10",
                "genre_ids": ["classic-literature-uuid"]
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = create_app()
app.openapi = custom_openapi
```

### Health Check and Monitoring (app/api/monitoring.py)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from datetime import datetime

from app.database import get_db
from app.schemas.common import APIResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Application health check endpoint"""
    start_time = time.time()
    
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db_response_time = round((time.time() - start_time) * 1000, 2)
    except Exception as e:
        db_status = "unhealthy"
        db_response_time = None
    
    total_response_time = round((time.time() - start_time) * 1000, 2)
    
    health_data = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": {
                "status": db_status,
                "response_time_ms": db_response_time
            }
        },
        "response_time_ms": total_response_time
    }
    
    return APIResponse(
        status="success",
        message="Health check completed",
        data=health_data
    )

@router.get("/metrics")
async def get_metrics():
    """API metrics and statistics"""
    # This would typically integrate with monitoring tools
    return APIResponse(
        status="success",
        message="Metrics retrieved",
        data={
            "uptime": "24h 30m",
            "total_requests": 15420,
            "active_users": 234,
            "response_time_avg": "120ms"
        }
    )
```

## Testing

### Documentation Tests
- [ ] OpenAPI schema validation
- [ ] Example request/response validation
- [ ] Documentation completeness check
- [ ] API endpoint coverage verification

### Validation Tests
- [ ] Input validation with various invalid inputs
- [ ] Error message accuracy and helpfulness
- [ ] Edge case validation handling
- [ ] Security validation (XSS, injection prevention)

### API Response Format Tests
- [ ] Consistent response structure across endpoints
- [ ] Proper HTTP status codes
- [ ] Error response format validation
- [ ] Pagination metadata accuracy

## Definition of Done

- [ ] Complete OpenAPI 3.0 documentation generated
- [ ] All endpoints documented with examples
- [ ] Enhanced input validation implemented
- [ ] Standardized response format across all endpoints
- [ ] Error handling with informative messages
- [ ] Health check and monitoring endpoints functional
- [ ] API versioning strategy in place
- [ ] Interactive documentation (Swagger UI) working
- [ ] Rate limiting configured
- [ ] Documentation quality reviewed and approved

## Next Steps

After completion, this task enables:
- **Task 10**: Deployment & Production Setup
- Production-ready API with comprehensive documentation
- Developer-friendly API for frontend integration

## Notes

- Keep documentation updated as API evolves
- Include real-world examples in documentation
- Consider API changelog for version tracking
- Plan for API deprecation and migration strategies
- Monitor API usage patterns for optimization opportunities
