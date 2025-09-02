"""User management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.book import BookSummary
from app.schemas.review import ReviewWithBook
from app.core.auth import get_current_active_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile information."""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information."""

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


@router.get("/favorites", response_model=List[BookSummary])
async def get_user_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite books with pagination."""

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
    """Add a book to user's favorites."""

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
    """Remove a book from user's favorites."""

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
    """Get user's reviews with book information."""

    reviews = db.query(Review).filter(
        Review.user_id == current_user.id
    ).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()

    return reviews
