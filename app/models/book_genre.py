from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


# Association table for many-to-many relationship between books and genres
book_genres = Table(
    'book_genres',
    Base.metadata,
    Column('book_id', UUID(as_uuid=True), ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', UUID(as_uuid=True), ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)
