#!/usr/bin/env python3
"""Fix development database and create admin user"""
import os
import sys
import getpass
from app import create_app
from app.models import db, User

def fix_dev_database():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        
        # Check if admin exists
        admin_email = 'admin@cibozer.com'
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"Admin user already exists: {admin_email}")
            # Update password
            password = os.environ.get('ADMIN_PASSWORD')
            if not password:
                password = getpass.getpass('Enter new admin password: ')
                if not password:
                    print("Error: Password is required")
                    sys.exit(1)
            admin.set_password(password)
            db.session.commit()
            print("Password updated!")
        else:
            # Create admin user
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
            print("Admin user created!")
        
        print(f"\nAdmin Login Credentials:")
        print(f"   Email: {admin_email}")
        print(f"   Password: SecureAdminPassword123!")
        print(f"\nLogin at: http://localhost:5000/auth/login")

if __name__ == '__main__':
    fix_dev_database()