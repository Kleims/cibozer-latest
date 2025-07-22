#!/usr/bin/env python
"""
Production setup script for Cibozer
Sets up admin user and validates configuration
"""

import os
import sys
import getpass
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path('.env.production')
if not env_file.exists():
    print("\n⚠️  ERROR: .env.production file not found!")
    print("Please copy .env.production.example and configure it first.")
    sys.exit(1)

load_dotenv('.env.production')

# Check critical environment variables
required_vars = ['SECRET_KEY', 'ADMIN_EMAIL', 'ADMIN_PASSWORD']
missing_vars = [var for var in required_vars if not os.getenv(var) or os.getenv(var) == 'CHANGE_THIS_IN_PRODUCTION']

if missing_vars:
    print(f"\n⚠️  ERROR: Missing or default values for: {', '.join(missing_vars)}")
    print("Please edit .env.production and set proper values.")
    sys.exit(1)

# Import app components
try:
    from app import app, db
    from models import User
    from datetime import datetime, timezone
    print("✅ Successfully imported application components")
except Exception as e:
    print(f"❌ Failed to import app components: {e}")
    sys.exit(1)

def setup_admin():
    """Create or update admin user"""
    with app.app_context():
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        
        # Check if admin exists
        admin = User.query.filter_by(email=admin_email).first()
        
        if admin:
            print(f"\n✅ Admin user '{admin_email}' already exists")
            update = input("Do you want to update the password? (y/N): ").lower()
            
            if update == 'y':
                # Get new password securely
                while True:
                    new_password = getpass.getpass("Enter new admin password: ")
                    confirm_password = getpass.getpass("Confirm password: ")
                    
                    if new_password == confirm_password:
                        if len(new_password) < 8:
                            print("❌ Password must be at least 8 characters long")
                            continue
                        admin.set_password(new_password)
                        db.session.commit()
                        print("✅ Admin password updated successfully")
                        break
                    else:
                        print("❌ Passwords don't match. Try again.")
        else:
            # Create new admin
            print(f"\n📝 Creating admin user: {admin_email}")
            
            admin = User(
                email=admin_email,
                full_name='Administrator',
                subscription_tier='premium',
                subscription_status='active',
                credits_balance=999999,  # Unlimited
                is_active=True,
                email_verified=True,
                created_at=datetime.now(timezone.utc)
            )
            admin.set_password(admin_password)
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created successfully!")

def validate_configuration():
    """Validate critical configuration"""
    print("\n🔍 Validating configuration...")
    
    issues = []
    
    # Check SECRET_KEY
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or len(secret_key) < 32:
        issues.append("SECRET_KEY is too short (minimum 32 characters)")
    
    # Check database
    db_url = os.getenv('DATABASE_URL', 'sqlite:///cibozer.db')
    print(f"   Database: {db_url}")
    
    # Check debug mode
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'
    if debug_mode:
        issues.append("DEBUG mode is enabled - should be False for production")
    
    if issues:
        print("\n⚠️  Configuration issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ Configuration validated successfully")
    return True

def main():
    """Main setup process"""
    print("\n🚀 Cibozer Production Setup")
    print("=" * 40)
    
    # Validate configuration
    if not validate_configuration():
        fix = input("\nDo you want to continue anyway? (y/N): ").lower()
        if fix != 'y':
            print("Setup cancelled.")
            sys.exit(1)
    
    # Setup admin
    setup_admin()
    
    # Create required directories
    dirs = ['logs', 'uploads', 'videos', 'pdfs', 'saved_plans', 'static/generated']
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print(f"\n✅ Created {len(dirs)} required directories")
    
    print("\n✅ Production setup complete!")
    print("\n📋 Next steps:")
    print("1. Set environment variables for production deployment")
    print("2. Configure your web server (nginx, Apache, etc.)")
    print("3. Set up SSL certificate for HTTPS")
    print("4. Configure firewall rules")
    print("5. Set up monitoring and logging")
    print("\n🌐 Your app is ready for production deployment!")

if __name__ == '__main__':
    main()