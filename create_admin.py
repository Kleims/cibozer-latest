#!/usr/bin/env python3
"""Create admin user for Cibozer"""

import os
import sys
from datetime import datetime, timezone

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User

def create_admin_user():
    """Create admin user with the credentials from .env"""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if admin_user:
            print(f"Admin user already exists: {admin_email}")
            print(f"Full name: {admin_user.full_name}")
            print(f"Subscription tier: {admin_user.subscription_tier}")
            print(f"Credits: {admin_user.credits_balance}")
        else:
            # Create new admin user
            admin_password = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'SecureAdmin2024!MVP')
            
            admin_user = User(
                email=admin_email,
                full_name='Admin User',
                subscription_tier='premium',
                credits_balance=1000,
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            
            admin_user.set_password(admin_password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"Admin user created successfully!")
            print(f"Email: {admin_email}")
            print(f"Password: {admin_password}")
            print(f"Premium tier: premium")
            print(f"Credits: 1000")
        
        # Also show the admin panel credentials
        print("\nAdmin Panel Login:")
        print(f"URL: http://localhost:5000/admin")
        print(f"Username: {os.environ.get('ADMIN_USERNAME', 'admin')}")
        print(f"Password: {os.environ.get('ADMIN_PASSWORD', 'SecureAdmin2024!MVP')}")

if __name__ == '__main__':
    create_admin_user()