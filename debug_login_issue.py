#!/usr/bin/env python3
"""Debug login issue by testing directly"""
import os
import sys
from app import create_app
from app.models import db, User
import traceback

def debug_login():
    app = create_app()
    
    with app.app_context():
        print("=== DATABASE CONNECTION ===")
        print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        print("\n=== CHECKING USER TABLE SCHEMA ===")
        # Get actual columns in database
        result = db.session.execute(db.text("PRAGMA table_info(users)"))
        db_columns = [row[1] for row in result]
        print(f"Columns in database: {db_columns}")
        
        print("\n=== USER MODEL FIELDS ===")
        # Get fields expected by User model
        model_columns = [col.name for col in User.__table__.columns]
        print(f"Columns in User model: {model_columns}")
        
        print("\n=== MISSING COLUMNS ===")
        missing = set(model_columns) - set(db_columns)
        if missing:
            print(f"Missing in database: {missing}")
        else:
            print("No missing columns")
            
        print("\n=== ATTEMPTING USER QUERY ===")
        try:
            # Try to query user
            user = User.query.filter_by(email='admin@cibozer.com').first()
            if user:
                print(f"User found: {user.email}")
                print(f"User ID: {user.id}")
                print(f"Subscription: {user.subscription_tier}")
                
                # Test password check
                print("\n=== TESTING PASSWORD CHECK ===")
                test_password = os.environ.get('TEST_PASSWORD', '')
                if test_password:
                    try:
                        result = user.check_password(test_password)
                        print(f"Password check result: {result}")
                    except Exception as e:
                        print(f"Password check error: {e}")
                        traceback.print_exc()
                else:
                    print("Skipping password check (set TEST_PASSWORD env var to test)")
            else:
                print("User not found!")
                
        except Exception as e:
            print(f"\nERROR during query: {type(e).__name__}: {e}")
            print("\nFull traceback:")
            traceback.print_exc()
            
            # Try raw SQL query
            print("\n=== TRYING RAW SQL ===")
            try:
                result = db.session.execute(
                    db.text("SELECT email, password_hash FROM users WHERE email = :email"),
                    {"email": "admin@cibozer.com"}
                )
                row = result.fetchone()
                if row:
                    print(f"Raw query successful: {row[0]}")
                    print(f"Password hash exists: {bool(row[1])}")
                else:
                    print("No user found with raw query")
            except Exception as e2:
                print(f"Raw query error: {e2}")

if __name__ == '__main__':
    debug_login()