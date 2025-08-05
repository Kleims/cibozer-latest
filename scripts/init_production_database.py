#!/usr/bin/env python3
"""
Production Database Initialization Script

This script initializes a fresh PostgreSQL database for production use.
It creates the schema, sets up initial data, and performs basic validation.

Usage:
    python scripts/init_production_database.py [--reset] [--skip-admin]
    
Options:
    --reset        Drop existing tables and recreate (DANGEROUS!)
    --skip-admin   Skip admin user creation
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ProductionDatabaseInitializer:
    """Initializes production database."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.completed_tasks = []
    
    def log_success(self, message):
        """Log successful operation."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        self.completed_tasks.append(message)
    
    def log_error(self, message):
        """Log error."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.errors.append(message)
    
    def log_warning(self, message):
        """Log warning."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        self.warnings.append(message)
    
    def log_info(self, message):
        """Log information."""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    def validate_environment(self):
        """Validate production environment."""
        self.log_info("Validating production environment...")
        
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'ADMIN_USERNAME',
            'ADMIN_EMAIL',
            'ADMIN_PASSWORD'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        self.log_success("Environment variables validated")
        return True
    
    def test_database_connection(self):
        """Test PostgreSQL database connection."""
        self.log_info("Testing database connection...")
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            database_url = os.environ.get('DATABASE_URL')
            parsed = urlparse(database_url)
            
            if parsed.scheme not in ['postgresql', 'postgres']:
                self.log_error(f"Invalid database scheme: {parsed.scheme}")
                return False
            
            # Test connection
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic operations
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.log_success("Database connection successful")
            self.log_info(f"PostgreSQL version: {version}")
            
            # Check if we have necessary permissions
            cursor.execute("SELECT current_user, current_database();")
            user, db_name = cursor.fetchone()
            self.log_info(f"Connected as user '{user}' to database '{db_name}'")
            
            conn.close()
            return True
            
        except ImportError:
            self.log_error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            self.log_error(f"Database connection failed: {e}")
            return False
    
    def create_database_schema(self, reset=False):
        """Create database schema using Flask-SQLAlchemy."""
        self.log_info("Creating database schema...")
        
        try:
            # Set environment for production
            os.environ['FLASK_ENV'] = 'production'
            
            from app import create_app
            from app.models import db
            
            app = create_app('production')
            
            with app.app_context():
                if reset:
                    self.log_warning("Dropping all existing tables...")
                    db.drop_all()
                    self.log_success("Existing tables dropped")
                
                # Create all tables
                db.create_all()
                self.log_success("Database schema created")
                
                # Verify tables were created
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                
                expected_tables = ['users', 'saved_meal_plans', 'usage_logs', 'error_logs', 'payments']
                created_tables = [table for table in expected_tables if table in tables]
                
                self.log_success(f"Created {len(created_tables)} tables: {', '.join(created_tables)}")
                
                if len(created_tables) != len(expected_tables):
                    missing = set(expected_tables) - set(created_tables)
                    self.log_warning(f"Some tables may not have been created: {', '.join(missing)}")
                
                return True
                
        except Exception as e:
            self.log_error(f"Failed to create database schema: {e}")
            return False
    
    def create_admin_user(self):
        """Create initial admin user."""
        self.log_info("Creating admin user...")
        
        try:
            from app import create_app
            from app.models import db, User
            
            app = create_app('production')
            
            with app.app_context():
                # Check if admin user already exists
                admin_email = os.environ.get('ADMIN_EMAIL')
                existing_admin = User.query.filter_by(email=admin_email).first()
                
                if existing_admin:
                    self.log_warning(f"Admin user already exists: {admin_email}")
                    return True
                
                # Create admin user
                admin_user = User(
                    email=admin_email,
                    full_name=os.environ.get('ADMIN_USERNAME', 'Administrator'),
                    subscription_tier='premium',
                    subscription_status='active',
                    credits_balance=1000,
                    is_active=True,
                    email_verified=True,
                    created_at=datetime.now(timezone.utc)
                )
                
                # Set password
                admin_password = os.environ.get('ADMIN_PASSWORD')
                admin_user.set_password(admin_password)
                
                db.session.add(admin_user)
                db.session.commit()
                
                self.log_success(f"Admin user created: {admin_email}")
                self.log_info("Admin user has premium subscription with 1000 credits")
                
                return True
                
        except Exception as e:
            self.log_error(f"Failed to create admin user: {e}")
            return False
    
    def create_database_indexes(self):
        """Create performance indexes."""
        self.log_info("Creating database indexes...")
        
        try:
            from app import create_app
            from app.models import db
            
            app = create_app('production')
            
            with app.app_context():
                # Execute custom indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
                    "CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_tier, subscription_status);",
                    "CREATE INDEX IF NOT EXISTS idx_saved_meal_plans_user_created ON saved_meal_plans(user_id, created_at DESC);",
                    "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_action ON usage_logs(user_id, action);",
                    "CREATE INDEX IF NOT EXISTS idx_usage_logs_created ON usage_logs(created_at DESC);",
                    "CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity, resolved);",
                    "CREATE INDEX IF NOT EXISTS idx_error_logs_created ON error_logs(created_at DESC);",
                    "CREATE INDEX IF NOT EXISTS idx_payments_user_status ON payments(user_id, status);"
                ]
                
                for index_sql in indexes:
                    try:
                        db.session.execute(index_sql)
                        table_name = index_sql.split(' ON ')[1].split('(')[0]
                        self.log_success(f"Created index on {table_name}")
                    except Exception as e:
                        self.log_warning(f"Index creation failed: {e}")
                
                db.session.commit()
                self.log_success("Database indexes created")
                return True
                
        except Exception as e:
            self.log_error(f"Failed to create indexes: {e}")
            return False
    
    def validate_database_setup(self):
        """Validate the database setup."""
        self.log_info("Validating database setup...")
        
        try:
            from app import create_app
            from app.models import db, User, SavedMealPlan, UsageLog, ErrorLog
            
            app = create_app('production')
            
            with app.app_context():
                # Test basic queries
                user_count = User.query.count()
                self.log_success(f"Users table: {user_count} records")
                
                # Test admin user
                admin_email = os.environ.get('ADMIN_EMAIL')
                admin_user = User.query.filter_by(email=admin_email).first()
                
                if admin_user:
                    self.log_success("Admin user accessible")
                    if admin_user.check_password(os.environ.get('ADMIN_PASSWORD')):
                        self.log_success("Admin password correct")
                    else:
                        self.log_error("Admin password incorrect")
                        return False
                else:
                    self.log_error("Admin user not found")
                    return False
                
                # Test table operations
                test_tables = [
                    (SavedMealPlan, 'saved_meal_plans'),
                    (UsageLog, 'usage_logs'),
                    (ErrorLog, 'error_logs')
                ]
                
                for model, table_name in test_tables:
                    try:
                        count = model.query.count()
                        self.log_success(f"Table {table_name}: accessible ({count} records)")
                    except Exception as e:
                        self.log_warning(f"Table {table_name}: {e}")
                
                return True
                
        except Exception as e:
            self.log_error(f"Database validation failed: {e}")
            return False
    
    def run_initialization(self, reset=False, skip_admin=False):
        """Run the complete initialization process."""
        print(f"{Colors.BOLD}{Colors.BLUE}🗄️  Production Database Initialization{Colors.END}\n")
        
        steps = [
            ("Validate Environment", lambda: self.validate_environment()),
            ("Test Database Connection", lambda: self.test_database_connection()),
            ("Create Database Schema", lambda: self.create_database_schema(reset)),
            ("Create Database Indexes", lambda: self.create_database_indexes()),
        ]
        
        if not skip_admin:
            steps.append(("Create Admin User", lambda: self.create_admin_user()))
        
        steps.append(("Validate Database Setup", lambda: self.validate_database_setup()))
        
        for step_name, step_function in steps:
            print(f"\n{Colors.BOLD}📋 {step_name}{Colors.END}")
            try:
                success = step_function()
                if not success:
                    self.log_error(f"Critical step failed: {step_name}")
                    break
            except Exception as e:
                self.log_error(f"Exception in {step_name}: {str(e)}")
                break
        
        # Print summary
        print(f"\n{Colors.BOLD}📊 Initialization Summary{Colors.END}")
        print("=" * 50)
        print(f"{Colors.GREEN}Completed: {len(self.completed_tasks)}{Colors.END}")
        if self.warnings:
            print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        if self.errors:
            print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ INITIALIZATION FAILED{Colors.END}")
            print("Fix the above errors before proceeding.")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ INITIALIZATION SUCCESSFUL{Colors.END}")
            print("Production database is ready!")
            
            if not skip_admin:
                admin_email = os.environ.get('ADMIN_EMAIL')
                print(f"\n{Colors.BLUE}👤 Admin Access:{Colors.END}")
                print(f"   Email: {admin_email}")
                print(f"   Password: [from ADMIN_PASSWORD env var]")
                print(f"   Access: /admin")
            
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Initialize production database')
    parser.add_argument('--reset', action='store_true',
                       help='Drop existing tables and recreate (DANGEROUS!)')
    parser.add_argument('--skip-admin', action='store_true',
                       help='Skip admin user creation')
    
    args = parser.parse_args()
    
    if args.reset:
        print(f"{Colors.RED}{Colors.BOLD}⚠️  WARNING: This will delete all existing data!{Colors.END}")
        response = input("Are you sure you want to reset the database? (type 'yes'): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            sys.exit(0)
    
    initializer = ProductionDatabaseInitializer()
    success = initializer.run_initialization(
        reset=args.reset,
        skip_admin=args.skip_admin
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()