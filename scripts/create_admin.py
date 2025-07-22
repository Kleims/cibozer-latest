#!/usr/bin/env python3
"""
Simple script to create admin user
Run this if you need to manually create the admin user
"""

import os
import secrets
import getpass
from app import app
from models import db, User

def create_admin():
    with app.app_context():
        # Get admin email from environment or prompt
        admin_email = os.environ.get('ADMIN_EMAIL')
        if not admin_email:
            admin_email = input("Enter admin email (default: admin@cibozer.com): ").strip()
            if not admin_email:
                admin_email = 'admin@cibozer.com'
        
        # Check if admin exists
        admin = User.query.filter_by(email=admin_email).first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            update = input("Update password? (y/N): ").strip().lower()
            if update != 'y':
                return
        
        # Get admin password from environment or prompt
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            while True:
                admin_password = getpass.getpass("Enter admin password (min 12 chars): ")
                if len(admin_password) < 12:
                    print("Password must be at least 12 characters long!")
                    continue
                confirm_password = getpass.getpass("Confirm admin password: ")
                if admin_password != confirm_password:
                    print("Passwords do not match!")
                    continue
                break
        
        if not admin:
            # Create admin user
            admin = User(
                email=admin_email,
                full_name='Administrator',
                subscription_tier='premium',
                credits_balance=999999,
                is_active=True
            )
        
        admin.set_password(admin_password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✅ Admin user created/updated successfully!")
        print(f"Email: {admin_email}")
        print("⚠️  Store the password securely - it cannot be retrieved!")
        
        # Generate a secure token for first-time setup if needed
        if not os.environ.get('ADMIN_PASSWORD'):
            setup_token = secrets.token_urlsafe(32)
            print(f"\n🔐 One-time setup token: {setup_token}")
            print("Use this token for initial admin setup if needed.")

if __name__ == '__main__':
    create_admin()