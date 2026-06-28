-- USERS

INSERT INTO users 
(username, email, password_hash)
VALUES

('SirBarksALot', 'dog@example.com', 'hashed_pw'),
('ProfessorWhiskers', 'cat@example.com', 'hashed_pw'),
('Moozilla', 'cow@example.com', 'hashed_pw'),
('CaptainQuack', 'duck@example.com', 'hashed_pw'),
('LordHamster', 'hamster@example.com', 'hashed_pw'),
('QueenPaws', 'queen@example.com', 'hashed_pw'),
('SlyFoxington', 'fox@example.com', 'hashed_pw'),
('TinyTurtle', 'turtle@example.com', 'hashed_pw'),
('NightOwl', 'owl@example.com', 'hashed_pw'),
('DragonFlame', 'dragon@example.com', 'hashed_pw');


-- BOOKS

INSERT INTO books
(title, author, isbn, genre, description, page_count, average_rating, created_by)
VALUES

(
'Understanding Cats: A Survival Guide',
'Professor Whiskers',
'9780000000001',
'Self-Help',
'A practical guide explaining feline behaviour, mysterious midnight activities, and the proper way to serve cats.',
250,
0,
2
),

(
'101 Squirrels and Where to Chase Them',
'Sir Barks A Lot',
'9780000000002',
'Adventure',
'A thrilling adventure following a dog determined to solve the mystery of disappearing squirrels.',
320,
0,
1
),

(
'The Grass Is Always Greener',
'Moozilla',
'9780000000003',
'Philosophy',
'A philosophical exploration of happiness, grass quality, and the meaning of a perfect field.',
180,
0,
3
),

(
'Quack Holmes and the Missing Bread',
'Captain Quack',
'9780000000004',
'Mystery',
'A detective story about a duck investigating the disappearance of a very suspicious loaf.',
290,
0,
4
),

(
'Tiny Houses for Tiny Rodents',
'Lord Hamster',
'9780000000005',
'Non-Fiction',
'An interior design guide for creating comfortable and luxurious homes for small animals.',
120,
0,
5
),

(
'Advanced Techniques in Knocking Things Off Tables',
'Professor Whiskers',
'9780000000006',
'Education',
'A complete course on gravity experiments performed by professional cats.',
150,
0,
2
),

(
'Who Is a Good Boy? A Scientific Study',
'Sir Barks A Lot',
'9780000000007',
'Science',
'A research-based investigation proving that dogs deserve endless praise.',
400,
0,
1
),

(
'The Great Hay Debate',
'Moozilla',
'9780000000008',
'Historical Fiction',
'A dramatic story about farms, politics, and the legendary hay negotiations.',
220,
0,
3
),

(
'The Secret Life of Foxes',
'Sly Foxington',
'9780000000009',
'Fantasy',
'A mysterious journey into the hidden world of clever fox societies.',
310,
0,
7
),

(
'The Turtle Who Never Rushed',
'Tiny Turtle',
'9780000000010',
'Self-Help',
'A relaxing guide about patience, slow progress, and enjoying the journey.',
200,
0,
8
),

(
'Night Flights and Ancient Wisdom',
'NightOwl',
'9780000000011',
'Biography',
'The life story of an owl who became famous for solving problems after dark.',
270,
0,
9
),

(
'Dragon Cooking for Beginners',
'DragonFlame',
'9780000000012',
'Fantasy',
'A beginner-friendly cookbook teaching dragons how to prepare meals without burning everything.',
350,
0,
10
);



-- USER BOOKS / REVIEWS

INSERT INTO user_books
(user_id, book_id, status, rating, review)
VALUES

(1,1,'read',2,'This book suggests cats are superior. I strongly disagree.'),
(2,1,'read',5,'Finally a book that understands cats perfectly.'),
(4,1,'read',4,'Very informative, but ducks were ignored.'),

(2,2,'read',1,'Clearly dog propaganda.'),
(4,2,'read',4,'Inspired me to investigate every suspicious object.'),
(5,2,'read',3,'Good adventure but lacked hamster characters.'),

(3,3,'read',5,'The grass philosophy changed my entire worldview.'),
(1,3,'read',3,'Interesting but not enough squirrels.'),

(2,4,'read',5,'An excellent detective mystery.'),
(1,4,'read',4,'I suspected the bread immediately.'),

(3,5,'read',5,'Tiny furniture deserves more attention.'),
(5,5,'read',5,'The perfect book for my lifestyle.'),

(2,6,'read',5,'A masterpiece every cat should study.'),
(1,7,'read',5,'Scientific proof that dogs are amazing.'),

(3,8,'read',4,'A surprisingly deep discussion about hay policies.'),

(7,9,'read',5,'Foxes finally get the respect they deserve.'),

(8,10,'currently_reading',NULL,NULL),

(9,11,'currently_reading',NULL,NULL),

(10,12,'want_to_read',NULL,NULL),

(5,8,'want_to_read',NULL,NULL),

(6,2,'read',4,'A fun adventure with a lot of energy.'),

(7,6,'read',3,'Some techniques were questionable.');



-- LIKES

INSERT INTO likes
(user_id, book_id)
VALUES

(1,2),
(1,7),
(1,9),

(2,1),
(2,6),
(2,12),

(3,1),
(3,3),
(3,8),

(4,2),
(4,4),

(5,3),
(5,5),

(6,1),
(6,10),

(7,9),
(8,10),
(9,11),
(10,12);



-- FOLLOWS

INSERT INTO follows
(follower_id, following_id)
VALUES

(1,2),
(2,1),

(3,2),
(2,3),

(4,1),
(1,4),

(5,3),
(5,2),

(6,7),
(7,6),

(8,9),
(9,10),

(10,1);



-- RECALCULATE BOOK RATINGS

UPDATE books
SET average_rating =
COALESCE(
(
    SELECT ROUND(AVG(rating),2)
    FROM user_books
    WHERE user_books.book_id = books.id
    AND rating IS NOT NULL
),
0
);