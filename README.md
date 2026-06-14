# Book Tracker

A web application for readers to discover, organize, and track their reading journey. Users can manage their personal library, review books, rate titles, and connect with other readers.

## Current Features

### Authentication

* User registration and login

### Book Management

* Add new books
* Edit existing books
* Delete books

### Search

* Search books by title, author, ISBN, or keywords

### Reading Tracker

* Track reading status:

  * Want to Read
  * Currently Reading
  * Read

### Reviews & Ratings

* Rate books
* Write reviews
* View reviews from other users

### User Profiles

* Personal profile pages
* Reading statistics
* Lists of books read and currently reading

### Social Features

* Follow other readers
* Like books

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
