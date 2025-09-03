import pytest
from pydantic import ValidationError
from datetime import datetime, date
from decimal import Decimal
import uuid

from app.schemas.book import BookBase, BookCreate, BookUpdate, BookSummary


class TestBookBase:
    """Test BookBase schema validation."""
    
    def test_valid_book_base(self):
        """Test valid BookBase creation."""
        book_data = {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "isbn": "9780743273565",
            "description": "A classic American novel",
            "cover_image_url": "https://example.com/cover.jpg",
            "publication_date": date(1925, 4, 10)
        }
        
        book = BookBase(**book_data)
        
        assert book.title == "The Great Gatsby"
        assert book.author == "F. Scott Fitzgerald"
        assert book.isbn == "9780743273565"
        assert book.description == "A classic American novel"
        assert book.cover_image_url == "https://example.com/cover.jpg"
        assert book.publication_date == date(1925, 4, 10)
    
    def test_book_base_required_fields(self):
        """Test required fields in BookBase."""
        # Only title and author are required
        book = BookBase(title="Test Book", author="Test Author")
        
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.isbn is None
        assert book.description is None
        assert book.cover_image_url is None
        assert book.publication_date is None
    
    def test_book_base_missing_required_fields(self):
        """Test missing required fields."""
        # Missing title
        with pytest.raises(ValidationError) as exc_info:
            BookBase(author="Test Author")
        
        assert "title" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)
        
        # Missing author
        with pytest.raises(ValidationError) as exc_info:
            BookBase(title="Test Book")
        
        assert "author" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)
    
    def test_book_base_title_length_validation(self):
        """Test title length validation (max 500 characters)."""
        long_title = "x" * 501  # Exceeds limit
        
        with pytest.raises(ValidationError) as exc_info:
            BookBase(title=long_title, author="Test Author")
        
        assert "String should have at most 500 characters" in str(exc_info.value)
    
    def test_book_base_author_length_validation(self):
        """Test author length validation (max 300 characters)."""
        long_author = "x" * 301  # Exceeds limit
        
        with pytest.raises(ValidationError) as exc_info:
            BookBase(title="Test Book", author=long_author)
        
        assert "String should have at most 300 characters" in str(exc_info.value)
    
    def test_book_base_isbn_length_validation(self):
        """Test ISBN length validation (max 13 characters)."""
        long_isbn = "x" * 14  # Exceeds limit
        
        with pytest.raises(ValidationError) as exc_info:
            BookBase(title="Test Book", author="Test Author", isbn=long_isbn)
        
        assert "String should have at most 13 characters" in str(exc_info.value)
    
    def test_book_base_cover_image_url_length_validation(self):
        """Test cover image URL length validation (max 1000 characters)."""
        long_url = "https://example.com/" + "x" * 1000  # Exceeds limit
        
        with pytest.raises(ValidationError) as exc_info:
            BookBase(title="Test Book", author="Test Author", cover_image_url=long_url)
        
        assert "String should have at most 1000 characters" in str(exc_info.value)
    
    def test_book_base_empty_optional_fields(self):
        """Test empty string values for optional fields."""
        book = BookBase(
            title="Test Book",
            author="Test Author",
            isbn="",
            description="",
            cover_image_url=""
        )
        
        assert book.isbn == ""
        assert book.description == ""
        assert book.cover_image_url == ""
    
    def test_book_base_publication_date_validation(self):
        """Test publication date validation."""
        # Valid date
        book = BookBase(
            title="Test Book",
            author="Test Author",
            publication_date=date(2023, 1, 15)
        )
        assert book.publication_date == date(2023, 1, 15)
        
        # Invalid date format (Pydantic V2 is more lenient with date parsing)
        with pytest.raises(ValidationError):
            BookBase(
                title="Test Book",
                author="Test Author",
                publication_date="not-a-date"  # Invalid date string
            )


class TestBookCreate:
    """Test BookCreate schema validation."""
    
    def test_valid_book_create(self):
        """Test valid BookCreate."""
        genre_ids = [uuid.uuid4(), uuid.uuid4()]
        
        book_data = {
            "title": "New Book",
            "author": "New Author",
            "isbn": "1234567890123",
            "description": "A new book",
            "genre_ids": genre_ids
        }
        
        book = BookCreate(**book_data)
        
        assert book.title == "New Book"
        assert book.author == "New Author"
        assert book.genre_ids == genre_ids
    
    def test_book_create_default_genre_ids(self):
        """Test default empty genre_ids list."""
        book = BookCreate(title="Test Book", author="Test Author")
        
        assert book.genre_ids == []
    
    def test_book_create_genre_ids_validation(self):
        """Test genre_ids UUID validation."""
        # Invalid UUID in list
        with pytest.raises(ValidationError):
            BookCreate(
                title="Test Book",
                author="Test Author",
                genre_ids=["not_a_uuid"]
            )
        
        # Valid UUIDs
        valid_uuids = [uuid.uuid4(), uuid.uuid4()]
        book = BookCreate(
            title="Test Book",
            author="Test Author",
            genre_ids=valid_uuids
        )
        assert book.genre_ids == valid_uuids
    
    def test_book_create_inherits_base_validation(self):
        """Test BookCreate inherits validation from BookBase."""
        # Title required
        with pytest.raises(ValidationError):
            BookCreate(author="Test Author")
        
        # Title length validation
        with pytest.raises(ValidationError):
            BookCreate(title="x" * 501, author="Test Author")


