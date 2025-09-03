import pytest
from pydantic import ValidationError
from datetime import datetime
import uuid

from app.schemas.review import ReviewBase, ReviewCreate, ReviewUpdate, ReviewSummary


class TestReviewBase:
    """Test ReviewBase schema validation."""
    
    def test_valid_review_base(self):
        """Test valid ReviewBase creation."""
        review_data = {
            "rating": 5,
            "review_text": "Excellent book! Highly recommended."
        }
        
        review = ReviewBase(**review_data)
        
        assert review.rating == 5
        assert review.review_text == "Excellent book! Highly recommended."
    
    def test_review_base_rating_required(self):
        """Test rating is required in ReviewBase."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewBase(review_text="Great book!")
        
        assert "rating" in str(exc_info.value)
        assert "Field required" in str(exc_info.value)
    
    def test_review_base_rating_range_validation(self):
        """Test rating range validation (1-5)."""
        # Test invalid ratings
        invalid_ratings = [0, -1, 6, 10, -5]
        
        for invalid_rating in invalid_ratings:
            with pytest.raises(ValidationError) as exc_info:
                ReviewBase(rating=invalid_rating)
            
            error_msg = str(exc_info.value).lower()
            assert "input should be greater than or equal to 1" in error_msg or \
                   "input should be less than or equal to 5" in error_msg
    
    def test_review_base_valid_ratings(self):
        """Test all valid rating values."""
        valid_ratings = [1, 2, 3, 4, 5]
        
        for rating in valid_ratings:
            review = ReviewBase(rating=rating)
            assert review.rating == rating
    
    def test_review_base_optional_review_text(self):
        """Test review_text is optional."""
        review = ReviewBase(rating=4)
        
        assert review.rating == 4
        assert review.review_text is None
    
    def test_review_base_empty_review_text(self):
        """Test empty review text is allowed."""
        review = ReviewBase(rating=4, review_text="")
        
        assert review.rating == 4
        assert review.review_text == ""
    
    def test_review_base_review_text_length_validation(self):
        """Test review text length validation (max 2000 characters)."""
        long_text = "x" * 2001  # Exceeds limit
        
        with pytest.raises(ValidationError) as exc_info:
            ReviewBase(rating=5, review_text=long_text)
        
        assert "Review text cannot exceed 2000 characters" in str(exc_info.value)
    
    def test_review_base_max_review_text_length(self):
        """Test exactly maximum review text length."""
        max_text = "x" * 2000  # Exactly at limit
        review = ReviewBase(rating=5, review_text=max_text)
        
        assert review.review_text == max_text
    
    def test_review_base_rating_type_validation(self):
        """Test rating type coercion and validation."""
        # Pydantic V2 is more lenient with type coercion
        # String numbers and floats that can be converted to int are accepted
        valid_coercible = ["5", 5.0, True]  # These get coerced to valid integers
        
        for rating in valid_coercible:
            review = ReviewBase(rating=rating)
            assert isinstance(review.rating, int)
            assert 1 <= review.rating <= 5
        
        # These should still fail validation
        invalid_rating_types = ["five", "not_a_number"]
        
        for invalid_rating in invalid_rating_types:
            with pytest.raises(ValidationError):
                ReviewBase(rating=invalid_rating)


class TestReviewCreate:
    """Test ReviewCreate schema validation."""
    
    def test_valid_review_create(self):
        """Test valid ReviewCreate."""
        review_data = {
            "rating": 4,
            "review_text": "Good book with interesting plot."
        }
        
        review = ReviewCreate(**review_data)
        
        assert review.rating == 4
        assert review.review_text == "Good book with interesting plot."
    
    def test_review_create_inherits_validation(self):
        """Test ReviewCreate inherits all validation from ReviewBase."""
        # Rating required
        with pytest.raises(ValidationError):
            ReviewCreate(review_text="Great!")
        
        # Rating range validation
        with pytest.raises(ValidationError):
            ReviewCreate(rating=0)
        
        # Review text length validation
        with pytest.raises(ValidationError):
            ReviewCreate(rating=5, review_text="x" * 2001)
    
    def test_review_create_minimal_data(self):
        """Test ReviewCreate with minimal required data."""
        review = ReviewCreate(rating=3)
        
        assert review.rating == 3
        assert review.review_text is None


class TestReviewUpdate:
    """Test ReviewUpdate schema validation."""
    
    def test_valid_review_update(self):
        """Test valid ReviewUpdate."""
        update_data = {
            "rating": 5,
            "review_text": "Updated review text after re-reading."
        }
        
        review_update = ReviewUpdate(**update_data)
        
        assert review_update.rating == 5
        assert review_update.review_text == "Updated review text after re-reading."
    
    def test_review_update_all_fields_optional(self):
        """Test all fields are optional in ReviewUpdate."""
        review_update = ReviewUpdate()
        
        assert review_update.rating is None
        assert review_update.review_text is None
    
    def test_review_update_partial_updates(self):
        """Test partial field updates."""
        # Only rating
        review_update = ReviewUpdate(rating=4)
        assert review_update.rating == 4
        assert review_update.review_text is None
        
        # Only review text
        review_update = ReviewUpdate(review_text="New text")
        assert review_update.review_text == "New text"
        assert review_update.rating is None
    
    def test_review_update_rating_validation(self):
        """Test rating validation in ReviewUpdate."""
        # Invalid rating values
        with pytest.raises(ValidationError):
            ReviewUpdate(rating=0)
        
        with pytest.raises(ValidationError):
            ReviewUpdate(rating=6)
        
        # Valid rating values
        for rating in [1, 2, 3, 4, 5]:
            review_update = ReviewUpdate(rating=rating)
            assert review_update.rating == rating
    
    def test_review_update_review_text_validation(self):
        """Test review text validation in ReviewUpdate."""
        # Too long text
        with pytest.raises(ValidationError) as exc_info:
            ReviewUpdate(review_text="x" * 2001)
        
        assert "Review text cannot exceed 2000 characters" in str(exc_info.value)
        
        # Valid text
        valid_text = "x" * 2000
        review_update = ReviewUpdate(review_text=valid_text)
        assert review_update.review_text == valid_text
    
    def test_review_update_empty_values(self):
        """Test empty/None values in ReviewUpdate."""
        # Empty string for review text should be allowed
        review_update = ReviewUpdate(review_text="")
        assert review_update.review_text == ""
        
        # None values should be allowed (means no update)
        review_update = ReviewUpdate(rating=None, review_text=None)
        assert review_update.rating is None
        assert review_update.review_text is None


class TestReviewSummary:
    """Test ReviewSummary schema validation."""
    
    def test_valid_review_summary(self):
        """Test valid ReviewSummary."""
        user_id = uuid.uuid4()
        book_id = uuid.uuid4()
        review_id = uuid.uuid4()
        now = datetime.utcnow()
        
        review_data = {
            "id": review_id,
            "user_id": user_id,
            "book_id": book_id,
            "rating": 4,
            "review_text": "Good book!",
            "created_at": now,
            "updated_at": now
        }
        
        review = ReviewSummary(**review_data)
        
        assert review.id == review_id
        assert review.user_id == user_id
        assert review.book_id == book_id
        assert review.rating == 4
        assert review.review_text == "Good book!"
        assert review.created_at == now
        assert review.updated_at == now
    
    def test_review_summary_required_fields(self):
        """Test required fields in ReviewSummary."""
        required_fields = ["id", "user_id", "book_id", "rating", "created_at", "updated_at"]
        
        base_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "book_id": uuid.uuid4(),
            "rating": 5,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        for field in required_fields:
            incomplete_data = {k: v for k, v in base_data.items() if k != field}
            
            with pytest.raises(ValidationError) as exc_info:
                ReviewSummary(**incomplete_data)
            
            assert field in str(exc_info.value)
    
    def test_review_summary_uuid_validation(self):
        """Test UUID validation in ReviewSummary."""
        now = datetime.utcnow()
        
        # Invalid id
        with pytest.raises(ValidationError):
            ReviewSummary(
                id="not_a_uuid",
                user_id=uuid.uuid4(),
                book_id=uuid.uuid4(),
                rating=5,
                created_at=now,
                updated_at=now
            )
        
        # Invalid user_id
        with pytest.raises(ValidationError):
            ReviewSummary(
                id=uuid.uuid4(),
                user_id="not_a_uuid",
                book_id=uuid.uuid4(),
                rating=5,
                created_at=now,
                updated_at=now
            )
        
        # Invalid book_id
        with pytest.raises(ValidationError):
            ReviewSummary(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                book_id="not_a_uuid",
                rating=5,
                created_at=now,
                updated_at=now
            )
    
    def test_review_summary_datetime_validation(self):
        """Test datetime validation in ReviewSummary."""
        base_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "book_id": uuid.uuid4(),
            "rating": 5
        }
        
        # Invalid created_at
        with pytest.raises(ValidationError):
            ReviewSummary(
                **base_data,
                created_at="not_a_datetime",
                updated_at=datetime.utcnow()
            )
        
        # Invalid updated_at
        with pytest.raises(ValidationError):
            ReviewSummary(
                **base_data,
                created_at=datetime.utcnow(),
                updated_at="not_a_datetime"
            )


class TestReviewSchemaEdgeCases:
    """Test edge cases for review schemas."""
    
    def test_unicode_in_review_text(self):
        """Test unicode characters in review text."""
        unicode_text = "Great book! 📚✨ Très intéressant! 素晴らしい本です!"
        
        review = ReviewBase(rating=5, review_text=unicode_text)
        
        assert review.review_text == unicode_text
    
    def test_special_characters_in_review_text(self):
        """Test special characters in review text."""
        special_text = "Review with special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        
        review = ReviewBase(rating=4, review_text=special_text)
        
        assert review.review_text == special_text
    
    def test_multiline_review_text(self):
        """Test multiline review text."""
        multiline_text = """This is a multiline review.
        
        Paragraph 1: The plot was engaging.
        
        Paragraph 2: The characters were well developed.
        
        Overall: Highly recommended!"""
        
        review = ReviewBase(rating=5, review_text=multiline_text)
        
        assert review.review_text == multiline_text
    
    def test_whitespace_handling(self):
        """Test whitespace handling in review text."""
        # Leading/trailing whitespace
        text_with_whitespace = "  Review with spaces  "
        
        review = ReviewBase(rating=4, review_text=text_with_whitespace)
        
        # Pydantic preserves whitespace by default
        assert review.review_text == text_with_whitespace
    
    def test_null_vs_empty_review_text(self):
        """Test distinction between null and empty review text."""
        # None/null review text
        review_null = ReviewBase(rating=4, review_text=None)
        assert review_null.review_text is None
        
        # Empty string review text
        review_empty = ReviewBase(rating=4, review_text="")
        assert review_empty.review_text == ""
        
        # Default (should be None)
        review_default = ReviewBase(rating=4)
        assert review_default.review_text is None
    
    def test_rating_boundary_values(self):
        """Test rating boundary values."""
        # Minimum valid rating
        review_min = ReviewBase(rating=1)
        assert review_min.rating == 1
        
        # Maximum valid rating
        review_max = ReviewBase(rating=5)
        assert review_max.rating == 5
    
    def test_review_text_exactly_at_limit(self):
        """Test review text exactly at character limit."""
        # Exactly 2000 characters
        text_at_limit = "a" * 2000
        review = ReviewBase(rating=5, review_text=text_at_limit)
        assert len(review.review_text) == 2000
        
        # One character over limit should fail
        text_over_limit = "a" * 2001
        with pytest.raises(ValidationError):
            ReviewBase(rating=5, review_text=text_over_limit)
