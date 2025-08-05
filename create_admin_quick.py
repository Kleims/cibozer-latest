#!/usr/bin/env python3
"""Quick admin user creation script"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, User
from datetime import datetime, timezone

def create_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin exists
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"Admin user already exists: {admin_email}")
            # Update password just in case
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'SecureAdminPassword123!'))
            db.session.commit()
            print("Password updated successfully!")
        else:
            # Create new admin
            admin = User(
                email=admin_email,
                full_name=os.environ.get('ADMIN_USERNAME', 'Administrator'),
                subscription_tier='premium',
                subscription_status='active',
                credits_balance=1000,
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'SecureAdminPassword123!'))
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"Admin user created successfully!")
        
        print(f"\n✅ Admin Login Credentials:")
        print(f"   Email: {admin_email}")
        print(f"   Password: {os.environ.get('ADMIN_PASSWORD', 'SecureAdminPassword123!')}")

if __name__ == '__main__':
    create_admin()