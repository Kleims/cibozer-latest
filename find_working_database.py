#!/usr/bin/env python
"""Find the ACTUAL working database by starting the app the way it normally works."""
import os
import sys

# CRITICAL: Set environment BEFORE imports
os.environ['FLASK_ENV'] = 'development'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== FINDING THE REAL WORKING DATABASE ===\n")

# Start the app the EXACT way that works
print("1. Starting app the working way...")

# Import AFTER setting environment
from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    print(f"2. Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Create all tables if they don't exist
    print("\n3. Creating all tables...")
    db.create_all()
    print("   Tables created/verified")
    
    # Now check what we have
    print("\n4. Checking database contents...")
    try:
        users = User.query.all()
        print(f"   Found {len(users)} users:")
        for user in users:
            print(f"   - {user.email} (tier: {user.subscription_tier})")
    except Exception as e:
        print(f"   Error querying users: {e}")
        
    # Check the actual file
    if 'sqlite' in str(db.engine.url):
        db_path = str(db.engine.url).replace('sqlite:///', '')
        print(f"\n5. Database file location: {db_path}")
        print(f"   Absolute path: {os.path.abspath(db_path)}")
        
        # Get file info
        if os.path.exists(db_path):
            import time
            stat = os.stat(db_path)
            print(f"   File size: {stat.st_size} bytes")
            print(f"   Last modified: {time.ctime(stat.st_mtime)}")
        
print("\n=== END ===")