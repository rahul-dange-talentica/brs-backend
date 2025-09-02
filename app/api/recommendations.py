"""Recommendation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.genre import Genre
from app.schemas.book import BookSummary, BookResponse
from app.schemas.recommendation import RecommendationResponse
from app.core.auth import get_current_user, get_optional_current_user
from app.core.recommendations import (
    PopularRecommendationEngine,
    GenreRecommendationEngine,
    PersonalRecommendationEngine
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/popular", response_model=List[BookSummary])
async def get_popular_recommendations(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of books to return"),
    genre_id: Optional[str] = Query(None, description="Filter by specific genre"),
    min_reviews: int = Query(5, ge=1, description="Minimum number of reviews required"),
    days_back: Optional[int] = Query(None, ge=1, le=365, description="Only consider books from last N days"),
    db: Session = Depends(get_db)
):
    """
    Get popular book recommendations based on ratings and review counts.
    
    Uses a sophisticated popularity algorithm that balances rating quality with review quantity
    to prevent books with very few high ratings from dominating the recommendations.
    """
    try:
        engine = PopularRecommendationEngine(db)
        books = await engine.get_popular_books(
            limit=limit,
            genre_id=genre_id,
            min_reviews=min_reviews,
            days_back=days_back
        )
        
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating popular recommendations: {str(e)}"
        )


@router.get("/trending", response_model=List[BookSummary])
async def get_trending_recommendations(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of books to return"),
    days_back: int = Query(30, ge=1, le=365, description="Period to analyze for trending"),
    min_reviews_in_period: int = Query(3, ge=1, description="Minimum reviews in the period"),
    db: Session = Depends(get_db)
):
    """
    Get trending book recommendations based on recent review activity.
    
    Books are ranked by recent review activity and rating quality within the specified time period.
    """
    try:
        engine = PopularRecommendationEngine(db)
        books = await engine.get_trending_books(
            limit=limit,
            days_back=days_back,
            min_reviews_in_period=min_reviews_in_period
        )
        
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating trending recommendations: {str(e)}"
        )


@router.get("/genre/{genre_id}", response_model=List[BookSummary])
async def get_genre_recommendations(
    genre_id: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of books to return"),
    exclude_user_books: bool = Query(True, description="Exclude books user has already reviewed/favorited"),
    min_rating: float = Query(0.0, ge=0.0, le=5.0, description="Minimum average rating threshold"),
    min_reviews: int = Query(1, ge=1, description="Minimum number of reviews required"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendations for a specific genre.
    
    Returns top-rated books within the specified genre, optionally excluding books
    the authenticated user has already reviewed or favorited.
    """
    # Verify genre exists
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with ID {genre_id} not found"
        )
    
    try:
        engine = GenreRecommendationEngine(db)
        books = await engine.get_genre_books(
            genre_id=genre_id,
            limit=limit,
            exclude_user_id=str(current_user.id) if (current_user and exclude_user_books) else None,
            min_rating=min_rating,
            min_reviews=min_reviews
        )
        
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating genre recommendations: {str(e)}"
        )


@router.get("/genre/{genre_id}/similar-to/{book_id}", response_model=List[BookSummary])
async def get_similar_books_in_genre(
    genre_id: str,
    book_id: str,
    limit: int = Query(20, ge=1, le=50, description="Maximum number of books to return"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get books similar to a specific book within a genre.
    
    Finds books that share genres with the specified book and are highly rated.
    """
    # Verify genre exists
    genre = db.query(Genre).filter(Genre.id == genre_id).first()
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Genre with ID {genre_id} not found"
        )
    
    try:
        engine = GenreRecommendationEngine(db)
        books = await engine.get_similar_genre_books(
            book_id=book_id,
            limit=limit,
            exclude_user_id=str(current_user.id) if current_user else None
        )
        
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating similar book recommendations: {str(e)}"
        )


@router.get("/personal", response_model=RecommendationResponse)
async def get_personal_recommendations(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of books to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations based on user's preferences and history.
    
    Uses a combination of:
    - User's favorite genres and high-rated books
    - Collaborative filtering based on similar users
    - Fallback to popular recommendations for new users
    
    Requires authentication.
    """
    try:
        engine = PersonalRecommendationEngine(db)
        result = await engine.get_personal_recommendations(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return RecommendationResponse(
            books=result['books'],
            recommendation_type=result['recommendation_type'],
            explanation=result['explanation']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating personal recommendations: {str(e)}"
        )


@router.get("/diversity", response_model=List[BookSummary])
async def get_diverse_recommendations(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of books to return"),
    genre_count: int = Query(5, ge=2, le=10, description="Number of different genres to include"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Get diverse recommendations across multiple genres.
    
    Returns recommendations that span multiple genres to provide reading variety.
    If user is authenticated, considers their preferences.
    """
    try:
        if current_user:
            # Get user's preferred genres for diversity
            engine = PersonalRecommendationEngine(db)
            user_prefs = await engine._analyze_user_preferences(str(current_user.id))
            
            if user_prefs['has_activity'] and user_prefs['favorite_genres']:
                genre_engine = GenreRecommendationEngine(db)
                books = await genre_engine.get_genre_diversity_recommendations(
                    preferred_genres=user_prefs['favorite_genres'][:genre_count],
                    limit=limit,
                    exclude_user_id=str(current_user.id)
                )
                return books
        
        # For non-authenticated users or users without preferences,
        # get diverse popular books across different genres
        
        # Get top genres
        top_genres = db.query(Genre).limit(genre_count).all()
        genre_ids = [str(g.id) for g in top_genres]
        
        genre_engine = GenreRecommendationEngine(db)
        books = await genre_engine.get_genre_diversity_recommendations(
            preferred_genres=genre_ids,
            limit=limit,
            exclude_user_id=str(current_user.id) if current_user else None
        )
        
        return books
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating diverse recommendations: {str(e)}"
        )
