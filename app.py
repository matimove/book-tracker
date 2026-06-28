from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import secrets
from flask import abort
import config

app = Flask(__name__)
app.secret_key = config.secret_key

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
    conn = get_db_connection()

    user_books = []

    if 'user_id' in session:
        user_books = [dict(row) for row in conn.execute('''
            SELECT
                books.id AS book_id,
                books.title,
                books.author,
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


    popular_books = [dict(row) for row in conn.execute('''
        SELECT 
            b.id,
            b.title,
            b.author,
            b.genre,
            b.description,
            b.page_count,
            b.average_rating,
            COUNT(l.id) AS like_count
        FROM books b
        LEFT JOIN likes l ON b.id = l.book_id
        GROUP BY b.id
        ORDER BY like_count DESC
        LIMIT 5
    ''').fetchall()]


    recent_books = [dict(row) for row in conn.execute('''
        SELECT
            id,
            title,
            author,
            genre,
            description,
            page_count,
            average_rating,
            created_at
        FROM books
        ORDER BY created_at DESC
        LIMIT 5
    ''').fetchall()]


    conn.close()

    return render_template(
        'index.html',
        user_books=user_books,
        popular_books=popular_books,
        recent_books=recent_books
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(username) > 50:
            flash('Username too long!', 'error')
            return redirect(url_for('register'))

        if len(email) > 255:
            flash('Email too long!', 'error')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters!', 'error')
            return redirect(url_for('register'))

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
            SELECT
                id,
                username,
                password_hash
            FROM users
            WHERE username = ?
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
        SELECT
            id,
            username
        
    
        FROM users
        WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('index'))

    book_columns = '''
        b.id,
        b.title,
        b.author,
        b.genre,
        b.description,
      
        b.page_count,
        b.average_rating,
        b.created_at
    '''

    want_to_read = conn.execute(f'''
        SELECT {book_columns}
        FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'want_to_read'
    ''', (user['id'],)).fetchall()

    currently_reading = conn.execute(f'''
        SELECT {book_columns}
        FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'currently_reading'
    ''', (user['id'],)).fetchall()

    read = conn.execute(f'''
        SELECT {book_columns}
        FROM user_books ub
        JOIN books b ON ub.book_id = b.id
        WHERE ub.user_id = ? AND ub.status = 'read'
    ''', (user['id'],)).fetchall()


    added_books = conn.execute('''
        SELECT
            id,
            title,
            author,
            genre,
            description,
          
            page_count,
            average_rating,
            created_at
        FROM books
        WHERE created_by = ?
        ORDER BY created_at DESC
    ''', (user['id'],)).fetchall()


    is_following = False
    if 'user_id' in session and session['user_id'] != user['id']:
        follow = conn.execute('''
            SELECT id
            FROM follows
            WHERE follower_id = ? 
            AND following_id = ?
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
        added_books=added_books,
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

@app.route('/profile/<username>/following')
def following(username):

    conn = get_db_connection()

    user = conn.execute('''
        SELECT
            id,
            username
        
            
        FROM users
        WHERE username = ?
    ''', (username,)).fetchone()

    if not user:
        conn.close()
        flash('User not found!', 'error')
        return redirect(url_for('index'))


    following_users = conn.execute('''
        SELECT
            users.id,
            users.username
            
           
        FROM follows
        JOIN users
        ON follows.following_id = users.id
        WHERE follows.follower_id = ?
        ORDER BY users.username
    ''', (user['id'],)).fetchall()


    conn.close()

    return render_template(
        'following.html',
        user=user,
        users=following_users
    )



@app.route('/profile/<username>/followers')
def followers(username):

    conn = get_db_connection()

    user = conn.execute('''
        SELECT
            id,
            username,
         
            
        FROM users
        WHERE username = ?
    ''', (username,)).fetchone()


    if not user:
        conn.close()
        flash('User not found!', 'error')
        return redirect(url_for('index'))


    follower_users = conn.execute('''
        SELECT
            users.id,
            users.username,
            
        
        FROM follows
        JOIN users
        ON follows.follower_id = users.id
        WHERE follows.following_id = ?
        ORDER BY users.username
    ''', (user['id'],)).fetchall()


    conn.close()


    return render_template(
        'followers.html',
        user=user,
        users=follower_users
    )

@app.route('/book/<int:book_id>')
def book_detail(book_id):
    conn = get_db_connection()
    book = conn.execute('''
    SELECT 
        b.id,
        b.title,
        b.author,
        b.isbn,
        b.genre,
        b.description,
    
        b.published_date,
        b.page_count,
        b.average_rating,
        b.created_by,
        b.created_at,
        u.username AS added_by_username
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
            SELECT 
                id,
                user_id,
                book_id,
                status,
                rating,
                review,
                start_date,
                finish_date,
                created_at,
                updated_at
            FROM user_books
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
            SELECT id
            FROM likes
            WHERE user_id = ? AND book_id = ?
        ''', (session['user_id'], book_id)).fetchone()
        user_liked = like is not None

    # Get reviews
    reviews = conn.execute('''
        SELECT
            ub.id,
            ub.user_id,
            ub.book_id,
            ub.status,
            ub.rating,
            ub.review,
            ub.updated_at,
            u.username
            
        FROM user_books ub
        JOIN users u ON ub.user_id = u.id
        WHERE ub.book_id = ?
        AND ub.review IS NOT NULL
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

    if request.method == "POST":
        check_csrf()

        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        genre = request.form.get('genre', '').strip()
        isbn = request.form.get('isbn', '').strip()
        description = request.form.get('description', '').strip()
        published_date = request.form.get('published_date', '').strip()
        page_count = request.form.get('page_count', '').strip()
        


        # Required fields
        if not title or not author:
            flash('Title and author are required!', 'error')
            return redirect(url_for('add_book'))

        # Length checks
        if len(title) > 200:
            flash('Title is too long!', 'error')
            return redirect(url_for('add_book'))

        if len(author) > 200:
            flash('Author is too long!', 'error')
            return redirect(url_for('add_book'))

        if len(description) > 2000:
            flash('Description is too long!', 'error')
            return redirect(url_for('add_book'))
        
        if len(isbn) > 30:
            flash('ISBN is too long!', 'error')
            return redirect(url_for('add_book'))


        # Genre check
        allowed_genres = [
            '',
            'Fantasy',
            'Science Fiction',
            'Mystery',
            'Thriller',
            'Romance',
            'Historical Fiction',
            'Non-Fiction',
            'Biography',
            'Self-Help'
        ]

        if genre not in allowed_genres:
            flash('Invalid genre!', 'error')
            return redirect(url_for('add_book'))


        # Page count check
        if page_count:
            try:
                page_count = int(page_count)

                if page_count <= 0:
                    raise ValueError

            except ValueError:
                flash('Invalid page count!', 'error')
                return redirect(url_for('add_book'))
        else:
            page_count = None


        # Date check
        if published_date:
            try:
                datetime.strptime(published_date, "%Y-%m-%d")
            except ValueError:
                flash('Date must be YYYY-MM-DD!', 'error')
                return redirect(url_for('add_book'))


        conn = get_db_connection()

        # Duplicate title + author check
        existing = conn.execute('''
            SELECT id FROM books
            WHERE title = ? AND author = ?
        ''', (title, author)).fetchone()

        if existing:
            conn.close()
            flash('A book with this title and author already exists!', 'error')
            return redirect(url_for('add_book'))

        try:
            conn.execute('''
            INSERT INTO books (
                title, author, isbn, genre,
                description, 
                published_date, page_count,
                created_by
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                title,
                author,
                isbn or None,
                genre or None,
                description or None,
               
                published_date or None,
                int(page_count) if page_count else None,
                session['user_id']
            ))

            conn.commit()
            flash('Book added successfully!', 'success')

        except sqlite3.IntegrityError:
            flash('The book already exists!', 'error')

        finally:
            conn.close()

        return redirect(url_for('add_book'))

    return render_template('add_book.html')

@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        check_csrf()

    conn = get_db_connection()

    book = conn.execute(
            '''
            SELECT
                id,
                title,
                author,
                isbn,
                genre,
                description,
              
                published_date,
                page_count,
                average_rating,
                created_by,
                created_at
            FROM books
            WHERE id = ?
            ''',
            (book_id,)
        ).fetchone()

    if not book:
        conn.close()
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    if book['created_by'] != session['user_id']:
        conn.close()
        flash('You can only edit books you added.', 'error')
        return redirect(url_for('book_detail', book_id=book_id))


    if request.method == 'POST':

        # Clean inputs
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        genre = request.form.get('genre', '').strip()
        isbn = request.form.get('isbn', '').strip()
        description = request.form.get('description', '').strip()
       
        published_date = request.form.get('published_date', '').strip()
        page_count = request.form.get('page_count', '').strip()


        # Required fields
        if not title or not author:
            flash('Title and author are required!', 'error')
            conn.close()
            return redirect(url_for('edit_book', book_id=book_id))


        # Length checks
        if len(title) > 200:
            flash('Title is too long!', 'error')
            conn.close()
            return redirect(url_for('edit_book', book_id=book_id))

        if len(author) > 200:
            flash('Author is too long!', 'error')
            conn.close()
            return redirect(url_for('edit_book', book_id=book_id))

        if len(description) > 2000:
            flash('Description is too long!', 'error')
            conn.close()
            return redirect(url_for('edit_book', book_id=book_id))


        # Genre validation
        allowed_genres = [
            '',
            'Fantasy',
            'Science Fiction',
            'Mystery',
            'Thriller',
            'Romance',
            'Historical Fiction',
            'Non-Fiction',
            'Biography',
            'Self-Help'
        ]

        if genre not in allowed_genres:
            flash('Invalid genre!', 'error')
            conn.close()
            return redirect(url_for('edit_book', book_id=book_id))


        # Page count validation
        if page_count:
            try:
                page_count = int(page_count)

                if page_count <= 0:
                    raise ValueError

            except ValueError:
                flash('Invalid page count!', 'error')
                conn.close()
                return redirect(url_for('edit_book', book_id=book_id))

        else:
            page_count = None


        # Date validation
        if published_date:
            try:
                datetime.strptime(
                    published_date,
                    "%Y-%m-%d"
                )
            except ValueError:
                flash('Date must be YYYY-MM-DD!', 'error')
                conn.close()
                return redirect(url_for('edit_book', book_id=book_id))

        # Duplicate title + author check (ignore current book)
        existing = conn.execute('''
            SELECT id FROM books
            WHERE title = ?
            AND author = ?
            AND id != ?
        ''', (title, author, book_id)).fetchone()

        if existing:
            conn.close()
            flash('A book with this title and author already exists!', 'error')
            return redirect(url_for('edit_book', book_id=book_id))
                
        # Update
        conn.execute('''
            UPDATE books
            SET title = ?,
                author = ?,
                genre = ?,
                isbn = ?,
                description = ?,
               
                published_date = ?,
                page_count = ?
            WHERE id = ?
        ''', (
            title,
            author,
            genre or None,
            isbn or None,
            description or None,
           
            published_date or None,
            page_count,
            book_id
        ))

        conn.commit()
        conn.close()

        flash('Book updated successfully!', 'success')
        return redirect(
            url_for('book_detail', book_id=book_id)
        )


    conn.close()
    return render_template('edit_book.html', book=book)


@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    check_csrf()

    conn = get_db_connection()

    book = conn.execute(
        '''
        SELECT 
            id,
            title,
            created_by
        FROM books
        WHERE id = ?
        ''',
        (book_id,)
    ).fetchone()

    if not book:
        conn.close()
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    if book['created_by'] != session['user_id']:
        conn.close()
        flash('You can only delete books you added.', 'error')
        return redirect(
            url_for('book_detail', book_id=book_id)
        )

    conn.execute(
        'DELETE FROM books WHERE id = ?',
        (book_id,)
    )

    conn.commit()
    conn.close()

    flash('Book deleted successfully!', 'success')

    return redirect(url_for('index'))

@app.route('/confirm_delete/<int:book_id>')
def confirm_delete(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()

    book = conn.execute(
        '''
        SELECT
            id,
            title,
            created_by
        FROM books
        WHERE id = ?
        ''',
        (book_id,)
    ).fetchone()

    conn.close()

    if not book:
        flash('Book not found!', 'error')
        return redirect(url_for('index'))

    if book['created_by'] != session['user_id']:
        flash('You can only delete books you added.', 'error')
        return redirect(url_for('book_detail', book_id=book_id))

    return render_template(
        'confirm_delete.html',
        book=book
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()

    conn = get_db_connection()

    books = []

    if query:
        books = conn.execute('''
            SELECT
                id,
                title,
                author,
                isbn,
                genre,
                description,
             
                published_date,
                page_count,
                average_rating,
                created_by,
                created_at
            FROM books
            WHERE title LIKE ?
               OR author LIKE ?
               OR isbn LIKE ?
               OR genre LIKE ?
            ORDER BY title
        ''', (
            f'%{query}%',
            f'%{query}%',
            f'%{query}%',
            f'%{query}%'
        )).fetchall()

    conn.close()

    return render_template(
        'search.html',
        books=books,
        query=query
    )


@app.route('/add_to_collection/<int:book_id>', methods=['POST'])
def add_to_collection(book_id):
    if 'user_id' not in session:
        flash('Please log in to add books to your collection.', 'error')
        return redirect(url_for('login'))

    check_csrf()

    conn = get_db_connection()

    # Check book exists
    book = conn.execute('''
        SELECT id
        FROM books
        WHERE id = ?
    ''', (book_id,)).fetchone()

    if not book:
        conn.close()
        flash('Book not found!', 'error')
        return redirect(url_for('index'))


    user_book = conn.execute('''
        SELECT 
            id,
            status,
            rating,
            review,
            start_date,
            finish_date
        FROM user_books
        WHERE user_id = ?
        AND book_id = ?
    ''', (
        session['user_id'],
        book_id
    )).fetchone()


    # Clean inputs
    status = request.form.get('status', '').strip()
    rating = request.form.get('rating', '').strip()
    review = request.form.get('review', '').strip()
    start_date = request.form.get('start_date', '').strip()
    finish_date = request.form.get('finish_date', '').strip()


    # Status validation
    allowed_statuses = [
        'want_to_read',
        'currently_reading',
        'read'
    ]

    if status and status not in allowed_statuses:
        conn.close()
        flash('Invalid reading status!', 'error')
        return redirect(url_for('book_detail', book_id=book_id))


    # Rating validation
    if rating:
        try:
            rating = float(rating)

            if rating < 0 or rating > 5:
                raise ValueError

        except ValueError:
            conn.close()
            flash('Rating must be between 0 and 5!', 'error')
            return redirect(url_for('book_detail', book_id=book_id))
    else:
        rating = None


    # Review length
    if len(review) > 2000:
        conn.close()
        flash('Review is too long!', 'error')
        return redirect(url_for('book_detail', book_id=book_id))
    
    

    if user_book:

        status = status or user_book['status']
        rating = rating if rating is not None else user_book['rating']
        review = review if review else user_book['review']
        start_date = start_date or user_book['start_date']
        finish_date = finish_date or user_book['finish_date']


        conn.execute('''
            UPDATE user_books
            SET status = ?,
                rating = ?,
                review = ?,
                start_date = ?,
                finish_date = ?,
                updated_at = DATE('now')
            WHERE id = ?
        ''', (
            status,
            rating,
            review,
            start_date or None,
            finish_date or None,
            user_book['id']
        ))

    else:

        if not status:
            conn.close()
            flash('Please choose a reading status first.', 'error')
            return redirect(url_for('book_detail', book_id=book_id))


        conn.execute('''
            INSERT INTO user_books
            (
                user_id,
                book_id,
                status,
                rating,
                review,
                start_date,
                finish_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            book_id,
            status,
            rating,
            review or None,
            start_date or None,
            finish_date or None
        ))


    # Update average rating
    conn.execute('''
        UPDATE books
        SET average_rating = COALESCE((
            SELECT ROUND(AVG(rating), 2)
            FROM user_books
            WHERE book_id = ?
            AND rating IS NOT NULL
        ), 0.0)
        WHERE id = ?
    ''', (
        book_id,
        book_id
    ))


    conn.commit()
    conn.close()

    flash('Book entry updated successfully!', 'success')

    return redirect(
        url_for('book_detail', book_id=book_id)
    )


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

@app.route('/books')
def all_books():
    conn = get_db_connection()

    books = conn.execute('''
        SELECT
            id,
            title,
            author,
            isbn,
            genre,
            description,
           
            published_date,
            page_count,
            average_rating,
            created_by,
            created_at
        FROM books
        ORDER BY title
    ''').fetchall()

    conn.close()

    return render_template(
        'all_books.html',
        books=books
    )

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



if __name__ == '__main__':
    app.run(debug=True)
