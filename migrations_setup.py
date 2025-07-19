#!/usr/bin/env python3
"""
Flask-Migrate setup and initialization script
"""

from flask_migrate import Migrate, init, migrate, upgrade
from app import app
from models import db

# Initialize Flask-Migrate
migrate_instance = Migrate(app, db)

def setup_migrations():
    """Initialize migrations for the project"""
    with app.app_context():
        try:
            # Initialize migrations
            init(directory='migrations')
            print("✅ Migrations initialized successfully!")
            
            # Create initial migration
            migrate(message='Initial migration')
            print("✅ Initial migration created!")
            
            # Apply migrations
            upgrade()
            print("✅ Database upgraded successfully!")
            
        except Exception as e:
            print(f"❌ Error setting up migrations: {e}")
            print("\nIf migrations already exist, you can run:")
            print("  flask db migrate -m 'Your migration message'")
            print("  flask db upgrade")

if __name__ == '__main__':
    setup_migrations()