"""
Database initialization script with proper Flask app context
Fixes the context issues found during testing
"""

from app import app
from models import db, User, PricingPlan
import os

def init_database():
    """Initialize database with proper Flask app context"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Seeding default pricing plans...")
        PricingPlan.seed_default_plans()
        
        # Create admin user if doesn't exist
        # Only create admin user if credentials are provided
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if admin_password:
            admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User(
                    email=admin_email,
                    full_name='Administrator',
                    subscription_tier='premium',
                    credits_balance=999999,  # Unlimited credits
                    is_active=True
                )
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                print(f"[OK] Admin user created: {admin_email}")
            else:
                print("[OK] Admin user already exists")
        else:
            print("[INFO] ADMIN_PASSWORD not set - skipping admin user creation")
            print("[INFO] Run create_admin.py to create an admin user")
        
        print("[OK] Database initialization completed successfully")

if __name__ == '__main__':
    init_database()