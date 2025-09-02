from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .book import BookSummary


class UserFavoriteBase(BaseModel):
    """Base user favorite schema."""
    book_id: UUID4


class UserFavoriteCreate(UserFavoriteBase):
    """Schema for creating a new user favorite."""
    pass


class UserFavoriteResponse(UserFavoriteBase):
    """Schema for user favorite response data."""
    id: UUID4
    user_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserFavoriteWithBook(UserFavoriteResponse):
    """User favorite schema with book information."""
    book: Optional["BookSummary"] = None
    
    class Config:
        from_attributes = True
