"""Common response schemas for API standardization."""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, Union
from enum import Enum
from datetime import datetime
import uuid


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class APIResponse(BaseModel):
    """Standardized API response format."""
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data")
    pagination: Optional[PaginationMeta] = Field(None, description="Pagination metadata")
    errors: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(APIResponse):
    """Success response schema."""
    status: ResponseStatus = ResponseStatus.SUCCESS


class ErrorDetail(BaseModel):
    """Individual error detail."""
    field: str = Field(..., description="Field name where error occurred")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ErrorResponse(APIResponse):
    """Error response schema."""
    status: ResponseStatus = ResponseStatus.ERROR
    data: Optional[Any] = None
    errors: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    field: str = Field(..., description="Field name with validation error")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Validation error type")
    input: Optional[Any] = Field(None, description="Input value that caused the error")


class HealthStatus(BaseModel):
    """Health check status response."""
    status: str = Field(..., description="Overall health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Individual service statuses")
    response_time_ms: float = Field(..., description="Response time in milliseconds")


class MetricsResponse(BaseModel):
    """API metrics response."""
    uptime: str = Field(..., description="System uptime")
    total_requests: int = Field(..., description="Total number of requests")
    active_users: int = Field(..., description="Number of active users")
    response_time_avg: str = Field(..., description="Average response time")


def create_success_response(
    data: Any = None,
    message: str = "Operation successful",
    pagination: Optional[PaginationMeta] = None
) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = SuccessResponse(
        message=message,
        data=data,
        pagination=pagination
    )
    return response.dict(exclude_none=True)


def create_error_response(
    message: str,
    errors: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    response = ErrorResponse(
        message=message,
        errors=errors
    )
    return response.dict(exclude_none=True)


def create_pagination_meta(
    page: int,
    per_page: int,
    total: int
) -> PaginationMeta:
    """Create pagination metadata."""
    pages = (total + per_page - 1) // per_page
    has_next = page < pages
    has_prev = page > 1
    
    return PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )


def create_list_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
    message: str = "Items retrieved successfully"
) -> Dict[str, Any]:
    """Create a standardized list response with pagination."""
    pagination = create_pagination_meta(page, per_page, total)
    return create_success_response(
        data=items,
        message=message,
        pagination=pagination
    )
