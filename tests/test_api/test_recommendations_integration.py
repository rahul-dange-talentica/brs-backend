import pytest
from fastapi import status


class TestPopularRecommendationsAPI:
    """Test Popular Recommendations API integration."""
    
    def test_get_popular_recommendations_success(self, client, sample_books):
        """Test successful popular recommendations retrieval."""
        response = client.get("/api/v1/recommendations/popular")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert "recommendation_type" in data
        assert "total" in data
        assert data["recommendation_type"] == "popular"
        
        # Check recommendation structure
        if len(data["recommendations"]) > 0:
            rec = data["recommendations"][0]
            assert "id" in rec
            assert "title" in rec
            assert "author" in rec
            assert "average_rating" in rec
            assert "total_reviews" in rec
    
    def test_get_popular_recommendations_with_limit(self, client, sample_books):
        """Test popular recommendations with custom limit."""
        response = client.get("/api/v1/recommendations/popular?limit=5")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["recommendations"]) <= 5
    
    def test_get_popular_recommendations_with_genre(self, client, sample_books, test_genre):
        """Test popular recommendations filtered by genre."""
        response = client.get(f"/api/v1/recommendations/popular?genre_id={test_genre.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All recommendations should be from the specified genre
        for book in data["recommendations"]:
            genre_ids = [genre["id"] for genre in book.get("genres", [])]
            assert str(test_genre.id) in genre_ids
    
    def test_get_popular_recommendations_invalid_limit(self, client):
        """Test popular recommendations with invalid limit."""
        response = client.get("/api/v1/recommendations/popular?limit=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_popular_recommendations_invalid_genre(self, client):
        """Test popular recommendations with invalid genre ID."""
        response = client.get("/api/v1/recommendations/popular?genre_id=invalid-uuid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGenreRecommendationsAPI:
    """Test Genre Recommendations API integration."""
    
    def test_get_genre_recommendations_success(self, client, sample_books, test_genre):
        """Test successful genre recommendations retrieval."""
        response = client.get(f"/api/v1/recommendations/genre/{test_genre.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert "recommendation_type" in data
        assert "genre" in data
        assert data["recommendation_type"] == "genre-based"
        assert data["genre"]["id"] == str(test_genre.id)
        assert data["genre"]["name"] == test_genre.name
    
    def test_get_genre_recommendations_with_limit(self, client, test_genre):
        """Test genre recommendations with custom limit."""
        response = client.get(f"/api/v1/recommendations/genre/{test_genre.id}?limit=3")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["recommendations"]) <= 3
    
    def test_get_genre_recommendations_nonexistent_genre(self, client):
        """Test genre recommendations for non-existent genre."""
        import uuid
        fake_genre_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/recommendations/genre/{fake_genre_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Genre not found" in response.json()["detail"]
    
    def test_get_genre_recommendations_invalid_uuid(self, client):
        """Test genre recommendations with invalid UUID."""
        response = client.get("/api/v1/recommendations/genre/invalid-uuid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_genre_recommendations_user_exclusion(self, client, test_genre, auth_headers, test_review):
        """Test genre recommendations excluding user's books."""
        response = client.get(f"/api/v1/recommendations/genre/{test_genre.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # User's reviewed books should not be in recommendations
        book_ids = [book["id"] for book in data["recommendations"]]
        assert str(test_review.book_id) not in book_ids


class TestPersonalRecommendationsAPI:
    """Test Personal Recommendations API integration."""
    
    def test_get_personal_recommendations_success(self, client, auth_headers, test_review):
        """Test successful personal recommendations retrieval."""
        response = client.get("/api/v1/recommendations/personal", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert "recommendation_type" in data
        assert "explanation" in data
        
        # Should be personal or popular (if no activity)
        assert data["recommendation_type"] in ["personal", "popular"]
    
    def test_get_personal_recommendations_with_limit(self, client, auth_headers):
        """Test personal recommendations with custom limit."""
        response = client.get("/api/v1/recommendations/personal?limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["recommendations"]) <= 5
    
    def test_get_personal_recommendations_unauthorized(self, client):
        """Test personal recommendations without authentication."""
        response = client.get("/api/v1/recommendations/personal")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_personal_recommendations_new_user(self, client, test_user2, auth_headers2):
        """Test personal recommendations for user with no activity."""
        response = client.get("/api/v1/recommendations/personal", headers=auth_headers2)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should fall back to popular recommendations
        assert data["recommendation_type"] == "popular"
        assert "new to the platform" in data["explanation"].lower() or "popular" in data["explanation"].lower()
    
    def test_get_personal_recommendations_invalid_limit(self, client, auth_headers):
        """Test personal recommendations with invalid limit."""
        response = client.get("/api/v1/recommendations/personal?limit=0", headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestTrendingRecommendationsAPI:
    """Test Trending Recommendations API integration."""
    
    def test_get_trending_recommendations_success(self, client, sample_books):
        """Test successful trending recommendations retrieval."""
        response = client.get("/api/v1/recommendations/trending")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "recommendations" in data
        assert "recommendation_type" in data
        assert data["recommendation_type"] == "trending"
    
    def test_get_trending_recommendations_with_limit(self, client):
        """Test trending recommendations with custom limit."""
        response = client.get("/api/v1/recommendations/trending?limit=3")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["recommendations"]) <= 3
    
    def test_get_trending_recommendations_with_days(self, client):
        """Test trending recommendations with custom days period."""
        response = client.get("/api/v1/recommendations/trending?days=7")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should work even if no trending books in the period
        assert "recommendations" in data
    
    def test_get_trending_recommendations_invalid_params(self, client):
        """Test trending recommendations with invalid parameters."""
        # Invalid limit
        response = client.get("/api/v1/recommendations/trending?limit=-1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Invalid days
        response = client.get("/api/v1/recommendations/trending?days_back=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRecommendationsValidation:
    """Test Recommendations API validation."""
    
    def test_recommendations_limit_bounds(self, client):
        """Test recommendation limit boundary validation."""
        # Test minimum limit
        response = client.get("/api/v1/recommendations/popular?limit=1")
        assert response.status_code == status.HTTP_200_OK
        
        # Test maximum limit
        response = client.get("/api/v1/recommendations/popular?limit=100")
        assert response.status_code == status.HTTP_200_OK
        
        # Test over maximum
        response = client.get("/api/v1/recommendations/popular?limit=101")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_genre_id_validation(self, client):
        """Test genre ID validation in recommendations."""
        invalid_uuids = [
            "not-a-uuid",
            "123456",
            "abc-def-ghi",
            "",
        ]
        
        for invalid_uuid in invalid_uuids:
            response = client.get(f"/api/v1/recommendations/genre/{invalid_uuid}")
            # FastAPI can return either 404 or 422 for invalid UUID path parameters
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_trending_days_validation(self, client):
        """Test trending days parameter validation."""
        # Valid days
        response = client.get("/api/v1/recommendations/trending?days_back=30")
        assert response.status_code == status.HTTP_200_OK
        
        # Invalid days (too small)
        response = client.get("/api/v1/recommendations/trending?days_back=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Invalid days (too large)
        response = client.get("/api/v1/recommendations/trending?days_back=366")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestRecommendationsPerformance:
    """Test Recommendations API performance."""
    
    def test_popular_recommendations_performance(self, client, sample_books):
        """Test popular recommendations response time."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/recommendations/popular?limit=20")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 3.0  # Should respond within 3 seconds
    
    def test_genre_recommendations_performance(self, client, test_genre):
        """Test genre recommendations response time."""
        import time
        
        start_time = time.time()
        response = client.get(f"/api/v1/recommendations/genre/{test_genre.id}?limit=20")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 3.0  # Should respond within 3 seconds
    
    def test_personal_recommendations_performance(self, client, auth_headers):
        """Test personal recommendations response time."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/recommendations/personal?limit=20", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 5.0  # Personal recs may take longer


class TestRecommendationsEdgeCases:
    """Test Recommendations API edge cases."""
    
    def test_recommendations_empty_database(self, client, db_session):
        """Test recommendations when no books exist."""
        # Note: This would require clearing the database, which might not be safe
        # in this test context. Instead, test with very restrictive filters
        
        response = client.get("/api/v1/recommendations/popular?min_reviews=10000")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return empty recommendations gracefully
        assert data["recommendations"] == []
    
    def test_genre_recommendations_no_books(self, client, db_session):
        """Test genre recommendations for genre with no books."""
        from app.models.genre import Genre
        
        # Create a genre with no books
        empty_genre = Genre(name="Empty Genre", description="No books here")
        db_session.add(empty_genre)
        db_session.commit()
        
        response = client.get(f"/api/v1/recommendations/genre/{empty_genre.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return empty recommendations gracefully
        assert data["recommendations"] == []
    
    def test_concurrent_recommendation_requests(self, client, sample_books):
        """Test handling concurrent recommendation requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/recommendations/popular?limit=5")
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