class TestBookUpdate:
    """Test BookUpdate schema validation."""
    
    def test_valid_book_update(self):
        """Test valid BookUpdate."""
        genre_ids = [uuid.uuid4()]
        
        update_data = {
            "title": "Updated Title",
            "author": "Updated Author",
            "isbn": "9999999999999",
            "description": "Updated description",
            "cover_image_url": "https://example.com/new-cover.jpg",
            "publication_date": date(2024, 1, 1),
            "genre_ids": genre_ids
        }
        
        book_update = BookUpdate(**update_data)
        
        assert book_update.title == "Updated Title"
        assert book_update.author == "Updated Author"
        assert book_update.genre_ids == genre_ids
    
    def test_book_update_all_fields_optional(self):
        """Test all fields are optional in BookUpdate."""
        book_update = BookUpdate()
        
        assert book_update.title is None
        assert book_update.author is None
        assert book_update.isbn is None
        assert book_update.description is None
        assert book_update.cover_image_url is None
        assert book_update.publication_date is None
        assert book_update.genre_ids is None
    
    def test_book_update_partial_fields(self):
        """Test partial field updates."""
        # Only title
        book_update = BookUpdate(title="New Title")
        assert book_update.title == "New Title"
        assert book_update.author is None
        
        # Only genre_ids
        genre_ids = [uuid.uuid4()]
        book_update = BookUpdate(genre_ids=genre_ids)
        assert book_update.genre_ids == genre_ids
        assert book_update.title is None
    
    def test_book_update_field_validation(self):
        """Test field validation in BookUpdate."""
        # Title length validation
        with pytest.raises(ValidationError):
            BookUpdate(title="x" * 501)
        
        # Author length validation
        with pytest.raises(ValidationError):
            BookUpdate(author="x" * 301)
        
        # ISBN length validation
        with pytest.raises(ValidationError):
            BookUpdate(isbn="x" * 14)
        
        # Genre IDs validation
        with pytest.raises(ValidationError):
            BookUpdate(genre_ids=["not_a_uuid"])
    
    def test_book_update_empty_genre_ids(self):
        """Test empty genre_ids list."""
        book_update = BookUpdate(genre_ids=[])
        
        assert book_update.genre_ids == []


