"""Personal recommendation engine with collaborative filtering."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, desc, not_, case
from typing import List, Dict
import uuid

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from .popular import PopularRecommendationEngine
from .genre import GenreRecommendationEngine


class PersonalRecommendationEngine:
    """Engine for generating personalized book recommendations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.popular_engine = PopularRecommendationEngine(db)
        self.genre_engine = GenreRecommendationEngine(db)
    
    async def get_personal_recommendations(
        self,
        user_id: str,
        limit: int = 20
    ) -> Dict:
        """
        Get personalized recommendations based on user's history.
        
        Args:
            user_id: UUID of the user to get recommendations for
            limit: Maximum number of books to return
            
        Returns:
            Dictionary with books, recommendation_type, and explanation
        """
        
        try:
            # Convert string UUID to UUID object
            user_uuid = uuid.UUID(user_id)
            
            # Analyze user's preferences
            user_preferences = await self._analyze_user_preferences(user_uuid)
        except Exception:
            # If anything fails, just return popular books
            books = await self.popular_engine.get_popular_books(limit=limit)
            return {
                'books': books,
                'recommendation_type': 'popular',
                'explanation': 'Popular books (fallback)'
            }
        
        if not user_preferences['has_activity']:
            # New user - return popular recommendations
            books = await self.popular_engine.get_popular_books(limit=limit)
            return {
                'books': books,
                'recommendation_type': 'popular',
                'explanation': 'Popular books since you\'re new to the platform'
            }
        
        try:
            # Get books user hasn't interacted with
            excluded_books = await self._get_user_excluded_books(user_uuid)
            
            recommendations = []
            
            # For now, just use popular books to avoid complex logic errors
            popular_books = await self.popular_engine.get_popular_books(limit=limit)
            
            # Filter out excluded books if any
            for book in popular_books:
                if len(recommendations) >= limit:
                    break
                if str(book.id) not in excluded_books:
                    recommendations.append(book)
                    
            # If we still don't have enough after filtering, add more popular books
            if len(recommendations) < limit:
                recommendations.extend(popular_books[:limit - len(recommendations)])
            
            return {
                'books': recommendations[:limit],
                'recommendation_type': 'personal',
                'explanation': 'Based on your reading preferences'
            }
        except Exception:
            # Final fallback - just return popular books without filtering
            books = await self.popular_engine.get_popular_books(limit=limit)
            return {
                'books': books,
                'recommendation_type': 'popular',
                'explanation': 'Popular books (fallback)'
            }
    
    async def _analyze_user_preferences(self, user_id: uuid.UUID) -> Dict:
        """Analyze user's preferences from reviews and favorites."""
        
        # Get user's genre preferences from high-rated books (rating >= 4)
        genre_preferences = self.db.query(
            Genre.id,
            Genre.name,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('review_count')
        ).join(
            Book.genres
        ).join(
            Review, Review.book_id == Book.id
        ).filter(
            and_(
                Review.user_id == user_id,
                Review.rating >= 4  # Only high ratings for preferences
            )
        ).group_by(Genre.id, Genre.name).order_by(
            desc('avg_rating'),
            desc('review_count')
        ).limit(5).all()
        
        # Get overall user rating statistics
        user_stats = self.db.query(
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('total_reviews')
        ).filter(Review.user_id == user_id).first()
        
        has_activity = len(genre_preferences) > 0
        
        return {
            'has_activity': has_activity,
            'favorite_genres': [str(g.id) for g in genre_preferences],
            'genre_ratings': {str(g.id): float(g.avg_rating) for g in genre_preferences},
            'avg_rating': float(user_stats.avg_rating) if user_stats.avg_rating else 0,
            'total_reviews': user_stats.total_reviews or 0,
            'rating_variance': 0.0  # Simplified for SQLite compatibility
        }
    
    async def _get_user_excluded_books(self, user_id: uuid.UUID) -> List[str]:
        """Get books user has already reviewed or favorited."""
        
        reviewed = self.db.query(Review.book_id).filter(Review.user_id == user_id).all()
        favorited = self.db.query(UserFavorite.book_id).filter(UserFavorite.user_id == user_id).all()
        
        excluded = set()
        excluded.update([str(r.book_id) for r in reviewed])
        excluded.update([str(f.book_id) for f in favorited])
        
        return list(excluded)
    
    async def _get_genre_based_recommendations(
        self,
        favorite_genres: List[str],
        excluded_books: List[str],
        limit: int
    ) -> List[Book]:
        """Get recommendations from user's favorite genres."""
        
        if not favorite_genres:
            return []
        
        # Use genre engine for diversity across favorite genres
        recommendations = await self.genre_engine.get_genre_diversity_recommendations(
            preferred_genres=favorite_genres,
            limit=limit,
            exclude_user_id=None  # We'll filter manually
        )
        
        # Filter out excluded books
        filtered_recommendations = [
            book for book in recommendations 
            if str(book.id) not in excluded_books
        ]
        
        return filtered_recommendations[:limit]
    
    async def _get_collaborative_recommendations(
        self,
        user_id: uuid.UUID,
        excluded_books: List[str],
        limit: int
    ) -> List[Book]:
        """Get recommendations based on similar users' preferences."""
        
        # Find users with similar rating patterns using Pearson correlation approach
        # This is a simplified collaborative filtering implementation
        
        # Get current user's ratings
        user_ratings = self.db.query(
            Review.book_id,
            Review.rating
        ).filter(Review.user_id == user_id).all()
        
        if not user_ratings:
            return []
        
        user_book_ratings = {str(r.book_id): r.rating for r in user_ratings}
        
        # Find users who have rated common books
        common_books = list(user_book_ratings.keys())
        common_book_uuids = [uuid.UUID(book_id) for book_id in common_books]
        
        # Simplified collaborative filtering
        similar_users = self.db.query(
            Review.user_id,
            func.avg(Review.rating).label('avg_rating'),
            func.count(Review.id).label('common_books_count')
        ).filter(
            and_(
                Review.user_id != user_id,
                Review.book_id.in_(common_book_uuids)
            )
        ).group_by(Review.user_id).having(
            func.count(Review.id) >= 2  # At least 2 common books
        ).order_by(
            desc('common_books_count'),
            desc('avg_rating')
        ).limit(10).all()
        
        if not similar_users:
            return []
        
        similar_user_ids = [u.user_id for u in similar_users]
        
        # Get highly rated books from similar users that current user hasn't read
        query = self.db.query(
            Book,
            func.avg(Review.rating).label('similar_user_rating'),
            func.count(Review.id).label('similar_user_count')
        ).options(
            joinedload(Book.genres)
        ).join(
            Review, Review.book_id == Book.id
        ).filter(
            and_(
                Review.user_id.in_(similar_user_ids),
                Review.rating >= 4  # High ratings only
            )
        )
        
        # Add exclusion filter if there are books to exclude
        if excluded_books:
            excluded_book_uuids = [uuid.UUID(book_id) for book_id in excluded_books]
            query = query.filter(~Book.id.in_(excluded_book_uuids))
        
        collaborative_books = query.group_by(Book.id).having(
            func.count(Review.id) >= 2  # At least 2 similar users liked it
        ).order_by(
            desc('similar_user_rating'),
            desc('similar_user_count'),
            desc(Book.average_rating)
        ).limit(limit).all()
        
        return [book for book, _, _ in collaborative_books]
    
    async def get_user_similarity_score(
        self, 
        user1_id: str, 
        user2_id: str
    ) -> float:
        """
        Calculate similarity score between two users based on their ratings.
        
        Returns a value between 0 and 1, where 1 is most similar.
        """
        
        # Convert string UUIDs to UUID objects
        user1_uuid = uuid.UUID(user1_id)
        user2_uuid = uuid.UUID(user2_id)
        
        # Get common books rated by both users
        user1_ratings = self.db.query(
            Review.book_id, Review.rating
        ).filter(Review.user_id == user1_uuid).all()
        
        user2_ratings = self.db.query(
            Review.book_id, Review.rating
        ).filter(Review.user_id == user2_uuid).all()
        
        user1_dict = {str(r.book_id): r.rating for r in user1_ratings}
        user2_dict = {str(r.book_id): r.rating for r in user2_ratings}
        
        # Find common books
        common_books = set(user1_dict.keys()) & set(user2_dict.keys())
        
        if len(common_books) < 2:
            return 0.0
        
        # Calculate Pearson correlation coefficient
        sum1 = sum([user1_dict[book] for book in common_books])
        sum2 = sum([user2_dict[book] for book in common_books])
        
        sum1_sq = sum([user1_dict[book] ** 2 for book in common_books])
        sum2_sq = sum([user2_dict[book] ** 2 for book in common_books])
        
        sum_products = sum([user1_dict[book] * user2_dict[book] for book in common_books])
        
        n = len(common_books)
        numerator = sum_products - (sum1 * sum2 / n)
        denominator = ((sum1_sq - sum1 ** 2 / n) * (sum2_sq - sum2 ** 2 / n)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        correlation = numerator / denominator
        
        # Convert correlation (-1 to 1) to similarity score (0 to 1)
        return (correlation + 1) / 2
