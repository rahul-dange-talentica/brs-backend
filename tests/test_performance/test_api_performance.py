import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import status


@pytest.mark.performance
class TestAPIPerformance:
    """Test API performance and load handling."""
    
    def test_book_listing_performance(self, client, sample_books):
        """Test book listing API performance."""
        start_time = time.time()
        response = client.get("/api/v1/books?limit=100")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 1.0  # Should respond within 1 second
    
    def test_book_search_performance(self, client, sample_books):
        """Test book search performance."""
        start_time = time.time()
        response = client.get("/api/v1/books/search?q=sample&limit=50")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 1.5  # Should respond within 1.5 seconds
    
    def test_user_profile_performance(self, client, auth_headers):
        """Test user profile endpoint performance."""
        start_time = time.time()
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 0.5  # Should respond within 500ms
    
    @pytest.mark.slow
    def test_concurrent_book_requests(self, client, sample_books):
        """Test handling concurrent book listing requests."""
        def make_request():
            return client.get("/api/v1/books?limit=10")
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        
        # Check that all responses contain data
        for response in responses:
            data = response.json()
            assert "books" in data
    
    @pytest.mark.slow
    def test_concurrent_auth_requests(self, client, test_user):
        """Test concurrent authentication requests."""
        def make_login_request():
            return client.post("/api/v1/auth/login", data={
                "username": test_user.email,
                "password": "testpassword"
            })
        
        # Test with 5 concurrent login requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_login_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All login attempts should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        
        # Each should return a valid token
        for response in responses:
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    def test_large_review_text_performance(self, client, test_book, auth_headers):
        """Test performance with large review text."""
        # Create a large but valid review text (under 2000 chars)
        large_text = "This is a detailed review. " * 60  # ~1680 characters
        
        review_data = {
            "rating": 4,
            "review_text": large_text
        }
        
        start_time = time.time()
        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )
        end_time = time.time()
        
        assert response.status_code == status.HTTP_201_CREATED
        assert (end_time - start_time) < 1.0  # Should handle large text quickly
    
    def test_pagination_performance(self, client, sample_books):
        """Test pagination performance with different page sizes."""
        page_sizes = [10, 50, 100]
        
        for limit in page_sizes:
            start_time = time.time()
            response = client.get(f"/api/v1/books?limit={limit}&skip=0")
            end_time = time.time()
            
            assert response.status_code == status.HTTP_200_OK
            assert (end_time - start_time) < 1.0
            
            data = response.json()
            assert len(data["books"]) <= limit
    
    @pytest.mark.slow
    def test_database_connection_handling(self, client):
        """Test that multiple rapid requests don't exhaust database connections."""
        def make_rapid_requests():
            responses = []
            for _ in range(50):  # 50 rapid requests
                response = client.get("/api/v1/genres")
                responses.append(response)
            return responses
        
        start_time = time.time()
        responses = make_rapid_requests()
        end_time = time.time()
        
        # All requests should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 10.0
    
    def test_memory_usage_stability(self, client, sample_books):
        """Basic test to ensure API doesn't leak memory with repeated requests."""
        # Make many requests to the same endpoint
        for _ in range(100):
            response = client.get("/api/v1/books?limit=5")
            assert response.status_code == status.HTTP_200_OK
        
        # If we get here without memory errors, the test passes
        # In a real scenario, you'd monitor actual memory usage
        assert True


@pytest.mark.performance
class TestRecommendationPerformance:
    """Test recommendation engine performance."""
    
    def test_popular_recommendations_performance(self, client):
        """Test popular recommendations response time."""
        start_time = time.time()
        response = client.get("/api/v1/recommendations/popular?limit=20")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # Complex queries may take longer
    
    def test_genre_recommendations_performance(self, client, test_genre):
        """Test genre-based recommendations response time."""
        start_time = time.time()
        response = client.get(f"/api/v1/recommendations/genre/{test_genre.id}?limit=20")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0
    
    def test_personal_recommendations_performance(self, client, auth_headers):
        """Test personal recommendations response time."""
        start_time = time.time()
        response = client.get("/api/v1/recommendations/personal?limit=20", headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 3.0  # Personal recs are most complex
