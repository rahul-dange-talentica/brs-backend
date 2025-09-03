"""Genre-based recommendation engine."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, not_
from typing import List, Optional
import uuid

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite


class GenreRecommendationEngine:
    """Engine for generating genre-based book recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_genre_books(
        self,
        genre_id: str,
        limit: int = 20,
        exclude_user_id: Optional[str] = None,
        min_rating: float = 0.0,
        min_reviews: int = 1
    ) -> List[Book]:
        """
        Get top books in a specific genre.
        
        Args:
            genre_id: UUID of the genre to get recommendations for
            limit: Maximum number of books to return
            exclude_user_id: User ID to exclude books they've already interacted with
            min_rating: Minimum average rating threshold
            min_reviews: Minimum number of reviews required
            
        Returns:
            List of Book objects sorted by rating and popularity
        """
        
        # Convert string UUID to UUID object if needed
        if isinstance(genre_id, str):
            genre_uuid = uuid.UUID(genre_id)
        else:
            genre_uuid = genre_id
            
        query = self.db.query(Book).options(
            joinedload(Book.genres)
        ).filter(
            and_(
                Book.genres.any(Genre.id == genre_uuid),
                Book.average_rating >= min_rating,
                Book.total_reviews >= min_reviews
            )
        )
        
        # Exclude books user has already reviewed or favorited
        if exclude_user_id:
            # Convert string UUID to UUID object if needed
            if isinstance(exclude_user_id, str):
                user_uuid = uuid.UUID(exclude_user_id)
            else:
                user_uuid = exclude_user_id
                
            reviewed_books = self.db.query(Review.book_id).filter(
                Review.user_id == user_uuid
            ).subquery()
            
            favorited_books = self.db.query(UserFavorite.book_id).filter(
                UserFavorite.user_id == user_uuid
            ).subquery()
            
            query = query.filter(
                and_(
                    not_(Book.id.in_(reviewed_books)),
                    not_(Book.id.in_(favorited_books))
                )
            )
        
        # Order by rating and review count for quality
        query = query.order_by(
            desc(Book.average_rating),
            desc(Book.total_reviews),
            desc(Book.created_at)  # Tiebreaker for newer books
        )
        
        return query.limit(limit).all()
    
    async def get_similar_genre_books(
        self,
        book_id: str,
        limit: int = 20,
        exclude_user_id: Optional[str] = None
    ) -> List[Book]:
        """
        Get books similar to a given book based on shared genres.
        
        Args:
            book_id: UUID of the book to find similar books for
            limit: Maximum number of books to return
            exclude_user_id: User ID to exclude books they've already interacted with
            
        Returns:
            List of Book objects with similar genres
        """
        
        # Convert string UUID to UUID object if needed
        if isinstance(book_id, str):
            book_uuid = uuid.UUID(book_id)
        else:
            book_uuid = book_id
            
        # Get the genres of the given book
        book_genres = self.db.query(Genre.id).join(
            Genre.books
        ).filter(Book.id == book_uuid).subquery()
        
        # Find books that share at least one genre
        query = self.db.query(Book).filter(
            and_(
                Book.id != book_uuid,  # Exclude the original book
                Book.genres.any(Genre.id.in_(book_genres))
            )
        )
        
        # Exclude user's books if specified
        if exclude_user_id:
            # Convert string UUID to UUID object if needed
            if isinstance(exclude_user_id, str):
                user_uuid = uuid.UUID(exclude_user_id)
            else:
                user_uuid = exclude_user_id
                
            reviewed_books = self.db.query(Review.book_id).filter(
                Review.user_id == user_uuid
            ).subquery()
            
            favorited_books = self.db.query(UserFavorite.book_id).filter(
                UserFavorite.user_id == user_uuid
            ).subquery()
            
            query = query.filter(
                and_(
                    not_(Book.id.in_(reviewed_books)),
                    not_(Book.id.in_(favorited_books))
                )
            )
        
        # Order by rating and popularity
        query = query.order_by(
            desc(Book.average_rating),
            desc(Book.total_reviews)
        )
        
        return query.limit(limit).all()
    
    async def get_genre_diversity_recommendations(
        self,
        preferred_genres: List[str],
        limit: int = 20,
        exclude_user_id: Optional[str] = None
    ) -> List[Book]:
        """
        Get diverse recommendations across multiple preferred genres.
        
        Args:
            preferred_genres: List of genre IDs to get recommendations from
            limit: Maximum number of books to return
            exclude_user_id: User ID to exclude books they've already interacted with
            
        Returns:
            List of Book objects with diversity across genres
        """
        
        if not preferred_genres:
            return []
        
        # Calculate books per genre for diversity
        books_per_genre = max(1, limit // len(preferred_genres))
        remaining_books = limit % len(preferred_genres)
        
        all_recommendations = []
        
        for i, genre_id in enumerate(preferred_genres):
            genre_limit = books_per_genre
            if i < remaining_books:
                genre_limit += 1
                
            genre_books = await self.get_genre_books(
                genre_id=genre_id,
                limit=genre_limit,
                exclude_user_id=exclude_user_id
            )
            all_recommendations.extend(genre_books)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for book in all_recommendations:
            if book.id not in seen:
                seen.add(book.id)
                unique_recommendations.append(book)
        
        return unique_recommendations[:limit]
    
    async def get_similar_books_by_genre(
        self,
        book_id: str,
        limit: int = 20,
        exclude_user_id: Optional[str] = None
    ) -> List[Book]:
        """
        Get books similar to a given book based on shared genres.
        This is an alias for get_similar_genre_books for backward compatibility.
        
        Args:
            book_id: UUID of the book to find similar books for
            limit: Maximum number of books to return
            exclude_user_id: User ID to exclude books they've already interacted with
            
        Returns:
            List of Book objects with similar genres
        """
        return await self.get_similar_genre_books(book_id, limit, exclude_user_id)
    
    async def get_user_preferred_genres(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Get user's preferred genres based on their review and favorite activity.
        
        Args:
            user_id: UUID of the user
            limit: Maximum number of genres to return
            
        Returns:
            List of dictionaries with genre information and interaction counts
        """
        from sqlalchemy import func
        
        # Convert string UUID to UUID object if needed
        if isinstance(user_id, str):
            user_uuid = uuid.UUID(user_id)
        else:
            user_uuid = user_id
        
        # Get genres from user's reviewed books
        review_genres = self.db.query(
            Genre.id,
            Genre.name,
            func.count(Review.id).label('review_count')
        ).join(
            Book.genres
        ).join(
            Review, Book.id == Review.book_id
        ).filter(
            Review.user_id == user_uuid
        ).group_by(Genre.id, Genre.name).subquery()
        
        # Get genres from user's favorite books
        favorite_genres = self.db.query(
            Genre.id,
            Genre.name,
            func.count(UserFavorite.id).label('favorite_count')
        ).join(
            Book.genres
        ).join(
            UserFavorite, Book.id == UserFavorite.book_id
        ).filter(
            UserFavorite.user_id == user_uuid
        ).group_by(Genre.id, Genre.name).subquery()
        
        # Combine and aggregate the results
        combined_query = self.db.query(
            Genre.id,
            Genre.name,
            func.coalesce(review_genres.c.review_count, 0).label('reviews'),
            func.coalesce(favorite_genres.c.favorite_count, 0).label('favorites'),
            (func.coalesce(review_genres.c.review_count, 0) + 
             func.coalesce(favorite_genres.c.favorite_count, 0)).label('total_interactions')
        ).select_from(Genre).outerjoin(
            review_genres, Genre.id == review_genres.c.id
        ).outerjoin(
            favorite_genres, Genre.id == favorite_genres.c.id
        ).filter(
            (review_genres.c.review_count > 0) | 
            (favorite_genres.c.favorite_count > 0)
        ).order_by(
            desc('total_interactions'),
            desc('reviews'),
            desc('favorites')
        ).limit(limit)
        
        results = combined_query.all()
        
        return [
            {
                'genre_id': str(row.id),
                'genre_name': row.name,
                'review_count': row.reviews,
                'favorite_count': row.favorites,
                'interaction_count': row.total_interactions
            }
            for row in results
        ]