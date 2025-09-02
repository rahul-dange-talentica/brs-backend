"""Recommendation response schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from .book import BookSummary


class RecommendationResponse(BaseModel):
    """Response schema for book recommendations."""
    books: List[BookSummary] = Field(description="List of recommended books")
    recommendation_type: str = Field(description="Type of recommendation algorithm used")
    explanation: str = Field(description="Human-readable explanation of why these books were recommended")
    total_books: int = Field(default=0, description="Total number of books in the recommendation")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When the recommendation was generated")
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.total_books == 0:
            self.total_books = len(self.books)
    
    class Config:
        from_attributes = True


class PopularBooksParams(BaseModel):
    """Query parameters for popular book recommendations."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of books to return")
    genre_id: Optional[str] = Field(default=None, description="Filter by specific genre")
    min_reviews: int = Field(default=5, ge=1, description="Minimum number of reviews required")
    days_back: Optional[int] = Field(default=None, ge=1, le=365, description="Only consider books from last N days")


class GenreRecommendationParams(BaseModel):
    """Query parameters for genre-based recommendations."""
    limit: int = Field(default=20, ge=1, le=50, description="Maximum number of books to return")
    exclude_user_books: bool = Field(default=True, description="Exclude books user has already reviewed/favorited")
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Minimum average rating threshold")
    min_reviews: int = Field(default=1, ge=1, description="Minimum number of reviews required")


class PersonalRecommendationParams(BaseModel):
    """Query parameters for personal recommendations."""
    limit: int = Field(default=20, ge=1, le=50, description="Maximum number of books to return")


class TrendingBooksParams(BaseModel):
    """Query parameters for trending book recommendations."""
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of books to return")
    days_back: int = Field(default=30, ge=1, le=365, description="Period to analyze for trending activity")
    min_reviews_in_period: int = Field(default=3, ge=1, description="Minimum reviews in the trending period")


class RecommendationStats(BaseModel):
    """Statistics about recommendation performance."""
    algorithm_type: str = Field(description="Type of recommendation algorithm")
    user_id: Optional[str] = Field(default=None, description="User ID for personal recommendations")
    total_candidates: int = Field(description="Total number of candidate books considered")
    filtered_candidates: int = Field(description="Number of books after filtering")
    final_recommendations: int = Field(description="Number of final recommendations returned")
    processing_time_ms: float = Field(description="Time taken to generate recommendations in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether recommendations were served from cache")
    
    class Config:
        from_attributes = True


class UserPreferenceAnalysis(BaseModel):
    """Analysis of user's reading preferences."""
    user_id: str = Field(description="User ID")
    has_activity: bool = Field(description="Whether user has any reading activity")
    total_reviews: int = Field(default=0, description="Total number of reviews by user")
    average_rating: float = Field(default=0.0, description="User's average rating")
    rating_variance: float = Field(default=0.0, description="Variance in user's ratings")
    favorite_genres: List[str] = Field(default_factory=list, description="User's preferred genre IDs")
    top_authors: List[str] = Field(default_factory=list, description="User's most-read authors")
    reading_diversity: float = Field(default=0.0, description="Diversity score of user's reading habits")
    
    class Config:
        from_attributes = True
