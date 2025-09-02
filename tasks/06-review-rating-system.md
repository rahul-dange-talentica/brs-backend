# Task 06: Review & Rating System

**Phase**: 2 - Core Features  
**Sequence**: 06  
**Priority**: High  
**Estimated Effort**: 10-12 hours  
**Dependencies**: Task 03 (Authentication), Task 05 (Book Management)

---

## Objective

Implement comprehensive review and rating system including CRUD operations for reviews, rating aggregation, and review management with proper validation and performance optimization.

## Scope

- Review CRUD operations (Create, Read, Update, Delete)
- Rating system with 1-5 star validation
- Rating aggregation and book average calculation
- Review listing with pagination and filtering
- User review management and ownership validation
- Performance optimization for rating calculations

## Technical Requirements

### API Endpoints (from Technical PRD)
```
GET /books/{book_id}/reviews     # Book reviews with pagination
POST /books/{book_id}/reviews    # Create review
PUT /reviews/{review_id}         # Update own review
DELETE /reviews/{review_id}      # Delete own review
GET /reviews/{review_id}         # Review details
```

### Business Rules
- Users can only have one review per book
- Rating must be between 1-5 (integer)
- Users can only modify/delete their own reviews
- Average ratings update automatically when reviews change
- Reviews are soft-deletable for audit purposes

## Acceptance Criteria

### ✅ Review CRUD Operations
- [ ] POST /books/{book_id}/reviews creates new review with validation
- [ ] GET /books/{book_id}/reviews lists reviews with pagination
- [ ] GET /reviews/{review_id} returns review details
- [ ] PUT /reviews/{review_id} updates user's own review only
- [ ] DELETE /reviews/{review_id} removes user's own review only

### ✅ Rating System
- [ ] Rating validation (1-5 integer values only)
- [ ] One review per user per book constraint
- [ ] Automatic average rating calculation
- [ ] Total review count updates
- [ ] Rating history preservation

### ✅ Authorization & Ownership
- [ ] Authentication required for review operations
- [ ] Users can only modify their own reviews
- [ ] Proper error handling for unauthorized access
- [ ] Ownership validation on update/delete operations

### ✅ Performance & Aggregation
- [ ] Efficient rating aggregation using database triggers/functions
- [ ] Optimized queries for review listing
- [ ] Proper indexing for review queries
- [ ] Background rating recalculation capability

### ✅ Data Validation & Error Handling
- [ ] Review text length validation
- [ ] Rating range validation (1-5)
- [ ] Duplicate review prevention
- [ ] Non-existent book/review error handling

## Implementation Details

### Review API Routes (app/api/reviews.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, 
    ReviewWithUser, ReviewListResponse
)
from app.core.auth import get_current_active_user
from app.utils.rating_calculator import update_book_rating

router = APIRouter(tags=["reviews"])

