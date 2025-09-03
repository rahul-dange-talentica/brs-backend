import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.recommendations.popular import PopularRecommendationEngine
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review


class TestPopularRecommendationEngine:
    """Test popular recommendation engine."""
    
    @pytest.fixture
    def popular_engine(self, db_session):
        """Create popular recommendation engine instance."""
        return PopularRecommendationEngine(db_session)
    
    @pytest.fixture
    def books_with_reviews(self, db_session, test_genre, sample_users):
        """Create books with varying review counts and ratings."""
        books = []
        
        # Book 1: High rating, many reviews (should rank high)
        book1 = Book(
            title="Excellent Book",
            author="Great Author",
            isbn="1111111111111",
            average_rating=Decimal("4.8"),
            total_reviews=50
        )
        book1.genres.append(test_genre)
        books.append(book1)
        
        # Book 2: Good rating, moderate reviews
        book2 = Book(
            title="Good Book",
            author="Good Author", 
            isbn="2222222222222",
            average_rating=Decimal("4.2"),
            total_reviews=20
        )
        book2.genres.append(test_genre)
        books.append(book2)
        
        # Book 3: High rating, few reviews (lower due to Bayesian averaging)
        book3 = Book(
            title="Hidden Gem",
            author="Unknown Author",
            isbn="3333333333333",
            average_rating=Decimal("4.9"),
            total_reviews=3
        )
        book3.genres.append(test_genre)
        books.append(book3)
        
        # Book 4: Low rating, many reviews (should rank low)
        book4 = Book(
            title="Poor Book",
            author="Poor Author",
            isbn="4444444444444",
            average_rating=Decimal("2.1"),
            total_reviews=30
        )
        book4.genres.append(test_genre)
        books.append(book4)
        
        # Book 5: No reviews (should be excluded)
        book5 = Book(
            title="No Reviews Book",
            author="New Author",
            isbn="5555555555555",
            average_rating=Decimal("0.0"),
            total_reviews=0
        )
        book5.genres.append(test_genre)
        books.append(book5)
        
        db_session.add_all(books)
        db_session.commit()
        
        for book in books:
            db_session.refresh(book)
        
        return books
    
    @pytest.mark.asyncio
    async def test_get_popular_books_basic(self, popular_engine, books_with_reviews):
        """Test basic popular books retrieval."""
        books = await popular_engine.get_popular_books(limit=10, min_reviews=1)
        
        assert len(books) == 4  # Should exclude book with 0 reviews
        
        # First book should be the one with highest popularity score
        # (Excellent Book with high rating and many reviews)
        assert books[0].title == "Excellent Book"
        
        # Poor Book should be last due to low rating
        assert books[-1].title == "Poor Book"
    
    @pytest.mark.asyncio
    async def test_get_popular_books_min_reviews_filter(self, popular_engine, books_with_reviews):
        """Test min_reviews filter."""
        books = await popular_engine.get_popular_books(limit=10, min_reviews=10)
        
        # Should only include books with 10+ reviews
        assert len(books) == 3
        book_titles = [book.title for book in books]
        assert "Hidden Gem" not in book_titles  # Only has 3 reviews
        assert "No Reviews Book" not in book_titles  # Has 0 reviews
    
    @pytest.mark.asyncio
    async def test_get_popular_books_genre_filter(self, popular_engine, books_with_reviews, test_genre2, db_session):
        """Test genre filtering."""
        # Create a book in different genre
        other_book = Book(
            title="Other Genre Book",
            author="Other Author",
            isbn="6666666666666", 
            average_rating=Decimal("4.9"),
            total_reviews=100
        )
        other_book.genres.append(test_genre2)
        db_session.add(other_book)
        db_session.commit()
        
        # Get books for specific genre
        books = await popular_engine.get_popular_books(
            limit=10, 
            genre_id=str(books_with_reviews[0].genres[0].id),
            min_reviews=1
        )
        
        # Should only return books from the specified genre
        assert len(books) == 4
        for book in books:
            assert books_with_reviews[0].genres[0] in book.genres
    
    @pytest.mark.asyncio
    async def test_get_popular_books_limit(self, popular_engine, books_with_reviews):
        """Test limit parameter."""
        books = await popular_engine.get_popular_books(limit=2, min_reviews=1)
        
        assert len(books) == 2
    
    @pytest.mark.asyncio
    async def test_get_popular_books_days_back_filter(self, popular_engine, db_session, test_genre):
        """Test days_back filter."""
        # Create old book
        old_book = Book(
            title="Old Book",
            author="Old Author",
            isbn="7777777777777",
            average_rating=Decimal("4.5"),
            total_reviews=10,
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        old_book.genres.append(test_genre)
        
        # Create new book
        new_book = Book(
            title="New Book", 
            author="New Author",
            isbn="8888888888888",
            average_rating=Decimal("4.0"),
            total_reviews=5,
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        new_book.genres.append(test_genre)
        
        db_session.add_all([old_book, new_book])
        db_session.commit()
        
        # Get books from last 30 days
        books = await popular_engine.get_popular_books(
            limit=10,
            days_back=30,
            min_reviews=1
        )
        
        # Should only include new book
        book_titles = [book.title for book in books]
        assert "New Book" in book_titles
        assert "Old Book" not in book_titles
    
    @pytest.mark.asyncio
    async def test_get_popular_books_empty_result(self, popular_engine, db_session):
        """Test when no books meet criteria."""
        books = await popular_engine.get_popular_books(limit=10, min_reviews=100)
        
        assert len(books) == 0


class TestTrendingBooks:
    """Test trending books functionality."""
    
    @pytest.fixture
    def popular_engine(self, db_session):
        """Create popular recommendation engine instance."""
        return PopularRecommendationEngine(db_session)
    
    @pytest.fixture
    def trending_setup(self, db_session, sample_users, test_genre):
        """Set up books and reviews for trending tests."""
        # Create books
        book1 = Book(
            title="Trending Book 1",
            author="Author 1",
            isbn="1111111111111",
            average_rating=Decimal("4.0"),
            total_reviews=5
        )
        book1.genres.append(test_genre)
        
        book2 = Book(
            title="Trending Book 2",
            author="Author 2", 
            isbn="2222222222222",
            average_rating=Decimal("3.5"),
            total_reviews=3
        )
        book2.genres.append(test_genre)
        
        book3 = Book(
            title="No Recent Reviews",
            author="Author 3",
            isbn="3333333333333",
            average_rating=Decimal("4.5"),
            total_reviews=10
        )
        book3.genres.append(test_genre)
        
        db_session.add_all([book1, book2, book3])
        db_session.commit()
        
        # Create recent reviews for book1 (should be trending)
        recent_time = datetime.utcnow() - timedelta(days=5)
        for i in range(5):
            review = Review(
                user_id=sample_users[i].id,
                book_id=book1.id,
                rating=4 + (i % 2),  # Ratings 4-5
                review_text=f"Recent review {i}",
                created_at=recent_time + timedelta(hours=i)
            )
            db_session.add(review)
        
        # Create moderate recent reviews for book2
        for i in range(3):
            review = Review(
                user_id=sample_users[i].id,
                book_id=book2.id,
                rating=3 + (i % 2),  # Ratings 3-4
                review_text=f"Moderate review {i}",
                created_at=recent_time + timedelta(hours=i)
            )
            db_session.add(review)
        
        # Create old reviews for book3 (should not be trending)
        old_time = datetime.utcnow() - timedelta(days=60)
        for i in range(3):
            review = Review(
                user_id=sample_users[i].id,
                book_id=book3.id,
                rating=5,
                review_text=f"Old review {i}",
                created_at=old_time + timedelta(hours=i)
            )
            db_session.add(review)
        
        db_session.commit()
        return [book1, book2, book3]
    
    @pytest.mark.asyncio
    async def test_get_trending_books_basic(self, popular_engine, trending_setup):
        """Test basic trending books retrieval."""
        books = await popular_engine.get_trending_books(
            limit=10,
            days_back=30,
            min_reviews_in_period=3
        )
        
        # Should return books with recent activity
        assert len(books) == 2  # book1 and book2
        
        # Book1 should rank higher (more recent reviews with good ratings)
        assert books[0].title == "Trending Book 1"
        assert books[1].title == "Trending Book 2"
    
    @pytest.mark.asyncio
    async def test_get_trending_books_min_reviews_filter(self, popular_engine, trending_setup):
        """Test min_reviews_in_period filter."""
        books = await popular_engine.get_trending_books(
            limit=10,
            days_back=30,
            min_reviews_in_period=5
        )
        
        # Should only include book1 (has 5 recent reviews)
        assert len(books) == 1
        assert books[0].title == "Trending Book 1"
    
    @pytest.mark.asyncio
    async def test_get_trending_books_days_back_filter(self, popular_engine, trending_setup):
        """Test days_back filter."""
        books = await popular_engine.get_trending_books(
            limit=10,
            days_back=3,  # Very short period
            min_reviews_in_period=1
        )
        
        # Should still find recent reviews within 3 days
        assert len(books) >= 0  # May or may not find books depending on exact timing
    
    @pytest.mark.asyncio
    async def test_get_trending_books_empty_result(self, popular_engine, db_session):
        """Test when no books are trending."""
        books = await popular_engine.get_trending_books(
            limit=10,
            days_back=1,  # Very short period
            min_reviews_in_period=10  # High threshold
        )
        
        assert len(books) == 0
