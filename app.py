from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

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
        # Get user's books
        user_books = conn.execute('''
            SELECT b.*, ub.status
            FROM user_books ub
            JOIN books b ON ub.book_id = b.id
            WHERE ub.user_id = ?
            ORDER BY ub.updated_at DESC
            LIMIT 5
        ''', (session['user_id'],)).fetchall()

        # Get popular books
        popular_books = conn.execute('''
            SELECT b.*, COUNT(l.id) as like_count
            FROM books b
            LEFT JOIN likes l ON b.id = l.book_id
            GROUP BY b.id
            ORDER BY like_count DESC
            LIMIT 5
        ''').fetchall()

        # Get recently added books
        recent_books = conn.execute('''
            SELECT * FROM books
            ORDER BY created_at DESC
            LIMIT 5
        ''').fetchall()

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
            flash('Login successful!', 'success')
            return redirect(url_for('index'))

        flash('Invalid username or password!', 'error')

    return render_template('login.html')

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

    conn.close()

    return render_template('profile.html',
                         user=user,
                         want_to_read=want_to_read,
                         currently_reading=currently_reading,
                         read=read,
                         is_following=is_following)

@app.route('/follow/<username>', methods=['POST'])
def follow(username):
    if 'user_id' not in session:
        flash('Please log in to follow users.', 'error')
        return redirect(url_for('login'))

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
        SELECT * FROM books WHERE id = ?
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

    conn.close()

    return render_template('book.html',
                         book=book,
                         user_status=user_status,
                         likes_count=likes_count,
                         user_liked=user_liked,
                         reviews=reviews)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'user_id' not in session:
        flash('Please log in to add books.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        description = request.form['description']
        published_date = request.form['published_date']
        page_count = request.form['page_count']
        cover_image = request.form['cover_image']

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO books
                (title, author, isbn, description, cover_image, published_date, page_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, isbn, description, cover_image, published_date, page_count))
            conn.commit()
            flash('Book added successfully!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('A book with this ISBN already exists!', 'error')
        finally:
            conn.close()

    return render_template('add_book.html')

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

@app.route('/add_to_collection/<int:book_id>', methods=['POST'])
def add_to_collection(book_id):
    if 'user_id' not in session:
        flash('Please log in to add books to your collection.', 'error')
        return redirect(url_for('login'))

    status = request.form['status']
    rating = request.form.get('rating', None)
    review = request.form.get('review', None)
    start_date = request.form.get('start_date', None)
    finish_date = request.form.get('finish_date', None)

    conn = get_db_connection()

    # Check if book exists in user's collection
    user_book = conn.execute('''
        SELECT * FROM user_books
        WHERE user_id = ? AND book_id = ?
    ''', (session['user_id'], book_id)).fetchone()

    try:
        if user_book:
            # Update existing record
            conn.execute('''
                UPDATE user_books
                SET status = ?, rating = ?, review = ?,
                    start_date = ?, finish_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, rating, review, start_date, finish_date, user_book['id']))
        else:
            # Insert new record
            conn.execute('''
                INSERT INTO user_books
                (user_id, book_id, status, rating, review, start_date, finish_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session['user_id'], book_id, status, rating, review, start_date, finish_date))

        conn.commit()
        flash('Book added to your collection!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Error adding book to collection.', 'error')
    finally:
        conn.close()

    return redirect(url_for('book_detail', book_id=book_id))

@app.route('/like/<int:book_id>', methods=['POST'])
def like_book(book_id):
    if 'user_id' not in session:
        flash('Please log in to like books.', 'error')
        return redirect(url_for('login'))

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
