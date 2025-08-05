#!/usr/bin/env python
"""Setup database with proper data."""
import os
import sys

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from app.extensions import db

print("=== SETTING UP DATABASE PROPERLY ===\n")

app = create_app()

with app.app_context():
    print("1. Creating all tables...")
    db.create_all()
    
    print("\n2. Checking for existing admin...")
    admin = User.query.filter_by(email='admin@cibozer.com').first()
    
    if not admin:
        print("3. Creating admin user...")
        admin = User(
            email='admin@cibozer.com',
            full_name='Admin User',
            subscription_tier='premium',
            subscription_status='active',
            email_verified=True,
            is_active=True
        )
        admin.set_password('SecureAdmin2024!MVP')
        db.session.add(admin)
        
        # Also create a test user
        print("4. Creating test user...")
        test_user = User(
            email='jose_grd92@hotmail.com',
            full_name='Jose Test',
            subscription_tier='free',
            subscription_status='active',
            email_verified=True,
            is_active=True,
            credits_balance=3
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        
        db.session.commit()
        print("   Users created successfully!")
    else:
        print("   Admin already exists")
    
    print("\n5. Final verification:")
    users = User.query.all()
    print(f"   Total users: {len(users)}")
    for user in users:
        print(f"   - {user.email} (tier: {user.subscription_tier}, credits: {user.credits_balance})")

print("\n=== DATABASE SETUP COMPLETE ===")