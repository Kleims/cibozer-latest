#!/usr/bin/env python3
"""
Create admin user with credits
"""

from app import app
from models import db, User
import bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_admin_user():
    """Create admin user with credits"""
    with app.app_context():
        # Check if admin user exists
        admin_user = User.query.filter_by(email='admin@cibozer.com').first()
        
        if admin_user:
            print(f"[OK] Admin user already exists: {admin_user.email}")
            print(f"[CREDITS] Current credits: {admin_user.credits_balance}")
            
            # Add more credits if needed
            if admin_user.credits_balance < 50:
                admin_user.add_credits(100)
                print(f"[CREDITS] Added 100 credits! New balance: {admin_user.credits_balance}")
            
            return admin_user
        
        # Create new admin user
        print("[SETUP] Creating new admin user...")
        
        # Get password from environment or use secure default
        password = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'ChangeMeImmediately123!')
        if password == 'ChangeMeImmediately123!':
            print("[WARNING] Using default password. Set ADMIN_DEFAULT_PASSWORD in .env file!")
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        admin_user = User(
            email='admin@cibozer.com',
            password_hash=password_hash,
            full_name='Administrator',
            subscription_tier='premium',  # Give admin premium access
            credits_balance=1000,  # Lots of credits
            email_verified=True,
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"[OK] Created admin user: {admin_user.email}")
        print(f"[PASSWORD] Password: {password}")
        print(f"[CREDITS] Credits: {admin_user.credits_balance}")
        print(f"[TIER] Tier: {admin_user.subscription_tier}")
        
        return admin_user

if __name__ == '__main__':
    admin = create_admin_user()
    if admin:
        print(f"\n[SUCCESS] Admin user ready!")
        print(f"[EMAIL] Email: {admin.email}")
        print(f"[CREDITS] Credits: {admin.credits_balance}")
        print(f"[URL] Login at: http://localhost:5001/auth/login")
    else:
        print("\n[ERROR] Failed to create admin user.")