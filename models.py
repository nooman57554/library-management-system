from datetime import datetime
from database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    borrowed_books = db.relationship('BorrowedBook', back_populates='user')



class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    genre = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(255))
    year = db.Column(db.Integer)
    availability = db.Column(db.String(20), nullable=False, default='Available')
    borrowed_books = db.relationship('BorrowedBook', back_populates='book')


class BorrowedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    returned = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='borrowed_books')
    book = db.relationship('Book', back_populates='borrowed_books')

