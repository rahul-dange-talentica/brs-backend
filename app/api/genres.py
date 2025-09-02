from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from app.database import get_db
from app.models.genre import Genre
from app.models.book_genre import book_genres
from app.schemas.genre import GenreWithCount

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("", response_model=List[GenreWithCount])
async def get_genres(db: Session = Depends(get_db)):
    """Get all genres with book counts"""

    # Query genres with book counts using subquery
    subquery = db.query(
        book_genres.c.genre_id,
        func.count(book_genres.c.book_id).label('book_count')
    ).group_by(book_genres.c.genre_id).subquery()

    # Join genres with the book count subquery
    genres_with_counts = db.query(
        Genre,
        func.coalesce(subquery.c.book_count, 0).label('book_count')
    ).outerjoin(
        subquery, Genre.id == subquery.c.genre_id
    ).order_by(Genre.name).all()

    return [
        {
            "id": genre.id,
            "name": genre.name,
            "description": genre.description,
            "created_at": genre.created_at,
            "book_count": int(count)
        }
        for genre, count in genres_with_counts
    ]
