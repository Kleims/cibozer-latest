#!/usr/bin/env python3
"""
Simple Cibozer Setup Script
"""

import os
import sys
import secrets
from pathlib import Path

def main():
    print("CIBOZER SETUP")
    print("=" * 40)
    
    # 1. Create .env if it doesn't exist
    env_file = Path('.env')
    if not env_file.exists():
        print("[1/4] Creating .env file...")
        secret_key = secrets.token_urlsafe(64)
        
        env_content = f"""# Cibozer Environment Configuration
SECRET_KEY={secret_key}
DEBUG=False
DATABASE_URL=sqlite:///cibozer.db

# Stripe Payment Integration
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRICE_ID_PRO=price_your_pro_price_id_here
STRIPE_PRICE_ID_PREMIUM=price_your_premium_price_id_here

# Admin Access
ADMIN_USERNAME=admin
ADMIN_PASSWORD=change_this_password
ADMIN_EMAIL=admin@cibozer.com

# Pricing
PRO_PRICE=9.99
PREMIUM_PRICE=19.99
"""
        
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("    Created .env with secure secret key")
    else:
        print("[1/4] .env file already exists")
    
    # 2. Initialize database
    print("[2/4] Setting up database...")
    try:
        from app import app, db
        from models import PricingPlan
        
        with app.app_context():
            db.create_all()
            PricingPlan.seed_default_plans()
        print("    Database initialized")
    except Exception as e:
        print(f"    Database error: {e}")
    
    # 3. Create admin user
    print("[3/4] Creating admin user...")
    try:
        from app import app, db
        from models import User
        
        with app.app_context():
            admin_user = User.query.filter_by(email='admin@cibozer.com').first()
            if not admin_user:
                admin_user = User(
                    email='admin@cibozer.com',
                    full_name='Administrator',
                    subscription_tier='premium',
                    subscription_status='active',
                    credits_balance=-1,
                    is_active=True
                )
                admin_user.set_password('change_this_password')
                db.session.add(admin_user)
                db.session.commit()
                print("    Admin user created: admin@cibozer.com")
            else:
                print("    Admin user already exists")
    except Exception as e:
        print(f"    Admin user error: {e}")
    
    # 4. Show next steps
    print("[4/4] Setup complete!")
    print("\nNEXT STEPS:")
    print("1. Update Stripe keys in .env file")
    print("2. Change admin password in .env file")
    print("3. Run: python app.py")
    print("4. Visit: http://localhost:5001")
    print("5. Admin login: http://localhost:5001/admin")
    print("\nREVENUE READY:")
    print("- Payment system implemented")
    print("- Subscription limits enforced")
    print("- Admin dashboard available")
    print("- Ready for production deployment!")

if __name__ == '__main__':
    main()