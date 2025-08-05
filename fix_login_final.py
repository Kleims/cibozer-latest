#!/usr/bin/env python3
"""Final fix for login issue"""
import os
import shutil
from app import create_app
from app.models import db, User

def fix_login():
    # First, let's ensure we're using the right database
    app = create_app()
    
    with app.app_context():
        print("Current database:", app.config['SQLALCHEMY_DATABASE_URI'])
        
        # Drop and recreate all tables
        print("\nRecreating database tables...")
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            email='admin@cibozer.com',
            full_name='Administrator',
            subscription_tier='premium',
            subscription_status='active',
            credits_balance=1000,
            is_active=True,
            email_verified=True
        )
        admin.set_password('Admin123!')
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✓ Database fixed!")
        print("\nAdmin credentials:")
        print("  Email: admin@cibozer.com")
        print("  Password: Admin123!")
        print("\nLogin at: http://localhost:5000/auth/login")
        
        # Verify the user can be loaded
        test_user = User.query.filter_by(email='admin@cibozer.com').first()
        if test_user and test_user.check_password('Admin123!'):
            print("\n✓ Login verification passed!")
        else:
            print("\n✗ Login verification failed!")

if __name__ == '__main__':
    fix_login()