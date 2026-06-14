-- USERS

INSERT INTO users (username, email, password_hash, bio) VALUES
('SirBarksALot', 'dog@example.com', 'hashed_pw', 'Professional squirrel researcher'),
('ProfessorWhiskers', 'cat@example.com', 'hashed_pw', 'Expert in human manipulation'),
('Moozilla', 'cow@example.com', 'hashed_pw', 'Grass connoisseur and philosopher'),
('CaptainQuack', 'duck@example.com', 'hashed_pw', 'Part-time detective'),
('LordHamster', 'hamster@example.com', 'hashed_pw', 'Collector of tiny furniture');

-- BOOKS

INSERT INTO books
(title, author, isbn, genre, description, page_count, average_rating, created_by)
VALUES

(
'Understanding Cats: A Survival Guide',
'Professor Whiskers',
'9780000000001',
'Self-Help',
'A comprehensive guide for surviving life with cats.',
250,
0,
2
),

(
'101 Squirrels and Where to Chase Them',
'Sir Barks A Lot',
'9780000000002',
'Adventure',
'A field guide to the worlds most suspicious squirrels.',
320,
0,
1
),

(
'The Grass Is Always Greener',
'Moozilla',
'9780000000003',
'Philosophy',
'A deep philosophical discussion about grass quality.',
180,
0,
3
),

(
'Quack Holmes and the Missing Bread',
'Captain Quack',
'9780000000004',
'Mystery',
'A thrilling investigation into a stolen loaf of bread.',
290,
0,
4
),

(
'Tiny Houses for Tiny Rodents',
'Lord Hamster',
'9780000000005',
'Home & Garden',
'Luxury interior design for hamsters.',
120,
0,
5
),

(
'Advanced Techniques in Knocking Things Off Tables',
'Professor Whiskers',
'9780000000006',
'Education',
'A masterclass for ambitious cats.',
150,
0,
2
),

(
'Who Is a Good Boy? A Scientific Study',
'Sir Barks A Lot',
'9780000000007',
'Science',
'Peer-reviewed evidence that dogs are good boys.',
400,
0,
1
),

(
'The Great Hay Debate',
'Moozilla',
'9780000000008',
'Politics',
'An exploration of hay taxation and grazing rights.',
220,
0,
3
);

-- USER BOOKS / REVIEWS

INSERT INTO user_books
(user_id, book_id, status, rating, review)
VALUES

(1,1,'read',2,'This book claims cats are superior. Clearly biased.'),

(3,1,'read',5,'Excellent. I finally understand why cats knock things off shelves.'),

(4,1,'read',4,'Very informative, though slightly anti-duck.'),

(2,2,'read',1,'Dog propaganda.'),

(4,2,'read',4,'Inspired me to chase something immediately.'),

(5,2,'read',3,'Not enough chapters about small rodents.'),

(5,3,'read',5,'I cried twice. The chapter on premium grass changed my life.'),

(1,3,'read',3,'Interesting but lacked squirrel content.'),

(2,4,'read',5,'Outstanding detective work.'),

(1,4,'read',4,'I knew the bread was suspicious from chapter one.'),

(3,5,'read',5,'Tiny furniture is the future.'),

(2,6,'read',5,'A masterpiece. Every cat should own a copy.'),

(1,7,'read',5,'Finally, science confirms what I already knew.'),

(3,8,'read',4,'A compelling argument for better hay policies.'),

(5,8,'want_to_read',NULL,NULL),

(4,6,'currently_reading',NULL,NULL);

-- LIKES

INSERT INTO likes (user_id, book_id) VALUES
(1,2),
(1,7),
(2,1),
(2,6),
(3,1),
(3,3),
(4,2),
(4,4),
(5,3),
(5,5),
(1,4),
(2,8),
(3,8);

-- FOLLOWS

INSERT INTO follows (follower_id, following_id) VALUES
(1,2),
(2,1),
(3,2),
(4,1),
(5,3),
(1,4),
(2,3),
(5,2);

-- RECALCULATE BOOK AVERAGE RATINGS

UPDATE books
SET average_rating = COALESCE(
(
    SELECT ROUND(AVG(rating), 2)
    FROM user_books
    WHERE user_books.book_id = books.id
      AND rating IS NOT NULL
),
0
);