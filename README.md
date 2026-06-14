# Book Tracker

A web application for readers to discover, organize, and track their reading journey. Users can manage their personal library, review books, rate titles, and connect with other readers.

## Current Features

* Users can create an account and log in to the application.
* Users can add, edit, and delete books.
* Users can view all books that have been added to the application.
* Users can search for books by title, author, ISBN, genre, or other keywords.
* The application provides user profile pages showing reading statistics, book collections, and social information.
* Users can assign a genre to each book to classify and organize books in the system.
* Users can add additional information to books through ratings and reviews, which are visible to other users.
* Users can track their reading progress using the statuses:

  * Want to Read
  * Currently Reading
  * Read
* Users can follow other users and view their profiles.
* Users can like books added by other users.
* Users can view community reviews and ratings for books.

---

## Tech Stack

* Python
* Flask
* SQLite
* HTML/CSS
* JavaScript

---

## Database

The application uses SQLite for local development.

Initialize the database:

```bash
sqlite3 database.db < schema.sql
sqlite3 database.db < init.sql
```

---

## Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd book-tracker
```

### 2. Create a Virtual Environment

#### Windows

```bash
python -m venv venv
```

#### macOS / Linux

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

#### Windows (Command Prompt)

```bash
venv\Scripts\activate
```

#### Windows (PowerShell)

```powershell
.\venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the Database

```bash
sqlite3 database.db < schema.sql
sqlite3 database.db < init.sql
```

### 6. Run the Application

```bash
flask run
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

## Project Structure

```text
book-tracker/
├── app.py
├── database.db
├── init.sql
├── requirements.txt
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
└── README.md
```

---

## Future Improvements

* Book cover uploads
* Reading goals and challenges
* Book recommendations
* Activity feed
* Advanced filtering and sorting
* Email verification and password reset
* Public profile sharing

---

## License

This project is intended for educational purposes and personal development.
