#!/usr/bin/env python
"""
Secure Admin Setup Script for Cibozer
Generates secure credentials and updates the database
"""

import os
import sys
import secrets
import string
from datetime import datetime
from dotenv import load_dotenv, set_key
import bcrypt

# Load existing environment
load_dotenv()

def generate_secure_password(length=16):
    """Generate a cryptographically secure password"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Remove problematic characters for shell/env usage
    alphabet = alphabet.replace('"', '').replace("'", '').replace('\\', '').replace('`', '')
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

def update_admin_credentials():
    """Update admin credentials securely"""
    print("🔐 Cibozer Admin Setup")
    print("=" * 50)
    
    # Check if running in production
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    # Get or prompt for admin username
    current_username = os.environ.get('ADMIN_USERNAME', 'admin')
    username = input(f"Admin username [{current_username}]: ").strip() or current_username
    
    # Generate secure password
    if is_production or input("Generate secure password? (Y/n): ").lower() != 'n':
        password = generate_secure_password()
        print(f"\n✅ Generated secure password: {password}")
        print("⚠️  SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN")
    else:
        password = input("Enter admin password: ").strip()
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            return False
    
    # Update .env file
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    try:
        # Update environment variables
        set_key(env_path, 'ADMIN_USERNAME', username)
        set_key(env_path, 'ADMIN_PASSWORD', password)
        
        # Also update in-memory for database update
        os.environ['ADMIN_USERNAME'] = username
        os.environ['ADMIN_PASSWORD'] = password
        
        print("\n✅ Admin credentials updated in .env")
        
        # Update database if exists
        try:
            from app import app, db
            from models import User
            
            with app.app_context():
                # Check if admin user exists
                admin_user = User.query.filter_by(email=f"{username}@cibozer.local").first()
                
                if admin_user:
                    # Update existing admin
                    admin_user.set_password(password)
                    admin_user.full_name = f"Admin ({username})"
                    print("✅ Updated existing admin user in database")
                else:
                    # Create new admin
                    admin_user = User(
                        email=f"{username}@cibozer.local",
                        full_name=f"Admin ({username})",
                        subscription_tier='admin',
                        subscription_status='active',
                        credits_balance=999999,
                        email_verified=True,
                        is_active=True
                    )
                    admin_user.set_password(password)
                    db.session.add(admin_user)
                    print("✅ Created new admin user in database")
                
                db.session.commit()
                print("✅ Database updated successfully")
                
        except Exception as e:
            print(f"\n⚠️  Could not update database: {e}")
            print("   Run the app once to create database, then run this script again")
        
        print("\n" + "=" * 50)
        print("🎉 Admin setup complete!")
        print(f"   Username: {username}")
        print(f"   Password: [HIDDEN - check output above]")
        print("\n📝 Next steps:")
        print("   1. Start the application")
        print("   2. Visit /admin/login")
        print("   3. Use the credentials above")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating credentials: {e}")
        return False

def verify_environment():
    """Verify critical environment variables"""
    print("\n🔍 Verifying environment...")
    
    required_vars = {
        'SECRET_KEY': 'Application secret key',
        'DATABASE_URL': 'Database connection string'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing.append(f"   - {var}: {description}")
        else:
            print(f"   ✅ {var}: Set")
    
    if missing:
        print("\n⚠️  Missing required environment variables:")
        for item in missing:
            print(item)
        
        if 'SECRET_KEY' not in os.environ:
            if input("\nGenerate SECRET_KEY? (Y/n): ").lower() != 'n':
                secret_key = secrets.token_urlsafe(64)
                set_key('.env', 'SECRET_KEY', secret_key)
                print(f"✅ Generated SECRET_KEY")
    
    print()

if __name__ == "__main__":
    # Fix for Windows console encoding
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("🚀 Cibozer Admin Setup Tool")
    print("This tool helps you securely configure admin access\n")
    
    # Verify environment first
    verify_environment()
    
    # Update admin credentials
    if update_admin_credentials():
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check errors above.")
        sys.exit(1)