#!/usr/bin/env python3
"""Diagnose Flask app state issues"""
from app import create_app
from app.models import db, User
import os

def diagnose():
    print("=== ENVIRONMENT VARIABLES ===")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
    print(f"FLASK_DEBUG: {os.environ.get('FLASK_DEBUG', 'not set')}")
    print(f"SECRET_KEY: {'set' if os.environ.get('SECRET_KEY') else 'not set'}")
    
    app = create_app()
    
    with app.app_context():
        print("\n=== FLASK CONFIGURATION ===")
        print(f"DEBUG: {app.config.get('DEBUG')}")
        print(f"TESTING: {app.config.get('TESTING')}")
        print(f"SECRET_KEY: {'set' if app.config.get('SECRET_KEY') else 'not set'}")
        print(f"WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED', True)}")
        print(f"SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
        print(f"DATABASE: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        
        print("\n=== DATABASE CONNECTION TEST ===")
        try:
            # Test raw query
            result = db.session.execute(db.text("SELECT COUNT(*) FROM users"))
            count = result.scalar()
            print(f"Users in database: {count}")
            
            # Test ORM query
            users = User.query.all()
            print(f"Users via ORM: {len(users)}")
            
            # Test admin user
            admin = User.query.filter_by(email='admin@cibozer.com').first()
            if admin:
                print(f"Admin found: {admin.email}")
                print(f"Admin active: {admin.is_active}")
                print(f"Password hash exists: {bool(admin.password_hash)}")
            else:
                print("Admin user NOT FOUND!")
                
        except Exception as e:
            print(f"Database error: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n=== FLASK EXTENSIONS ===")
        print(f"Login Manager initialized: {hasattr(app, 'login_manager')}")
        print(f"CSRF initialized: {hasattr(app, 'csrf')}")
        print(f"Database initialized: {db is not None}")

if __name__ == '__main__':
    diagnose()