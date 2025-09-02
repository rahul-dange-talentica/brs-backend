from sqlalchemy import Column, String, Text, Date, DECIMAL, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Book(Base):
    """Book model with metadata and rating aggregation."""
    
    __tablename__ = "books"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Book fields
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=False)
    isbn = Column(String(13), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(1000), nullable=True)
    publication_date = Column(Date, nullable=True)
    
    # Rating aggregation fields
    average_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="book", cascade="all, delete-orphan")
    genres = relationship("Genre", secondary="book_genres", back_populates="books")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"
