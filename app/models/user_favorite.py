from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class UserFavorite(Base):
    """UserFavorite model for user's favorite books."""
    
    __tablename__ = "user_favorites"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_favorite'),
    )
    
    def __repr__(self):
        return f"<UserFavorite(id={self.id}, user_id={self.user_id}, book_id={self.book_id})>"
