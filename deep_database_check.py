#!/usr/bin/env python
"""Deep database verification - leave no stone unturned!"""
import os
import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== DEEP DATABASE INVESTIGATION ===\n")

# 1. Find ALL database files
print("1. SEARCHING FOR ALL DATABASE FILES:")
db_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            db_files.append(full_path)
            print(f"   Found: {full_path}")

print(f"\nTotal database files found: {len(db_files)}")

# 2. Check each database
print("\n2. CHECKING EACH DATABASE:")
for db_path in db_files:
    print(f"\n   Checking: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"   Tables: {[t[0] for t in tables]}")
        
        # Check for users table
        if any('users' in t for t in tables):
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"   User count: {user_count}")
            
            # Check for admin - use parameterized query to prevent SQL injection
            cursor.execute("SELECT email, subscription_tier FROM users WHERE email LIKE ?", ('%admin%',))
            admins = cursor.fetchall()
            if admins:
                for admin in admins:
                    print(f"   Admin found: {admin[0]} (tier: {admin[1]})")
        
        conn.close()
    except Exception as e:
        print(f"   ERROR: {str(e)}")

# 3. Check Flask app database configuration
print("\n3. CHECKING FLASK APP DATABASE CONFIG:")
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

with app.app_context():
    print(f"   Config DB URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    print(f"   Flask ENV: {app.config.get('ENV')}")
    print(f"   Debug Mode: {app.config.get('DEBUG')}")
    
    # Try to query through SQLAlchemy
    from app.models import User
    from app.extensions import db
    
    try:
        # Get the actual database file being used
        engine = db.engine
        db_url = str(engine.url)
        print(f"   Active DB URL: {db_url}")
        
        # Try a query
        user_count = User.query.count()
        print(f"   SQLAlchemy User Count: {user_count}")
        
        # List all users
        users = User.query.all()
        for user in users:
            print(f"   User: {user.email} (tier: {user.subscription_tier}, active: {user.is_active})")
            
    except Exception as e:
        print(f"   SQLAlchemy ERROR: {str(e)}")

# 4. Check which database file the app is actually using
print("\n4. VERIFYING ACTIVE DATABASE FILE:")
if 'sqlite' in app.config.get('SQLALCHEMY_DATABASE_URI', ''):
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    abs_path = os.path.abspath(db_path)
    print(f"   Absolute path: {abs_path}")
    print(f"   File exists: {os.path.exists(abs_path)}")
    if os.path.exists(abs_path):
        print(f"   File size: {os.path.getsize(abs_path)} bytes")

print("\n=== END OF DEEP DATABASE CHECK ===")