"""
Test script to create admin user and test login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User

with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(email='admin').first()
    
    if not admin:
        # Create admin user
        admin = User(
            email='admin',
            full_name='Admin User',
            subscription_tier='pro',
            credits_balance=100
        )
        admin.set_password('admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / admin")
    else:
        print("Admin user already exists: admin")
        # Update password to ensure it's 'admin'
        admin.set_password('admin')
        db.session.commit()
        print("Admin password updated to: admin")
        
    # Test login functionality
    print(f"Admin user ID: {admin.id}")
    print(f"Admin credits: {admin.credits_balance}")
    print(f"Admin tier: {admin.subscription_tier}")
    
    # Test password check
    if admin.check_password('admin'):
        print("[OK] Password check works")
    else:
        print("[ERROR] Password check failed")
        
    print("\nTry logging in with:")
    print("Username: admin")
    print("Password: admin")