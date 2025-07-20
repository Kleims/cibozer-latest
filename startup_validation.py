"""
Startup validation to ensure critical environment variables and configurations are set.
Run this before starting the application in production.
"""

import os
import sys
from typing import List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_critical_vars() -> Tuple[List[str], List[str]]:
    """Check for critical environment variables"""
    errors = []
    warnings = []
    
    # Critical security variables
    if not os.getenv('SECRET_KEY'):
        errors.append("CRITICAL: SECRET_KEY is not set!")
    elif len(os.getenv('SECRET_KEY', '')) < 32:
        errors.append("CRITICAL: SECRET_KEY is too short (minimum 32 characters)")
    
    # Database
    if not os.getenv('DATABASE_URL'):
        warnings.append("DATABASE_URL not set, will use default SQLite")
    
    # Admin configuration
    if not os.getenv('ADMIN_PASSWORD'):
        warnings.append("ADMIN_PASSWORD not set - admin panel will be disabled")
    elif len(os.getenv('ADMIN_PASSWORD', '')) < 12:
        errors.append("ADMIN_PASSWORD is too weak (minimum 12 characters)")
    
    # Stripe configuration
    if os.getenv('STRIPE_SECRET_KEY'):
        if os.getenv('STRIPE_SECRET_KEY', '').startswith('sk_test'):
            warnings.append("Stripe is in TEST mode")
        if not os.getenv('STRIPE_PUBLISHABLE_KEY'):
            errors.append("STRIPE_PUBLISHABLE_KEY missing but STRIPE_SECRET_KEY is set")
        if not os.getenv('STRIPE_WEBHOOK_SECRET'):
            warnings.append("STRIPE_WEBHOOK_SECRET not set - webhooks won't work")
    
    # Email configuration
    if os.getenv('MAIL_SERVER'):
        required_mail_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD']
        for var in required_mail_vars:
            if not os.getenv(var):
                errors.append(f"{var} is required when MAIL_SERVER is set")
    
    # Security settings
    if os.getenv('FLASK_DEBUG', '').lower() == 'true':
        warnings.append("FLASK_DEBUG is enabled - disable in production!")
    
    if os.getenv('SESSION_COOKIE_SECURE', 'True').lower() != 'true':
        warnings.append("SESSION_COOKIE_SECURE should be True in production")
    
    return errors, warnings

def check_directories() -> List[str]:
    """Check for required directories"""
    errors = []
    required_dirs = ['logs', 'instance', 'uploads', 'videos', 'pdfs', 'saved_plans']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            try:
                os.makedirs(dir_name, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create directory {dir_name}: {str(e)}")
    
    return errors

def check_file_permissions() -> List[str]:
    """Check file permissions"""
    warnings = []
    
    # Check if we can write to critical directories
    test_dirs = ['logs', 'uploads', 'videos', 'pdfs']
    for dir_name in test_dirs:
        if os.path.exists(dir_name):
            test_file = os.path.join(dir_name, '.write_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                warnings.append(f"Cannot write to {dir_name}: {str(e)}")
    
    return warnings

def main():
    """Run all startup validations"""
    print("=" * 60)
    print("CIBOZER STARTUP VALIDATION")
    print("=" * 60)
    
    # Check environment variables
    errors, warnings = check_critical_vars()
    
    # Check directories
    dir_errors = check_directories()
    errors.extend(dir_errors)
    
    # Check permissions
    perm_warnings = check_file_permissions()
    warnings.extend(perm_warnings)
    
    # Display results
    if errors:
        print("\n[X] CRITICAL ERRORS (must fix before running):")
        for error in errors:
            print(f"  - {error}")
    
    if warnings:
        print("\n[!] WARNINGS (should fix for production):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if not errors and not warnings:
        print("\n[OK] All checks passed! Ready to start.")
    
    print("\n" + "=" * 60)
    
    # Exit with error code if critical errors found
    if errors:
        print("\n[STOP] Cannot start application with critical errors.")
        sys.exit(1)
    else:
        print("\n[OK] Application can start (fix warnings if in production).")
        sys.exit(0)

if __name__ == "__main__":
    main()