# Task 04: User Management API

**Phase**: 1 - Foundation & Core Setup  
**Sequence**: 04  
**Priority**: High  
**Estimated Effort**: 6-8 hours  
**Dependencies**: Task 03 (Authentication System)

---

## Objective

Implement comprehensive user management API endpoints including user profile operations, preferences, and user-specific data management with proper authentication and authorization.

## Scope

- User profile CRUD operations
- User favorites management
- User reviews listing
- Profile update with validation
- User account management
- Proper authentication integration

## Technical Requirements

### API Endpoints (from Technical PRD)
```
GET /users/profile          # Get current user profile
PUT /users/profile          # Update user profile
GET /users/favorites        # Get user's favorite books
POST /users/favorites/{book_id}    # Add book to favorites
DELETE /users/favorites/{book_id}  # Remove book from favorites
GET /users/reviews          # Get user's reviews
```

### Authentication Integration
- All endpoints require valid JWT authentication
- Users can only access/modify their own data
- Proper error handling for unauthorized access

## Acceptance Criteria

### ✅ User Profile Management
- [ ] GET /users/profile returns current user data
- [ ] PUT /users/profile updates user information
- [ ] Profile updates validate email uniqueness
- [ ] Proper field validation (email format, names)
- [ ] No password exposure in profile responses

### ✅ Favorites Management
- [ ] GET /users/favorites lists user's favorite books with pagination
- [ ] POST /users/favorites/{book_id} adds book to favorites
- [ ] DELETE /users/favorites/{book_id} removes from favorites
- [ ] Prevents duplicate favorites
- [ ] Validates book existence before adding to favorites

### ✅ User Reviews
- [ ] GET /users/reviews lists user's reviews with pagination
- [ ] Includes book information in review responses
- [ ] Proper sorting (newest first)
- [ ] Review count and statistics

### ✅ Authentication & Authorization
- [ ] All endpoints require valid JWT token
- [ ] Proper error responses for unauthorized access
- [ ] User can only access their own data
- [ ] Consistent authentication handling

### ✅ Data Validation & Error Handling
- [ ] Input validation using Pydantic schemas
- [ ] Proper HTTP status codes
- [ ] Informative error messages
- [ ] Handles non-existent resources gracefully

## Implementation Details

### User API Routes (app/api/users.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.book import BookResponse
from app.schemas.review import ReviewWithBook
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile information"""
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    
    # Check email uniqueness if email is being updated
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Update user fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/favorites", response_model=List[BookResponse])
async def get_user_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite books with pagination"""
    
    favorites = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    books = [favorite.book for favorite in favorites]
    return books

@router.post("/favorites/{book_id}", status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    book_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a book to user's favorites"""
    
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Check if already in favorites
    existing_favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.book_id == book_id
    ).first()
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book already in favorites"
        )
    
    # Add to favorites
    favorite = UserFavorite(user_id=current_user.id, book_id=book_id)
    db.add(favorite)
    db.commit()
    
    return {"message": "Book added to favorites"}

@router.delete("/favorites/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorites(
    book_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a book from user's favorites"""
    
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == current_user.id,
        UserFavorite.book_id == book_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not in favorites"
        )
    
    db.delete(favorite)
    db.commit()

@router.get("/reviews", response_model=List[ReviewWithBook])
async def get_user_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's reviews with book information"""
    
    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    
    return reviews
```

### Enhanced User Schemas (app/schemas/user.py)
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

class UserStats(BaseModel):
    total_reviews: int
    total_favorites: int
    average_rating_given: Optional[float]

class UserWithStats(UserResponse):
    stats: UserStats
```

### Review with Book Schema (app/schemas/review.py)
```python
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

from app.schemas.book import BookResponse

class ReviewBase(BaseModel):
    rating: int
    review_text: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewUpdate(BaseModel):
    rating: Optional[int] = None
    review_text: Optional[str] = None

class ReviewResponse(ReviewBase):
    id: UUID4
    user_id: UUID4
    book_id: UUID4
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewWithBook(ReviewResponse):
    book: BookResponse
```

### User Favorite Model (app/models/user_favorite.py)
```python
from sqlalchemy import Column, UUID, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='unique_user_book_favorite'),
    )
```

## Testing

### Unit Tests
- [ ] User profile retrieval
- [ ] User profile update with valid data
- [ ] User profile update with invalid email (duplicate)
- [ ] Favorites CRUD operations
- [ ] User reviews listing with pagination

### Integration Tests
- [ ] Complete user workflow (register, update profile, add favorites)
- [ ] Authentication required for all endpoints
- [ ] Users can only access their own data
- [ ] Proper error handling for non-existent resources

### API Testing Examples
```bash
# Get user profile
curl -X GET "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update user profile
curl -X PUT "http://localhost:8000/api/v1/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Updated","last_name":"Name"}'

# Add book to favorites
curl -X POST "http://localhost:8000/api/v1/users/favorites/BOOK_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get user's reviews
curl -X GET "http://localhost:8000/api/v1/users/reviews?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Definition of Done

- [ ] All user management endpoints implemented
- [ ] Authentication integration working correctly
- [ ] Input validation and error handling
- [ ] Pagination implemented where appropriate
- [ ] Database relationships working (favorites, reviews)
- [ ] Comprehensive test suite (80%+ coverage)
- [ ] API documentation updated
- [ ] Proper HTTP status codes and responses
- [ ] Performance considerations addressed

## Next Steps

After completion, this task enables:
- **Task 05**: Book & Genre Management API
- **Task 06**: Review & Rating System (user association)
- Full user experience with personal data management

## Notes

- Ensure proper data privacy and security
- Users should only access their own data
- Consider rate limiting for profile updates
- Implement soft deletes if required for audit trails
