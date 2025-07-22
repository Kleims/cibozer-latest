#!/usr/bin/env python3
"""
Setup different environment configurations
Creates .env files for development, staging, and production
"""

import os
import sys
import secrets
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(64)

def create_env_file(filename, content):
    """Create an environment file if it doesn't exist"""
    path = Path(filename)
    if path.exists():
        print(f"{filename} already exists, skipping...")
        return False
    
    with open(path, 'w') as f:
        f.write(content)
    print(f"Created {filename}")
    return True

def main():
    """Create environment configuration files"""
    print("Setting up environment configurations...")
    
    # Development environment
    dev_content = f"""# Cibozer Development Environment
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY={generate_secret_key()}
DATABASE_URL=sqlite:///instance/cibozer_dev.db

# Optional services (uncomment to enable)
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...
# MAIL_SERVER=smtp.gmail.com
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password
"""
    
    # Production environment
    prod_content = f"""# Cibozer Production Environment
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY={generate_secret_key()}

# Database (use PostgreSQL for production)
DATABASE_URL=postgresql://user:password@localhost/cibozer

# Security
SESSION_COOKIE_SECURE=True
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Required for production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=noreply@yourdomain.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=Cibozer <noreply@yourdomain.com>

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD={secrets.token_urlsafe(32)}
"""
    
    # Base .env file (for local development)
    base_content = f"""# Cibozer Environment Configuration
# This is the default configuration for local development
# For production, use .env.production

FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY={generate_secret_key()}
DATABASE_URL=sqlite:///instance/cibozer.db

# Optional: Uncomment and configure as needed
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...
"""
    
    # Create files
    created = []
    if create_env_file('.env', base_content):
        created.append('.env')
    if create_env_file('.env.development', dev_content):
        created.append('.env.development')
    if create_env_file('.env.production', prod_content):
        created.append('.env.production')
    
    # Create .gitignore if needed
    gitignore_path = Path('.gitignore')
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
    else:
        gitignore_content = ""
    
    # Add env files to .gitignore
    env_patterns = ['.env', '.env.*', '!.env.example', '!.env.template']
    updated = False
    
    for pattern in env_patterns:
        if pattern not in gitignore_content:
            gitignore_content += f"\n{pattern}"
            updated = True
    
    if updated:
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content.strip() + '\n')
        print("Updated .gitignore to exclude environment files")
    
    # Summary
    print("\n" + "="*50)
    print("Environment setup complete!")
    print("="*50)
    
    if created:
        print(f"\nCreated {len(created)} environment file(s):")
        for file in created:
            print(f"  - {file}")
    
    print("\nNext steps:")
    print("1. Review and update the environment files with your actual values")
    print("2. Never commit .env files to version control")
    print("3. Use .env for local development")
    print("4. Use .env.production for production deployment")
    print("\nTo switch environments:")
    print("  export FLASK_ENV=production  # Use production settings")
    print("  export FLASK_ENV=development # Use development settings")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())