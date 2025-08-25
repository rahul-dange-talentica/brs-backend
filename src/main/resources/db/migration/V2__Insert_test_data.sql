-- =====================================================
-- Book Review System - Test Data
-- Version: 1.0
-- Date: December 2024
-- =====================================================

-- Insert test users
INSERT INTO users (username, email, first_name, last_name, password, is_active) VALUES
('john_doe', 'john.doe@example.com', 'John', 'Doe', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDa', true),
('jane_smith', 'jane.smith@example.com', 'Jane', 'Smith', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDa', true),
('bob_wilson', 'bob.wilson@example.com', 'Bob', 'Wilson', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDa', true),
('alice_brown', 'alice.brown@example.com', 'Alice', 'Brown', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDa', true),
('charlie_davis', 'charlie.davis@example.com', 'Charlie', 'Davis', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iKTVEFDa', true);

-- Insert test books
INSERT INTO books (isbn, title, author, description, cover_image_url, genres, published_year) VALUES
('978-0-7475-3269-9', 'Harry Potter and the Philosopher''s Stone', 'J.K. Rowling', 'The first novel in the Harry Potter series, following the journey of a young wizard.', 'https://example.com/hp1.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 1997),
('978-0-7475-3270-5', 'Harry Potter and the Chamber of Secrets', 'J.K. Rowling', 'The second novel in the Harry Potter series.', 'https://example.com/hp2.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 1998),
('978-0-7475-3271-2', 'Harry Potter and the Prisoner of Azkaban', 'J.K. Rowling', 'The third novel in the Harry Potter series.', 'https://example.com/hp3.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 1999),
('978-0-7475-3272-9', 'Harry Potter and the Goblet of Fire', 'J.K. Rowling', 'The fourth novel in the Harry Potter series.', 'https://example.com/hp4.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 2000),
('978-0-7475-3273-6', 'Harry Potter and the Order of the Phoenix', 'J.K. Rowling', 'The fifth novel in the Harry Potter series.', 'https://example.com/hp5.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 2003),
('978-0-7475-3274-3', 'Harry Potter and the Half-Blood Prince', 'J.K. Rowling', 'The sixth novel in the Harry Potter series.', 'https://example.com/hp6.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 2005),
('978-0-7475-3275-0', 'Harry Potter and the Deathly Hallows', 'J.K. Rowling', 'The seventh and final novel in the Harry Potter series.', 'https://example.com/hp7.jpg', ARRAY['Fantasy', 'Adventure', 'Young Adult'], 2007),
('978-0-7475-3276-7', 'The Hobbit', 'J.R.R. Tolkien', 'A fantasy novel about a hobbit''s journey with thirteen dwarves.', 'https://example.com/hobbit.jpg', ARRAY['Fantasy', 'Adventure', 'Classic'], 1937),
('978-0-7475-3277-4', 'The Lord of the Rings: The Fellowship of the Ring', 'J.R.R. Tolkien', 'The first volume of The Lord of the Rings.', 'https://example.com/lotr1.jpg', ARRAY['Fantasy', 'Adventure', 'Classic'], 1954),
('978-0-7475-3278-1', 'The Lord of the Rings: The Two Towers', 'J.R.R. Tolkien', 'The second volume of The Lord of the Rings.', 'https://example.com/lotr2.jpg', ARRAY['Fantasy', 'Adventure', 'Classic'], 1954),
('978-0-7475-3279-8', 'The Lord of the Rings: The Return of the King', 'J.R.R. Tolkien', 'The third volume of The Lord of the Rings.', 'https://example.com/lotr3.jpg', ARRAY['Fantasy', 'Adventure', 'Classic'], 1955),
('978-0-7475-3280-4', 'The Catcher in the Rye', 'J.D. Salinger', 'A classic novel about teenage alienation and loss of innocence.', 'https://example.com/catcher.jpg', ARRAY['Fiction', 'Classic', 'Coming-of-age'], 1951),
('978-0-7475-3281-1', 'To Kill a Mockingbird', 'Harper Lee', 'A novel about racial injustice in the American South.', 'https://example.com/mockingbird.jpg', ARRAY['Fiction', 'Classic', 'Drama'], 1960),
('978-0-7475-3282-8', '1984', 'George Orwell', 'A dystopian novel about totalitarianism and surveillance society.', 'https://example.com/1984.jpg', ARRAY['Fiction', 'Dystopian', 'Classic'], 1949),
('978-0-7475-3283-5', 'Pride and Prejudice', 'Jane Austen', 'A romantic novel of manners set in Georgian-era England.', 'https://example.com/pride.jpg', ARRAY['Romance', 'Classic', 'Historical Fiction'], 1813),
('978-0-7475-3284-2', 'The Great Gatsby', 'F. Scott Fitzgerald', 'A novel about the American Dream and the Jazz Age.', 'https://example.com/gatsby.jpg', ARRAY['Fiction', 'Classic', 'Drama'], 1925),
('978-0-7475-3285-9', 'One Hundred Years of Solitude', 'Gabriel García Márquez', 'A magical realist novel about the Buendía family.', 'https://example.com/solitude.jpg', ARRAY['Magical Realism', 'Fiction', 'Classic'], 1967),
('978-0-7475-3286-6', 'The Alchemist', 'Paulo Coelho', 'A novel about a young Andalusian shepherd who dreams of finding a worldly treasure.', 'https://example.com/alchemist.jpg', ARRAY['Fiction', 'Adventure', 'Philosophy'], 1988),
('978-0-7475-3287-3', 'The Kite Runner', 'Khaled Hosseini', 'A novel about the unlikely friendship between a wealthy boy and the son of his father''s servant.', 'https://example.com/kite.jpg', ARRAY['Fiction', 'Drama', 'Historical Fiction'], 2003),
('978-0-7475-3288-0', 'The Book Thief', 'Markus Zusak', 'A novel set in Nazi Germany, narrated by Death.', 'https://example.com/bookthief.jpg', ARRAY['Historical Fiction', 'Drama', 'Young Adult'], 2005);

-- Insert test reviews
INSERT INTO reviews (book_id, user_id, rating, review_text) VALUES
(1, 1, 5, 'Absolutely magical! A perfect introduction to the wizarding world.'),
(1, 2, 4, 'Great book for all ages. The world-building is incredible.'),
(1, 3, 5, 'One of my favorite books ever. J.K. Rowling is a master storyteller.'),
(2, 1, 4, 'Excellent sequel that builds on the first book perfectly.'),
(2, 2, 5, 'Even better than the first! The mystery element adds so much.'),
(3, 1, 5, 'The best book in the series! The time travel plot is brilliant.'),
(3, 3, 4, 'Great character development and an exciting plot.'),
(4, 2, 5, 'The tournament concept is fantastic. Really raises the stakes.'),
(4, 4, 4, 'Excellent world-building and character development.'),
(5, 1, 4, 'Longer but worth it. The Order and prophecy elements are great.'),
(6, 2, 5, 'Dark and complex. The best book in the series.'),
(6, 3, 4, 'Excellent character development and plot twists.'),
(7, 1, 5, 'Perfect conclusion to an amazing series.'),
(7, 2, 5, 'Emotional and satisfying ending. A masterpiece.'),
(8, 4, 5, 'Classic fantasy that never gets old.'),
(8, 5, 4, 'Wonderful adventure story with great characters.'),
(9, 1, 5, 'Epic fantasy at its finest.'),
(9, 3, 5, 'The world-building is absolutely incredible.'),
(10, 2, 4, 'Great continuation of the story.'),
(11, 1, 5, 'Perfect ending to an epic trilogy.'),
(12, 4, 4, 'Classic coming-of-age story.'),
(12, 5, 3, 'Good but a bit dated for modern readers.'),
(13, 1, 5, 'Powerful and important book.'),
(13, 2, 5, 'A must-read classic.'),
(14, 3, 4, 'Disturbing but brilliant dystopian novel.'),
(15, 4, 4, 'Charming romance with witty dialogue.'),
(16, 5, 5, 'Beautifully written American classic.'),
(17, 1, 4, 'Magical realism at its best.'),
(18, 2, 4, 'Inspiring and philosophical.'),
(19, 3, 5, 'Heartbreaking and beautiful.'),
(20, 4, 4, 'Unique perspective on WWII. Beautifully written.');

-- Insert test favorites
INSERT INTO favorites (user_id, book_id) VALUES
(1, 1), (1, 3), (1, 6), (1, 9), (1, 13),
(2, 1), (2, 2), (2, 4), (2, 6), (2, 20),
(3, 1), (3, 3), (3, 9), (3, 19),
(4, 8), (4, 13), (4, 15), (4, 20),
(5, 8), (5, 12), (5, 16);
