"""Enhanced error handling and custom exceptions for BRS API."""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app.schemas.common import ErrorResponse, ValidationErrorDetail, create_error_response


# Configure logging
logger = logging.getLogger(__name__)


class BRSException(Exception):
    """Base exception for BRS application."""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(self.message)


class ValidationException(BRSException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field_errors": field_errors or {}},
            error_code="VALIDATION_ERROR"
        )


class AuthenticationError(BRSException):
    """Exception for authentication failures."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(BRSException):
    """Exception for authorization failures."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class ResourceNotFoundError(BRSException):
    """Exception for resource not found errors."""
    
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} with ID '{resource_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type, "resource_id": resource_id},
            error_code="RESOURCE_NOT_FOUND"
        )


class BookNotFoundError(ResourceNotFoundError):
    """Exception for book not found errors."""
    
    def __init__(self, book_id: str):
        super().__init__("Book", book_id)


class UserNotFoundError(ResourceNotFoundError):
    """Exception for user not found errors."""
    
    def __init__(self, user_id: str):
        super().__init__("User", user_id)


class ReviewNotFoundError(ResourceNotFoundError):
    """Exception for review not found errors."""
    
    def __init__(self, review_id: str):
        super().__init__("Review", review_id)


class GenreNotFoundError(ResourceNotFoundError):
    """Exception for genre not found errors."""
    
    def __init__(self, genre_id: str):
        super().__init__("Genre", genre_id)


class ConflictError(BRSException):
    """Exception for resource conflict errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            error_code="CONFLICT_ERROR"
        )


class DuplicateReviewError(ConflictError):
    """Exception for duplicate review attempts."""
    
    def __init__(self, user_id: str, book_id: str):
        super().__init__(
            message="You have already reviewed this book",
            details={"user_id": user_id, "book_id": book_id}
        )


class DuplicateEmailError(ConflictError):
    """Exception for duplicate email registration."""
    
    def __init__(self, email: str):
        super().__init__(
            message="An account with this email address already exists",
            details={"email": email}
        )


class BusinessRuleError(BRSException):
    """Exception for business rule violations."""
    
    def __init__(self, message: str, rule_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_code=f"BUSINESS_RULE_{rule_code}"
        )


class RateLimitExceededError(BRSException):
    """Exception for rate limit violations."""
    
    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"limit": limit, "window": window},
            error_code="RATE_LIMIT_EXCEEDED"
        )


async def brs_exception_handler(request: Request, exc: BRSException) -> JSONResponse:
    """Handle custom BRS exceptions."""
    logger.error(
        f"BRS Exception: {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.message,
            errors={
                "code": exc.error_code,
                "details": exc.details
            }
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = {}
    validation_details = []
    
    for error in exc.errors():
        field = ".".join(str(x) for x in error["loc"][1:])  # Skip 'body'
        if not field:
            field = str(error["loc"][-1]) if error["loc"] else "unknown"
        
        error_detail = ValidationErrorDetail(
            field=field,
            message=error["msg"],
            type=error["type"],
            input=error.get("input")
        )
        validation_details.append(error_detail.dict())
        errors[field] = error_detail.dict()
    
    logger.warning(
        f"Validation error on {request.method} {request.url.path}",
        extra={"validation_errors": validation_details}
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            message="Validation error occurred",
            errors={
                "code": "VALIDATION_ERROR",
                "fields": errors,
                "details": validation_details
            }
        )
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions."""
    logger.warning(
        f"HTTP Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Map common HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=exc.detail,
            errors={
                "code": error_code,
                "status_code": exc.status_code
            }
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = str(uuid.uuid4())
    
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            message="An unexpected error occurred",
            errors={
                "code": "INTERNAL_SERVER_ERROR",
                "request_id": request_id
            }
        )
    )


def raise_not_found(resource_type: str, resource_id: str) -> None:
    """Convenience function to raise not found exceptions."""
    raise ResourceNotFoundError(resource_type, resource_id)


def raise_conflict(message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise conflict exceptions."""
    raise ConflictError(message, details)


def raise_validation_error(message: str, field_errors: Optional[Dict[str, str]] = None) -> None:
    """Convenience function to raise validation exceptions."""
    raise ValidationException(message, field_errors)


def raise_business_rule_error(message: str, rule_code: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Convenience function to raise business rule exceptions."""
    raise BusinessRuleError(message, rule_code, details)
