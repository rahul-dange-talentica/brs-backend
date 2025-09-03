"""Tests for enhanced input validation and error handling."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestEnhancedValidation:
    """Test enhanced validation functionality."""
    
    def test_password_validation_requirements(self):
        """Test comprehensive password validation."""
        # Test missing uppercase
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "weakpass123!",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "error"
        assert "uppercase letter" in str(data["errors"])
        
        # Test missing special character
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com", 
            "password": "WeakPass123",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "special character" in str(response.json()["errors"])
        
        # Test too short
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "Weak1!",
            "first_name": "John", 
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "8 characters" in str(response.json()["errors"])
        
        # Test common weak password
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "too common" in str(response.json()["errors"])
    
    def test_name_validation(self):
        """Test name field validation."""
        # Test empty name
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "ValidPass123!",
            "first_name": "",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        data = response.json()
        assert "cannot be empty" in str(data["errors"])
        
        # Test invalid characters
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "ValidPass123!",
            "first_name": "John<script>",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "invalid characters" in str(response.json()["errors"])
        
        # Test too long name
        response = client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "ValidPass123!",
            "first_name": "J" * 51,
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "exceed 50 characters" in str(response.json()["errors"])
    
    def test_email_validation(self):
        """Test email validation."""
        # Test invalid email format
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "ValidPass123!",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        
        # Test disposable email (if validation is implemented)
        response = client.post("/api/v1/auth/register", json={
            "email": "test@10minutemail.com",
            "password": "ValidPass123!",
            "first_name": "John",
            "last_name": "Doe"
        })
        assert response.status_code == 422
        assert "disposable email" in str(response.json()["errors"])
    
    def test_isbn_validation(self):
        """Test ISBN validation for books."""
        # Test invalid ISBN format
        book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "isbn": "invalid-isbn",
            "description": "A test book",
            "genre_ids": []
        }
        # Note: This would require authentication, so we'll test the validation logic directly
        from app.schemas.validation import EnhancedBookCreate
        
        with pytest.raises(ValueError) as exc_info:
            EnhancedBookCreate(**book_data)
        assert "10 or 13 digits" in str(exc_info.value)
        
        # Test valid ISBN-10
        book_data["isbn"] = "0743273565"
        book = EnhancedBookCreate(**book_data)
        assert book.isbn == "0743273565"
        
        # Test valid ISBN-13
        book_data["isbn"] = "9780743273565"
        book = EnhancedBookCreate(**book_data)
        assert book.isbn == "9780743273565"
    
    def test_review_validation(self):
        """Test review validation."""
        from app.schemas.validation import EnhancedReviewCreate
        
        # Test invalid rating
        with pytest.raises(ValueError) as exc_info:
            EnhancedReviewCreate(rating=6, review_text="Good book")
        assert "between 1 and 5" in str(exc_info.value)
        
        # Test too short review
        with pytest.raises(ValueError) as exc_info:
            EnhancedReviewCreate(rating=5, review_text="Too short")
        assert "at least 10 characters" in str(exc_info.value)
        
        # Test too long review
        long_text = "x" * 2001
        with pytest.raises(ValueError) as exc_info:
            EnhancedReviewCreate(rating=5, review_text=long_text)
        assert "exceed 2000 characters" in str(exc_info.value)
        
        # Test spam pattern
        spam_text = "a" * 11 + " this is a spam review with repeated characters"
        with pytest.raises(ValueError) as exc_info:
            EnhancedReviewCreate(rating=5, review_text=spam_text)
        assert "spam" in str(exc_info.value)


class TestStandardizedErrorResponses:
    """Test standardized error response format."""
    
    def test_validation_error_format(self):
        """Test that validation errors follow the standard format."""
        response = client.post("/api/v1/auth/register", json={
            "email": "invalid-email",
            "password": "weak",
            "first_name": "",
            "last_name": "Doe"
        })
        
        assert response.status_code == 422
        data = response.json()
        
        # Check standard error response structure
        assert "status" in data
        assert data["status"] == "error"
        assert "message" in data
        assert "errors" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        # Check error details structure
        assert "code" in data["errors"]
        assert data["errors"]["code"] == "VALIDATION_ERROR"
        assert "fields" in data["errors"]
    
    def test_not_found_error_format(self):
        """Test 404 error format."""
        response = client.get("/api/v1/books/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404
        data = response.json()
        
        # Check standard error response structure
        assert data["status"] == "error"
        assert "message" in data
        assert "timestamp" in data
        assert "request_id" in data
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present."""
        response = client.get("/api/v1/books")
        
        # Check for rate limit headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        assert "X-RateLimit-Window" in response.headers


