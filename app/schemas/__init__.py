from .user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
)
from .genre import (
    GenreBase,
    GenreCreate,
    GenreUpdate,
    GenreResponse,
    GenreWithBooks,
)
from .book import (
    BookBase,
    BookCreate,
    BookUpdate,
    BookSummary,
    BookResponse,
    BookWithStats,
)
from .review import (
    ReviewBase,
    ReviewCreate,
    ReviewUpdate,
    ReviewSummary,
    ReviewResponse,
    ReviewWithUser,
)
from .user_favorite import (
    UserFavoriteBase,
    UserFavoriteCreate,
    UserFavoriteResponse,
    UserFavoriteWithBook,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate", 
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    # Genre schemas
    "GenreBase",
    "GenreCreate",
    "GenreUpdate", 
    "GenreResponse",
    "GenreWithBooks",
    # Book schemas
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "BookSummary", 
    "BookResponse",
    "BookWithStats",
    # Review schemas
    "ReviewBase",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewSummary",
    "ReviewResponse", 
    "ReviewWithUser",
    # User favorite schemas
    "UserFavoriteBase",
    "UserFavoriteCreate",
    "UserFavoriteResponse",
    "UserFavoriteWithBook",
]
