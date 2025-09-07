#!/usr/bin/env python3
"""
Seed data script for BRS Backend
Populates the database with initial books and genres for demo/testing purposes
"""

import asyncio
import sys
import uuid
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add the app directory to the path so we can import our models
sys.path.append('/app')

from app.database import engine
from app.models.book import Book
from app.models.genre import Genre
from app.models.book_genre import book_genres


def create_seed_data():
    """Create seed data for genres and books"""
    
    # Sample genres data
    genres_data = [
        {
            "name": "Fiction",
            "description": "Literary works that are imaginary or invented rather than factual"
        },
        {
            "name": "Science Fiction", 
            "description": "Fiction that deals with futuristic concepts and advanced science and technology"
        },
        {
            "name": "Fantasy",
            "description": "Fiction that contains magical or supernatural elements"
        },
        {
            "name": "Mystery",
            "description": "Fiction dealing with puzzling crimes and their solutions"
        },
        {
            "name": "Romance",
            "description": "Fiction that focuses on love stories and relationships"
        },
        {
            "name": "Thriller",
            "description": "Fiction characterized by suspense, excitement, and high emotional impact"
        },
        {
            "name": "Biography",
            "description": "Non-fiction accounts of someone's life written by another person"
        },
        {
            "name": "History",
            "description": "Non-fiction books about past events and civilizations"
        },
        {
            "name": "Self-Help",
            "description": "Books designed to help readers improve aspects of their lives"
        },
        {
            "name": "Technology",
            "description": "Books about computers, programming, and technological advancement"
        }
    ]
    
    # Sample books data
    books_data = [
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "isbn": "9780743273565",
            "description": "A classic American novel about the Jazz Age and the American Dream",
            "publication_date": date(1925, 4, 10),
            "average_rating": Decimal("4.2"),
            "total_reviews": 1523,
            "genres": ["Fiction"]
        },
        {
            "title": "Dune",
            "author": "Frank Herbert",
            "isbn": "9780441172719",
            "description": "A science fiction epic set on the desert planet Arrakis",
            "publication_date": date(1965, 8, 1),
            "average_rating": Decimal("4.5"),
            "total_reviews": 2156,
            "genres": ["Science Fiction", "Fiction"]
        },
        {
            "title": "The Lord of the Rings: The Fellowship of the Ring",
            "author": "J.R.R. Tolkien",
            "isbn": "9780547928210",
            "description": "The first volume of the epic fantasy trilogy",
            "publication_date": date(1954, 7, 29),
            "average_rating": Decimal("4.7"),
            "total_reviews": 3421,
            "genres": ["Fantasy", "Fiction"]
        },
        {
            "title": "Murder on the Orient Express",
            "author": "Agatha Christie",
            "isbn": "9780062693662",
            "description": "A classic mystery featuring detective Hercule Poirot",
            "publication_date": date(1934, 1, 1),
            "average_rating": Decimal("4.3"),
            "total_reviews": 1876,
            "genres": ["Mystery", "Fiction"]
        },
        {
            "title": "Pride and Prejudice",
            "author": "Jane Austen",
            "isbn": "9780141439518",
            "description": "A romantic novel about Elizabeth Bennet and Mr. Darcy",
            "publication_date": date(1813, 1, 28),
            "average_rating": Decimal("4.4"),
            "total_reviews": 2943,
            "genres": ["Romance", "Fiction"]
        },
        {
            "title": "The Girl with the Dragon Tattoo",
            "author": "Stieg Larsson",
            "isbn": "9780307949486",
            "description": "A psychological thriller about murder and corruption",
            "publication_date": date(2005, 8, 1),
            "average_rating": Decimal("4.1"),
            "total_reviews": 1654,
            "genres": ["Thriller", "Mystery"]
        },
        {
            "title": "Steve Jobs",
            "author": "Walter Isaacson",
            "isbn": "9781451648539",
            "description": "The authorized biography of Apple's co-founder",
            "publication_date": date(2011, 10, 24),
            "average_rating": Decimal("4.3"),
            "total_reviews": 987,
            "genres": ["Biography", "Technology"]
        },
        {
            "title": "Sapiens: A Brief History of Humankind",
            "author": "Yuval Noah Harari",
            "isbn": "9780062316110",
            "description": "An exploration of human history and evolution",
            "publication_date": date(2014, 2, 10),
            "average_rating": Decimal("4.6"),
            "total_reviews": 2134,
            "genres": ["History"]
        },
        {
            "title": "Atomic Habits",
            "author": "James Clear",
            "isbn": "9780735211292",
            "description": "An easy and proven way to build good habits and break bad ones",
            "publication_date": date(2018, 10, 16),
            "average_rating": Decimal("4.8"),
            "total_reviews": 3542,
            "genres": ["Self-Help"]
        },
        {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "9780132350884",
            "description": "A handbook of agile software craftsmanship",
            "publication_date": date(2008, 8, 1),
            "average_rating": Decimal("4.4"),
            "total_reviews": 1432,
            "genres": ["Technology"]
        },
        {
            "title": "1984",
            "author": "George Orwell",
            "isbn": "9780451524935",
            "description": "A dystopian social science fiction novel about totalitarian control",
            "publication_date": date(1949, 6, 8),
            "average_rating": Decimal("4.5"),
            "total_reviews": 4321,
            "genres": ["Fiction", "Science Fiction"]
        },
        {
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "isbn": "9780547928227",
            "description": "A fantasy adventure about Bilbo Baggins and his unexpected journey",
            "publication_date": date(1937, 9, 21),
            "average_rating": Decimal("4.6"),
            "total_reviews": 2876,
            "genres": ["Fantasy", "Fiction"]
        }
    ]
    
    print("🌱 Starting database seeding...")
    
    with Session(engine) as session:
        try:
            # Check if data already exists
            existing_genres = session.query(Genre).count()
            existing_books = session.query(Book).count()
            
            if existing_genres > 0 or existing_books > 0:
                print(f"📚 Database already contains {existing_genres} genres and {existing_books} books")
                print("⏭️  Skipping seed data insertion")
                return
            
            print("📝 Creating genres...")
            genre_map = {}
            for genre_data in genres_data:
                genre = Genre(
                    id=uuid.uuid4(),
                    name=genre_data["name"],
                    description=genre_data["description"]
                )
                session.add(genre)
                genre_map[genre_data["name"]] = genre
                print(f"   ✓ {genre_data['name']}")
            
            session.flush()  # Get IDs for genres
            
            print("📚 Creating books...")
            for book_data in books_data:
                book = Book(
                    id=uuid.uuid4(),
                    title=book_data["title"],
                    author=book_data["author"],
                    isbn=book_data["isbn"],
                    description=book_data["description"],
                    publication_date=book_data["publication_date"],
                    average_rating=book_data["average_rating"],
                    total_reviews=book_data["total_reviews"]
                )
                session.add(book)
                session.flush()  # Get ID for book
                
                # Add genre associations
                for genre_name in book_data["genres"]:
                    if genre_name in genre_map:
                        # Insert into association table
                        session.execute(
                            book_genres.insert().values(
                                book_id=book.id,
                                genre_id=genre_map[genre_name].id
                            )
                        )
                
                print(f"   ✓ {book_data['title']} by {book_data['author']}")
            
            session.commit()
            
            # Verify counts
            final_genres = session.query(Genre).count()
            final_books = session.query(Book).count()
            final_associations = session.execute(text("SELECT COUNT(*) FROM book_genres")).scalar()
            
            print(f"✅ Seed data created successfully!")
            print(f"   📁 {final_genres} genres")
            print(f"   📚 {final_books} books") 
            print(f"   🔗 {final_associations} book-genre associations")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating seed data: {e}")
            raise


if __name__ == "__main__":
    print("🚀 BRS Database Seeding Script")
    create_seed_data()
    print("🎉 Seeding complete!")

