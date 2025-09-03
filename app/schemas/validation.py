"""Enhanced validation models with comprehensive input validation."""

from pydantic import BaseModel, validator, EmailStr, Field, UUID4
from typing import Optional, List
import re
from datetime import date, datetime
from decimal import Decimal


class EnhancedUserCreate(BaseModel):
    """Enhanced user creation schema with comprehensive validation."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password")
    first_name: str = Field(..., min_length=1, max_length=50, description="User first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User last name")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        # Check for common weak patterns
        if re.search(r'(.)\1{2,}', v):  # Three or more consecutive identical characters
            raise ValueError('Password cannot contain three or more consecutive identical characters')
        if v.lower() in ['password', '12345678', 'qwerty', 'abc123']:
            raise ValueError('Password is too common and not secure')
        return v
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Validate name fields."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v.strip()) < 1:
            raise ValueError('Name must be at least 1 character long')
        if len(v) > 50:
            raise ValueError('Name cannot exceed 50 characters')
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
        # Check for suspicious patterns
        if re.search(r'[<>{}]', v):
            raise ValueError('Name contains invalid characters')
        return v.strip()
    
    @validator('email')
    def validate_email_additional(cls, v):
        """Additional email validation."""
        email_str = str(v).lower()
        # Check for disposable email domains (basic list)
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'tempmail.org',
            'mailinator.com', 'throwaway.email'
        ]
        domain = email_str.split('@')[1] if '@' in email_str else ''
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')
        return v


class EnhancedUserUpdate(BaseModel):
    """Enhanced user update schema with validation."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User last name")
    email: Optional[EmailStr] = Field(None, description="User email address")
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Validate name fields."""
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty')
            if len(v) > 50:
                raise ValueError('Name cannot exceed 50 characters')
            if not re.match(r'^[a-zA-Z\s\-\'\.]+$', v):
                raise ValueError('Name can only contain letters, spaces, hyphens, apostrophes, and periods')
            return v.strip()
        return v


class EnhancedBookCreate(BaseModel):
    """Enhanced book creation schema with comprehensive validation."""
    title: str = Field(..., min_length=1, max_length=500, description="Book title")
    author: str = Field(..., min_length=1, max_length=300, description="Book author")
    isbn: Optional[str] = Field(None, max_length=17, description="Book ISBN")
    description: Optional[str] = Field(None, max_length=2000, description="Book description")
    cover_image_url: Optional[str] = Field(None, max_length=1000, description="Book cover image URL")
    publication_date: Optional[date] = Field(None, description="Book publication date")
    genre_ids: List[UUID4] = Field(default_factory=list, description="Genre IDs associated with the book")
    
    @validator('title', 'author')
    def validate_required_fields(cls, v):
        """Validate required text fields."""
        if not v or not v.strip():
            raise ValueError('This field is required and cannot be empty')
        if len(v.strip()) < 1:
            raise ValueError('Field must be at least 1 character long')
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', v.strip())
        # Check for suspicious content
        if re.search(r'[<>{}]', cleaned):
            raise ValueError('Field contains invalid characters')
        return cleaned
    
    @validator('isbn')
    def validate_isbn(cls, v):
        """Validate ISBN format."""
        if v:
            # Remove hyphens, spaces, and other common separators
            isbn = re.sub(r'[-\s]', '', v)
            # Check if it's a valid ISBN-10 or ISBN-13
            if not re.match(r'^\d{10}$|^\d{13}$', isbn):
                raise ValueError('ISBN must be 10 or 13 digits')
            # Basic ISBN checksum validation for ISBN-10
            if len(isbn) == 10:
                try:
                    checksum = sum(int(isbn[i]) * (10 - i) for i in range(9))
                    check_digit = (11 - checksum % 11) % 11
                    if check_digit == 10:
                        check_digit = 'X'
                    if str(check_digit) != isbn[9].upper():
                        raise ValueError('Invalid ISBN-10 checksum')
                except (ValueError, IndexError):
                    raise ValueError('Invalid ISBN format')
            return isbn
        return v
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description field."""
        if v:
            if len(v.strip()) == 0:
                return None  # Convert empty string to None
            if len(v) > 2000:
                raise ValueError('Description cannot exceed 2000 characters')
            # Basic content validation
            if re.search(r'[<>]', v):
                raise ValueError('Description contains invalid characters')
            return v.strip()
        return v
    
    @validator('cover_image_url')
    def validate_image_url(cls, v):
        """Validate image URL format."""
        if v:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(v):
                raise ValueError('Invalid URL format')
            # Check for common image extensions
            if not re.search(r'\.(jpg|jpeg|png|gif|webp)(\?.*)?$', v.lower()):
                raise ValueError('URL must point to a valid image file (jpg, jpeg, png, gif, webp)')
        return v
    
    @validator('publication_date')
    def validate_publication_date(cls, v):
        """Validate publication date."""
        if v:
            if v > date.today():
                raise ValueError('Publication date cannot be in the future')
            if v.year < 1000:
                raise ValueError('Publication date must be after year 1000')
        return v
    
    @validator('genre_ids')
    def validate_genre_ids(cls, v):
        """Validate genre IDs list."""
        if len(v) > 10:
            raise ValueError('A book cannot have more than 10 genres')
        # Remove duplicates while preserving order
        seen = set()
        unique_genres = []
        for genre_id in v:
            if genre_id not in seen:
                seen.add(genre_id)
                unique_genres.append(genre_id)
        return unique_genres


