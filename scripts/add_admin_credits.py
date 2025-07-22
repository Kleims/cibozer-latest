#!/usr/bin/env python3
"""
Add credits to admin user
"""

from app import app
from models import db, User
from flask import Flask
import os

def add_admin_credits():
    """Add credits to admin user"""
    with app.app_context():
        # Find admin user (usually the first user or one with admin email)
        admin_user = User.query.filter_by(email='admin@cibozer.com').first()
        
        if not admin_user:
            # Try to find any user with 'admin' in email
            admin_user = User.query.filter(User.email.like('%admin%')).first()
        
        if not admin_user:
            # Get the first user (likely admin)
            admin_user = User.query.first()
        
        if not admin_user:
            print("❌ No users found in database")
            return False
        
        print(f"📧 Found user: {admin_user.email}")
        print(f"💰 Current credits: {admin_user.credits_balance}")
        
        # Add 100 credits
        admin_user.add_credits(100)
        
        print(f"✅ Added 100 credits!")
        print(f"💰 New balance: {admin_user.credits_balance}")
        
        return True

if __name__ == '__main__':
    success = add_admin_credits()
    if success:
        print("\n🚀 Credits added successfully! You can now generate meal plans.")
    else:
        print("\n❌ Failed to add credits.")