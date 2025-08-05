#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script

This script safely migrates data from SQLite development database to PostgreSQL production database.
It handles data export, schema creation, and data import with validation.

Usage:
    python scripts/migrate_to_postgresql.py [--backup-only] [--validate-only]
    
Options:
    --backup-only    Only create backup, don't migrate
    --validate-only  Only validate the migration, don't make changes
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess

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

class DatabaseMigrator:
    """Handles SQLite to PostgreSQL migration."""
    
    def __init__(self):
        self.project_root = project_root
        self.backup_dir = self.project_root / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Database paths
        self.sqlite_path = self.project_root / 'instance' / 'dev_cibozer.db'
        if not self.sqlite_path.exists():
            self.sqlite_path = self.project_root / 'instance' / 'cibozer.db'
        
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
    
    def validate_sqlite_database(self):
        """Validate the source SQLite database."""
        self.log_info("Validating SQLite database...")
        
        if not self.sqlite_path.exists():
            self.log_error(f"SQLite database not found: {self.sqlite_path}")
            return False
        
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            # Get table list
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                self.log_warning("SQLite database appears to be empty")
                return True
            
            self.log_success(f"Found {len(tables)} tables in SQLite database")
            
            # Validate critical tables exist
            table_names = [table[0] for table in tables]
            expected_tables = ['users', 'saved_meal_plans', 'usage_logs', 'error_logs']
            
            for expected_table in expected_tables:
                if expected_table in table_names:
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {expected_table}")
                    count = cursor.fetchone()[0]
                    self.log_success(f"Table '{expected_table}': {count} records")
                else:
                    self.log_warning(f"Expected table '{expected_table}' not found")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_error(f"Failed to validate SQLite database: {e}")
            return False
    
    def create_database_backup(self):
        """Create backup of SQLite database."""
        self.log_info("Creating database backup...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"cibozer_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy SQLite database
            import shutil
            shutil.copy2(self.sqlite_path, backup_path)
            self.log_success(f"Database backup created: {backup_filename}")
            
            # Also create JSON export for additional safety
            json_backup_path = self.backup_dir / f"cibozer_data_{timestamp}.json"
            self.export_data_to_json(json_backup_path)
            
            return backup_path
            
        except Exception as e:
            self.log_error(f"Failed to create backup: {e}")
            return None
    
    def export_data_to_json(self, json_path):
        """Export all data to JSON format."""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            export_data = {
                'export_timestamp': datetime.now(timezone.utc).isoformat(),
                'source_database': str(self.sqlite_path),
                'tables': {}
            }
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries
                export_data['tables'][table] = [dict(row) for row in rows]
                self.log_success(f"Exported {len(rows)} records from table '{table}'")
            
            conn.close()
            
            # Write JSON file
            with open(json_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self.log_success(f"JSON backup created: {json_path.name}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create JSON export: {e}")
            return False
    
    def validate_postgresql_connection(self):
        """Validate PostgreSQL connection and setup."""
        self.log_info("Validating PostgreSQL connection...")
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            self.log_error("DATABASE_URL environment variable not set")
            return False
        
        try:
            import psycopg2
            from urllib.parse import urlparse
            
            # Parse database URL
            parsed = urlparse(database_url)
            
            if parsed.scheme not in ['postgresql', 'postgres']:
                self.log_error(f"Invalid database scheme: {parsed.scheme}")
                return False
            
            # Test connection
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.log_success(f"PostgreSQL connection successful")
            self.log_info(f"PostgreSQL version: {version}")
            
            conn.close()
            return True
            
        except ImportError:
            self.log_error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            return False
        except Exception as e:
            self.log_error(f"PostgreSQL connection failed: {e}")
            return False
    
    def create_postgresql_schema(self):
        """Create PostgreSQL schema using Flask-Migrate."""
        self.log_info("Creating PostgreSQL schema...")
        
        try:
            # Set environment to use PostgreSQL
            env = os.environ.copy()
            env['FLASK_ENV'] = 'production'
            
            # Initialize migrations if needed
            migrations_dir = self.project_root / 'migrations'
            if not migrations_dir.exists():
                result = subprocess.run([
                    sys.executable, '-m', 'flask', 'db', 'init'
                ], cwd=self.project_root, env=env, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log_error(f"Failed to initialize migrations: {result.stderr}")
                    return False
                
                self.log_success("Initialized database migrations")
            
            # Create migration
            result = subprocess.run([
                sys.executable, '-m', 'flask', 'db', 'migrate', 
                '-m', 'Initial production migration'
            ], cwd=self.project_root, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_warning(f"Migration creation warning: {result.stderr}")
            else:
                self.log_success("Created database migration")
            
            # Apply migration
            result = subprocess.run([
                sys.executable, '-m', 'flask', 'db', 'upgrade'
            ], cwd=self.project_root, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log_error(f"Failed to apply migrations: {result.stderr}")
                return False
            
            self.log_success("Applied database migrations to PostgreSQL")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create PostgreSQL schema: {e}")
            return False
    
    def migrate_data(self):
        """Migrate data from SQLite to PostgreSQL."""
        self.log_info("Migrating data from SQLite to PostgreSQL...")
        
        try:
            # Load Flask app to get models
            os.environ['FLASK_ENV'] = 'production'
            from app import create_app
            from app.models import db, User, SavedMealPlan, UsageLog, ErrorLog, Payment
            
            app = create_app('production')
            
            with app.app_context():
                # Connect to SQLite
                sqlite_conn = sqlite3.connect(str(self.sqlite_path))
                sqlite_conn.row_factory = sqlite3.Row
                sqlite_cursor = sqlite_conn.cursor()
                
                # Migration order (respecting foreign key dependencies)
                migration_tasks = [
                    ('users', User, self.migrate_users),
                    ('saved_meal_plans', SavedMealPlan, self.migrate_saved_meal_plans),
                    ('usage_logs', UsageLog, self.migrate_usage_logs),
                    ('error_logs', ErrorLog, self.migrate_error_logs),
                    ('payments', Payment, self.migrate_payments)
                ]
                
                for table_name, model_class, migration_func in migration_tasks:
                    try:
                        # Check if table exists in SQLite
                        sqlite_cursor.execute(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                            (table_name,)
                        )
                        
                        if sqlite_cursor.fetchone():
                            count = migration_func(sqlite_cursor, model_class, db)
                            if count is not None:
                                self.log_success(f"Migrated {count} records from {table_name}")
                            else:
                                self.log_warning(f"Migration of {table_name} had issues")
                        else:
                            self.log_info(f"Table {table_name} not found in SQLite, skipping")
                            
                    except Exception as e:
                        self.log_error(f"Failed to migrate {table_name}: {e}")
                
                sqlite_conn.close()
                
            self.log_success("Data migration completed")
            return True
            
        except Exception as e:
            self.log_error(f"Data migration failed: {e}")
            return False
    
    def migrate_users(self, sqlite_cursor, User, db):
        """Migrate users table."""
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        migrated_count = 0
        for user_row in users:
            try:
                user = User(
                    email=user_row['email'],
                    full_name=user_row['full_name'],
                    password_hash=user_row['password_hash'],
                    is_active=user_row['is_active'],
                    email_verified=user_row.get('email_verified', False),
                    subscription_tier=user_row.get('subscription_tier', 'free'),
                    subscription_status=user_row.get('subscription_status', 'active'),
                    credits_balance=user_row.get('credits_balance', 3),
                    created_at=datetime.fromisoformat(user_row['created_at']) if user_row.get('created_at') else datetime.now(timezone.utc),
                    last_login=datetime.fromisoformat(user_row['last_login']) if user_row.get('last_login') else None
                )
                
                db.session.add(user)
                migrated_count += 1
                
            except Exception as e:
                self.log_warning(f"Failed to migrate user {user_row.get('email', 'unknown')}: {e}")
        
        try:
            db.session.commit()
            return migrated_count
        except Exception as e:
            db.session.rollback()
            self.log_error(f"Failed to commit users: {e}")
            return None
    
    def migrate_saved_meal_plans(self, sqlite_cursor, SavedMealPlan, db):
        """Migrate saved meal plans."""
        sqlite_cursor.execute("SELECT * FROM saved_meal_plans")
        plans = sqlite_cursor.fetchall()
        
        migrated_count = 0
        for plan_row in plans:
            try:
                # Parse JSON meal plan data
                meal_plan_data = json.loads(plan_row['meal_plan_data']) if plan_row.get('meal_plan_data') else {}
                
                plan = SavedMealPlan(
                    user_id=plan_row['user_id'],
                    name=plan_row['name'],
                    meal_plan_data=meal_plan_data,
                    total_calories=plan_row.get('total_calories'),
                    diet_type=plan_row.get('diet_type'),
                    days=plan_row.get('days', 1),
                    created_at=datetime.fromisoformat(plan_row['created_at']) if plan_row.get('created_at') else datetime.now(timezone.utc)
                )
                
                db.session.add(plan)
                migrated_count += 1
                
            except Exception as e:
                self.log_warning(f"Failed to migrate meal plan {plan_row.get('id', 'unknown')}: {e}")
        
        try:
            db.session.commit()
            return migrated_count
        except Exception as e:
            db.session.rollback()
            self.log_error(f"Failed to commit meal plans: {e}")
            return None
    
    def migrate_usage_logs(self, sqlite_cursor, UsageLog, db):
        """Migrate usage logs."""
        sqlite_cursor.execute("SELECT * FROM usage_logs")
        logs = sqlite_cursor.fetchall()
        
        migrated_count = 0
        for log_row in logs:
            try:
                # Parse JSON metadata
                metadata = json.loads(log_row['metadata']) if log_row.get('metadata') else {}
                
                log = UsageLog(
                    user_id=log_row.get('user_id'),
                    action=log_row['action'],
                    resource_type=log_row.get('resource_type'),
                    resource_id=log_row.get('resource_id'),
                    metadata=metadata,
                    ip_address=log_row.get('ip_address'),
                    user_agent=log_row.get('user_agent'),
                    endpoint=log_row.get('endpoint'),
                    method=log_row.get('method'),
                    created_at=datetime.fromisoformat(log_row['created_at']) if log_row.get('created_at') else datetime.now(timezone.utc)
                )
                
                db.session.add(log)
                migrated_count += 1
                
            except Exception as e:
                self.log_warning(f"Failed to migrate usage log {log_row.get('id', 'unknown')}: {e}")
        
        try:
            db.session.commit()
            return migrated_count
        except Exception as e:
            db.session.rollback()
            self.log_error(f"Failed to commit usage logs: {e}")
            return None
    
    def migrate_error_logs(self, sqlite_cursor, ErrorLog, db):
        """Migrate error logs."""
        try:
            sqlite_cursor.execute("SELECT * FROM error_logs")
            logs = sqlite_cursor.fetchall()
        except:
            # Table might not exist in older schemas
            return 0
        
        migrated_count = 0
        for log_row in logs:
            try:
                log = ErrorLog(
                    error_id=log_row['error_id'],
                    error_type=log_row['error_type'],
                    error_message=log_row['error_message'],
                    traceback=log_row.get('traceback'),
                    severity=log_row['severity'],
                    context=log_row.get('context'),
                    request_info=log_row.get('request_info'),
                    user_id=log_row.get('user_id'),
                    resolved=log_row.get('resolved', False),
                    counter=log_row.get('counter', 1),
                    created_at=datetime.fromisoformat(log_row['created_at']) if log_row.get('created_at') else datetime.now(timezone.utc)
                )
                
                db.session.add(log)
                migrated_count += 1
                
            except Exception as e:
                self.log_warning(f"Failed to migrate error log {log_row.get('error_id', 'unknown')}: {e}")
        
        try:
            db.session.commit()
            return migrated_count
        except Exception as e:
            db.session.rollback()
            self.log_error(f"Failed to commit error logs: {e}")
            return None
    
    def migrate_payments(self, sqlite_cursor, Payment, db):
        """Migrate payments."""
        try:
            sqlite_cursor.execute("SELECT * FROM payments")
            payments = sqlite_cursor.fetchall()
        except:
            # Table might not exist
            return 0
        
        migrated_count = 0
        for payment_row in payments:
            try:
                payment = Payment(
                    user_id=payment_row['user_id'],
                    stripe_payment_intent_id=payment_row.get('stripe_payment_intent_id'),
                    amount=payment_row['amount'],
                    currency=payment_row.get('currency', 'usd'),
                    status=payment_row['status'],
                    description=payment_row.get('description'),
                    created_at=datetime.fromisoformat(payment_row['created_at']) if payment_row.get('created_at') else datetime.now(timezone.utc)
                )
                
                db.session.add(payment)
                migrated_count += 1
                
            except Exception as e:
                self.log_warning(f"Failed to migrate payment {payment_row.get('id', 'unknown')}: {e}")
        
        try:
            db.session.commit()
            return migrated_count
        except Exception as e:
            db.session.rollback()
            self.log_error(f"Failed to commit payments: {e}")
            return None
    
    def validate_migration(self):
        """Validate the migration was successful."""
        self.log_info("Validating migration...")
        
        try:
            os.environ['FLASK_ENV'] = 'production'
            from app import create_app
            from app.models import db, User, SavedMealPlan, UsageLog
            
            app = create_app('production')
            
            with app.app_context():
                # Count records in PostgreSQL
                user_count = User.query.count()
                plan_count = SavedMealPlan.query.count()
                log_count = UsageLog.query.count()
                
                self.log_success(f"PostgreSQL contains:")
                self.log_success(f"  Users: {user_count}")
                self.log_success(f"  Meal Plans: {plan_count}")
                self.log_success(f"  Usage Logs: {log_count}")
                
                # Basic data integrity checks
                if user_count > 0:
                    sample_user = User.query.first()
                    if sample_user.email and '@' in sample_user.email:
                        self.log_success("User data integrity: ✓")
                    else:
                        self.log_warning("User data integrity issues detected")
                
                return True
                
        except Exception as e:
            self.log_error(f"Migration validation failed: {e}")
            return False
    
    def run_migration(self, backup_only=False, validate_only=False):
        """Run the complete migration process."""
        print(f"{Colors.BOLD}{Colors.BLUE}🔄 SQLite to PostgreSQL Migration{Colors.END}\n")
        
        # Step 1: Validate source database
        if not self.validate_sqlite_database():
            return False
        
        # Step 2: Create backup
        backup_path = self.create_database_backup()
        if not backup_path:
            return False
        
        if backup_only:
            self.log_success("Backup completed successfully")
            return True
        
        # Step 3: Validate PostgreSQL connection
        if not self.validate_postgresql_connection():
            return False
        
        if validate_only:
            self.log_success("Validation completed successfully")
            return True
        
        # Step 4: Create PostgreSQL schema
        if not self.create_postgresql_schema():
            return False
        
        # Step 5: Migrate data
        if not self.migrate_data():
            return False
        
        # Step 6: Validate migration
        if not self.validate_migration():
            return False
        
        # Print summary
        print(f"\n{Colors.BOLD}📊 Migration Summary{Colors.END}")
        print("=" * 50)
        print(f"{Colors.GREEN}Completed: {len(self.completed_tasks)}{Colors.END}")
        if self.warnings:
            print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        if self.errors:
            print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ MIGRATION HAD ERRORS{Colors.END}")
            print("Review the errors above. Your backup is safe.")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ MIGRATION SUCCESSFUL{Colors.END}")
            print(f"Backup created: {backup_path.name}")
            print("Your data has been successfully migrated to PostgreSQL!")
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Migrate SQLite database to PostgreSQL')
    parser.add_argument('--backup-only', action='store_true', 
                       help='Only create backup, don\'t migrate')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate connections, don\'t migrate')
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    success = migrator.run_migration(
        backup_only=args.backup_only,
        validate_only=args.validate_only
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()