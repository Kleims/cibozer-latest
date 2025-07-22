#!/usr/bin/env python3
"""
Cibozer Phase 1: Foundation Setup Script
Automates production environment setup and configuration
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"[*] {title}")
    print("="*60)

def print_step(step, description):
    """Print formatted step"""
    print(f"\n[Step {step}] {description}")
    print("-" * 40)

def check_requirements():
    """Check if all requirements are met"""
    print_header("PHASE 1: FOUNDATION SETUP")
    print("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8+ required")
        return False
    print(f"[OK] Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if virtual environment is active
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("[WARN] Virtual environment not detected. Recommended to use venv.")
    else:
        print("[OK] Virtual environment active")
    
    # Check key files exist
    required_files = ['app.py', 'models.py', 'requirements.txt', '.env']
    for file in required_files:
        if not os.path.exists(file):
            print(f"[ERROR] Missing required file: {file}")
            return False
        print(f"[OK] Found {file}")
    
    return True

def setup_environment():
    """Set up environment configuration"""
    print_step(1, "Environment Configuration")
    
    # Load current .env
    load_dotenv()
    
    # Check SECRET_KEY
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or len(secret_key) < 32:
        print("[KEY] Generating new SECRET_KEY...")
        new_secret = secrets.token_urlsafe(64)
        print(f"[OK] New SECRET_KEY generated (64 chars)")
        
        # Update .env file
        with open('.env', 'r') as f:
            content = f.read()
        
        if 'SECRET_KEY=' in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('SECRET_KEY='):
                    lines[i] = f'SECRET_KEY={new_secret}'
                    break
            content = '\n'.join(lines)
        else:
            content = f'SECRET_KEY={new_secret}\n' + content
        
        with open('.env', 'w') as f:
            f.write(content)
    else:
        print("✅ SECRET_KEY already configured")
    
    # Check admin configuration
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')
    
    if not admin_email or not admin_password:
        print("⚠️  Admin credentials not fully configured")
        print("   Current .env has default values - update for production")
    else:
        print("✅ Admin credentials configured")
    
    # Check database configuration
    db_url = os.getenv('DATABASE_URL', 'sqlite:///instance/cibozer.db')
    print(f"📊 Database: {db_url}")
    
    return True

def setup_directories():
    """Create necessary directories"""
    print_step(2, "Directory Structure")
    
    directories = [
        'instance',
        'uploads', 
        'videos',
        'pdfs',
        'saved_plans',
        'logs',
        'static/generated'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created/verified: {directory}")
    
    return True

def setup_database():
    """Initialize database"""
    print_step(3, "Database Initialization")
    
    try:
        # Import after ensuring .env is loaded
        from app import app, db
        from models import User, PricingPlan
        
        with app.app_context():
            print("🗄️  Creating database tables...")
            db.create_all()
            print("✅ Database tables created")
            
            # Seed pricing plans
            print("💰 Seeding pricing plans...")
            PricingPlan.seed_default_plans()
            print("✅ Pricing plans seeded")
            
            # Create admin user if credentials are set
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            
            if admin_email and admin_password:
                admin_user = User.query.filter_by(email=admin_email).first()
                if not admin_user:
                    admin_user = User(
                        email=admin_email,
                        full_name='Administrator',
                        subscription_tier='premium',
                        credits_balance=999999,
                        is_active=True
                    )
                    admin_user.set_password(admin_password)
                    db.session.add(admin_user)
                    db.session.commit()
                    print(f"✅ Admin user created: {admin_email}")
                else:
                    print(f"✅ Admin user already exists: {admin_email}")
            else:
                print("⚠️  Admin user not created - credentials not set")
            
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False

def test_application():
    """Test basic application functionality"""
    print_step(4, "Application Testing")
    
    try:
        from app import app
        
        with app.app_context():
            # Test app import
            print("✅ App imports successfully")
            
            # Test database connection
            from models import db, User
            user_count = User.query.count()
            print(f"✅ Database connection works ({user_count} users)")
            
            # Test meal optimizer
            try:
                from meal_optimizer_web import get_web_optimizer
                optimizer = get_web_optimizer()
                diet_types = list(optimizer.diet_profiles.keys())
                print(f"✅ Meal optimizer works ({len(diet_types)} diet types)")
            except Exception as e:
                print(f"⚠️  Meal optimizer issue: {str(e)}")
            
            # Test configuration
            from app_config import get_app_config, validate_config
            if validate_config():
                print("✅ Configuration validation passed")
            else:
                print("⚠️  Configuration validation issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Application test failed: {str(e)}")
        return False

def run_tests():
    """Run basic test suite"""
    print_step(5, "Running Tests")
    
    try:
        # Try to run pytest
        result = subprocess.run(['python', '-m', 'pytest', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pytest available")
            
            # Run quick tests
            print("🧪 Running basic tests...")
            result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-v', '--tb=short', '-x'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Basic tests passed")
            else:
                print("⚠️  Some tests failed - check logs")
                print(f"Test output: {result.stdout[-500:] if result.stdout else 'No output'}")
            
        else:
            print("⚠️  pytest not available - skipping tests")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("⚠️  Tests timed out - continuing setup")
        return True
    except Exception as e:
        print(f"⚠️  Test run failed: {str(e)}")
        return True

def generate_report():
    """Generate setup report"""
    print_header("PHASE 1 SETUP COMPLETE")
    
    load_dotenv()
    
    print("🎯 CONFIGURATION STATUS:")
    print(f"   Secret Key: {'✅ Set' if os.getenv('SECRET_KEY') else '❌ Missing'}")
    print(f"   Admin User: {'✅ Set' if os.getenv('ADMIN_EMAIL') else '❌ Missing'}")
    print(f"   Database: {os.getenv('DATABASE_URL', 'sqlite:///instance/cibozer.db')}")
    print(f"   Payments: {'✅ Enabled' if os.getenv('STRIPE_SECRET_KEY') else '⚠️  Disabled'}")
    
    print("\n🎯 NEXT STEPS:")
    print("   1. Configure Stripe for payments (if needed)")
    print("   2. Run Phase 2: Quality & Testing")
    print("   3. Set up performance monitoring")
    print("   4. Configure production deployment")
    
    print("\n🚀 QUICK START:")
    print("   python app.py                    # Start development server")
    print("   python create_admin.py          # Create/update admin user")
    print("   python -m pytest tests/         # Run test suite")
    print("   python setup_phase2.py          # Continue to Phase 2")

def main():
    """Main setup function"""
    print("[TARGET] Cibozer MVP Phase 1: Foundation Setup")
    print("This script will set up your production environment\n")
    
    # Step-by-step setup
    steps = [
        ("System Requirements", check_requirements),
        ("Environment Setup", setup_environment),
        ("Directory Creation", setup_directories),
        ("Database Setup", setup_database),
        ("Application Test", test_application),
        ("Test Suite", run_tests)
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"\n❌ {step_name} failed - setup incomplete")
                return False
        except KeyboardInterrupt:
            print(f"\n⏹️  Setup interrupted during {step_name}")
            return False
        except Exception as e:
            print(f"\n❌ Unexpected error in {step_name}: {str(e)}")
            return False
    
    # Generate final report
    generate_report()
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
