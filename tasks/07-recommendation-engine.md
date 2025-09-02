# Task 07: Recommendation Engine

**Phase**: 2 - Core Features  
**Sequence**: 07  
**Priority**: Medium  
**Estimated Effort**: 8-10 hours  
**Dependencies**: Task 05 (Book Management), Task 06 (Review System)

---

## Objective

Implement a basic recommendation engine providing personalized and general book recommendations using rating data, user preferences, and genre associations according to technical PRD specifications.

## Scope

- Popular book recommendations (top-rated books)
- Genre-based recommendations
- Personal recommendations based on user ratings and favorites
- Basic collaborative filtering algorithm
- Performance optimization for recommendation queries
- Caching mechanism for popular recommendations

## Technical Requirements

### API Endpoints (from Technical PRD)
```
GET /recommendations/popular        # Top-rated books
GET /recommendations/genre/{id}     # Genre-based recommendations
GET /recommendations/personal       # User-based recommendations
```

### Recommendation Algorithms
- **Popular**: Books with highest average ratings and review counts
- **Genre-based**: Top books within specific genres
- **Personal**: Based on user's rating history and favorite genres
- **Collaborative filtering**: Users with similar tastes (basic implementation)

## Acceptance Criteria

### ✅ Popular Recommendations
- [ ] GET /recommendations/popular returns top-rated books
- [ ] Considers both rating average and review count for popularity score
- [ ] Pagination support for large result sets
- [ ] Filtering options (genre, publication date range)
- [ ] Performance optimized queries

### ✅ Genre-based Recommendations
- [ ] GET /recommendations/genre/{id} returns top books in specific genre
- [ ] Proper sorting by rating and popularity
- [ ] Excludes books user has already reviewed (if authenticated)
- [ ] Genre validation and error handling

### ✅ Personal Recommendations
- [ ] GET /recommendations/personal requires authentication
- [ ] Analyzes user's rating patterns and favorite genres
- [ ] Excludes books user has already reviewed/favorited
- [ ] Provides diverse recommendations across genres
- [ ] Falls back to popular recommendations for new users

### ✅ Performance & Caching
- [ ] Recommendation queries optimized with proper indexes
- [ ] Caching for popular recommendations (Redis-compatible)
- [ ] Background recommendation pre-calculation
- [ ] Response time under 1 second for all recommendation types

### ✅ Algorithm Quality
- [ ] Recommendation diversity (not all from same author/genre)
- [ ] Relevance scoring based on multiple factors
- [ ] Handles edge cases (new users, users with few ratings)
- [ ] Configurable recommendation parameters

## Implementation Details

