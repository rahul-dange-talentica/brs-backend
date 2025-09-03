"""Popular recommendation engine based on ratings and review counts."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review


class PopularRecommendationEngine:
    """Engine for generating popular book recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_popular_books(
        self,
        limit: int = 20,
        genre_id: Optional[str] = None,
        min_reviews: int = 5,
        days_back: Optional[int] = None
    ) -> List[Book]:
        """
        Get popular books based on ratings and review counts.
        
        Uses a popularity score formula: (average_rating * review_count) / (review_count + min_reviews)
        This balances rating quality with review quantity, preventing books with 
        very few high ratings from dominating.
        
        Args:
            limit: Maximum number of books to return
            genre_id: Optional genre filter 
            min_reviews: Minimum number of reviews required
            days_back: Only consider books from last N days
            
        Returns:
            List of Book objects sorted by popularity score
        """
        
        # Calculate popularity score using Bayesian averaging
        # Formula prevents bias toward books with very few reviews
        popularity_score = (
            (Book.average_rating * Book.total_reviews) / 
            (Book.total_reviews + min_reviews)
        ).label('popularity_score')
        
        query = self.db.query(
            Book,
            popularity_score
        ).options(
            joinedload(Book.genres)
        ).filter(
            Book.total_reviews >= min_reviews
        )
        
        # Filter by genre if specified
        if genre_id:
            # Convert string UUID to UUID object if needed
            if isinstance(genre_id, str):
                genre_uuid = uuid.UUID(genre_id)
            else:
                genre_uuid = genre_id
            query = query.filter(Book.genres.any(Genre.id == genre_uuid))
        
        # Filter by date range if specified
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(Book.created_at >= cutoff_date)
        
        # Order by popularity score, then by average rating as tiebreaker
        query = query.order_by(
            desc('popularity_score'), 
            desc(Book.average_rating),
            desc(Book.total_reviews)
        )
        
        # Get results and extract books
        results = query.limit(limit).all()
        return [book for book, _ in results]
    
    async def get_trending_books(
        self,
        limit: int = 20,
        days_back: int = 30,
        min_reviews_in_period: int = 3
    ) -> List[Book]:
        """
        Get trending books based on recent review activity.
        
        Args:
            limit: Maximum number of books to return
            days_back: Period to analyze for trending
            min_reviews_in_period: Minimum reviews in the period
            
        Returns:
            List of Book objects sorted by recent activity
        """
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get books with recent review activity
        recent_activity = self.db.query(
            Review.book_id,
            func.count(Review.id).label('recent_reviews'),
            func.avg(Review.rating).label('recent_avg_rating')
        ).filter(
            Review.created_at >= cutoff_date
        ).group_by(Review.book_id).having(
            func.count(Review.id) >= min_reviews_in_period
        ).subquery()
        
        # Join with books and calculate trending score
        trending_score = (
            recent_activity.c.recent_avg_rating * 
            func.log(recent_activity.c.recent_reviews + 1)
        ).label('trending_score')
        
        query = self.db.query(
            Book,
            trending_score
        ).options(
            joinedload(Book.genres)
        ).join(
            recent_activity, Book.id == recent_activity.c.book_id
        ).order_by(
            desc('trending_score'),
            desc(recent_activity.c.recent_avg_rating)
        )
        
        results = query.limit(limit).all()
        return [book for book, _ in results]
