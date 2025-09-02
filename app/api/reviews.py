from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
import uuid

from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.review import Review
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse,
    ReviewListResponse, ReviewSummary
)
from app.core.auth import get_current_active_user
from app.utils.rating_calculator import update_book_rating

router = APIRouter(tags=["reviews"])


@router.get("/books/{book_id}/reviews", response_model=ReviewListResponse)
async def get_book_reviews(
    book_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at",
                         regex="^(created_at|rating|updated_at)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    rating_filter: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db)
):
    """Get reviews for a specific book with pagination and filtering"""

    # Convert book_id to UUID
    try:
        book_uuid = uuid.UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book ID format"
        )

    # Verify book exists
    book = db.query(Book).filter(Book.id == book_uuid).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # Build query
    query = db.query(Review).filter(Review.book_id == book_uuid)

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

    # Convert to response format with user info
    reviews_with_user = []
    for review in reviews:
        user_name = (f"{review.user.first_name} {review.user.last_name}"
                     .strip() if review.user.first_name or
                     review.user.last_name else review.user.email)
        review_dict = {
            "id": review.id,
            "user_id": review.user_id,
            "book_id": review.book_id,
            "rating": review.rating,
            "review_text": review.review_text,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "user_name": user_name
        }
        reviews_with_user.append(review_dict)

    return {
        "reviews": reviews_with_user,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0,
        "book_id": book_id
    }


@router.post("/books/{book_id}/reviews", response_model=ReviewSummary,
             status_code=status.HTTP_201_CREATED)
async def create_review(
    book_id: str,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new review for a book"""

    # Convert book_id to UUID
    try:
        book_uuid = uuid.UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book ID format"
        )

    # Verify book exists
    book = db.query(Book).filter(Book.id == book_uuid).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    # Check if user already reviewed this book
    existing_review = db.query(Review).filter(
        and_(Review.user_id == current_user.id, Review.book_id == book_uuid)
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this book. "
                   "Use PUT to update your review."
        )

    # Create new review
    new_review = Review(
        user_id=current_user.id,
        book_id=book_uuid,
        rating=review_data.rating,
        review_text=review_data.review_text
    )

    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    # Update book's average rating
    await update_book_rating(db, book_uuid)

    return new_review


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: Session = Depends(get_db)
):
    """Get review details by ID"""

    # Convert review_id to UUID
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )

    review = db.query(Review).filter(Review.id == review_uuid).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    return review


@router.put("/reviews/{review_id}", response_model=ReviewSummary)
async def update_review(
    review_id: str,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update user's own review"""

    # Convert review_id to UUID
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )

    # Get review and verify ownership
    review = db.query(Review).filter(Review.id == review_uuid).first()
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

    # Convert review_id to UUID
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )

    # Get review and verify ownership
    review = db.query(Review).filter(Review.id == review_uuid).first()
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