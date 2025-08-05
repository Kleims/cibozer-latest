#!/usr/bin/env python
"""
Initialize the database for Cibozer
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from app.extensions import db

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Initializing database...")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Create all tables
            db.create_all()
            
            print("✓ Database tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import text
            tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            
            print(f"✓ Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing database: {e}")
            return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)