class TestSuccessResponseFormat:
    """Test standardized success response format."""
    
    def test_root_endpoint_response_format(self):
        """Test root endpoint follows standard response format."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standard success response structure
        assert data["status"] == "success"
        assert "message" in data
        assert "data" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        # Check data content
        assert "name" in data["data"]
        assert "version" in data["data"]
        assert "documentation" in data["data"]
        assert "endpoints" in data["data"]
    
    def test_health_endpoint_response_format(self):
        """Test health endpoint follows standard response format."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standard success response structure
        assert data["status"] == "success"
        assert data["message"] == "Service is healthy and operational"
        assert "data" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        # Check health data content
        assert data["data"]["status"] == "healthy"
        assert data["data"]["service"] == "Book Review System API"
        assert data["data"]["version"] == "1.0.0"


class TestMonitoringEndpoints:
    """Test monitoring and health check endpoints."""
    
    def test_detailed_health_check(self):
        """Test detailed health check endpoint."""
        response = client.get("/api/v1/monitoring/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        health_data = data["data"]
        
        # Check required health check components
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "version" in health_data
        assert "services" in health_data
        assert "system" in health_data
        assert "response_time_ms" in health_data
        
        # Check database service
        assert "database" in health_data["services"]
        assert "status" in health_data["services"]["database"]
    
    def test_readiness_check(self):
        """Test readiness probe endpoint."""
        response = client.get("/api/v1/monitoring/health/readiness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["ready"] is True
    
    def test_liveness_check(self):
        """Test liveness probe endpoint."""
        response = client.get("/api/v1/monitoring/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["data"]["alive"] is True
    
    def test_version_info(self):
        """Test version information endpoint."""
        response = client.get("/api/v1/monitoring/version")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        version_data = data["data"]
        
        assert "version" in version_data
        assert "name" in version_data
        assert "environment" in version_data
        assert "documentation" in version_data
    
    def test_service_status(self):
        """Test service status endpoint."""
        response = client.get("/api/v1/monitoring/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        status_data = data["data"]
        
        assert "overall_status" in status_data
        assert "database_status" in status_data
        assert "database_response_time_ms" in status_data
        assert "timestamp" in status_data
        assert "version" in status_data


class TestAPIDocumentation:
    """Test API documentation accessibility."""
    
    def test_openapi_spec_available(self):
        """Test that OpenAPI specification is accessible."""
        response = client.get("/api/v1/openapi.json")
        
        assert response.status_code == 200
        spec = response.json()
        
        # Check OpenAPI spec structure
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert "components" in spec
        
        # Check API info
        assert spec["info"]["title"] == "Book Review System API"
        assert spec["info"]["version"] == "1.0.0"
        
        # Check security schemes
        assert "securitySchemes" in spec["components"]
        assert "bearerAuth" in spec["components"]["securitySchemes"]
    
    def test_swagger_ui_available(self):
        """Test that Swagger UI is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()
    
    def test_redoc_available(self):
        """Test that ReDoc documentation is accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


@pytest.mark.asyncio
async def test_rate_limiting_functionality():
    """Test rate limiting functionality."""
    from app.middleware.rate_limit import InMemoryRateLimiter
    
    limiter = InMemoryRateLimiter()
    
    # Test within limit
    allowed, remaining, reset_time = await limiter.is_allowed("test_user", 5, 60)
    assert allowed is True
    assert remaining == 4
    
    # Test multiple requests
    for _ in range(4):
        allowed, remaining, reset_time = await limiter.is_allowed("test_user", 5, 60)
        assert allowed is True
    
    # Test limit exceeded
    allowed, remaining, reset_time = await limiter.is_allowed("test_user", 5, 60)
    assert allowed is False
    assert remaining == 0
