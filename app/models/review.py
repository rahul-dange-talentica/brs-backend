from sqlalchemy import (Column, Text, Integer, DateTime, ForeignKey, 
                        CheckConstraint, UniqueConstraint)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Review(Base):
    """Review model for user reviews and ratings."""
    
    __tablename__ = "reviews"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), 
                      ForeignKey('users.id', ondelete='CASCADE'), 
                      nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), 
                      ForeignKey('books.id', ondelete='CASCADE'), 
                      nullable=False, index=True)
    
    # Review fields
    rating = Column(Integer, nullable=False, index=True)
    review_text = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), 
                        server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), 
                        server_default=func.now(), 
                        onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', 
                        name='check_rating_range'),
        # Ensure one review per user per book
        UniqueConstraint('user_id', 'book_id', 
                         name='unique_user_book_review'),
    )
    
    def __repr__(self):
        return (f"<Review(id={self.id}, user_id={self.user_id}, "
                f"book_id={self.book_id}, rating={self.rating})>")
