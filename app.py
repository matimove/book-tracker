from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import secrets
from flask import abort

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Database configuration
DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        with app.open_resource('schema.sql', mode='r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

# Initialize database
init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db_connection()
        
        #user_books = [dict(row) for row in conn.execute('SELECT * FROM user_books WHERE user_id = ?', (session['user_id'],)).fetchall()]
        user_books = [dict(row) for row in conn.execute('''
    SELECT
        books.id AS book_id,
        books.title,
        books.author,
        books.cover_image,
        books.genre,
        books.description,
        books.page_count,
        books.average_rating,
        user_books.status,
        user_books.updated_at
    FROM user_books
    JOIN books ON user_books.book_id = books.id
    WHERE user_books.user_id = ?
    ORDER BY user_books.updated_at DESC
    LIMIT 6
''', (session['user_id'],)).fetchall()]
        popular_books = [dict(row) for row in conn.execute('SELECT b.*, COUNT(l.id) as like_count FROM books b LEFT JOIN likes l ON b.id = l.book_id GROUP BY b.id ORDER BY like_count DESC LIMIT 5').fetchall()]
        recent_books = [dict(row) for row in conn.execute('SELECT * FROM books ORDER BY created_at DESC LIMIT 5').fetchall()]


        print("User Books:", user_books)
        print("Popular Books:", popular_books)
        print("Recent Books:", recent_books)

        conn.close()
        return render_template('index.html',
                             user_books=user_books,
                             popular_books=popular_books,
                             recent_books=recent_books)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            ''', (username, email, generate_password_hash(password)))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users WHERE username = ?
        ''', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['csrf_token'] = secrets.token_hex(16)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid username or password!', 'error')

    return render_template('login.html')

def check_csrf():
    if 'csrf_token' not in session:
        abort(403)

    if request.form.get('csrf_token') != session['csrf_token']:
        abort(403)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    # Get user's books by status
    want_to_read = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'want_to_read'
    ''', (user['id'],)).fetchall()

    currently_reading = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'currently_reading'
    ''', (user['id'],)).fetchall()

    read = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'read'
    ''', (user['id'],)).fetchall()

    # Check if current user is following this profile
    is_following = False
    if 'user_id' in session and session['user_id'] != user['id']:
        follow = conn.execute('''
            SELECT * FROM follows
            WHERE follower_id = ? AND following_id = ?
        ''', (session['user_id'], user['id'])).fetchone()
        is_following = follow is not None

    follows_count = conn.execute('''
        SELECT COUNT(*) AS count
        FROM follows
        WHERE follower_id = ?
    ''', (user['id'],)).fetchone()['count']

    followers_count = conn.execute('''
        SELECT COUNT(*) AS count
        FROM follows
        WHERE following_id = ?
    ''', (user['id'],)).fetchone()['count']

    conn.close()

    return render_template(
        'profile.html',
        user=user,
        want_to_read=want_to_read,
        currently_reading=currently_reading,
        read=read,
        is_following=is_following,
        follows_count=follows_count,
        followers_count=followers_count
    )

@app.route('/follow/<username>', methods=['POST'])
def follow(username):
    if 'user_id' not in session:
        flash('Please log in to follow users.', 'error')
        return redirect(url_for('login'))
    
    check_csrf()

    conn = get_db_connection()
    user = conn.execute('''
        SELECT id FROM users WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    if user['id'] == session['user_id']:
        flash('You cannot follow yourself!', 'error')
        return redirect(url_for('profile', username=username))

    try:
        conn.execute('''
            INSERT INTO follows (follower_id, following_id)
            VALUES (?, ?)
        ''', (session['user_id'], user['id']))
        conn.commit()
        flash(f'You are now following {username}!', 'success')
    except sqlite3.IntegrityError:
        flash(f'You are already following {username}!', 'error')

    conn.close()
    return redirect(url_for('profile', username=username))

