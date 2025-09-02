from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserResponse
    from .book import BookSummary


class ReviewBase(BaseModel):
    """Base review schema with common fields."""
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None

    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError('Review text cannot exceed 2000 characters')
        return v


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    pass


class ReviewUpdate(BaseModel):
    """Schema for updating review information."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None

    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError('Review text cannot exceed 2000 characters')
        return v


class ReviewSummary(ReviewBase):
    """Summary schema for review (minimal data)."""
    id: UUID4
    user_id: UUID4
    book_id: UUID4
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewResponse(ReviewSummary):
    """Full schema for review response data with relationships."""
    user: Optional["UserResponse"] = None
    book: Optional["BookSummary"] = None

    class Config:
        from_attributes = True


class ReviewWithUser(ReviewSummary):
    """Review schema with user information."""
    # Computed field from user.first_name + last_name
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewWithBook(ReviewSummary):
    """Review schema with book information for user's reviews."""
    book: Optional["BookSummary"] = None

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Schema for paginated review list responses."""
    reviews: List[ReviewWithUser]
    total: int
    skip: int
    limit: int
    pages: int
    book_id: str
