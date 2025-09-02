from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Genre(Base):
    """Genre model for book categorization."""
    
    __tablename__ = "genres"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Genre fields
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    books = relationship("Book", secondary="book_genres", back_populates="genres")
    
    def __repr__(self):
        return f"<Genre(id={self.id}, name='{self.name}')>"