@app.route('/unfollow/<username>', methods=['POST'])
def unfollow(username):
    if 'user_id' not in session:
        flash('Please log in to unfollow users.', 'error')
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()
    user = conn.execute('''
        SELECT id FROM users WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    conn.execute('''
        DELETE FROM follows
        WHERE follower_id = ? AND following_id = ?
    ''', (session['user_id'], user['id']))
    conn.commit()
    conn.close()

    flash(f'You have unfollowed {username}.', 'success')
    return redirect(url_for('profile', username=username))

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    conn = get_db_connection()
    book = conn.execute('''
    SELECT b.*, u.username AS added_by_username
    FROM books b
    LEFT JOIN users u ON b.created_by = u.id
    WHERE b.id = ?
''', (book_id,)).fetchone()

    if not book:
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    # Get user's status for this book if logged in
    user_status = None
    if 'user_id' in session:
        user_book = conn.execute('''
            SELECT * FROM user_books
            WHERE user_id = ? AND book_id = ?
        ''', (session['user_id'], book_id)).fetchone()
        if user_book:
            user_status = user_book['status']

    # Get likes count
    likes_count = conn.execute('''
        SELECT COUNT(*) as count FROM likes WHERE book_id = ?
    ''', (book_id,)).fetchone()['count']

    # Check if current user has liked this book
    user_liked = False
    if 'user_id' in session:
        like = conn.execute('''
            SELECT * FROM likes
            WHERE user_id = ? AND book_id = ?
        ''', (session['user_id'], book_id)).fetchone()
        user_liked = like is not None

    # Get reviews
    reviews = conn.execute('''
        SELECT ub.*, u.username, u.profile_picture
        FROM user_books ub
        JOIN users u ON ub.user_id = u.id
        WHERE ub.book_id = ? AND ub.review IS NOT NULL
        ORDER BY ub.updated_at DESC
    ''', (book_id,)).fetchall()

    is_owner = 'user_id' in session and book['created_by'] == session['user_id']

    conn.close()

    return render_template('book.html',
                         book=book,
                         user_status=user_status,
                         likes_count=likes_count,
                         user_liked=user_liked,
                         reviews=reviews,
                         is_owner=is_owner)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session:
        flash('Please log in to add books.', 'error')
        return redirect(url_for('login'))
    check_csrf()
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form.get('genre')
        isbn = request.form.get('isbn')
        description = request.form.get('description')
        published_date = request.form.get('published_date')
        page_count = request.form.get('page_count')
        cover_image = request.form.get('cover_image')

        conn = get_db_connection()
        try:
            conn.execute('''
    INSERT INTO books (
        title, author, isbn, genre,
        description, cover_image,
        published_date, page_count,
        created_by
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    title,
    author,
    isbn,
    genre,
    description,
    cover_image,
    published_date,
    page_count,
    session['user_id']
))
            conn.commit()
            flash('Book added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('A book with this ISBN already exists!', 'error')
        finally:
            conn.close()

        return redirect(url_for('add_book'))

    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()

    if not book:
        conn.close()
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    if book['created_by'] != session['user_id']:
        conn.close()
        flash('You can only edit books you added.', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    if request.method == 'POST':
        conn.execute('''
            UPDATE books
            SET title = ?, author = ?, genre = ?, isbn = ?, description = ?,
                cover_image = ?, published_date = ?, page_count = ?
            WHERE id = ?
        ''', (
            request.form['title'],
            request.form['author'],
            request.form.get('genre'),
            request.form.get('isbn'),
            request.form.get('description'),
            request.form.get('cover_image'),
            request.form.get('published_date'),
            request.form.get('page_count'),
            book_id
        ))

        conn.commit()
        conn.close()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('book_detail', book_id=book_id))

    conn.close()
    return render_template('edit_book.html', book=book)


@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM books WHERE id = ?', (book_id,)).fetchone()

    if not book:
        conn.close()
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    if book['created_by'] != session['user_id']:
        conn.close()
        flash('You can only delete books you added.', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    conn.execute('DELETE FROM books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()

    flash('Book deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('index'))

    conn = get_db_connection()
    books = conn.execute('''
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ?
        ORDER BY title
    ''', (f'%{query}%', f'%{query}%')).fetchall()
    conn.close()

    return render_template('search.html', books=books, query=query)

@app.route('/search_books')
def search_books():
    query = request.args.get('q', '').strip()

    conn = get_db_connection()
    books = conn.execute('''
        SELECT id, title, author, isbn, description, cover_image, published_date, page_count
        FROM books
        WHERE title LIKE ?
           OR author LIKE ?
           OR isbn LIKE ?
        ORDER BY title
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()

    return {'books': [dict(book) for book in books]}

@app.route('/add_to_collection/<int:book_id>', methods=['POST'])
def add_to_collection(book_id):
    if 'user_id' not in session:
        flash('Please log in to add books to your collection.', 'error')
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()

    user_book = conn.execute('''
        SELECT * FROM user_books
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()

    status = request.form.get('status')
    rating = request.form.get('rating')
    review = request.form.get('review')
    start_date = request.form.get('start_date')
    finish_date = request.form.get('finish_date')

    if user_book:
        status = status or user_book['status']
        rating = rating or user_book['rating']
        review = review if review is not None else user_book['review']
        start_date = start_date or user_book['start_date']
        finish_date = finish_date or user_book['finish_date']
    else:
        if not status:
            flash('Please choose a reading status first.', 'error')
            conn.close()
            return redirect(url_for('book_detail', book_id=book_id))

    try:
        if user_book:
            conn.execute('''
                UPDATE user_books
                SET status = ?, rating = ?, review = ?,
                    start_date = ?, finish_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, rating, review, start_date, finish_date, user_book['id']))
        else:
            conn.execute('''
                INSERT INTO user_books
                (user_id, book_id, status, rating, review, start_date, finish_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], book_id, status, rating, review, start_date, finish_date))

        conn.execute('''
            UPDATE books
            SET average_rating = COALESCE((
                SELECT ROUND(AVG(rating), 2)
                FROM user_books
                WHERE book_id = ?
                AND rating IS NOT NULL
            ), 0.0)
            WHERE id = ?
        ''', (book_id, book_id))

        conn.commit()
        flash('Book entry updated successfully!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error adding book to collection: {e}', 'error')

    finally:
        conn.close()

    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/like/<int:book_id>', methods=['POST'])
def like_book(book_id):
    if 'user_id' not in session:
        flash('Please log in to like books.', 'error')
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()

    try:
        conn.execute('''
            INSERT INTO likes (user_id, book_id)
            VALUES (?, ?)
        ''', (session['user_id'], book_id))
        conn.commit()
        flash('Book liked!', 'success')
    except sqlite3.IntegrityError:
        flash('You have already liked this book!', 'error')

    conn.close()
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/unlike/<int:book_id>', methods=['POST'])
def unlike_book(book_id):
    if 'user_id' not in session:
        flash('Please log in to unlike books.', 'error')
        return redirect(url_for('login'))
    check_csrf()
    conn = get_db_connection()
    conn.execute('''
        DELETE FROM likes
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id))
    conn.commit()
    conn.close()

    flash('Book unliked.', 'success')
    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/my_books')
def my_books():
    if 'user_id' not in session:
        flash('Please log in to view your books.', 'error')
        return redirect(url_for('login'))

    conn = get_db_connection()

    # Get books by status
    want_to_read = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'want_to_read'
    ''', (session['user_id'],)).fetchall()

    currently_reading = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'currently_reading'
    ''', (session['user_id'],)).fetchall()

    read = conn.execute('''
        SELECT b.* FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'read'
    ''', (session['user_id'],)).fetchall()

    # Get user's ratings for read books
    user_book_ratings = {}
    for book in read:
        rating = conn.execute('''
            SELECT rating FROM user_books
            WHERE user_id = ? AND book_id = ?
        ''', (session['user_id'], book['id'])).fetchone()
        if rating:
            user_book_ratings[book['id']] = {'rating': rating['rating']}

    conn.close()

    return render_template('user_books.html',
                         want_to_read=want_to_read,
                         currently_reading=currently_reading,
                         read=read,
                         user_book_ratings=user_book_ratings)


if __name__ == '__main__':
    app.run(debug=True)
