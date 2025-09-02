from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from typing import Optional, List


class GenreBase(BaseModel):
    """Base genre schema with common fields."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreCreate(GenreBase):
    """Schema for creating a new genre."""
    pass


class GenreUpdate(BaseModel):
    """Schema for updating genre information."""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class GenreResponse(GenreBase):
    """Schema for genre response data."""
    id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


# For nested responses
class GenreWithBooks(GenreResponse):
    """Schema for genre with associated books."""
    from .book import BookSummary  # Forward reference
    books: List["BookSummary"] = []
    
    class Config:
        from_attributes = True
