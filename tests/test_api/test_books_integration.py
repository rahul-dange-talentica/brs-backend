import pytest
from fastapi import status
from decimal import Decimal


class TestBooksAPI:
    """Test Books API integration."""
    
    def test_get_books_success(self, client, sample_books):
        """Test successful books listing."""
        response = client.get("/api/v1/books")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "books" in data
        assert "total" in data
        assert "pages" in data
        assert len(data["books"]) > 0
        
        # Check book structure
        book = data["books"][0]
        assert "id" in book
        assert "title" in book
        assert "author" in book
        assert "average_rating" in book
        assert "total_reviews" in book
    
    def test_get_books_pagination(self, client, sample_books):
        """Test books pagination."""
        # First page
        response = client.get("/api/v1/books?limit=3&skip=0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["books"]) <= 3
        assert data["skip"] == 0
        
        # Second page
        response = client.get("/api/v1/books?limit=3&skip=3")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["skip"] == 3
    
    def test_get_books_genre_filter(self, client, sample_books, test_genre):
        """Test books filtering by genre."""
        response = client.get(f"/api/v1/books?genre_id={test_genre.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All returned books should have the specified genre
        for book in data["books"]:
            genre_ids = [genre["id"] for genre in book.get("genres", [])]
            assert str(test_genre.id) in genre_ids
    
    def test_get_books_rating_filter(self, client, sample_books):
        """Test books filtering by minimum rating."""
        response = client.get("/api/v1/books?min_rating=4.0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # All returned books should have rating >= 4.0
        for book in data["books"]:
            assert float(book["average_rating"]) >= 4.0
    
    def test_get_books_sorting(self, client, sample_books):
        """Test books sorting."""
        # Sort by rating (highest first)
        response = client.get("/api/v1/books?sort_by=average_rating&sort_order=desc")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        books = data["books"]
        if len(books) > 1:
            # Check that books are sorted by rating descending
            for i in range(len(books) - 1):
                assert float(books[i]["average_rating"]) >= float(books[i + 1]["average_rating"])
    
    def test_get_book_by_id_success(self, client, test_book):
        """Test successful book retrieval by ID."""
        response = client.get(f"/api/v1/books/{test_book.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(test_book.id)
        assert data["title"] == test_book.title
        assert data["author"] == test_book.author
        assert "genres" in data
        assert "recent_reviews" in data
    
    def test_get_book_by_id_not_found(self, client):
        """Test book retrieval with non-existent ID."""
        import uuid
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/v1/books/{fake_id}")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Book not found" in response.json()["detail"]
    
    def test_get_book_by_id_invalid_uuid(self, client):
        """Test book retrieval with invalid UUID."""
        response = client.get("/api/v1/books/invalid-uuid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_books_success(self, client, sample_books):
        """Test successful book search."""
        response = client.get("/api/v1/books/search?q=sample")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "books" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "sample"
        
        # Search results should contain the query term
        for book in data["books"]:
            search_text = f"{book['title']} {book['author']} {book.get('description', '')}".lower()
            assert "sample" in search_text
    
    def test_search_books_by_title(self, client, test_book):
        """Test book search by title."""
        # Search for part of the book title
        search_term = test_book.title.split()[0] if " " in test_book.title else test_book.title[:3]
        response = client.get(f"/api/v1/books/search?q={search_term}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should find our test book
        book_ids = [book["id"] for book in data["books"]]
        assert str(test_book.id) in book_ids
    
    def test_search_books_by_author(self, client, test_book):
        """Test book search by author."""
        # Search for part of the author name
        search_term = test_book.author.split()[0] if " " in test_book.author else test_book.author[:3]
        response = client.get(f"/api/v1/books/search?q={search_term}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should find our test book
        book_ids = [book["id"] for book in data["books"]]
        assert str(test_book.id) in book_ids
    
    def test_search_books_empty_query(self, client):
        """Test book search with empty query."""
        response = client.get("/api/v1/books/search?q=")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        # Empty query should be rejected due to min_length validation
    
    def test_search_books_no_results(self, client):
        """Test book search with no matching results."""
        response = client.get("/api/v1/books/search?q=nonexistentbookquery12345")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["books"] == []
        assert data["total"] == 0
    
    def test_search_books_pagination(self, client, sample_books):
        """Test book search with pagination."""
        response = client.get("/api/v1/books/search?q=book&limit=2&skip=0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["books"]) <= 2
        assert "pages" in data
        assert "query" in data


class TestBooksValidation:
    """Test Books API validation."""
    
    def test_get_books_invalid_limit(self, client):
        """Test books listing with invalid limit."""
        response = client.get("/api/v1/books?limit=-1")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_books_invalid_skip(self, client):
        """Test books listing with invalid skip."""
        response = client.get("/api/v1/books?skip=-1")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_books_invalid_min_rating(self, client):
        """Test books listing with invalid min_rating."""
        response = client.get("/api/v1/books?min_rating=6.0")  # Should be max 5.0
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_books_invalid_sort_by(self, client):
        """Test books listing with invalid sort_by."""
        response = client.get("/api/v1/books?sort_by=invalid_field")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_books_invalid_sort_order(self, client):
        """Test books listing with invalid sort_order."""
        response = client.get("/api/v1/books?sort_order=invalid")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_search_books_invalid_limit(self, client):
        """Test book search with invalid limit."""
        response = client.get("/api/v1/books/search?q=test&limit=0")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestBooksPerformance:
    """Test Books API performance characteristics."""
    
    def test_books_response_time(self, client, sample_books):
        """Test that books listing responds quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/books?limit=50")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds
    
    def test_search_response_time(self, client, sample_books):
        """Test that book search responds quickly."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/books/search?q=test&limit=20")
        end_time = time.time()
        
        assert response.status_code == status.HTTP_200_OK
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds


class TestBooksEdgeCases:
    """Test Books API edge cases."""
    
    def test_get_books_large_limit(self, client, sample_books):
        """Test books listing with very large limit."""
        response = client.get("/api/v1/books?limit=1000")
        
        # Should reject limits over 100
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_books_large_skip(self, client, sample_books):
        """Test books listing with skip beyond available books."""
        response = client.get("/api/v1/books?skip=10000")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Should return empty results
        assert data["books"] == []
    
    def test_search_special_characters(self, client, sample_books):
        """Test book search with special characters."""
        special_queries = ["book+author", "book&test", "book/test", "book.test"]
        
        for query in special_queries:
            response = client.get(f"/api/v1/books/search?q={query}")
            
            assert response.status_code == status.HTTP_200_OK
            # Should not crash, even if no results
    
    def test_concurrent_book_requests(self, client, sample_books):
        """Test handling concurrent book requests."""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/books?limit=5")
        
        # Make 5 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
