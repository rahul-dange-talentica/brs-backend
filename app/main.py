"""Book Review System - FastAPI Application with Enhanced Documentation and Error Handling."""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.api import auth, users, books, genres, reviews, recommendations, monitoring
from app.core.exceptions import (
    brs_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    BRSException
)
from app.schemas.common import create_success_response
from app.middleware.rate_limit import EnhancedRateLimitMiddleware


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    application = FastAPI(
        title="Book Review System API",
        description="""
        ## Book Review System Backend API
        
        A comprehensive REST API for managing books, reviews, and user recommendations
        built with FastAPI, PostgreSQL, and modern Python practices.
        
        ### Features
        
        - **User Management**: Secure registration, authentication, and profile management
        - **Book Catalog**: Comprehensive book management with search and filtering
        - **Review System**: User reviews and ratings with validation and moderation
        - **Recommendation Engine**: Personalized book recommendations using collaborative filtering
        - **Favorites**: Personal book collection management
        - **Genre Management**: Categorization and genre-based discovery
        
        ### Authentication
        
        This API uses JWT (JSON Web Tokens) for stateless authentication. Include the token 
        in the Authorization header for protected endpoints:
        
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ### Response Format
        
        All API responses follow a consistent JSON structure:
        
        ```json
        {
            "status": "success",
            "message": "Operation completed successfully",
            "data": {...},
            "pagination": {...},
            "timestamp": "2024-01-01T12:00:00Z",
            "request_id": "uuid-here"
        }
        ```
        
        ### Error Handling
        
        Errors are returned with appropriate HTTP status codes and detailed information:
        
        - **400 Bad Request**: Invalid request data or business rule violations
        - **401 Unauthorized**: Authentication required or invalid credentials  
        - **403 Forbidden**: Insufficient permissions for the requested action
        - **404 Not Found**: Requested resource does not exist
        - **422 Unprocessable Entity**: Request validation failed
        - **429 Too Many Requests**: Rate limit exceeded
        - **500 Internal Server Error**: Unexpected server error
        
        ### Rate Limiting
        
        API requests are limited to 100 requests per minute per authenticated user.
        Anonymous requests are limited to 20 requests per minute per IP address.
        
        ### Pagination
        
        List endpoints support pagination with the following parameters:
        - `page`: Page number (default: 1, min: 1, max: 10000)
        - `per_page`: Items per page (default: 20, min: 1, max: 100)
        
        ### Validation
        
        All input data is validated with detailed error messages for each field.
        Validation rules include:
        - Required field validation
        - Format validation (email, URL, ISBN, etc.)
        - Length constraints
        - Business rule validation
        - Content sanitization for security
        
        ### Version History
        
        - **v1.0.0**: Initial release with core functionality
        
        For detailed documentation on each endpoint, explore the sections below.
        """,
        version="1.0.0",
        terms_of_service="https://brs.example.com/terms",
        contact={
            "name": "BRS API Support Team",
            "url": "https://brs.example.com/support",
            "email": "api-support@brs.example.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
        debug=settings.debug
    )
    
    # Add exception handlers
    application.add_exception_handler(BRSException, brs_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(Exception, general_exception_handler)
    
    # Rate limiting middleware (should be added early)
    application.add_middleware(
        EnhancedRateLimitMiddleware,
        authenticated_limit=100,  # 100 requests per minute for authenticated users
        anonymous_limit=20,       # 20 requests per minute for anonymous users
        window_seconds=60,        # 1 minute window
        burst_limit=10,          # Max 10 requests in 10 seconds (burst protection)
        burst_window=10
    )
    
    # Security middleware - TrustedHost should be added first
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )
    
    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining", "X-Rate-Limit-Reset"]
    )
    
    return application


