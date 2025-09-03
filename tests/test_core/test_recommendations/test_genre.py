import pytest
from decimal import Decimal

from app.core.recommendations.genre import GenreRecommendationEngine
from app.models.book import Book
from app.models.genre import Genre
from app.models.review import Review
from app.models.user_favorite import UserFavorite


class TestGenreRecommendationEngine:
    """Test genre-based recommendation engine."""
    
    @pytest.fixture
    def genre_engine(self, db_session):
        """Create genre recommendation engine instance."""
        return GenreRecommendationEngine(db_session)
    
    @pytest.fixture
    def genre_setup(self, db_session, test_user, test_user2):
        """Set up genres and books for testing."""
        # Create genres
        sci_fi = Genre(name="Science Fiction", description="Sci-fi books")
        fantasy = Genre(name="Fantasy", description="Fantasy books")
        
        db_session.add_all([sci_fi, fantasy])
        db_session.commit()
        
        # Create sci-fi books
        sci_fi_book1 = Book(
            title="Dune",
            author="Frank Herbert",
            isbn="1111111111111",
            average_rating=Decimal("4.8"),
            total_reviews=100
        )
        sci_fi_book1.genres.append(sci_fi)
        
        sci_fi_book2 = Book(
            title="Foundation",
            author="Isaac Asimov",
            isbn="2222222222222",
            average_rating=Decimal("4.5"),
            total_reviews=50
        )
        sci_fi_book2.genres.append(sci_fi)
        
        # Create fantasy books
        fantasy_book1 = Book(
            title="The Hobbit",
            author="J.R.R. Tolkien",
            isbn="3333333333333",
            average_rating=Decimal("4.7"),
            total_reviews=200
        )
        fantasy_book1.genres.append(fantasy)
        
        fantasy_book2 = Book(
            title="Harry Potter",
            author="J.K. Rowling",
            isbn="4444444444444",
            average_rating=Decimal("4.6"),
            total_reviews=150
        )
        fantasy_book2.genres.append(fantasy)
        
        # Low-rated book
        low_rated = Book(
            title="Poor Sci-Fi",
            author="Bad Author",
            isbn="5555555555555",
            average_rating=Decimal("2.0"),
            total_reviews=10
        )
        low_rated.genres.append(sci_fi)
        
        # Book with few reviews
        few_reviews = Book(
            title="New Sci-Fi",
            author="New Author",
            isbn="6666666666666",
            average_rating=Decimal("4.0"),
            total_reviews=2
        )
        few_reviews.genres.append(sci_fi)
        
        db_session.add_all([
            sci_fi_book1, sci_fi_book2, fantasy_book1, 
            fantasy_book2, low_rated, few_reviews
        ])
        db_session.commit()
        
        # Create user interactions
        # User1 reviews Dune
        review1 = Review(
            user_id=test_user.id,
            book_id=sci_fi_book1.id,
            rating=5,
            review_text="Amazing book!"
        )
        
        # User1 favorites Foundation
        favorite1 = UserFavorite(
            user_id=test_user.id,
            book_id=sci_fi_book2.id
        )
        
        db_session.add_all([review1, favorite1])
        db_session.commit()
        
        return {
            'sci_fi': sci_fi,
            'fantasy': fantasy,
            'sci_fi_books': [sci_fi_book1, sci_fi_book2, low_rated, few_reviews],
            'fantasy_books': [fantasy_book1, fantasy_book2]
        }
    
    @pytest.mark.asyncio
    async def test_get_genre_books_basic(self, genre_engine, genre_setup):
        """Test basic genre book retrieval."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=10,
            min_rating=0.0,
            min_reviews=1
        )
        
        # Should return all sci-fi books meeting criteria
        assert len(books) == 4
        
        # Should be ordered by rating/popularity
        assert books[0].title == "Dune"  # Highest rating and most reviews
    
    @pytest.mark.asyncio
    async def test_get_genre_books_min_rating_filter(self, genre_engine, genre_setup):
        """Test minimum rating filter."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=10,
            min_rating=4.0,
            min_reviews=1
        )
        
        # Should exclude low-rated book (2.0 rating)
        assert len(books) == 3
        book_titles = [book.title for book in books]
        assert "Poor Sci-Fi" not in book_titles
    
    @pytest.mark.asyncio
    async def test_get_genre_books_min_reviews_filter(self, genre_engine, genre_setup):
        """Test minimum reviews filter."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=10,
            min_rating=0.0,
            min_reviews=10
        )
        
        # Should exclude book with only 2 reviews
        assert len(books) == 3
        book_titles = [book.title for book in books]
        assert "New Sci-Fi" not in book_titles
    
    @pytest.mark.asyncio
    async def test_get_genre_books_exclude_user_interactions(self, genre_engine, genre_setup, test_user):
        """Test excluding books user has already interacted with."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=10,
            exclude_user_id=str(test_user.id),
            min_rating=0.0,
            min_reviews=1
        )
        
        # Should exclude Dune (reviewed) and Foundation (favorited)
        assert len(books) == 2
        book_titles = [book.title for book in books]
        assert "Dune" not in book_titles
        assert "Foundation" not in book_titles
        assert "Poor Sci-Fi" in book_titles
        assert "New Sci-Fi" in book_titles
    
    @pytest.mark.asyncio
    async def test_get_genre_books_different_genre(self, genre_engine, genre_setup):
        """Test getting books from different genre."""
        fantasy_id = str(genre_setup['fantasy'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=fantasy_id,
            limit=10,
            min_rating=0.0,
            min_reviews=1
        )
        
        # Should return fantasy books only
        assert len(books) == 2
        book_titles = [book.title for book in books]
        assert "The Hobbit" in book_titles
        assert "Harry Potter" in book_titles
        
        # Should be ordered by review count (Hobbit has more)
        assert books[0].title == "The Hobbit"
    
    @pytest.mark.asyncio
    async def test_get_genre_books_limit(self, genre_engine, genre_setup):
        """Test limit parameter."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=2,
            min_rating=0.0,
            min_reviews=1
        )
        
        assert len(books) == 2
    
    @pytest.mark.asyncio
    async def test_get_genre_books_nonexistent_genre(self, genre_engine, db_session):
        """Test with non-existent genre ID."""
        import uuid
        fake_genre_id = str(uuid.uuid4())
        
        books = await genre_engine.get_genre_books(
            genre_id=fake_genre_id,
            limit=10,
            min_rating=0.0,
            min_reviews=1
        )
        
        assert len(books) == 0
    
    @pytest.mark.asyncio
    async def test_get_similar_books_by_genre(self, genre_engine, genre_setup, test_user):
        """Test getting similar books by shared genres."""
        # Use Dune (sci-fi) as the base book
        dune_book = genre_setup['sci_fi_books'][0]
        
        books = await genre_engine.get_similar_books_by_genre(
            book_id=str(dune_book.id),
            limit=10,
            exclude_user_id=str(test_user.id)
        )
        
        # Should return other sci-fi books, excluding Foundation (favorited by user)
        assert len(books) >= 1
        book_titles = [book.title for book in books]
        assert "Foundation" not in book_titles  # Excluded due to user interaction
        assert "Dune" not in book_titles  # Should exclude the source book itself
    
    @pytest.mark.asyncio
    async def test_get_user_preferred_genres(self, genre_engine, genre_setup, test_user):
        """Test getting user's preferred genres based on activity."""
        preferences = await genre_engine.get_user_preferred_genres(
            user_id=str(test_user.id),
            limit=5
        )
        
        # User has activity in sci-fi (review + favorite)
        assert len(preferences) >= 1
        
        # Sci-fi should be the top preference
        top_genre = preferences[0]
        assert top_genre['genre_name'] == "Science Fiction"
        assert top_genre['interaction_count'] >= 2  # 1 review + 1 favorite
    
    @pytest.mark.asyncio
    async def test_get_user_preferred_genres_no_activity(self, genre_engine, test_user2):
        """Test getting preferred genres for user with no activity."""
        preferences = await genre_engine.get_user_preferred_genres(
            user_id=str(test_user2.id),
            limit=5
        )
        
        # Should return empty list for user with no activity
        assert len(preferences) == 0
    
    @pytest.mark.asyncio
    async def test_get_genre_books_ordering(self, genre_engine, genre_setup):
        """Test that books are properly ordered by popularity."""
        sci_fi_id = str(genre_setup['sci_fi'].id)
        
        books = await genre_engine.get_genre_books(
            genre_id=sci_fi_id,
            limit=10,
            min_rating=0.0,
            min_reviews=1
        )
        
        # Books should be ordered by: average_rating desc, total_reviews desc
        for i in range(len(books) - 1):
            current_book = books[i]
            next_book = books[i + 1]
            
            # Current book should have higher or equal rating
            # If ratings are equal, current should have more or equal reviews
            assert (current_book.average_rating > next_book.average_rating or
                    (current_book.average_rating == next_book.average_rating and
                     current_book.total_reviews >= next_book.total_reviews))


class TestGenreRecommendationEdgeCases:
    """Test edge cases for genre recommendations."""
    
    @pytest.fixture
    def genre_engine(self, db_session):
        """Create genre recommendation engine instance."""
        return GenreRecommendationEngine(db_session)
    
    @pytest.mark.asyncio
    async def test_books_with_multiple_genres(self, genre_engine, db_session, test_genre, test_genre2):
        """Test books that belong to multiple genres."""
        # Create book with multiple genres
        multi_genre_book = Book(
            title="Multi-Genre Book",
            author="Versatile Author",
            isbn="1111111111111",
            average_rating=Decimal("4.5"),
            total_reviews=20
        )
        multi_genre_book.genres.extend([test_genre, test_genre2])
        db_session.add(multi_genre_book)
        db_session.commit()
        
        # Should appear in results for both genres
        books1 = await genre_engine.get_genre_books(
            genre_id=str(test_genre.id),
            limit=10
        )
        books2 = await genre_engine.get_genre_books(
            genre_id=str(test_genre2.id),
            limit=10
        )
        
        book_titles1 = [book.title for book in books1]
        book_titles2 = [book.title for book in books2]
        
        assert "Multi-Genre Book" in book_titles1
        assert "Multi-Genre Book" in book_titles2
