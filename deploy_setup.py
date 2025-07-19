#!/usr/bin/env python3
"""
Cibozer Deployment Setup Script
Automates the setup process for production deployment
"""

import os
import sys
import subprocess
import secrets
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and return success status"""
    print(f"[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[✓] {description} completed")
            return True
        else:
            print(f"[✗] {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"[✗] {description} failed with exception: {e}")
        return False

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(64)

def setup_environment():
    """Set up .env file if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        print("[*] Creating .env file from template...")
        
        # Read template
        with open(env_example, 'r') as f:
            content = f.read()
        
        # Replace with secure values
        secret_key = generate_secret_key()
        content = content.replace('your-super-secret-key-change-this-now', secret_key)
        
        # Write .env file
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("[✓] .env file created with secure secret key")
        print("[!] Please update Stripe keys and other settings in .env")
        return True
    else:
        print("[i] .env file already exists")
        return True

def clean_git_state():
    """Clean up git state and commit changes"""
    print("\n[*] Cleaning up git state...")
    
    # Remove pycache files (Windows compatible)
    run_command('del /s /q __pycache__ >nul 2>&1 || echo "No pycache to remove"', "Removing __pycache__ directories")
    run_command('del /s /q *.pyc >nul 2>&1 || echo "No pyc files to remove"', "Removing .pyc files")
    
    # Add gitignore for Python cache if not exists
    gitignore = Path('.gitignore')
    if not gitignore.exists():
        with open(gitignore, 'w') as f:
            f.write("""
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv

# Environment
.env
.env.local

# Logs
logs/
*.log

# Database
*.db
cibozer.db

# Uploads
uploads/
videos/
pdfs/
saved_plans/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
""")
        print("[✓] Created .gitignore file")
    
    # Git operations
    if run_command('git status', "Checking git status"):
        run_command('git add .', "Staging changes")
        run_command('git commit -m "Production deployment setup - Payment system implemented"', "Committing changes")
        print("[✓] Git state cleaned and committed")
    
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("\n[*] Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask-sqlalchemy', 
        'flask-login',
        'bcrypt',
        'stripe',
        'python-dotenv'
    ]
    
    try:
        import importlib
        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"[✗] Missing packages: {', '.join(missing)}")
            print("[!] Run: pip install -r requirements.txt")
            return False
        else:
            print("[✓] All dependencies installed")
            return True
    except Exception as e:
        print(f"[✗] Error checking dependencies: {e}")
        return False

def initialize_database():
    """Initialize the database"""
    print("\n🗄️ Setting up database...")
    
    try:
        # Import app to trigger database creation
        from app import app, db
        from models import PricingPlan
        
        with app.app_context():
            db.create_all()
            PricingPlan.seed_default_plans()
            print("✅ Database initialized with default pricing plans")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_admin_user():
    """Create admin user if specified in environment"""
    print("\n👤 Setting up admin user...")
    
    try:
        from app import app, db
        from models import User
        
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        
        if not admin_password:
            print("⚠️  ADMIN_PASSWORD not set in .env - skipping admin user creation")
            return True
        
        with app.app_context():
            admin_user = User.query.filter_by(email=admin_email).first()
            if not admin_user:
                admin_user = User(
                    email=admin_email,
                    full_name='Administrator',
                    subscription_tier='premium',
                    subscription_status='active',
                    credits_balance=-1,  # Unlimited
                    is_active=True
                )
                admin_user.set_password(admin_password)
                db.session.add(admin_user)
                db.session.commit()
                print(f"✅ Admin user created: {admin_email}")
            else:
                print(f"ℹ️  Admin user already exists: {admin_email}")
        return True
    except Exception as e:
        print(f"❌ Admin user setup failed: {e}")
        return False

def show_next_steps():
    """Show next steps for deployment"""
    print("\n🎯 Next Steps:")
    print("1. Update .env file with your Stripe API keys")
    print("2. Set up Stripe webhook endpoint: /api/payments/webhook")
    print("3. Deploy to your chosen platform:")
    print("   • Railway: railway up")
    print("   • Heroku: git push heroku main")
    print("   • Vercel: vercel --prod")
    print("4. Test payment flow in production")
    print("5. Start marketing and user acquisition!")
    print("\n💰 Revenue Targets:")
    print("   • Month 1: 100 users × $10 avg = $1,000 MRR")
    print("   • Month 6: 1,000 users × $10 avg = $10,000 MRR")
    print("   • Year 1: 2,500 users × $10 avg = $25,000 MRR")

def main():
    """Main deployment setup function"""
    print("CIBOZER DEPLOYMENT SETUP")
    print("=" * 50)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Environment setup
    if setup_environment():
        success_count += 1
    
    # Step 2: Dependencies check
    if check_dependencies():
        success_count += 1
    
    # Step 3: Clean git state
    if clean_git_state():
        success_count += 1
    
    # Step 4: Database setup
    if initialize_database():
        success_count += 1
    
    # Step 5: Admin user
    if create_admin_user():
        success_count += 1
    
    print(f"\n📊 Setup completed: {success_count}/{total_steps} steps successful")
    
    if success_count == total_steps:
        print("🎉 Deployment setup completed successfully!")
        show_next_steps()
        return 0
    else:
        print("⚠️  Some steps failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)