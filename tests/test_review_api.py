import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.models import User, Book, Review
from app.core.security import hash_password, create_access_token

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency override."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        first_name="John",
        last_name="Doe",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user2(db_session):
    """Create a second test user."""
    user = User(
        email="test2@example.com",
        password_hash=hash_password("testpassword"),
        first_name="Jane",
        last_name="Smith",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_book(db_session):
    """Create a test book."""
    book = Book(
        title="Test Book",
        author="Test Author",
        description="A test book for testing reviews",
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user."""
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers2(test_user2):
    """Create authentication headers for second test user."""
    access_token = create_access_token(data={"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestCreateReview:
    """Test review creation endpoints."""

    def test_create_review_success(self, client, test_user, test_book,
                                   auth_headers):
        """Test successful review creation."""
        review_data = {
            "rating": 5,
            "review_text": "Excellent book! Highly recommended."
        }

        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == 5
        assert data["review_text"] == "Excellent book! Highly recommended."
        assert data["user_id"] == str(test_user.id)
        assert data["book_id"] == str(test_book.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_review_no_auth(self, client, test_book):
        """Test review creation without authentication."""
        review_data = {
            "rating": 5,
            "review_text": "Great book!"
        }

        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data
        )

        assert response.status_code == 403

    def test_create_review_invalid_rating(self, client, test_book,
                                          auth_headers):
        """Test review creation with invalid rating."""
        review_data = {
            "rating": 6,  # Invalid rating (should be 1-5)
            "review_text": "Good book"
        }

        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_review_nonexistent_book(self, client, auth_headers):
        """Test review creation for non-existent book."""
        fake_book_id = str(uuid.uuid4())
        review_data = {
            "rating": 5,
            "review_text": "Great book!"
        }

        response = client.post(
            f"/api/v1/books/{fake_book_id}/reviews",
            json=review_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_create_duplicate_review(self, client, test_user, test_book,
                                     auth_headers, db_session):
        """Test creating duplicate review (should fail)."""
        # Create first review
        first_review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="First review"
        )
        db_session.add(first_review)
        db_session.commit()

        # Try to create second review
        review_data = {
            "rating": 5,
            "review_text": "Second review"
        }

        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "already reviewed" in response.json()["detail"]


class TestGetReviews:
    """Test review retrieval endpoints."""

    def test_get_book_reviews_empty(self, client, test_book):
        """Test getting reviews for book with no reviews."""
        response = client.get(f"/api/v1/books/{test_book.id}/reviews")

        assert response.status_code == 200
        data = response.json()
        assert data["reviews"] == []
        assert data["total"] == 0
        assert data["book_id"] == str(test_book.id)

    def test_get_book_reviews_with_data(self, client, test_user, test_user2,
                                        test_book, db_session):
        """Test getting reviews for book with multiple reviews."""
        # Create test reviews
        review1 = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=5,
            review_text="Excellent book!"
        )
        review2 = Review(
            user_id=test_user2.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good read"
        )
        db_session.add_all([review1, review2])
        db_session.commit()

        response = client.get(f"/api/v1/books/{test_book.id}/reviews")

        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 2
        assert data["total"] == 2
        assert data["book_id"] == str(test_book.id)

        # Check review content
        review_ratings = [r["rating"] for r in data["reviews"]]
        assert 5 in review_ratings
        assert 4 in review_ratings

    def test_get_book_reviews_pagination(self, client, test_user, test_book,
                                         db_session):
        """Test review pagination."""
        # Create multiple reviews (need multiple users for unique constraint)
        users = []
        for i in range(5):
            user = User(
                email=f"user{i}@example.com",
                password_hash=hash_password("password"),
                first_name=f"User{i}",
                is_active=True
            )
            db_session.add(user)
            users.append(user)
        db_session.commit()

        for i, user in enumerate(users):
            review = Review(
                user_id=user.id,
                book_id=test_book.id,
                rating=5,
                review_text=f"Review {i}"
            )
            db_session.add(review)
        db_session.commit()

        # Test pagination
        response = client.get(
            f"/api/v1/books/{test_book.id}/reviews?skip=0&limit=3"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 3
        assert data["total"] == 5
        assert data["pages"] == 2

    def test_get_book_reviews_rating_filter(self, client, test_user,
                                            test_user2, test_book, db_session):
        """Test filtering reviews by rating."""
        # Create reviews with different ratings
        review1 = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=5,
            review_text="Excellent!"
        )
        review2 = Review(
            user_id=test_user2.id,
            book_id=test_book.id,
            rating=3,
            review_text="Okay"
        )
        db_session.add_all([review1, review2])
        db_session.commit()

        # Filter for 5-star reviews only
        response = client.get(
            f"/api/v1/books/{test_book.id}/reviews?rating_filter=5"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 1
        assert data["reviews"][0]["rating"] == 5

    def test_get_book_reviews_nonexistent_book(self, client):
        """Test getting reviews for non-existent book."""
        fake_book_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/books/{fake_book_id}/reviews")

        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_get_review_by_id(self, client, test_user, test_book, db_session):
        """Test getting individual review by ID."""
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        response = client.get(f"/api/v1/reviews/{review.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(review.id)
        assert data["rating"] == 4
        assert data["review_text"] == "Good book"

    def test_get_review_by_id_not_found(self, client):
        """Test getting non-existent review."""
        fake_review_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/reviews/{fake_review_id}")

        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]


class TestUpdateReview:
    """Test review update endpoints."""

    def test_update_review_success(self, client, test_user, test_book,
                                   auth_headers, db_session):
        """Test successful review update."""
        # Create review
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        # Update review
        update_data = {
            "rating": 5,
            "review_text": "Actually, it's excellent!"
        }

        response = client.put(
            f"/api/v1/reviews/{review.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["review_text"] == "Actually, it's excellent!"

    def test_update_review_partial(self, client, test_user, test_book,
                                   auth_headers, db_session):
        """Test partial review update (rating only)."""
        # Create review
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        # Update only rating
        update_data = {"rating": 5}

        response = client.put(
            f"/api/v1/reviews/{review.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        assert data["review_text"] == "Good book"  # Should remain unchanged

    def test_update_review_wrong_user(self, client, test_user, test_user2,
                                      test_book, auth_headers2, db_session):
        """Test updating another user's review (should fail)."""
        # Create review by first user
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        # Try to update with second user's credentials
        update_data = {"rating": 5}

        response = client.put(
            f"/api/v1/reviews/{review.id}",
            json=update_data,
            headers=auth_headers2
        )

        assert response.status_code == 403
        assert "only update your own" in response.json()["detail"]

    def test_update_review_not_found(self, client, auth_headers):
        """Test updating non-existent review."""
        fake_review_id = str(uuid.uuid4())
        update_data = {"rating": 5}

        response = client.put(
            f"/api/v1/reviews/{fake_review_id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]


class TestDeleteReview:
    """Test review deletion endpoints."""

    def test_delete_review_success(self, client, test_user, test_book,
                                   auth_headers, db_session):
        """Test successful review deletion."""
        # Create review
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        review_id = review.id

        # Delete review
        response = client.delete(
            f"/api/v1/reviews/{review_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify review is deleted
        deleted_review = db_session.get(Review, review_id)
        assert deleted_review is None

    def test_delete_review_wrong_user(self, client, test_user, test_user2,
                                      test_book, auth_headers2, db_session):
        """Test deleting another user's review (should fail)."""
        # Create review by first user
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=4,
            review_text="Good book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        # Try to delete with second user's credentials
        response = client.delete(
            f"/api/v1/reviews/{review.id}",
            headers=auth_headers2
        )

        assert response.status_code == 403
        assert "only delete your own" in response.json()["detail"]

    def test_delete_review_not_found(self, client, auth_headers):
        """Test deleting non-existent review."""
        fake_review_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/reviews/{fake_review_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]


class TestRatingAggregation:
    """Test rating aggregation functionality."""

    def test_book_rating_updates_on_review_creation(self, client, test_user,
                                                     test_book, auth_headers,
                                                     db_session):
        """Test that book rating updates when review is created."""
        initial_rating = test_book.average_rating
        initial_count = test_book.total_reviews

        # Create review
        review_data = {
            "rating": 5,
            "review_text": "Excellent book!"
        }

        response = client.post(
            f"/api/v1/books/{test_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )

        assert response.status_code == 201

        # Refresh book and check updated rating
        db_session.refresh(test_book)
        assert test_book.average_rating != initial_rating
        assert test_book.total_reviews == initial_count + 1

    def test_book_rating_updates_on_review_update(self, client, test_user,
                                                   test_book, auth_headers,
                                                   db_session):
        """Test that book rating updates when review is updated."""
        # Create initial review
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=3,
            review_text="Okay book"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        # Update book rating manually to test update
        test_book.average_rating = 3.0
        test_book.total_reviews = 1
        db_session.commit()

        initial_rating = test_book.average_rating

        # Update review rating
        update_data = {"rating": 5}

        response = client.put(
            f"/api/v1/reviews/{review.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200

        # Check that book rating was updated
        db_session.refresh(test_book)
        assert test_book.average_rating != initial_rating

    def test_book_rating_updates_on_review_deletion(self, client, test_user,
                                                     test_book, auth_headers,
                                                     db_session):
        """Test that book rating updates when review is deleted."""
        # Create review
        review = Review(
            user_id=test_user.id,
            book_id=test_book.id,
            rating=5,
            review_text="Great book"
        )
        db_session.add(review)
        db_session.commit()
        review_id = review.id

        # Set initial book rating
        test_book.average_rating = 5.0
        test_book.total_reviews = 1
        db_session.commit()

        # Delete review
        response = client.delete(
            f"/api/v1/reviews/{review_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Check that book rating was updated
        db_session.refresh(test_book)
        assert test_book.total_reviews == 0
        assert test_book.average_rating == 0.0
