#!/usr/bin/env python3
"""
Simple script to create admin user
Run this if you need to manually create the admin user
"""

from app import app
from models import db, User

def create_admin():
    with app.app_context():
        # Check if admin exists
        admin = User.query.filter_by(email='admin').first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return
        
        # Create admin user
        admin = User(
            email='admin',
            full_name='Administrator',
            subscription_tier='premium',
            credits_balance=999999,
            is_active=True
        )
        admin.set_password('admin')
        
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin")

if __name__ == '__main__':
    create_admin()