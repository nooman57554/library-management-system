import csv
from io import StringIO
from flask import Flask, Response, render_template, request, redirect, url_for, session, flash
from database import db
from models import User, Book, BorrowedBook
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            session['role'] = user.role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = 'user'
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    books = Book.query.all()
    return render_template('admin_dashboard.html', books=books, user_role='admin')

@app.route('/user_dashboard', methods=['GET'])
def user_dashboard():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    # Search functionality for books
    search = request.args.get('search', '')
    if search:
        books = Book.query.filter(Book.title.contains(search) | Book.author.contains(search)).all()
    else:
        books = Book.query.all()  # Only available books

    # Fetch borrowed books for the logged-in user
    borrowed_books = BorrowedBook.query.filter_by(user_id=user.id, returned=False).all()

    return render_template('user_dashboard.html', books=books, borrowed_books=borrowed_books, user_role='user')


@app.route('/admin/users')
def admin_users():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    users = User.query.all()  # Get all users
    return render_template('admin_users.html', users=users)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role = request.form['role']  # Update the role
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))





@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        year = request.form['year']
        description = request.form['description']
        cover_url = request.form['cover_url']
        availability = 'Available'

        book = Book(
            title=title, author=author, genre=genre,
            year=year, description=description, cover_url=cover_url, availability=availability
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('add_book.html')

@app.route('/admin/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    book = Book.query.get_or_404(book_id)

    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form['genre']
        book.year = request.form['year']
        book.description = request.form['description']
        book.cover_url = request.form['cover_url']

        db.session.commit()
        flash('Book details updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    
    if book:
        # Check if the book is borrowed
        borrowed_book = BorrowedBook.query.filter_by(book_id=book_id, returned=False).first()
        
        if borrowed_book:  # If there is a borrowed entry and the book has not been returned
            user = User.query.get(borrowed_book.user_id)  # Get the user who borrowed the book
            flash(f"Book is currently borrowed by {user.username}. Cannot delete the book.", "danger")
        else:
            db.session.delete(book)
            db.session.commit()
            flash("Book deleted successfully!", "success")
    else:
        flash("Book not found!", "danger")

    return redirect(url_for('admin_dashboard'))


@app.route('/borrow_book/<int:book_id>', methods=['GET'])
def borrow_book(book_id):
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    book = Book.query.get_or_404(book_id)

    # Check if the user has already borrowed this book
    existing_borrow = BorrowedBook.query.filter_by(user_id=user.id, book_id=book.id, returned=False).first()
    if existing_borrow:
        flash('You have already borrowed this book.', 'error')
        return redirect(url_for('user_dashboard'))

    # Borrow the book
    due_date = datetime.utcnow() + timedelta(days=14)
    borrowed_book = BorrowedBook(user_id=user.id, book_id=book.id, due_date=due_date)
    book.availability = 'Not Available'  # Update book availability
    db.session.add(borrowed_book)
    db.session.commit()

    flash('Book borrowed successfully.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/return_book/<int:borrowed_book_id>', methods=['GET'])
def return_book(borrowed_book_id):
    # Check if the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    borrowed_book = BorrowedBook.query.get_or_404(borrowed_book_id)

    # Ensure that the logged-in user is the one who borrowed the book
    if borrowed_book.user.username != session['username']:
        flash('You cannot return this book.', 'error')
        return redirect(url_for('user_dashboard'))

    # Return the book
    borrowed_book.returned = True
    borrowed_book.book.availability = 'Available'  # Update book availability back to 'Available'
    
    # Commit changes before deleting the borrowed_book record
    db.session.commit()  # First commit to save the book's availability change

    # Now, delete the borrowed_book record
    db.session.delete(borrowed_book)
    db.session.commit()  # Commit again to delete the borrowed_book record

    flash('Book returned successfully and record deleted.', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/book_details/<int:book_id>')
def book_details(book_id):
    # Replace with the actual database query to fetch book details
    book = db.session.query(Book).filter_by(id=book_id).first()  # Example ORM query
    if not book:
        return "Book not found", 404

    return render_template('book_details.html', book=book)


@app.route('/borrowed_books_report')
def borrowed_books_report():
    # Query all borrowed books
    borrowed_books = BorrowedBook.query.filter_by(returned=False).all()
    
    # Render the report in HTML
    return render_template('borrowed_books_report.html', borrowed_books=borrowed_books)


@app.route('/overdue_books_report')
def overdue_books_report():
    # Get the current date
    current_date = datetime.utcnow()
    
    # Query overdue books (borrowed books whose due date is before the current date and not returned)
    overdue_books = BorrowedBook.query.filter(BorrowedBook.due_date < current_date, BorrowedBook.returned == False).all()
    
    # Render the report in HTML
    return render_template('overdue_books_report.html', overdue_books=overdue_books)

@app.route('/user_activity_report')
def user_activity_report():
    # Get the logged-in user (assuming you're using Flask session to store user data)
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Query the borrowed books by the logged-in user
    user_borrowed_books = BorrowedBook.query.filter_by(user_id=user.id).all()
    
    # Render the report in HTML
    return render_template('user_activity_report.html', user_borrowed_books=user_borrowed_books)


@app.route('/export_borrowed_books_csv')
def export_borrowed_books_csv():
    # Fetch the borrowed books data (you should adapt this to your database structure)
    borrowed_books = BorrowedBook.query.all()

    # Create a CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Book Title', 'User', 'Borrowed Date', 'Due Date'])  # Write header

    # Write data rows
    for record in borrowed_books:
        writer.writerow([record.book.title, record.user.username, record.borrow_date, record.due_date])

    # Prepare the response as a downloadable CSV file
    output.seek(0)
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=borrowed_books_report.csv'

    return response

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
