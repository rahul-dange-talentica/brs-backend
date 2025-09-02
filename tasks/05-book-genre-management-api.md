# Task 05: Book & Genre Management API

**Phase**: 2 - Core Features  
**Sequence**: 05  
**Priority**: High  
**Estimated Effort**: 8-10 hours  
**Dependencies**: Task 02 (Database Models), Task 03 (Authentication)

---

## Objective

Implement comprehensive book and genre management API endpoints including book catalog, search functionality, filtering, and genre management according to technical PRD specifications.

## Scope

- Book catalog with pagination and filtering
- Advanced book search functionality
- Book details with genre associations
- Genre management and listing
- Performance optimization for book queries
- Integration with rating system placeholders

## Technical Requirements

### API Endpoints (from Technical PRD)
```
GET /books                    # List with pagination, filtering
GET /books/{book_id}         # Book details
GET /books/search            # Search books
GET /genres                  # List genres
```

### Performance Requirements
- Support pagination for large book catalogs
- Efficient search across title, author, and description
- Proper indexing for common queries
- Genre-based filtering capability

## Acceptance Criteria

### ✅ Book Catalog Management
- [ ] GET /books with pagination (skip/limit)
- [ ] Filtering by genre, rating, publication date
- [ ] Sorting options (title, author, rating, date)
- [ ] Proper response format with metadata
- [ ] Performance optimized queries

### ✅ Book Details & Search
- [ ] GET /books/{book_id} with complete book information
- [ ] Book details include genres, average rating, review count
- [ ] GET /books/search with text search across title/author/description
- [ ] Search supports partial matches and relevance scoring
- [ ] Combine search with filters

### ✅ Genre Management
- [ ] GET /genres lists all available genres
- [ ] Genre responses include book count
- [ ] Efficient genre-book associations
- [ ] Alphabetical sorting of genres

### ✅ Data Validation & Error Handling
- [ ] Proper validation for query parameters
- [ ] 404 responses for non-existent books
- [ ] Informative error messages
- [ ] Input sanitization for search queries

### ✅ Performance & Optimization
- [ ] Database queries optimized with proper joins
- [ ] Pagination prevents large data loads
- [ ] Search performance with database indexes
- [ ] Response time under 500ms for catalog queries

## Implementation Details

### Book API Routes (app/api/books.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional

from app.database import get_db
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookResponse, BookListResponse, BookSearchParams
from app.schemas.genre import GenreResponse

router = APIRouter(prefix="/books", tags=["books"])

