import pytest
from fastapi import status


class TestUserProfileAPI:
    """Test User Profile API integration."""
    
    def test_get_profile_success(self, client, auth_headers, test_user):
        """Test successful profile retrieval."""
        response = client.get("/api/v1/users/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["id"] == str(test_user.id)
        assert data["email"] == test_user.email
        assert data["first_name"] == test_user.first_name
        assert data["last_name"] == test_user.last_name
        assert data["is_active"] == test_user.is_active
        assert "created_at" in data
        assert "updated_at" in data
        
        # Password should not be in response
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_get_profile_unauthorized(self, client):
        """Test profile retrieval without authentication."""
        response = client.get("/api/v1/users/profile")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_profile_invalid_token(self, client):
        """Test profile retrieval with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/users/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_update_profile_success(self, client, auth_headers, test_user, db_session):
        """Test successful profile update."""
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["first_name"] == "Updated"
        assert data["last_name"] == "Name"
        assert data["email"] == "updated@example.com"
        
        # Verify in database
        db_session.refresh(test_user)
        assert test_user.first_name == "Updated"
        assert test_user.last_name == "Name"
        assert test_user.email == "updated@example.com"
    
    def test_update_profile_partial(self, client, auth_headers, test_user, db_session):
        """Test partial profile update."""
        original_email = test_user.email
        update_data = {
            "first_name": "OnlyFirstName"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["first_name"] == "OnlyFirstName"
        assert data["email"] == original_email  # Should remain unchanged
    
    def test_update_profile_invalid_email(self, client, auth_headers):
        """Test profile update with invalid email."""
        update_data = {
            "email": "invalid_email"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_profile_duplicate_email(self, client, auth_headers, test_user2):
        """Test profile update with existing email."""
        update_data = {
            "email": test_user2.email
        }
        
        response = client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_update_profile_unauthorized(self, client):
        """Test profile update without authentication."""
        update_data = {
            "first_name": "Unauthorized"
        }
        
        response = client.put("/api/v1/users/profile", json=update_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserFavoritesAPI:
    """Test User Favorites API integration."""
    
    def test_get_favorites_empty(self, client, auth_headers):
        """Test getting favorites when user has none."""
        response = client.get("/api/v1/users/favorites", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["favorites"] == []
        assert data["total"] == 0
    
    def test_add_favorite_success(self, client, auth_headers, test_book, db_session):
        """Test successfully adding a book to favorites."""
        response = client.post(f"/api/v1/users/favorites/{test_book.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["message"] == "Book added to favorites"
    
    def test_add_favorite_duplicate(self, client, auth_headers, test_favorite):
        """Test adding a book that's already in favorites."""
        response = client.post(f"/api/v1/users/favorites/{test_favorite.book_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already in favorites" in response.json()["detail"]
    
    def test_add_favorite_nonexistent_book(self, client, auth_headers):
        """Test adding non-existent book to favorites."""
        import uuid
        fake_book_id = str(uuid.uuid4())
        
        response = client.post(f"/api/v1/users/favorites/{fake_book_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Book not found" in response.json()["detail"]
    
    def test_add_favorite_unauthorized(self, client, test_book):
        """Test adding favorite without authentication."""
        response = client.post(f"/api/v1/users/favorites/{test_book.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_remove_favorite_success(self, client, auth_headers, test_favorite, db_session):
        """Test successfully removing a book from favorites."""
        response = client.delete(f"/api/v1/users/favorites/{test_favorite.book_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_remove_favorite_not_in_favorites(self, client, auth_headers, test_book):
        """Test removing a book that's not in favorites."""
        response = client.delete(f"/api/v1/users/favorites/{test_book.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not in favorites" in response.json()["detail"]
    
    def test_remove_favorite_unauthorized(self, client, test_book):
        """Test removing favorite without authentication."""
        response = client.delete(f"/api/v1/users/favorites/{test_book.id}")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_favorites_with_data(self, client, auth_headers, test_favorite):
        """Test getting favorites when user has some."""
        response = client.get("/api/v1/users/favorites", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["favorites"]) == 1
        assert data["total"] == 1
        
        favorite = data["favorites"][0]
        assert favorite["id"] == str(test_favorite.book_id)
        assert "title" in favorite
        assert "author" in favorite
        assert "created_at" in favorite
    
    def test_get_favorites_pagination(self, client, auth_headers, sample_books, test_user, db_session):
        """Test favorites pagination."""
        from app.models.user_favorite import UserFavorite
        
        # Add multiple books to favorites
        for book in sample_books[:5]:
            favorite = UserFavorite(user_id=test_user.id, book_id=book.id)
            db_session.add(favorite)
        db_session.commit()
        
        # Test pagination
        response = client.get("/api/v1/users/favorites?limit=2&skip=0", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["favorites"]) == 2
        assert data["pages"] >= 1
        assert data["total"] >= 5


class TestUserReviewsAPI:
    """Test User Reviews API integration."""
    
    def test_get_user_reviews_empty(self, client, auth_headers):
        """Test getting user reviews when they have none."""
        response = client.get("/api/v1/users/reviews", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["reviews"] == []
        assert data["total"] == 0
    
    def test_get_user_reviews_with_data(self, client, auth_headers, test_review):
        """Test getting user reviews when they have some."""
        response = client.get("/api/v1/users/reviews", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["reviews"]) == 1
        assert data["total"] == 1
        
        review = data["reviews"][0]
        assert review["id"] == str(test_review.id)
        assert review["rating"] == test_review.rating
        assert review["review_text"] == test_review.review_text
        assert "book" in review
    
    def test_get_user_reviews_pagination(self, client, auth_headers, sample_books, test_user, db_session):
        """Test user reviews pagination."""
        from app.models.review import Review
        
        # Add multiple reviews
        for i, book in enumerate(sample_books[:3]):
            review = Review(
                user_id=test_user.id, 
                book_id=book.id, 
                rating=5, 
                review_text=f"Review {i}"
            )
            db_session.add(review)
        db_session.commit()
        
        # Test pagination
        response = client.get("/api/v1/users/reviews?limit=2&skip=0", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["reviews"]) == 2
        assert data["pages"] >= 1
        assert data["total"] >= 3
    
    def test_get_user_reviews_unauthorized(self, client):
        """Test getting user reviews without authentication."""
        response = client.get("/api/v1/users/reviews")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserValidation:
    """Test User API validation."""
    
    def test_profile_update_invalid_data(self, client, auth_headers):
        """Test profile update with invalid data types."""
        invalid_updates = [
            {"first_name": 123},  # Should be string
            {"last_name": True},  # Should be string
            {"email": 12345},     # Should be string
        ]
        
        for update_data in invalid_updates:
            response = client.put("/api/v1/users/profile", json=update_data, headers=auth_headers)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_profile_update_empty_data(self, client, auth_headers):
        """Test profile update with empty data."""
        response = client.put("/api/v1/users/profile", json={}, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        # Empty update should not change anything but return current profile
    
    def test_favorites_invalid_book_id(self, client, auth_headers):
        """Test favorites operations with invalid book ID."""
        response = client.post("/api/v1/users/favorites/invalid-uuid", headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_reviews_invalid_pagination(self, client, auth_headers):
        """Test reviews with invalid pagination parameters."""
        response = client.get("/api/v1/users/reviews?limit=-1", headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
