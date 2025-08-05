#!/usr/bin/env python3
"""Fix database schema by creating all tables"""
import os
import sys
import getpass
from app import create_app
from app.models import db, User

def fix_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating all tables...")
        db.create_all()
        
        # Create admin user
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            admin_password = getpass.getpass('Enter admin password: ')
            if not admin_password:
                print("Error: Password is required")
                sys.exit(1)
        
        admin = User(
            email=admin_email,
            full_name='Administrator',
            subscription_tier='premium',
            subscription_status='active',
            credits_balance=1000,
            is_active=True,
            email_verified=True
        )
        admin.set_password(admin_password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"\n✅ Database fixed and admin created!")
        print(f"   Email: {admin_email}")
        print(f"   Password: {admin_password}")
        print(f"\nLogin at: http://localhost:5000/auth/login")

if __name__ == '__main__':
    fix_database()