@router.get("", response_model=BookListResponse)
async def get_books(
    skip: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of books to return"),
    genre_id: Optional[str] = Query(None, description="Filter by genre ID"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum average rating"),
    max_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Maximum average rating"),
    sort_by: str = Query("created_at", regex="^(title|author|average_rating|publication_date|created_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get books with pagination and filtering"""
    
    # Build query with filters
    query = db.query(Book).options(joinedload(Book.genres))
    
    # Apply filters
    if genre_id:
        query = query.filter(Book.genres.any(Genre.id == genre_id))
    
    if min_rating is not None:
        query = query.filter(Book.average_rating >= min_rating)
    
    if max_rating is not None:
        query = query.filter(Book.average_rating <= max_rating)
    
    # Apply sorting
    sort_column = getattr(Book, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get total count for pagination
    total = query.count()
    
    # Apply pagination
    books = query.offset(skip).limit(limit).all()
    
    return {
        "books": books,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/search", response_model=BookListResponse)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    genre_id: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0),
    db: Session = Depends(get_db)
):
    """Search books by title, author, or description"""
    
    # Build search query
    search_filter = or_(
        Book.title.ilike(f"%{q}%"),
        Book.author.ilike(f"%{q}%"),
        Book.description.ilike(f"%{q}%")
    )
    
    query = db.query(Book).options(joinedload(Book.genres)).filter(search_filter)
    
    # Apply additional filters
    if genre_id:
        query = query.filter(Book.genres.any(Genre.id == genre_id))
    
    if min_rating is not None:
        query = query.filter(Book.average_rating >= min_rating)
    
    # Order by relevance (title matches first, then author, then description)
    query = query.order_by(
        Book.title.ilike(f"%{q}%").desc(),
        Book.author.ilike(f"%{q}%").desc(),
        Book.average_rating.desc()
    )
    
    total = query.count()
    books = query.offset(skip).limit(limit).all()
    
    return {
        "books": books,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "search_query": q
    }

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    db: Session = Depends(get_db)
):
    """Get book details by ID"""
    
    book = db.query(Book).options(
        joinedload(Book.genres),
        joinedload(Book.reviews)
    ).filter(Book.id == book_id).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book
```

### Genre API Routes (app/api/genres.py)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.genre import Genre
from app.models.book import Book
from app.schemas.genre import GenreWithCount

router = APIRouter(prefix="/genres", tags=["genres"])

@router.get("", response_model=List[GenreWithCount])
async def get_genres(db: Session = Depends(get_db)):
    """Get all genres with book counts"""
    
    # Query genres with book counts
    genres_with_counts = db.query(
        Genre,
        func.count(Book.id).label('book_count')
    ).outerjoin(
        Book.genres
    ).group_by(Genre.id).order_by(Genre.name).all()
    
    return [
        {
            "id": genre.id,
            "name": genre.name,
            "description": genre.description,
            "created_at": genre.created_at,
            "book_count": count
        }
        for genre, count in genres_with_counts
    ]
```

### Book Schemas (app/schemas/book.py)
```python
from pydantic import BaseModel, UUID4
from datetime import datetime, date
from typing import List, Optional, Dict

from app.schemas.genre import GenreResponse

class BookBase(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    publication_date: Optional[date] = None

class BookCreate(BookBase):
    genre_ids: List[UUID4] = []

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    cover_image_url: Optional[str] = None
    publication_date: Optional[date] = None
    genre_ids: Optional[List[UUID4]] = None

class BookResponse(BookBase):
    id: UUID4
    average_rating: float
    total_reviews: int
    created_at: datetime
    updated_at: datetime
    genres: List[GenreResponse] = []
    
    class Config:
        from_attributes = True

class BookListResponse(BaseModel):
    books: List[BookResponse]
    total: int
    skip: int
    limit: int
    pages: int
    search_query: Optional[str] = None

class BookSearchParams(BaseModel):
    q: Optional[str] = None
    genre_id: Optional[UUID4] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
```

### Genre Schemas (app/schemas/genre.py)
```python
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class GenreBase(BaseModel):
    name: str
    description: Optional[str] = None

class GenreCreate(GenreBase):
    pass

class GenreResponse(GenreBase):
    id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True

class GenreWithCount(GenreResponse):
    book_count: int
```

### Database Optimization
```python
# Add to Book model for search optimization
from sqlalchemy import Index

class Book(Base):
    # ... existing fields ...
    
    __table_args__ = (
        Index('idx_book_search', 'title', 'author'),
        Index('idx_book_rating_date', 'average_rating', 'publication_date'),
        Index('idx_book_title_gin', 'title', postgresql_using='gin'),  # For PostgreSQL
    )
```

## Testing

### Unit Tests
- [ ] Book listing with various filter combinations
- [ ] Book search functionality and relevance
- [ ] Book details retrieval
- [ ] Genre listing with counts
- [ ] Pagination edge cases

### Performance Tests
- [ ] Response time under 500ms for book listing
- [ ] Search performance with large datasets
- [ ] Memory usage with large result sets
- [ ] Database query optimization verification

### Integration Tests
- [ ] Complete book discovery workflow
- [ ] Search and filter combinations
- [ ] Genre-based book filtering
- [ ] Error handling for invalid parameters

### API Testing Examples
```bash
# Get books with pagination and filters
curl "http://localhost:8000/api/v1/books?skip=0&limit=10&genre_id=GENRE_ID&min_rating=4.0&sort_by=average_rating&sort_order=desc"

# Search books
curl "http://localhost:8000/api/v1/books/search?q=python&skip=0&limit=10"

# Get book details
curl "http://localhost:8000/api/v1/books/BOOK_ID"

# Get all genres
curl "http://localhost:8000/api/v1/genres"
```

## Definition of Done

- [ ] All book and genre endpoints implemented
- [ ] Search functionality working with relevance scoring
- [ ] Filtering and sorting working correctly
- [ ] Pagination implemented properly
- [ ] Performance requirements met (<500ms response time)
- [ ] Database queries optimized with proper indexes
- [ ] Comprehensive test suite (80%+ coverage)
- [ ] API documentation complete
- [ ] Error handling for edge cases
- [ ] Input validation and sanitization

## Next Steps

After completion, this task enables:
- **Task 06**: Review & Rating System (book association)
- **Task 07**: Recommendation Engine (book data available)
- Full book discovery and catalog functionality

## Notes

- Consider implementing full-text search for better performance
- Monitor query performance and add indexes as needed
- Implement caching for frequently accessed book data
- Consider book availability/stock management for future enhancements
