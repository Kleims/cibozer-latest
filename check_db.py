from app import app, db
from models import User

with app.app_context():
    # Check if tables exist
    try:
        user_count = User.query.count()
        print(f"Users in database: {user_count}")
        print("Database is working!")
    except Exception as e:
        print(f"Database error: {e}")
        print("Creating tables...")
        db.create_all()
        print("Tables created!")