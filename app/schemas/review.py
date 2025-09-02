from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime
from typing import Optional


class ReviewBase(BaseModel):
    """Base review schema with common fields."""
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    book_id: UUID4


class ReviewUpdate(BaseModel):
    """Schema for updating review information."""
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None


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
    from .user import UserResponse  # Forward reference
    from .book import BookSummary   # Forward reference
    
    user: Optional["UserResponse"] = None
    book: Optional["BookSummary"] = None
    
    class Config:
        from_attributes = True


class ReviewWithUser(ReviewSummary):
    """Review schema with user information."""
    user_name: Optional[str] = None  # Computed field from user.first_name + last_name
    
    class Config:
        from_attributes = True
