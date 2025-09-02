from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from app.models.book import Book
from app.models.review import Review


async def update_book_rating(db: Session, book_id):
    """Update book's average rating and total review count"""

    # Handle both string and UUID objects
    if isinstance(book_id, str):
        try:
            book_uuid = uuid.UUID(book_id)
        except ValueError:
            return  # Invalid UUID, skip update
    elif isinstance(book_id, uuid.UUID):
        book_uuid = book_id
    else:
        return  # Invalid type, skip update

    # Calculate average rating and total reviews
    rating_stats = db.query(
        func.avg(Review.rating).label('avg_rating'),
        func.count(Review.id).label('total_reviews')
    ).filter(Review.book_id == book_uuid).first()

    # Update book record
    book = db.query(Book).filter(Book.id == book_uuid).first()
    if book:
        book.average_rating = round(rating_stats.avg_rating or 0.0, 2)
        book.total_reviews = rating_stats.total_reviews or 0
        db.commit()


async def recalculate_all_ratings(db: Session):
    """Recalculate ratings for all books (background task)"""

    books = db.query(Book).all()
    for book in books:
        await update_book_rating(db, book.id)
