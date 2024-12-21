from database import db
from models import User
from app import app

# Setup the database
with app.app_context():
    db.create_all()

    # Check if an admin already exists
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")