@router.get("/books/{book_id}/reviews", response_model=ReviewListResponse)
async def get_book_reviews(
    book_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at", regex="^(created_at|rating|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    rating_filter: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """Get reviews for a specific book with pagination and filtering"""
    
    # Verify book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Build query
    query = db.query(Review).filter(Review.book_id == book_id)
    
    # Apply rating filter
    if rating_filter:
        query = query.filter(Review.rating == rating_filter)
    
    # Apply sorting
    sort_column = getattr(Review, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Get total count
    total = query.count()
    
    # Apply pagination and get results with user info
    reviews = query.offset(skip).limit(limit).all()
    
    return {
        "reviews": reviews,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "book_id": book_id
    }

@router.post("/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    book_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new review for a book"""
    
    # Verify book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if user already reviewed this book
    existing_review = db.query(Review).filter(
        and_(Review.user_id == current_user.id, Review.book_id == book_id)
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this book. Use PUT to update your review."
        )
    
    # Create new review
    new_review = Review(
        user_id=current_user.id,
        book_id=book_id,
        rating=review_data.rating,
        review_text=review_data.review_text
    )
    
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    
    # Update book's average rating
    await update_book_rating(db, book_id)
    
    return new_review

@router.get("/reviews/{review_id}", response_model=ReviewWithUser)
async def get_review(
    review_id: str,
    db: Session = Depends(get_db)
):
    """Get review details by ID"""
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's own review"""
    
    # Get review and verify ownership
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own reviews"
        )
    
    # Update review fields
    update_data = review_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(review, field, value)
    
    db.commit()
    db.refresh(review)
    
    # Update book's average rating if rating changed
    if 'rating' in update_data:
        await update_book_rating(db, review.book_id)
    
    return review

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete user's own review"""
    
    # Get review and verify ownership
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )
    
    book_id = review.book_id
    db.delete(review)
    db.commit()
    
    # Update book's average rating
    await update_book_rating(db, book_id)
```

### Rating Calculator Utility (app/utils/rating_calculator.py)
```python
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.book import Book
from app.models.review import Review

async def update_book_rating(db: Session, book_id: str):
    """Update book's average rating and total review count"""
    
    # Calculate average rating and total reviews
    rating_stats = db.query(
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('total_reviews')
    ).filter(Review.book_id == book_id).first()
    
    # Update book record
    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.average_rating = round(rating_stats.avg_rating or 0.0, 2)
        book.total_reviews = rating_stats.total_reviews or 0
        db.commit()

async def recalculate_all_ratings(db: Session):
    """Recalculate ratings for all books (background task)"""
    
    books = db.query(Book).all()
    for book in books:
        await update_book_rating(db, book.id)
```

### Enhanced Review Schemas (app/schemas/review.py)
```python
from pydantic import BaseModel, UUID4, validator
from datetime import datetime
from typing import Optional, List

from app.schemas.user import UserResponse
from app.schemas.book import BookResponse

class ReviewBase(BaseModel):
    rating: int
    review_text: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError('Review text cannot exceed 2000 characters')
        return v

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    review_text: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Rating must be between 1 and 5')
        return v

class ReviewResponse(ReviewBase):
    id: UUID4
    user_id: UUID4
    book_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewWithUser(ReviewResponse):
    user: UserResponse

class ReviewWithBook(ReviewResponse):
    book: BookResponse

class ReviewListResponse(BaseModel):
    reviews: List[ReviewWithUser]
    total: int
    skip: int
    limit: int
    pages: int
    book_id: str
```

### Enhanced Review Model (app/models/review.py)
```python
from sqlalchemy import Column, String, Text, Integer, DateTime, UUID, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range_check'),
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_review'),
    )
```

## Testing

### Unit Tests
- [ ] Review creation with valid data
- [ ] Review creation validation (rating range, duplicate prevention)
- [ ] Review update by owner
- [ ] Review update/delete authorization
- [ ] Rating aggregation calculation

### Integration Tests
- [ ] Complete review workflow (create, read, update, delete)
- [ ] Book rating updates after review changes
- [ ] Multi-user review scenarios
- [ ] Review pagination and filtering

### Performance Tests
- [ ] Rating calculation performance
- [ ] Review listing performance with large datasets
- [ ] Concurrent review creation handling

### API Testing Examples
```bash
# Create review
curl -X POST "http://localhost:8000/api/v1/books/BOOK_ID/reviews" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":5,"review_text":"Excellent book!"}'

# Get book reviews
curl "http://localhost:8000/api/v1/books/BOOK_ID/reviews?skip=0&limit=10&rating_filter=5"

# Update review
curl -X PUT "http://localhost:8000/api/v1/reviews/REVIEW_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":4,"review_text":"Good book, updated review"}'

# Delete review
curl -X DELETE "http://localhost:8000/api/v1/reviews/REVIEW_ID" \
  -H "Authorization: Bearer TOKEN"
```

## Definition of Done

- [ ] All review CRUD endpoints implemented and tested
- [ ] Rating system with proper validation (1-5 range)
- [ ] Authorization and ownership controls working
- [ ] Automatic rating aggregation functioning
- [ ] One review per user per book constraint enforced
- [ ] Performance optimization for rating calculations
- [ ] Comprehensive test suite (80%+ coverage)
- [ ] API documentation complete
- [ ] Error handling for all edge cases
- [ ] Database indexes for review queries

## Next Steps

After completion, this task enables:
- **Task 07**: Recommendation Engine (rating data available)
- Complete book review functionality
- User engagement metrics and analytics

## Notes

- Consider implementing review helpful/upvote functionality
- Monitor performance of rating aggregation with large datasets
- Implement soft deletes for reviews if audit trails are needed
- Consider rate limiting for review creation to prevent spam
