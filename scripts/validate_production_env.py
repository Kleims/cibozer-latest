#!/usr/bin/env python3
"""
Production Environment Validation Script

This script validates that all required environment variables are properly configured
for production deployment. Run this before deploying to catch configuration issues early.

Usage:
    python scripts/validate_production_env.py
"""

import os
import sys
import re
from urllib.parse import urlparse

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class EnvironmentValidator:
    """Validates production environment configuration."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
    
    def validate_required_var(self, var_name, description, validator=None):
        """Validate a required environment variable."""
        value = os.environ.get(var_name)
        
        if not value:
            self.errors.append(f"Missing required variable: {var_name} ({description})")
            return False
        
        if validator and not validator(value):
            self.errors.append(f"Invalid value for {var_name}: {description}")
            return False
        
        self.passed.append(f"{var_name}: ✓")
        return True
    
    def validate_optional_var(self, var_name, description, validator=None):
        """Validate an optional environment variable."""
        value = os.environ.get(var_name)
        
        if not value:
            self.warnings.append(f"Optional variable not set: {var_name} ({description})")
            return False
        
        if validator and not validator(value):
            self.warnings.append(f"Invalid value for {var_name}: {description}")
            return False
        
        self.passed.append(f"{var_name}: ✓")
        return True
    
    def validate_database_url(self, url):
        """Validate PostgreSQL database URL format."""
        if not url:
            return False
        
        parsed = urlparse(url)
        return (
            parsed.scheme in ['postgresql', 'postgres'] and
            parsed.hostname and
            parsed.username and
            parsed.password and
            parsed.path
        )
    
    def validate_email(self, email):
        """Basic email validation."""
        return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None
    
    def validate_stripe_key(self, key, key_type):
        """Validate Stripe API key format."""
        if key_type == 'secret':
            return key.startswith('sk_')
        elif key_type == 'publishable':
            return key.startswith('pk_')
        elif key_type == 'webhook':
            return key.startswith('whsec_')
        return False
    
    def validate_url(self, url):
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def run_validation(self):
        """Run complete production environment validation."""
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 Cibozer Production Environment Validation{Colors.END}\n")
        
        # Core Application Settings
        print(f"{Colors.BOLD}📱 Core Application Settings{Colors.END}")
        self.validate_required_var('SECRET_KEY', 'Flask secret key for session security', 
                                 lambda x: len(x) >= 32)
        self.validate_required_var('FLASK_ENV', 'Flask environment', 
                                 lambda x: x == 'production')
        
        # Database Configuration
        print(f"{Colors.BOLD}🗄️  Database Configuration{Colors.END}")
        self.validate_required_var('DATABASE_URL', 'PostgreSQL database connection string', 
                                 self.validate_database_url)
        
        # Email Configuration
        print(f"{Colors.BOLD}📧 Email Configuration{Colors.END}")
        self.validate_required_var('MAIL_SERVER', 'SMTP server for sending emails')
        self.validate_required_var('MAIL_PORT', 'SMTP port', 
                                 lambda x: x.isdigit() and 1 <= int(x) <= 65535)
        self.validate_required_var('MAIL_USERNAME', 'SMTP username')
        self.validate_required_var('MAIL_PASSWORD', 'SMTP password')
        self.validate_required_var('MAIL_DEFAULT_SENDER', 'Default email sender', 
                                 self.validate_email)
        
        # Stripe Payment Configuration
        print(f"{Colors.BOLD}💳 Stripe Payment Configuration{Colors.END}")
        self.validate_required_var('STRIPE_SECRET_KEY', 'Stripe secret key', 
                                 lambda x: self.validate_stripe_key(x, 'secret'))
        self.validate_required_var('STRIPE_PUBLISHABLE_KEY', 'Stripe publishable key', 
                                 lambda x: self.validate_stripe_key(x, 'publishable'))
        self.validate_required_var('STRIPE_WEBHOOK_SECRET', 'Stripe webhook secret', 
                                 lambda x: self.validate_stripe_key(x, 'webhook'))
        self.validate_required_var('STRIPE_PRICE_ID_PRO', 'Stripe Pro price ID')
        self.validate_required_var('STRIPE_PRICE_ID_PREMIUM', 'Stripe Premium price ID')
        
        # Admin Configuration
        print(f"{Colors.BOLD}👤 Admin Configuration{Colors.END}")
        self.validate_required_var('ADMIN_USERNAME', 'Admin username')
        self.validate_required_var('ADMIN_EMAIL', 'Admin email', self.validate_email)
        self.validate_required_var('ADMIN_PASSWORD', 'Admin password', 
                                 lambda x: len(x) >= 12)
        
        # Optional but Recommended
        print(f"{Colors.BOLD}🔧 Optional Configuration{Colors.END}")
        self.validate_optional_var('REDIS_URL', 'Redis for caching and rate limiting', 
                                 self.validate_url)
        self.validate_optional_var('SENTRY_DSN', 'Sentry for error tracking', 
                                 self.validate_url)
        self.validate_optional_var('OPENAI_API_KEY', 'OpenAI for enhanced meal generation')
        self.validate_optional_var('SERVER_NAME', 'Production domain name')
        
        # Security Validation
        print(f"{Colors.BOLD}🔒 Security Validation{Colors.END}")
        debug = os.environ.get('DEBUG', 'false').lower()
        if debug == 'true':
            self.errors.append("DEBUG=True is not allowed in production!")
        else:
            self.passed.append("DEBUG: ✓ (False)")
        
        ssl_scheme = os.environ.get('PREFERRED_URL_SCHEME', 'https')
        if ssl_scheme != 'https':
            self.warnings.append("PREFERRED_URL_SCHEME should be 'https' in production")
        else:
            self.passed.append("PREFERRED_URL_SCHEME: ✓ (https)")
        
        # Print Results
        self.print_results()
        
        return len(self.errors) == 0
    
    def print_results(self):
        """Print validation results."""
        print(f"\n{Colors.BOLD}📊 Validation Results{Colors.END}")
        print("=" * 50)
        
        if self.passed:
            print(f"{Colors.GREEN}✅ Passed ({len(self.passed)}):{Colors.END}")
            for item in self.passed:
                print(f"   {item}")
        
        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠️  Warnings ({len(self.warnings)}):{Colors.END}")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.errors:
            print(f"\n{Colors.RED}❌ Errors ({len(self.errors)}):{Colors.END}")
            for error in self.errors:
                print(f"   {error}")
        
        print("=" * 50)
        
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}❌ VALIDATION FAILED{Colors.END}")
            print(f"Fix {len(self.errors)} error(s) before deploying to production.")
            return False
        elif self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  VALIDATION PASSED WITH WARNINGS{Colors.END}")
            print(f"Consider addressing {len(self.warnings)} warning(s) for optimal production setup.")
            return True
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ VALIDATION PASSED{Colors.END}")
            print("Environment is ready for production deployment!")
            return True

def main():
    """Main function."""
    print("Loading environment variables from .env file...")
    
    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.production', override=True)
        print("✅ Loaded .env.production")
    except ImportError:
        print("⚠️  python-dotenv not installed. Loading from system environment only.")
    except FileNotFoundError:
        print("⚠️  .env.production not found. Loading from system environment only.")
    
    validator = EnvironmentValidator()
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()