class EnhancedBookUpdate(BaseModel):
    """Enhanced book update schema with validation."""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Book title")
    author: Optional[str] = Field(None, min_length=1, max_length=300, description="Book author")
    isbn: Optional[str] = Field(None, max_length=17, description="Book ISBN")
    description: Optional[str] = Field(None, max_length=2000, description="Book description")
    cover_image_url: Optional[str] = Field(None, max_length=1000, description="Book cover image URL")
    publication_date: Optional[date] = Field(None, description="Book publication date")
    genre_ids: Optional[List[UUID4]] = Field(None, description="Genre IDs associated with the book")
    
    # Apply the same validators as create schema
    _validate_title_author = validator('title', 'author', allow_reuse=True)(EnhancedBookCreate.validate_required_fields)
    _validate_isbn = validator('isbn', allow_reuse=True)(EnhancedBookCreate.validate_isbn)
    _validate_description = validator('description', allow_reuse=True)(EnhancedBookCreate.validate_description)
    _validate_image_url = validator('cover_image_url', allow_reuse=True)(EnhancedBookCreate.validate_image_url)
    _validate_publication_date = validator('publication_date', allow_reuse=True)(EnhancedBookCreate.validate_publication_date)
    _validate_genre_ids = validator('genre_ids', allow_reuse=True)(EnhancedBookCreate.validate_genre_ids)


class EnhancedReviewCreate(BaseModel):
    """Enhanced review creation schema with validation."""
    rating: int = Field(..., ge=1, le=5, description="Book rating (1-5)")
    review_text: Optional[str] = Field(None, max_length=2000, description="Review text")
    
    @validator('rating')
    def validate_rating(cls, v):
        """Validate rating value."""
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('review_text')
    def validate_review_text(cls, v):
        """Validate review text."""
        if v is not None:
            if len(v.strip()) == 0:
                return None  # Convert empty string to None
            if len(v) > 2000:
                raise ValueError('Review text cannot exceed 2000 characters')
            if len(v.strip()) < 10:
                raise ValueError('Review text must be at least 10 characters long')
            # Basic content validation
            if re.search(r'[<>{}]', v):
                raise ValueError('Review text contains invalid characters')
            # Check for spam patterns
            if re.search(r'(.)\1{10,}', v):  # 10+ consecutive identical characters
                raise ValueError('Review text appears to contain spam')
            return v.strip()
        return v


class EnhancedReviewUpdate(BaseModel):
    """Enhanced review update schema with validation."""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Book rating (1-5)")
    review_text: Optional[str] = Field(None, max_length=2000, description="Review text")
    
    # Apply the same validators as create schema
    _validate_rating = validator('rating', allow_reuse=True)(EnhancedReviewCreate.validate_rating)
    _validate_review_text = validator('review_text', allow_reuse=True)(EnhancedReviewCreate.validate_review_text)


class EnhancedGenreCreate(BaseModel):
    """Enhanced genre creation schema with validation."""
    name: str = Field(..., min_length=1, max_length=100, description="Genre name")
    description: Optional[str] = Field(None, max_length=500, description="Genre description")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate genre name."""
        if not v or not v.strip():
            raise ValueError('Genre name is required and cannot be empty')
        if len(v.strip()) < 1:
            raise ValueError('Genre name must be at least 1 character long')
        # Normalize name
        cleaned = re.sub(r'\s+', ' ', v.strip().title())
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z\s\-&]+$', cleaned):
            raise ValueError('Genre name can only contain letters, spaces, hyphens, and ampersands')
        return cleaned
    
    @validator('description')
    def validate_description(cls, v):
        """Validate genre description."""
        if v:
            if len(v.strip()) == 0:
                return None
            if len(v) > 500:
                raise ValueError('Description cannot exceed 500 characters')
            if re.search(r'[<>{}]', v):
                raise ValueError('Description contains invalid characters')
            return v.strip()
        return v


class EnhancedGenreUpdate(BaseModel):
    """Enhanced genre update schema with validation."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Genre name")
    description: Optional[str] = Field(None, max_length=500, description="Genre description")
    
    # Apply the same validators as create schema
    _validate_name = validator('name', allow_reuse=True)(EnhancedGenreCreate.validate_name)
    _validate_description = validator('description', allow_reuse=True)(EnhancedGenreCreate.validate_description)


class PaginationParams(BaseModel):
    """Enhanced pagination parameters with validation."""
    page: int = Field(1, ge=1, le=10000, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    @validator('page')
    def validate_page(cls, v):
        """Validate page number."""
        if v < 1:
            raise ValueError('Page number must be 1 or greater')
        if v > 10000:
            raise ValueError('Page number cannot exceed 10000')
        return v
    
    @validator('per_page')
    def validate_per_page(cls, v):
        """Validate items per page."""
        if v < 1:
            raise ValueError('Items per page must be 1 or greater')
        if v > 100:
            raise ValueError('Items per page cannot exceed 100')
        return v


class SearchParams(BaseModel):
    """Enhanced search parameters with validation."""
    q: Optional[str] = Field(None, min_length=1, max_length=200, description="Search query")
    sort_by: str = Field(
        "created_at",
        regex=r"^(title|author|average_rating|publication_date|created_at|updated_at)$",
        description="Sort field"
    )
    sort_order: str = Field(
        "desc",
        regex=r"^(asc|desc)$",
        description="Sort order"
    )
    
    @validator('q')
    def validate_search_query(cls, v):
        """Validate search query."""
        if v:
            if len(v.strip()) == 0:
                return None
            if len(v.strip()) < 1:
                raise ValueError('Search query must be at least 1 character long')
            # Basic sanitization
            cleaned = re.sub(r'\s+', ' ', v.strip())
            if re.search(r'[<>{}]', cleaned):
                raise ValueError('Search query contains invalid characters')
            return cleaned
        return v
