from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc, func
from typing import Optional

from app.database import get_db
from app.models.book import Book
from app.models.genre import Genre
from app.schemas.book import BookResponse

router = APIRouter(prefix="/books", tags=["books"])


@router.get("", response_model=dict)
async def get_books(
    skip: int = Query(0, ge=0, description="Number of books to skip"),
    limit: int = Query(
        20, ge=1, le=100, description="Number of books to return"
    ),
    genre_id: Optional[str] = Query(None, description="Filter by genre ID"),
    min_rating: Optional[float] = Query(
        None, ge=0.0, le=5.0, description="Minimum average rating"
    ),
    max_rating: Optional[float] = Query(
        None, ge=0.0, le=5.0, description="Maximum average rating"
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(title|author|average_rating|publication_date|created_at)$"
    ),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """Get books with pagination and filtering"""

    # Build query with eager loading
    query = db.query(Book).options(joinedload(Book.genres))

    # Apply filters
    if genre_id:
        try:
            # Validate UUID format
            from uuid import UUID
            UUID(genre_id)
            query = query.filter(Book.genres.any(Genre.id == genre_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid genre ID format"
            )

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
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@router.get("/search", response_model=dict)
async def search_books(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    genre_id: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0),
    db: Session = Depends(get_db)
):
    """Search books by title, author, or description"""

    # Sanitize search query
    search_term = q.strip().replace('%', '\\%').replace('_', '\\_')

    # Build search query with case-insensitive matching
    search_filter = or_(
        Book.title.ilike(f"%{search_term}%"),
        Book.author.ilike(f"%{search_term}%"),
        Book.description.ilike(f"%{search_term}%")
    )

    query = db.query(Book).options(
        joinedload(Book.genres)
    ).filter(search_filter)

    # Apply additional filters
    if genre_id:
        try:
            from uuid import UUID
            UUID(genre_id)
            query = query.filter(Book.genres.any(Genre.id == genre_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid genre ID format"
            )

    if min_rating is not None:
        query = query.filter(Book.average_rating >= min_rating)

    # Order by relevance (title matches first, then author, then by rating)
    # Using CASE WHEN for relevance scoring
    relevance_score = (
        func.case(
            (Book.title.ilike(f"%{search_term}%"), 3),
            (Book.author.ilike(f"%{search_term}%"), 2),
            (Book.description.ilike(f"%{search_term}%"), 1),
            else_=0
        )
    )

    query = query.order_by(
        desc(relevance_score),
        desc(Book.average_rating),
        desc(Book.created_at)
    )

    total = query.count()
    books = query.offset(skip).limit(limit).all()

    return {
        "books": books,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0,
        "search_query": q
    }


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: str,
    db: Session = Depends(get_db)
):
    """Get book details by ID"""

    # Validate UUID format
    try:
        from uuid import UUID
        UUID(book_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid book ID format"
        )

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
