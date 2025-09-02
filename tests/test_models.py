import pytest
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.models import User, Book, Genre, Review, UserFavorite, book_genres


# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()


class TestUserModel:
    """Test cases for User model."""
    
    def test_create_user(self, db_session):
        """Test creating a new user."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is not None
        
    def test_user_email_unique_constraint(self, db_session):
        """Test that email must be unique."""
        user1 = User(email="test@example.com", password_hash="hash1")
        user2 = User(email="test@example.com", password_hash="hash2")
        
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_user_repr(self, db_session):
        """Test User string representation."""
        user = User(email="test@example.com", password_hash="hash")
        db_session.add(user)
        db_session.commit()
        
        expected = f"<User(id={user.id}, email='test@example.com')>"
        assert str(user) == expected


class TestGenreModel:
    """Test cases for Genre model."""
    
    def test_create_genre(self, db_session):
        """Test creating a new genre."""
        genre = Genre(
            name="Science Fiction",
            description="Books about future technology and space"
        )
        
        db_session.add(genre)
        db_session.commit()
        
        assert genre.id is not None
        assert genre.name == "Science Fiction"
        assert genre.description == "Books about future technology and space"
        assert genre.created_at is not None
        
    def test_genre_name_unique_constraint(self, db_session):
        """Test that genre name must be unique."""
        genre1 = Genre(name="Fantasy")
        genre2 = Genre(name="Fantasy")
        
        db_session.add(genre1)
        db_session.commit()
        
        db_session.add(genre2)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_genre_repr(self, db_session):
        """Test Genre string representation."""
        genre = Genre(name="Mystery")
        db_session.add(genre)
        db_session.commit()
        
        expected = f"<Genre(id={genre.id}, name='Mystery')>"
        assert str(genre) == expected


class TestBookModel:
    """Test cases for Book model."""
    
    def test_create_book(self, db_session):
        """Test creating a new book."""
        book = Book(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
            isbn="9780743273565",
            description="A classic American novel",
            publication_date=date(1925, 4, 10),
            average_rating=Decimal("4.25"),
            total_reviews=100
        )
        
        db_session.add(book)
        db_session.commit()
        
        assert book.id is not None
        assert book.title == "The Great Gatsby"
        assert book.author == "F. Scott Fitzgerald"
        assert book.isbn == "9780743273565"
        assert book.average_rating == Decimal("4.25")
        assert book.total_reviews == 100
        assert book.created_at is not None
        assert book.updated_at is not None
        
    def test_book_isbn_unique_constraint(self, db_session):
        """Test that ISBN must be unique when provided."""
        book1 = Book(title="Book 1", author="Author 1", isbn="1234567890123")
        book2 = Book(title="Book 2", author="Author 2", isbn="1234567890123")
        
        db_session.add(book1)
        db_session.commit()
        
        db_session.add(book2)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_book_default_values(self, db_session):
        """Test book default values."""
        book = Book(title="Test Book", author="Test Author")
        
        db_session.add(book)
        db_session.commit()
        
        assert book.average_rating == Decimal("0.00")
        assert book.total_reviews == 0
        
    def test_book_repr(self, db_session):
        """Test Book string representation."""
        book = Book(title="Test Book", author="Test Author")
        db_session.add(book)
        db_session.commit()
        
        expected = f"<Book(id={book.id}, title='Test Book', author='Test Author')>"
        assert str(book) == expected


class TestReviewModel:
    """Test cases for Review model."""
    
    @pytest.fixture
    def user_and_book(self, db_session):
        """Create a user and book for testing reviews."""
        user = User(email="reviewer@example.com", password_hash="hash")
        book = Book(title="Review Test Book", author="Test Author")
        
        db_session.add(user)
        db_session.add(book)
        db_session.commit()
        
        return user, book
        
    def test_create_review(self, db_session, user_and_book):
        """Test creating a new review."""
        user, book = user_and_book
        
        review = Review(
            user_id=user.id,
            book_id=book.id,
            rating=5,
            review_text="Excellent book!"
        )
        
        db_session.add(review)
        db_session.commit()
        
        assert review.id is not None
        assert review.user_id == user.id
        assert review.book_id == book.id
        assert review.rating == 5
        assert review.review_text == "Excellent book!"
        assert review.created_at is not None
        assert review.updated_at is not None
        
    def test_review_rating_constraint(self, db_session, user_and_book):
        """Test that rating must be between 1 and 5."""
        user, book = user_and_book
        
        # Test invalid rating (too low)
        review_low = Review(user_id=user.id, book_id=book.id, rating=0)
        db_session.add(review_low)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
        db_session.rollback()
        
        # Test invalid rating (too high)
        review_high = Review(user_id=user.id, book_id=book.id, rating=6)
        db_session.add(review_high)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_review_repr(self, db_session, user_and_book):
        """Test Review string representation."""
        user, book = user_and_book
        
        review = Review(user_id=user.id, book_id=book.id, rating=4)
        db_session.add(review)
        db_session.commit()
        
        expected = f"<Review(id={review.id}, user_id={user.id}, book_id={book.id}, rating=4)>"
        assert str(review) == expected


class TestUserFavoriteModel:
    """Test cases for UserFavorite model."""
    
    @pytest.fixture
    def user_and_book(self, db_session):
        """Create a user and book for testing favorites."""
        user = User(email="favuser@example.com", password_hash="hash")
        book = Book(title="Favorite Test Book", author="Test Author")
        
        db_session.add(user)
        db_session.add(book)
        db_session.commit()
        
        return user, book
        
    def test_create_user_favorite(self, db_session, user_and_book):
        """Test creating a new user favorite."""
        user, book = user_and_book
        
        favorite = UserFavorite(
            user_id=user.id,
            book_id=book.id
        )
        
        db_session.add(favorite)
        db_session.commit()
        
        assert favorite.id is not None
        assert favorite.user_id == user.id
        assert favorite.book_id == book.id
        assert favorite.created_at is not None
        
    def test_user_favorite_unique_constraint(self, db_session, user_and_book):
        """Test that user can only favorite a book once."""
        user, book = user_and_book
        
        favorite1 = UserFavorite(user_id=user.id, book_id=book.id)
        favorite2 = UserFavorite(user_id=user.id, book_id=book.id)
        
        db_session.add(favorite1)
        db_session.commit()
        
        db_session.add(favorite2)
        with pytest.raises(IntegrityError):
            db_session.commit()
            
    def test_user_favorite_repr(self, db_session, user_and_book):
        """Test UserFavorite string representation."""
        user, book = user_and_book
        
        favorite = UserFavorite(user_id=user.id, book_id=book.id)
        db_session.add(favorite)
        db_session.commit()
        
        expected = f"<UserFavorite(id={favorite.id}, user_id={user.id}, book_id={book.id})>"
        assert str(favorite) == expected


class TestRelationships:
    """Test model relationships."""
    
    @pytest.fixture
    def sample_data(self, db_session):
        """Create sample data for relationship testing."""
        # Create user
        user = User(email="relationship@example.com", password_hash="hash")
        
        # Create genres
        genre1 = Genre(name="Fiction")
        genre2 = Genre(name="Drama")
        
        # Create book
        book = Book(title="Relationship Test Book", author="Test Author")
        
        db_session.add_all([user, genre1, genre2, book])
        db_session.commit()
        
        # Add genres to book
        book.genres.extend([genre1, genre2])
        db_session.commit()
        
        return user, book, genre1, genre2
        
    def test_user_reviews_relationship(self, db_session, sample_data):
        """Test user-reviews relationship."""
        user, book, _, _ = sample_data
        
        # Create a second book for the second review (due to unique constraint)
        book2 = Book(title="Second Test Book", author="Test Author 2")
        db_session.add(book2)
        db_session.commit()
        
        # Create reviews (one per book due to unique constraint)
        review1 = Review(user_id=user.id, book_id=book.id, rating=5)
        review2 = Review(user_id=user.id, book_id=book2.id, rating=4)
        
        db_session.add_all([review1, review2])
        db_session.commit()
        
        # Test relationship
        db_session.refresh(user)
        assert len(user.reviews) == 2
        assert review1 in user.reviews
        assert review2 in user.reviews
        
    def test_user_favorites_relationship(self, db_session, sample_data):
        """Test user-favorites relationship."""
        user, book, _, _ = sample_data
        
        # Create favorite
        favorite = UserFavorite(user_id=user.id, book_id=book.id)
        db_session.add(favorite)
        db_session.commit()
        
        # Test relationship
        db_session.refresh(user)
        assert len(user.favorites) == 1
        assert favorite in user.favorites
        
    def test_book_genres_relationship(self, db_session, sample_data):
        """Test book-genres many-to-many relationship."""
        user, book, genre1, genre2 = sample_data
        
        # Test relationship
        db_session.refresh(book)
        db_session.refresh(genre1)
        db_session.refresh(genre2)
        
        assert len(book.genres) == 2
        assert genre1 in book.genres
        assert genre2 in book.genres
        
        assert book in genre1.books
        assert book in genre2.books
        
    def test_cascade_delete_user_reviews(self, db_session, sample_data):
        """Test cascade delete for user reviews."""
        user, book, _, _ = sample_data
        
        # Create review
        review = Review(user_id=user.id, book_id=book.id, rating=5)
        db_session.add(review)
        db_session.commit()
        
        review_id = review.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Check that review was also deleted
        deleted_review = db_session.get(Review, review_id)
        assert deleted_review is None
        
    def test_cascade_delete_book_reviews(self, db_session, sample_data):
        """Test cascade delete for book reviews."""
        user, book, _, _ = sample_data
        
        # Create review
        review = Review(user_id=user.id, book_id=book.id, rating=5)
        db_session.add(review)
        db_session.commit()
        
        review_id = review.id
        
        # Delete book
        db_session.delete(book)
        db_session.commit()
        
        # Check that review was also deleted
        deleted_review = db_session.get(Review, review_id)
        assert deleted_review is None