def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        servers=[
            {"url": "https://api.brs.example.com", "description": "Production server"},
            {"url": "https://staging-api.brs.example.com", "description": "Staging server"},
            {"url": "http://localhost:8000", "description": "Development server"}
        ]
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login or /auth/register"
        }
    }
    
    # Add common response examples
    openapi_schema["components"]["examples"] = {
        "SuccessResponse": {
            "summary": "Successful Response",
            "value": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"id": "123", "name": "Example"},
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "ErrorResponse": {
            "summary": "Error Response",
            "value": {
                "status": "error",
                "message": "Validation error occurred",
                "errors": {
                    "code": "VALIDATION_ERROR",
                    "fields": {
                        "email": {
                            "field": "email",
                            "message": "Invalid email format",
                            "type": "value_error.email"
                        }
                    }
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "PaginatedResponse": {
            "summary": "Paginated List Response",
            "value": {
                "status": "success",
                "message": "Items retrieved successfully",
                "data": [{"id": "1", "name": "Item 1"}, {"id": "2", "name": "Item 2"}],
                "pagination": {
                    "page": 1,
                    "per_page": 20,
                    "total": 50,
                    "pages": 3,
                    "has_next": True,
                    "has_prev": False
                },
                "timestamp": "2024-01-01T12:00:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "UserCreateExample": {
            "summary": "User Registration Request",
            "value": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe"
            }
        },
        "BookCreateExample": {
            "summary": "Book Creation Request",
            "value": {
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "isbn": "9780743273565",
                "description": "A classic American novel set in the Jazz Age",
                "cover_image_url": "https://example.com/covers/great-gatsby.jpg",
                "publication_date": "1925-04-10",
                "genre_ids": ["550e8400-e29b-41d4-a716-446655440001"]
            }
        },
        "ReviewCreateExample": {
            "summary": "Review Creation Request", 
            "value": {
                "rating": 5,
                "review_text": "An absolutely brilliant novel that captures the essence of the American Dream and its disillusionment. Fitzgerald's prose is both beautiful and haunting."
            }
        }
    }
    
    # Add common response schemas
    openapi_schema["components"]["schemas"]["StandardResponse"] = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "error"],
                "description": "Response status"
            },
            "message": {
                "type": "string",
                "description": "Human-readable message"
            },
            "data": {
                "description": "Response data (varies by endpoint)"
            },
            "pagination": {
                "$ref": "#/components/schemas/PaginationMeta"
            },
            "errors": {
                "type": "object",
                "description": "Error details (only present for error responses)"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Response timestamp"
            },
            "request_id": {
                "type": "string",
                "format": "uuid",
                "description": "Unique request identifier"
            }
        },
        "required": ["status", "message", "timestamp", "request_id"]
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Create the application instance
app = create_application()
app.openapi = custom_openapi

# Include API routers with enhanced configuration
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(books.router, prefix="/api/v1", tags=["Books"])
app.include_router(genres.router, prefix="/api/v1", tags=["Genres"])
app.include_router(reviews.router, prefix="/api/v1", tags=["Reviews"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])

app.include_router(monitoring.router, prefix="/api/v1", tags=["Monitoring"])


@app.get("/", 
         summary="API Root",
         description="Root endpoint providing API information and navigation links",
         response_description="API welcome message with navigation links",
         tags=["Root"])
async def root():
    """Root endpoint - API welcome message and navigation."""
    return create_success_response(
        data={
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "Book Review System Backend API",
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_spec": "/api/v1/openapi.json"
            },
            "endpoints": {
                "health": "/health",
                "authentication": "/api/v1/auth",
                "users": "/api/v1/users",
                "books": "/api/v1/books",
                "genres": "/api/v1/genres",
                "reviews": "/api/v1/reviews",
                "recommendations": "/api/v1/recommendations"
            },
            "support": {
                "email": "api-support@brs.example.com",
                "documentation": "https://brs.example.com/docs"
            }
        },
        message=f"Welcome to {settings.app_name} API v{settings.app_version}"
    )


@app.get("/health",
         summary="Basic Health Check", 
         description="Basic health check endpoint for load balancers and monitoring",
         response_description="Simple health status",
         tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return create_success_response(
        data={
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": "2024-01-01T12:00:00Z"
        },
        message="Service is healthy and operational"
    )
