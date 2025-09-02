from pydantic import BaseModel, UUID4, Field, validator
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from .genre import GenreResponse
    from .review import ReviewSummary


class BookBase(BaseModel):
    """Base book schema with common fields."""
    title: str = Field(..., max_length=500)
    author: str = Field(..., max_length=300)
    isbn: Optional[str] = Field(None, max_length=13)
    description: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=1000)
    publication_date: Optional[date] = None


class BookCreate(BookBase):
    """Schema for creating a new book."""
    genre_ids: List[UUID4] = Field(default_factory=list)


class BookUpdate(BaseModel):
    """Schema for updating book information."""
    title: Optional[str] = Field(None, max_length=500)
    author: Optional[str] = Field(None, max_length=300)
    isbn: Optional[str] = Field(None, max_length=13)
    description: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=1000)
    publication_date: Optional[date] = None
    genre_ids: Optional[List[UUID4]] = None


class BookSummary(BookBase):
    """Summary schema for book (without relationships)."""
    id: UUID4
    average_rating: Decimal
    total_reviews: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BookResponse(BookSummary):
    """Full schema for book response data with relationships."""
    genres: List["GenreResponse"] = []
    recent_reviews: List["ReviewSummary"] = []
    
    class Config:
        from_attributes = True


class BookWithStats(BookSummary):
    """Book schema with additional statistics."""
    rating_distribution: Optional[dict] = None  # {1: count, 2: count, ...}
    total_favorites: Optional[int] = None
    
    class Config:
        from_attributes = True
