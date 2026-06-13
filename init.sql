-- Sample users
INSERT INTO users (username, email, password_hash, bio) VALUES
('alice', 'alice@example.com', 'hashed_password_1', 'Fantasy and sci-fi lover'),
('bob', 'bob@example.com', 'hashed_password_2', 'Reading one book at a time'),
('charlie', 'charlie@example.com', 'hashed_password_3', 'Book reviewer and blogger'),
('diana', 'diana@example.com', 'hashed_password_4', 'Always looking for recommendations');

-- Sample books
INSERT INTO books (
    title,
    author,
    isbn,
    description,
    published_date,
    page_count,
    average_rating
) VALUES
(
    'The Hobbit',
    'J.R.R. Tolkien',
    '9780547928227',
    'A fantasy adventure before the Lord of the Rings.',
    '1937-09-21',
    310,
    4.8
),
(
    '1984',
    'George Orwell',
    '9780451524935',
    'A dystopian novel about surveillance and control.',
    '1949-06-08',
    328,
    4.7
),
(
    'Dune',
    'Frank Herbert',
    '9780441172719',
    'Epic science fiction set on the desert planet Arrakis.',
    '1965-08-01',
    412,
    4.9
),
(
    'Atomic Habits',
    'James Clear',
    '9780735211292',
    'Practical guide to building good habits.',
    '2018-10-16',
    320,
    4.6
);

-- User reading lists
INSERT INTO user_books (
    user_id,
    book_id,
    status,
    rating,
    review,
    start_date,
    finish_date
) VALUES
(
    1,
    1,
    'read',
    5.0,
    'One of my favorite fantasy books.',
    '2024-01-01',
    '2024-01-10'
),
(
    1,
    3,
    'currently_reading',
    NULL,
    NULL,
    '2025-01-15',
    NULL
),
(
    2,
    2,
    'read',
    4.5,
    'Still relevant today.',
    '2024-02-01',
    '2024-02-05'
),
(
    3,
    4,
    'want_to_read',
    NULL,
    NULL,
    NULL,
    NULL
),
(
    4,
    3,
    'read',
    5.0,
    'Amazing world-building.',
    '2024-03-01',
    '2024-03-20'
);

-- Likes
INSERT INTO likes (user_id, book_id) VALUES
(1, 3),
(2, 2),
(3, 1),
(4, 3),
(4, 1);

-- Follows
INSERT INTO follows (follower_id, following_id) VALUES
(1, 2),
(1, 3),
(2, 1),
(3, 4),
(4, 1);