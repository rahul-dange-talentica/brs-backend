# Task 02: Database Models & Migrations

**Phase**: 1 - Foundation & Core Setup  
**Sequence**: 02  
**Priority**: Critical  
**Estimated Effort**: 8-10 hours  
**Dependencies**: Task 01 (Project Setup)

---

## Objective

Implement all SQLAlchemy database models, relationships, and Alembic migrations for the BRS backend according to the technical PRD specifications.

## Scope

- Complete SQLAlchemy models for all entities (User, Book, Genre, Review, UserFavorites)
- Database relationships and constraints
- Alembic migration setup and initial migration
- Database indexes for performance
- Pydantic schemas for API serialization
- Database session management

## Technical Requirements

### Database Entities
- **Users**: Authentication and profile information
- **Books**: Book catalog with metadata
- **Genres**: Book categorization
- **Reviews**: User reviews and ratings
- **UserFavorites**: User's favorite books
- **BookGenres**: Many-to-many relationship between books and genres

### Database Schema (from Technical PRD)
```sql
-- Core tables with relationships
users (id, email, password_hash, first_name, last_name, created_at, updated_at, is_active)
genres (id, name, description, created_at)
books (id, title, author, isbn, description, cover_image_url, publication_date, average_rating, total_reviews, created_at, updated_at)
book_genres (book_id, genre_id) -- Many-to-many
reviews (id, user_id, book_id, rating, review_text, created_at, updated_at)
user_favorites (id, user_id, book_id, created_at)
```

## Acceptance Criteria

### ✅ SQLAlchemy Models
- [ ] User model with all required fields and constraints
- [ ] Book model with rating aggregation fields
- [ ] Genre model with description
- [ ] Review model with rating constraints (1-5)
- [ ] UserFavorites model with composite unique constraint
- [ ] BookGenres association table for many-to-many relationship

### ✅ Database Relationships
- [ ] User → Reviews (one-to-many)
- [ ] User → UserFavorites (one-to-many)
- [ ] Book → Reviews (one-to-many)
- [ ] Book → UserFavorites (one-to-many)
- [ ] Book ↔ Genres (many-to-many via BookGenres)
- [ ] Proper foreign key constraints and cascade deletes

### ✅ Alembic Migrations
- [ ] Alembic initialization and configuration
- [ ] Initial migration creating all tables
- [ ] Migration creates all required indexes
- [ ] Migration includes proper constraints and defaults

### ✅ Pydantic Schemas
- [ ] Request/Response schemas for all models
- [ ] Nested schemas for relationships
- [ ] Validation rules matching database constraints
- [ ] Separate Create/Update/Response schemas

### ✅ Database Session Management
- [ ] Database connection and session factory
- [ ] Session dependency for FastAPI
- [ ] Proper session lifecycle management
- [ ] Connection pooling configuration

## Implementation Details

### User Model (app/models/user.py)
```python
from sqlalchemy import Column, String, Boolean, DateTime, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="user", cascade="all, delete-orphan")
```

### Book Model (app/models/book.py)
```python
from sqlalchemy import Column, String, Text, Date, DECIMAL, Integer, DateTime, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    author = Column(String(300), nullable=False)
    isbn = Column(String(13), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    cover_image_url = Column(String(1000), nullable=True)
    publication_date = Column(Date, nullable=True)
    average_rating = Column(DECIMAL(3, 2), default=0.00, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    favorites = relationship("UserFavorite", back_populates="book", cascade="all, delete-orphan")
    genres = relationship("Genre", secondary="book_genres", back_populates="books")
```

### Database Performance Indexes
```sql
-- From Technical PRD
CREATE INDEX idx_books_average_rating ON books(average_rating DESC);
CREATE INDEX idx_book_genres_book ON book_genres(book_id);
CREATE INDEX idx_book_genres_genre ON book_genres(genre_id);
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
```

### Pydantic Schemas (app/schemas/user.py example)
```python
from pydantic import BaseModel, EmailStr, UUID4
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
```

### Database Session (app/database.py)
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=5,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## Testing

### Unit Tests for Models
- [ ] Model creation and field validation
- [ ] Relationship integrity tests
- [ ] Constraint validation (unique, check constraints)
- [ ] Cascade delete behavior

### Migration Tests
- [ ] Migration applies successfully
- [ ] All tables created with correct schema
- [ ] Indexes created correctly
- [ ] Rollback functionality works

### Schema Validation Tests
- [ ] Pydantic schema validation
- [ ] Serialization/deserialization
- [ ] Nested relationship handling

## Database Migration Commands
```bash
# Initialize Alembic (if not done in Task 01)
poetry run alembic init alembic

# Create initial migration
poetry run alembic revision --autogenerate -m "Initial database schema"

# Apply migration
poetry run alembic upgrade head

# Verify schema
poetry run python -c "from app.database import engine; print(engine.table_names())"
```

## Definition of Done

- [ ] All SQLAlchemy models implemented and tested
- [ ] Database relationships working correctly
- [ ] Alembic migrations created and applied successfully
- [ ] All required indexes created
- [ ] Pydantic schemas for all models
- [ ] Database session management working
- [ ] Unit tests passing (80%+ coverage for models)
- [ ] Migration rollback tested
- [ ] Performance indexes verified

## Next Steps

After completion, this task enables:
- **Task 03**: Authentication & Security System (User model ready)
- **Task 04**: User Management API (User schemas ready)
- **Task 05**: Book & Genre Management API (Book/Genre models ready)
- **Task 06**: Review & Rating System (Review model ready)

## Notes

- Follow the exact schema from Technical PRD
- Ensure proper foreign key relationships
- Test all constraints thoroughly
- Document any schema deviations
- Consider future scalability in index design