### Recommendations API Routes (app/api/recommendations.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from app.schemas.book import BookResponse
from app.schemas.recommendation import RecommendationResponse
from app.core.auth import get_current_user
from app.core.recommendations import (
    PopularRecommendationEngine,
    GenreRecommendationEngine,
    PersonalRecommendationEngine
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/popular", response_model=List[BookResponse])
async def get_popular_recommendations(
    limit: int = Query(20, ge=1, le=100),
    genre_id: Optional[str] = Query(None),
    min_reviews: int = Query(5, ge=1),
    days_back: Optional[int] = Query(None, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get popular book recommendations based on ratings and review counts"""
    
    engine = PopularRecommendationEngine(db)
    recommendations = await engine.get_popular_books(
        limit=limit,
        genre_id=genre_id,
        min_reviews=min_reviews,
        days_back=days_back
    )
    
    return recommendations

@router.get("/genre/{genre_id}", response_model=List[BookResponse])
async def get_genre_recommendations(
    genre_id: str,
    limit: int = Query(20, ge=1, le=50),
    exclude_user_books: bool = Query(True),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommendations for a specific genre"""
    
    # Verify genre exists
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Genre not found"
        )
    
    engine = GenreRecommendationEngine(db)
    recommendations = await engine.get_genre_books(
        genre_id=genre_id,
        limit=limit,
        exclude_user_id=current_user.id if (current_user and exclude_user_books) else None
    )
    
    return recommendations

@router.get("/personal", response_model=RecommendationResponse)
async def get_personal_recommendations(
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized recommendations based on user's preferences and history"""
    
    engine = PersonalRecommendationEngine(db)
    recommendations = await engine.get_personal_recommendations(
        user_id=current_user.id,
        limit=limit
    )
    
    return recommendations
```

### Popular Recommendation Engine (app/core/recommendations/popular.py)
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Optional

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review

class PopularRecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_popular_books(
        self,
        limit: int = 20,
        genre_id: Optional[str] = None,
        min_reviews: int = 5,
        days_back: Optional[int] = None
    ) -> List[Book]:
        """Get popular books based on ratings and review counts"""
        
        # Calculate popularity score: (average_rating * review_count) / (review_count + min_reviews)
        # This balances rating quality with review quantity
        query = self.db.query(
            Book,
            ((Book.average_rating * Book.total_reviews) / (Book.total_reviews + min_reviews)).label('popularity_score')
        ).filter(
            Book.total_reviews >= min_reviews
        )
        
        # Filter by genre if specified
        if genre_id:
            query = query.filter(Book.genres.any(Genre.id == genre_id))
        
        # Filter by date range if specified
        if days_back:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(Book.created_at >= cutoff_date)
        
        # Order by popularity score
        query = query.order_by(desc('popularity_score'), desc(Book.average_rating))
        
        # Get results
        results = query.limit(limit).all()
        return [book for book, _ in results]
```

### Genre Recommendation Engine (app/core/recommendations/genre.py)
```python
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, not_
from typing import List, Optional

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite

class GenreRecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_genre_books(
        self,
        genre_id: str,
        limit: int = 20,
        exclude_user_id: Optional[str] = None
    ) -> List[Book]:
        """Get top books in a specific genre"""
        
        query = self.db.query(Book).filter(
            Book.genres.any(Genre.id == genre_id)
        )
        
        # Exclude books user has already reviewed or favorited
        if exclude_user_id:
            reviewed_books = self.db.query(Review.book_id).filter(
                Review.user_id == exclude_user_id
            ).subquery()
            
            favorited_books = self.db.query(UserFavorite.book_id).filter(
                UserFavorite.user_id == exclude_user_id
            ).subquery()
            
            query = query.filter(
                and_(
                    not_(Book.id.in_(reviewed_books)),
                    not_(Book.id.in_(favorited_books))
                )
            )
        
        # Order by rating and review count
        query = query.order_by(
            desc(Book.average_rating),
            desc(Book.total_reviews)
        )
        
        return query.limit(limit).all()
```

### Personal Recommendation Engine (app/core/recommendations/personal.py)
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, not_
from typing import List, Dict
from collections import defaultdict

from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from app.schemas.recommendation import RecommendationResponse

class PersonalRecommendationEngine:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_personal_recommendations(
        self,
        user_id: str,
        limit: int = 20
    ) -> RecommendationResponse:
        """Get personalized recommendations based on user's history"""
        
        # Get user's rating and favorite patterns
        user_preferences = await self._analyze_user_preferences(user_id)
        
        if not user_preferences['has_activity']:
            # New user - return popular recommendations
            popular_engine = PopularRecommendationEngine(self.db)
            books = await popular_engine.get_popular_books(limit=limit)
            return RecommendationResponse(
                books=books,
                recommendation_type="popular",
                explanation="Popular books since you're new to the platform"
            )
        
        # Get books user hasn't interacted with
        excluded_books = await self._get_user_excluded_books(user_id)
        
        recommendations = []
        
        # 60% from favorite genres
        genre_recommendations = await self._get_genre_based_recommendations(
            user_preferences['favorite_genres'],
            excluded_books,
            int(limit * 0.6)
        )
        recommendations.extend(genre_recommendations)
        
        # 40% from collaborative filtering
        collaborative_recommendations = await self._get_collaborative_recommendations(
            user_id,
            excluded_books,
            limit - len(recommendations)
        )
        recommendations.extend(collaborative_recommendations)
        
        return RecommendationResponse(
            books=recommendations[:limit],
            recommendation_type="personal",
            explanation="Based on your reading preferences and similar users"
        )
    
    async def _analyze_user_preferences(self, user_id: str) -> Dict:
        """Analyze user's preferences from reviews and favorites"""
        
        # Get user's genre preferences from high-rated books
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
            Review.user_id == user_id,
            Review.rating >= 4  # High ratings only
        ).group_by(Genre.id, Genre.name).order_by(
            desc('avg_rating'),
            desc('review_count')
        ).limit(5).all()
        
        has_activity = len(genre_preferences) > 0
        
        return {
            'has_activity': has_activity,
            'favorite_genres': [g.id for g in genre_preferences],
            'avg_rating': sum(g.avg_rating for g in genre_preferences) / len(genre_preferences) if genre_preferences else 0
        }
    
    async def _get_user_excluded_books(self, user_id: str) -> List[str]:
        """Get books user has already reviewed or favorited"""
        
        reviewed = self.db.query(Review.book_id).filter(Review.user_id == user_id).all()
        favorited = self.db.query(UserFavorite.book_id).filter(UserFavorite.user_id == user_id).all()
        
        excluded = set()
        excluded.update([r.book_id for r in reviewed])
        excluded.update([f.book_id for f in favorited])
        
        return list(excluded)
    
    async def _get_genre_based_recommendations(
        self,
        favorite_genres: List[str],
        excluded_books: List[str],
        limit: int
    ) -> List[Book]:
        """Get recommendations from user's favorite genres"""
        
        if not favorite_genres:
            return []
        
        query = self.db.query(Book).filter(
            Book.genres.any(Genre.id.in_(favorite_genres))
        )
        
        if excluded_books:
            query = query.filter(not_(Book.id.in_(excluded_books)))
        
        return query.order_by(
            desc(Book.average_rating),
            desc(Book.total_reviews)
        ).limit(limit).all()
    
    async def _get_collaborative_recommendations(
        self,
        user_id: str,
        excluded_books: List[str],
        limit: int
    ) -> List[Book]:
        """Get recommendations based on similar users' preferences"""
        
        # Find users with similar rating patterns
        similar_users = self.db.query(
            Review.user_id,
            func.avg(func.abs(Review.rating - 4)).label('rating_similarity')  # Simplified similarity
        ).filter(
            Review.user_id != user_id
        ).group_by(Review.user_id).order_by('rating_similarity').limit(10).all()
        
        if not similar_users:
            return []
        
        similar_user_ids = [u.user_id for u in similar_users]
        
        # Get highly rated books from similar users
        query = self.db.query(Book).join(
            Review, Review.book_id == Book.id
        ).filter(
            and_(
                Review.user_id.in_(similar_user_ids),
                Review.rating >= 4
            )
        )
        
        if excluded_books:
            query = query.filter(not_(Book.id.in_(excluded_books)))
        
        return query.order_by(
            desc(Book.average_rating)
        ).limit(limit).all()
```

### Recommendation Schemas (app/schemas/recommendation.py)
```python
from pydantic import BaseModel
from typing import List

from app.schemas.book import BookResponse

class RecommendationResponse(BaseModel):
    books: List[BookResponse]
    recommendation_type: str
    explanation: str
    total_books: int = 0
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_books = len(self.books)
```

## Testing

### Unit Tests
- [ ] Popular recommendation algorithm
- [ ] Genre-based recommendation filtering
- [ ] Personal recommendation logic
- [ ] User preference analysis
- [ ] Collaborative filtering basics

### Integration Tests
- [ ] Recommendation API endpoints
- [ ] Authentication for personal recommendations
- [ ] Performance with large datasets
- [ ] Recommendation diversity and quality

### API Testing Examples
```bash
# Get popular recommendations
curl "http://localhost:8000/api/v1/recommendations/popular?limit=10&min_reviews=5"

# Get genre recommendations
curl "http://localhost:8000/api/v1/recommendations/genre/GENRE_ID?limit=10"

# Get personal recommendations (authenticated)
curl "http://localhost:8000/api/v1/recommendations/personal?limit=20" \
  -H "Authorization: Bearer TOKEN"
```

## Definition of Done

- [ ] All recommendation endpoints implemented
- [ ] Popular recommendation algorithm working
- [ ] Genre-based recommendations functional
- [ ] Personal recommendations with user analysis
- [ ] Basic collaborative filtering implemented
- [ ] Performance optimized (<1 second response time)
- [ ] Recommendation diversity ensured
- [ ] Comprehensive test suite (80%+ coverage)
- [ ] API documentation complete
- [ ] Handles edge cases (new users, no data)

## Next Steps

After completion, this task enables:
- **Task 08**: Testing & Code Quality (recommendation testing)
- Complete user engagement features
- Analytics and recommendation improvement

## Notes

- Consider implementing more sophisticated algorithms (matrix factorization)
- Monitor recommendation click-through rates for algorithm improvement
- Implement A/B testing for recommendation algorithms
- Consider caching popular recommendations with Redis
- Plan for recommendation explanation features
