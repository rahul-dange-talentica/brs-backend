"""add_book_search_optimization_indexes

Revision ID: 4145f14198c3
Revises: 0dc08447ccf6
Create Date: 2025-09-02 19:39:35.644520

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4145f14198c3'
down_revision = '0dc08447ccf6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indexes for book search optimization
    
    # Index for search across title and author
    op.create_index('idx_book_search_title_author', 'books', ['title', 'author'])
    
    # Index for rating and publication date filtering
    op.create_index('idx_book_rating_date', 'books', ['average_rating', 'publication_date'])
    
    # Index for created_at sorting (commonly used for pagination)
    op.create_index('idx_book_created_at', 'books', ['created_at'])
    
    # Index for title search (case-insensitive optimization)
    op.execute("CREATE INDEX idx_book_title_lower ON books (LOWER(title))")
    
    # Index for author search (case-insensitive optimization)
    op.execute("CREATE INDEX idx_book_author_lower ON books (LOWER(author))")


def downgrade() -> None:
    # Drop the indexes in reverse order
    op.execute("DROP INDEX IF EXISTS idx_book_author_lower")
    op.execute("DROP INDEX IF EXISTS idx_book_title_lower")
    op.drop_index('idx_book_created_at', 'books')
    op.drop_index('idx_book_rating_date', 'books')
    op.drop_index('idx_book_search_title_author', 'books')
