-- =====================================================
-- Book Review System - Initial Database Schema
-- Version: 1.0
-- Date: December 2024
-- =====================================================

-- Enable UUID extension for future use
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Users Table
-- =====================================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- =====================================================
-- Books Table
-- =====================================================
CREATE TABLE books (
    id BIGSERIAL PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_url TEXT,
    genres TEXT[] NOT NULL DEFAULT '{}',
    published_year INTEGER,
    average_rating DECIMAL(2,1) DEFAULT 0.0,
    total_ratings INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- =====================================================
-- Reviews Table
-- =====================================================
CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    rating INTEGER NOT NULL,
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    CONSTRAINT fk_reviews_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT chk_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT uk_review_unique UNIQUE(book_id, user_id)
);

-- =====================================================
-- Favorites Table
-- =====================================================
CREATE TABLE favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_favorites_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    CONSTRAINT uk_favorite_unique UNIQUE(user_id, book_id)
);

-- =====================================================
-- Performance Indexes
-- =====================================================

-- Users table indexes
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE deleted_at IS NULL;

-- Books table indexes
CREATE INDEX idx_books_author ON books(author) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_published_year ON books(published_year) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_genres ON books USING GIN(genres) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_average_rating ON books(average_rating) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_total_ratings ON books(total_ratings) WHERE deleted_at IS NULL;
CREATE INDEX idx_books_isbn ON books(isbn) WHERE deleted_at IS NULL;

-- Reviews table indexes
CREATE INDEX idx_reviews_book_id ON reviews(book_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_reviews_user_id ON reviews(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_reviews_rating ON reviews(rating) WHERE deleted_at IS NULL;
CREATE INDEX idx_reviews_created_at ON reviews(created_at) WHERE deleted_at IS NULL;

-- Favorites table indexes
CREATE INDEX idx_favorites_user_id ON favorites(user_id);
CREATE INDEX idx_favorites_book_id ON favorites(book_id);
CREATE INDEX idx_favorites_created_at ON favorites(created_at);

-- =====================================================
-- Full-text Search Index
-- =====================================================
CREATE INDEX idx_books_search ON books USING gin(
    to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(author, '') || ' ' || 
        COALESCE(description, '') || ' ' || 
        COALESCE(cover_image_url, '')
    )
) WHERE deleted_at IS NULL;

-- =====================================================
-- Rating Aggregation Function
-- =====================================================
CREATE OR REPLACE FUNCTION update_book_rating()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE books 
        SET average_rating = ROUND(
            ((average_rating * total_ratings + NEW.rating) / (total_ratings + 1))::numeric, 1
        ),
            total_ratings = total_ratings + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.book_id;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE books 
        SET average_rating = ROUND(
            ((average_rating * total_ratings - OLD.rating + NEW.rating) / total_ratings)::numeric, 1
        ),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.book_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE books 
        SET average_rating = CASE 
            WHEN total_ratings > 1 THEN ROUND(
                ((average_rating * total_ratings - OLD.rating) / (total_ratings - 1))::numeric, 1
            )
            ELSE 0.0
        END,
        total_ratings = GREATEST(total_ratings - 1, 0),
        updated_at = CURRENT_TIMESTAMP
        WHERE id = OLD.book_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Rating Update Triggers
-- =====================================================
CREATE TRIGGER trigger_review_rating_insert
    AFTER INSERT ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_book_rating();

CREATE TRIGGER trigger_review_rating_update
    AFTER UPDATE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_book_rating();

CREATE TRIGGER trigger_review_rating_delete
    AFTER DELETE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_book_rating();

-- =====================================================
-- Updated Timestamp Triggers
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Comments
-- =====================================================
COMMENT ON TABLE users IS 'User accounts for the Book Review System';
COMMENT ON TABLE books IS 'Book catalog with metadata and aggregated ratings';
COMMENT ON TABLE reviews IS 'User reviews and ratings for books';
COMMENT ON TABLE favorites IS 'User favorite books relationship';

COMMENT ON COLUMN books.genres IS 'Array of book genres for flexible categorization';
COMMENT ON COLUMN books.average_rating IS 'Aggregated average rating (1-5 scale)';
COMMENT ON COLUMN books.total_ratings IS 'Total number of active reviews';
COMMENT ON COLUMN reviews.rating IS 'User rating from 1-5 stars';
