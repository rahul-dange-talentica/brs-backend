import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.database import Base, get_db
from app.config import settings
from app.models.user import User
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite
from app.core.security import hash_password, create_access_token

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create test client with test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db_session):
    """Create async test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        first_name="Test",
        last_name="User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user2(db_session):
    """Create second test user"""
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
def inactive_user(db_session):
    """Create inactive test user"""
    user = User(
        email="inactive@example.com",
        password_hash=hash_password("testpassword"),
        first_name="Inactive",
        last_name="User",
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_genre(db_session):
    """Create test genre"""
    genre = Genre(
        name="Science Fiction",
        description="Books about future technology and space"
    )
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre

@pytest.fixture
def test_genre2(db_session):
    """Create second test genre"""
    genre = Genre(
        name="Fantasy",
        description="Books with magical elements"
    )
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre

@pytest.fixture
def test_book(db_session, test_genre):
    """Create test book"""
    book = Book(
        title="Test Book",
        author="Test Author",
        isbn="1234567890123",
        description="A test book for testing",
        average_rating=4.5,
        total_reviews=10
    )
    book.genres.append(test_genre)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book

@pytest.fixture
def test_book2(db_session, test_genre2):
    """Create second test book"""
    book = Book(
        title="Test Book 2",
        author="Test Author 2",
        isbn="9876543210987",
        description="Another test book for testing",
        average_rating=3.8,
        total_reviews=5
    )
    book.genres.append(test_genre2)
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book

@pytest.fixture
def test_review(db_session, test_user, test_book):
    """Create test review"""
    review = Review(
        user_id=test_user.id,
        book_id=test_book.id,
        rating=5,
        review_text="Excellent book! Highly recommended."
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review

@pytest.fixture
def test_favorite(db_session, test_user, test_book):
    """Create test user favorite"""
    favorite = UserFavorite(
        user_id=test_user.id,
        book_id=test_book.id
    )
    db_session.add(favorite)
    db_session.commit()
    db_session.refresh(favorite)
    return favorite

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user"""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def auth_headers2(test_user2):
    """Create authentication headers for second test user"""
    token = create_access_token(data={"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def inactive_auth_headers(inactive_user):
    """Create authentication headers for inactive user"""
    token = create_access_token(data={"sub": str(inactive_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def invalid_auth_headers():
    """Create invalid authentication headers"""
    return {"Authorization": "Bearer invalid_token"}

@pytest.fixture
def sample_users(db_session):
    """Create multiple sample users for testing"""
    users = []
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            password_hash=hash_password("testpassword"),
            first_name=f"User{i}",
            last_name="Sample",
            is_active=True
        )
        db_session.add(user)
        users.append(user)
    db_session.commit()
    for user in users:
        db_session.refresh(user)
    return users

@pytest.fixture
def sample_books(db_session, test_genre, test_genre2):
    """Create multiple sample books for testing"""
    books = []
    for i in range(10):
        book = Book(
            title=f"Sample Book {i}",
            author=f"Author {i}",
            isbn=f"123456789{i:04d}",
            description=f"Sample book {i} for testing",
            average_rating=3.0 + (i % 3),
            total_reviews=i * 2
        )
        # Alternate between genres
        if i % 2 == 0:
            book.genres.append(test_genre)
        else:
            book.genres.append(test_genre2)
        db_session.add(book)
        books.append(book)
    db_session.commit()
    for book in books:
        db_session.refresh(book)
    return books

@pytest.fixture
def sample_reviews(db_session, sample_users, sample_books):
    """Create multiple sample reviews for testing"""
    reviews = []
    for i, (user, book) in enumerate(zip(sample_users, sample_books[:5])):
        review = Review(
            user_id=user.id,
            book_id=book.id,
            rating=3 + (i % 3),  # Ratings between 3-5
            review_text=f"Sample review {i} for testing"
        )
        db_session.add(review)
        reviews.append(review)
    db_session.commit()
    for review in reviews:
        db_session.refresh(review)
    return reviews

# Additional test fixtures
@pytest.fixture
def test_user2(db_session):
    """Create a second test user."""
    user = User(
        email="user2@example.com",
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
def auth_headers2(test_user2):
    """Create authentication headers for second test user."""
    access_token = create_access_token(data={"sub": str(test_user2.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_review(db_session, test_user, test_book):
    """Create a test review."""
    review = Review(
        user_id=test_user.id,
        book_id=test_book.id,
        rating=5,
        review_text="This is a test review for integration testing."
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


@pytest.fixture
def test_favorite(db_session, test_user, test_book):
    """Create a test favorite."""
    from app.models.user_favorite import UserFavorite
    
    favorite = UserFavorite(
        user_id=test_user.id,
        book_id=test_book.id
    )
    db_session.add(favorite)
    db_session.commit()
    db_session.refresh(favorite)
    return favorite


# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_db(db_session):
    """Clean up database after each test"""
    yield
    # The transaction rollback in db_session fixture handles cleanup
    pass