class TestBookSummary:
    """Test BookSummary schema validation."""
    
    def test_valid_book_summary(self):
        """Test valid BookSummary."""
        book_id = uuid.uuid4()
        now = datetime.utcnow()
        
        book_data = {
            "id": book_id,
            "title": "Summary Book",
            "author": "Summary Author",
            "isbn": "1111111111111",
            "description": "Book summary",
            "cover_image_url": "https://example.com/cover.jpg",
            "publication_date": date(2023, 1, 1),
            "average_rating": Decimal("4.25"),
            "total_reviews": 42,
            "created_at": now,
            "updated_at": now
        }
        
        book = BookSummary(**book_data)
        
        assert book.id == book_id
        assert book.title == "Summary Book"
        assert book.average_rating == Decimal("4.25")
        assert book.total_reviews == 42
        assert book.created_at == now
    
    def test_book_summary_required_fields(self):
        """Test required fields in BookSummary."""
        required_fields = [
            "id", "title", "author", "average_rating", 
            "total_reviews", "created_at", "updated_at"
        ]
        
        base_data = {
            "id": uuid.uuid4(),
            "title": "Test Book",
            "author": "Test Author",
            "average_rating": Decimal("4.0"),
            "total_reviews": 10,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        for field in required_fields:
            incomplete_data = {k: v for k, v in base_data.items() if k != field}
            
            with pytest.raises(ValidationError) as exc_info:
                BookSummary(**incomplete_data)
            
            assert field in str(exc_info.value)
    
    def test_book_summary_uuid_validation(self):
        """Test UUID validation in BookSummary."""
        now = datetime.utcnow()
        
        with pytest.raises(ValidationError):
            BookSummary(
                id="not_a_uuid",
                title="Test Book",
                author="Test Author",
                average_rating=Decimal("4.0"),
                total_reviews=10,
                created_at=now,
                updated_at=now
            )
    
    def test_book_summary_decimal_validation(self):
        """Test Decimal validation for average_rating."""
        book_id = uuid.uuid4()
        now = datetime.utcnow()
        
        # Valid decimal values
        valid_ratings = [Decimal("0.0"), Decimal("2.5"), Decimal("5.0")]
        
        for rating in valid_ratings:
            book = BookSummary(
                id=book_id,
                title="Test Book",
                author="Test Author",
                average_rating=rating,
                total_reviews=1,
                created_at=now,
                updated_at=now
            )
            assert book.average_rating == rating
    
    def test_book_summary_integer_validation(self):
        """Test integer validation for total_reviews."""
        book_id = uuid.uuid4()
        now = datetime.utcnow()
        
        # Valid integer
        book = BookSummary(
            id=book_id,
            title="Test Book",
            author="Test Author",
            average_rating=Decimal("4.0"),
            total_reviews=0,
            created_at=now,
            updated_at=now
        )
        assert book.total_reviews == 0
        
        # Negative should work (though not realistic)
        book = BookSummary(
            id=book_id,
            title="Test Book",
            author="Test Author",
            average_rating=Decimal("4.0"),
            total_reviews=-1,
            created_at=now,
            updated_at=now
        )
        assert book.total_reviews == -1
    
    def test_book_summary_datetime_validation(self):
        """Test datetime validation."""
        book_id = uuid.uuid4()
        
        # Invalid created_at
        with pytest.raises(ValidationError):
            BookSummary(
                id=book_id,
                title="Test Book",
                author="Test Author",
                average_rating=Decimal("4.0"),
                total_reviews=1,
                created_at="not_a_datetime",
                updated_at=datetime.utcnow()
            )


class TestBookSchemaEdgeCases:
    """Test edge cases for book schemas."""
    
    def test_unicode_in_text_fields(self):
        """Test unicode characters in text fields."""
        book = BookBase(
            title="El Quijote de la Mancha",
            author="Miguel de Cervantes Saavedra",
            description="Una novela española clásica 📚"
        )
        
        assert "Quijote" in book.title
        assert "Cervantes" in book.author
        assert "📚" in book.description
    
    def test_special_characters_in_fields(self):
        """Test special characters in fields."""
        book = BookBase(
            title="Book: A Story of Life & Death",
            author="John Doe Jr.",
            isbn="1234567890123",  # Use 13-digit ISBN without hyphens
            description="A book about life & death, with lots of @#$%^&*() characters!"
        )
        
        assert book.title == "Book: A Story of Life & Death"
        assert book.author == "John Doe Jr."
        assert book.isbn == "1234567890123"
    
    def test_whitespace_handling(self):
        """Test whitespace handling."""
        book = BookBase(
            title="  Title with spaces  ",
            author="  Author with spaces  "
        )
        
        # Pydantic preserves whitespace by default
        assert book.title == "  Title with spaces  "
        assert book.author == "  Author with spaces  "
    
    def test_very_long_description(self):
        """Test very long description (no explicit length limit)."""
        long_description = "This is a very long description. " * 1000
        
        book = BookBase(
            title="Long Description Book",
            author="Verbose Author",
            description=long_description
        )
        
        assert len(book.description) > 1000
        assert book.description == long_description
    
    def test_isbn_formats(self):
        """Test various ISBN formats."""
        valid_isbns = [
            "1234567890",      # 10 digit
            "1234567890123",   # 13 digit (exact limit)
            "123456789X",      # 10 digit with X check digit
            ""                 # Empty string
        ]
        
        for isbn in valid_isbns:
            book = BookBase(
                title="ISBN Test",
                author="Test Author",
                isbn=isbn
            )
            assert book.isbn == isbn
            
        # Test ISBNs that exceed character limit
        invalid_isbns = [
            "978-1234567890",  # With hyphens (14 chars, exceeds 13 chars limit)
            "978-12345678901", # 15 chars, exceeds limit
        ]

        for isbn in invalid_isbns:
            with pytest.raises(ValidationError):
                BookBase(
                    title="ISBN Test",
                    author="Test Author",
                    isbn=isbn
                )
    
    def test_future_publication_date(self):
        """Test publication date in the future."""
        future_date = date(2030, 12, 31)
        
        book = BookBase(
            title="Future Book",
            author="Time Traveler",
            publication_date=future_date
        )
        
        assert book.publication_date == future_date
    
    def test_very_old_publication_date(self):
        """Test very old publication date."""
        old_date = date(1, 1, 1)  # Year 1 AD
        
        book = BookBase(
            title="Ancient Book",
            author="Ancient Author",
            publication_date=old_date
        )
        
        assert book.publication_date == old_date
    
    def test_decimal_precision_in_rating(self):
        """Test decimal precision in average rating."""
        book_id = uuid.uuid4()
        now = datetime.utcnow()
        
        # High precision decimal
        precise_rating = Decimal("4.123456789")
        
        book = BookSummary(
            id=book_id,
            title="Precise Rating Book",
            author="Math Author",
            average_rating=precise_rating,
            total_reviews=1,
            created_at=now,
            updated_at=now
        )
        
        assert book.average_rating == precise_rating
