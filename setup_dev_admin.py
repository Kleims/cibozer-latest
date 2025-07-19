#!/usr/bin/env python
"""
Development admin setup script
Creates an admin user for local development
"""

import os
import sys
from datetime import datetime, timezone

# Force development environment
os.environ['FLASK_ENV'] = 'development'

# Use development env file
from pathlib import Path
if Path('.env.development').exists():
    from dotenv import load_dotenv
    load_dotenv('.env.development')

try:
    from app import app, db
    from models import User
    
    print("Setting up development admin user...")
    
    with app.app_context():
        # Check if admin already exists
        admin_email = 'admin@localhost'
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"[OK] Admin user already exists: {admin_email}")
            print(f"   Credits: {admin.credits_balance}")
            print(f"   Tier: {admin.subscription_tier}")
        else:
            # Create admin user
            admin = User(
                email=admin_email,
                full_name='Development Admin',
                subscription_tier='premium',
                subscription_status='active',
                credits_balance=999999,
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password('admin123')  # Default dev password
            
            db.session.add(admin)
            db.session.commit()
            
            print(f"[OK] Created admin user: {admin_email}")
            print(f"   Password: admin123")
            print(f"   Tier: premium (unlimited)")
            
        # Create a test user too
        test_email = 'test@localhost'
        test_user = User.query.filter_by(email=test_email).first()
        
        if not test_user:
            test_user = User(
                email=test_email,
                full_name='Test User',
                subscription_tier='free',
                subscription_status='active',
                credits_balance=3,
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            test_user.set_password('test123')
            
            db.session.add(test_user)
            db.session.commit()
            
            print(f"\n[OK] Created test user: {test_email}")
            print(f"   Password: test123")
            print(f"   Tier: free (3 credits)")
            
        print("\nDevelopment users ready!")
        print("   Admin URL: http://localhost:5001/admin")
        print("   Login URL: http://localhost:5001/auth/login")
        
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)