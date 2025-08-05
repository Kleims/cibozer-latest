"""Database validation and integrity checking utilities."""
import logging
from datetime import datetime, timezone
from flask import current_app
from sqlalchemy import text, inspect, MetaData
from sqlalchemy.exc import IntegrityError, DataError
from app.extensions import db
from app.models import User, SavedMealPlan, UsageLog, APIKey, SharedMealPlan


class DatabaseValidator:
    """Comprehensive database validation and integrity checker."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.recommendations = []
        
    def run_full_validation(self):
        """Run comprehensive database validation."""
        self.errors = []
        self.warnings = []
        self.recommendations = []
        
        current_app.logger.info("Starting comprehensive database validation...")
        
        # Run all validation checks
        self.validate_schema_integrity()
        self.validate_foreign_key_constraints()
        self.validate_data_consistency()
        self.validate_indexes()
        self.validate_user_data()
        self.validate_meal_plan_data()
        self.validate_usage_log_data()
        self.check_orphaned_records()
        self.analyze_data_quality()
        
        # Generate report
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'PASS' if not self.errors else 'FAIL',
            'errors': self.errors,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
            'total_issues': len(self.errors) + len(self.warnings)
        }
        
        current_app.logger.info(f"Database validation completed. Status: {report['status']}")
        return report
    
    def validate_schema_integrity(self):
        """Validate database schema integrity."""
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'saved_meal_plans', 'usage_logs', 
                'api_keys', 'shared_meal_plans', 'meal_plan_shares'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                self.errors.append(f"Missing required tables: {', '.join(missing_tables)}")
            
            # Check for required columns in each table
            for table_name in tables:
                if table_name in required_tables:
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    
                    if table_name == 'users':
                        required_cols = ['id', 'email', 'password_hash', 'created_at']
                        missing_cols = [col for col in required_cols if col not in columns]
                        if missing_cols:
                            self.errors.append(f"Table '{table_name}' missing columns: {', '.join(missing_cols)}")
                    
                    elif table_name == 'saved_meal_plans':
                        required_cols = ['id', 'user_id', 'name', 'meal_plan_data', 'created_at']
                        missing_cols = [col for col in required_cols if col not in columns]
                        if missing_cols:
                            self.errors.append(f"Table '{table_name}' missing columns: {', '.join(missing_cols)}")
            
        except Exception as e:
            self.errors.append(f"Schema integrity check failed: {str(e)}")
    
    def validate_foreign_key_constraints(self):
        """Validate foreign key relationships."""
        try:
            # Check user_id references in dependent tables
            
            # SavedMealPlan -> User
            orphaned_meal_plans = db.session.execute(text("""
                SELECT COUNT(*) FROM saved_meal_plans 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)).scalar()
            
            if orphaned_meal_plans > 0:
                self.errors.append(f"Found {orphaned_meal_plans} meal plans with invalid user_id references")
            
            # UsageLog -> User
            orphaned_usage_logs = db.session.execute(text("""
                SELECT COUNT(*) FROM usage_logs 
                WHERE user_id NOT IN (SELECT id FROM users)
            """)).scalar()
            
            if orphaned_usage_logs > 0:
                self.errors.append(f"Found {orphaned_usage_logs} usage logs with invalid user_id references")
            
            # APIKey -> User
            try:
                orphaned_api_keys = db.session.execute(text("""
                    SELECT COUNT(*) FROM api_keys 
                    WHERE user_id NOT IN (SELECT id FROM users)
                """)).scalar()
                
                if orphaned_api_keys > 0:
                    self.errors.append(f"Found {orphaned_api_keys} API keys with invalid user_id references")
            except:
                # API keys table might not exist
                pass
            
        except Exception as e:
            self.errors.append(f"Foreign key validation failed: {str(e)}")
    
    def validate_data_consistency(self):
        """Validate data consistency across tables."""
        try:
            # Check for users with negative credits
            users_negative_credits = User.query.filter(User.credits_balance < 0).count()
            if users_negative_credits > 0:
                self.warnings.append(f"Found {users_negative_credits} users with negative credit balance")
            
            # Check for meal plans with invalid days
            meal_plans_invalid_days = SavedMealPlan.query.filter(
                db.or_(SavedMealPlan.days < 1, SavedMealPlan.days > 30)
            ).count()
            if meal_plans_invalid_days > 0:
                self.errors.append(f"Found {meal_plans_invalid_days} meal plans with invalid days count")
            
            # Check for usage logs with invalid credits
            usage_logs_invalid_credits = UsageLog.query.filter(UsageLog.credits_used < 0).count()
            if usage_logs_invalid_credits > 0:
                self.errors.append(f"Found {usage_logs_invalid_credits} usage logs with negative credits used")
            
            # Check for users with inconsistent subscription data
            users_inconsistent_sub = User.query.filter(
                db.and_(
                    User.subscription_tier.in_(['pro', 'premium']),
                    User.subscription_status == 'expired'
                )
            ).count()
            if users_inconsistent_sub > 0:
                self.warnings.append(f"Found {users_inconsistent_sub} users with premium tier but expired status")
            
        except Exception as e:
            self.errors.append(f"Data consistency validation failed: {str(e)}")
    
    def validate_indexes(self):
        """Validate that required indexes exist."""
        try:
            inspector = inspect(db.engine)
            
            # Check for indexes on frequently queried columns
            required_indexes = {
                'users': ['email', 'created_at', 'subscription_tier'],
                'saved_meal_plans': ['user_id', 'created_at'],
                'usage_logs': ['user_id', 'created_at', 'action'],
                'api_keys': ['key', 'user_id']
            }
            
            for table_name, required_cols in required_indexes.items():
                try:
                    indexes = inspector.get_indexes(table_name)
                    indexed_columns = set()
                    
                    for index in indexes:
                        indexed_columns.update(index['column_names'])
                    
                    missing_indexes = [col for col in required_cols if col not in indexed_columns]
                    if missing_indexes:
                        self.recommendations.append(
                            f"Table '{table_name}' missing indexes on: {', '.join(missing_indexes)}"
                        )
                        
                except Exception:
                    # Table might not exist
                    pass
            
        except Exception as e:
            self.warnings.append(f"Index validation failed: {str(e)}")
    
    def validate_user_data(self):
        """Validate user-specific data integrity."""
        try:
            # Check for duplicate emails
            duplicate_emails = db.session.execute(text("""
                SELECT email, COUNT(*) as count 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_emails:
                self.errors.append(f"Found {len(duplicate_emails)} duplicate email addresses")
            
            # Check for users without password hashes
            users_no_password = User.query.filter(
                db.or_(User.password_hash.is_(None), User.password_hash == '')
            ).count()
            if users_no_password > 0:
                self.errors.append(f"Found {users_no_password} users without password hashes")
            
            # Check for users with invalid email formats
            users_invalid_email = User.query.filter(
                ~User.email.contains('@')
            ).count()
            if users_invalid_email > 0:
                self.errors.append(f"Found {users_invalid_email} users with invalid email format")
            
            # Check for locked users that should be unlocked
            now = datetime.now(timezone.utc)
            users_should_unlock = User.query.filter(
                db.and_(
                    User.locked_until.isnot(None),
                    User.locked_until < now
                )
            ).count()
            if users_should_unlock > 0:
                self.recommendations.append(f"Found {users_should_unlock} users that should be unlocked")
            
        except Exception as e:
            self.errors.append(f"User data validation failed: {str(e)}")
    
    def validate_meal_plan_data(self):
        """Validate meal plan data integrity."""
        try:
            # Check for meal plans with empty/null JSON data
            meal_plans_invalid_json = SavedMealPlan.query.filter(
                db.or_(
                    SavedMealPlan.meal_plan_data.is_(None),
                    SavedMealPlan.meal_plan_data == {}
                )
            ).count()
            if meal_plans_invalid_json > 0:
                self.errors.append(f"Found {meal_plans_invalid_json} meal plans with invalid JSON data")
            
            # Check for meal plans with invalid calorie ranges
            meal_plans_invalid_calories = SavedMealPlan.query.filter(
                db.and_(
                    SavedMealPlan.total_calories.isnot(None),
                    db.or_(
                        SavedMealPlan.total_calories < 500,
                        SavedMealPlan.total_calories > 5000
                    )
                )
            ).count()
            if meal_plans_invalid_calories > 0:
                self.warnings.append(f"Found {meal_plans_invalid_calories} meal plans with unusual calorie counts")
            
            # Check for meal plans with empty names
            meal_plans_empty_names = SavedMealPlan.query.filter(
                db.or_(
                    SavedMealPlan.name.is_(None),
                    SavedMealPlan.name == ''
                )
            ).count()
            if meal_plans_empty_names > 0:
                self.warnings.append(f"Found {meal_plans_empty_names} meal plans with empty names")
            
        except Exception as e:
            self.errors.append(f"Meal plan data validation failed: {str(e)}")
    
    def validate_usage_log_data(self):
        """Validate usage log data integrity."""
        try:
            # Check for usage logs with invalid response times
            invalid_response_times = UsageLog.query.filter(
                db.and_(
                    UsageLog.response_time_ms.isnot(None),
                    db.or_(
                        UsageLog.response_time_ms < 0,
                        UsageLog.response_time_ms > 300000  # 5 minutes
                    )
                )
            ).count()
            if invalid_response_times > 0:
                self.warnings.append(f"Found {invalid_response_times} usage logs with unusual response times")
            
            # Check for usage logs with invalid status codes
            invalid_status_codes = UsageLog.query.filter(
                db.and_(
                    UsageLog.status_code.isnot(None),
                    db.or_(
                        UsageLog.status_code < 100,
                        UsageLog.status_code > 599
                    )
                )
            ).count()
            if invalid_status_codes > 0:
                self.warnings.append(f"Found {invalid_status_codes} usage logs with invalid status codes")
            
        except Exception as e:
            self.errors.append(f"Usage log data validation failed: {str(e)}")
    
    def check_orphaned_records(self):
        """Check for orphaned records that should be cleaned up."""
        try:
            # Check for old usage logs (older than 1 year)
            one_year_ago = datetime.now(timezone.utc).replace(year=datetime.now().year - 1)
            old_usage_logs = UsageLog.query.filter(UsageLog.created_at < one_year_ago).count()
            if old_usage_logs > 0:
                self.recommendations.append(f"Found {old_usage_logs} usage logs older than 1 year (consider archiving)")
            
            # Check for inactive API keys
            try:
                inactive_api_keys = APIKey.query.filter(APIKey.is_active == False).count()
                if inactive_api_keys > 0:
                    self.recommendations.append(f"Found {inactive_api_keys} inactive API keys (consider cleanup)")
            except:
                pass
            
            # Check for expired shares
            expired_shares = SharedMealPlan.query.filter(
                db.and_(
                    SharedMealPlan.expires_at.isnot(None),
                    SharedMealPlan.expires_at < datetime.now(timezone.utc)
                )
            ).count()
            if expired_shares > 0:
                self.recommendations.append(f"Found {expired_shares} expired shared meal plans (consider cleanup)")
            
        except Exception as e:
            self.warnings.append(f"Orphaned records check failed: {str(e)}")
    
    def analyze_data_quality(self):
        """Analyze overall data quality and patterns."""
        try:
            # Check user distribution
            total_users = User.query.count()
            if total_users > 0:
                premium_users = User.query.filter(User.subscription_tier.in_(['pro', 'premium'])).count()
                premium_percentage = (premium_users / total_users) * 100
                
                if premium_percentage < 5:
                    self.recommendations.append(f"Low premium user percentage ({premium_percentage:.1f}%)")
                
                # Check user activity
                active_users = User.query.filter(User.last_login.isnot(None)).count()
                activity_percentage = (active_users / total_users) * 100
                
                if activity_percentage < 50:
                    self.recommendations.append(f"Low user activity rate ({activity_percentage:.1f}%)")
            
            # Check meal plan usage patterns
            total_meal_plans = SavedMealPlan.query.count()
            if total_meal_plans > 0 and total_users > 0:
                avg_plans_per_user = total_meal_plans / total_users
                
                if avg_plans_per_user < 1:
                    self.recommendations.append(f"Low meal plan creation rate ({avg_plans_per_user:.1f} per user)")
            
        except Exception as e:
            self.warnings.append(f"Data quality analysis failed: {str(e)}")
    
    def fix_data_inconsistencies(self):
        """Attempt to fix common data inconsistencies."""
        fixes_applied = []
        
        try:
            # Fix users with negative credits
            negative_credit_users = User.query.filter(User.credits_balance < 0).all()
            for user in negative_credit_users:
                user.credits_balance = 0
                fixes_applied.append(f"Reset negative credits for user {user.email}")
            
            # Unlock users whose lock time has expired
            now = datetime.now(timezone.utc)
            locked_users = User.query.filter(
                db.and_(
                    User.locked_until.isnot(None),
                    User.locked_until < now
                )
            ).all()
            
            for user in locked_users:
                user.locked_until = None
                user.failed_login_attempts = 0
                fixes_applied.append(f"Unlocked user {user.email}")
            
            # Commit fixes
            if fixes_applied:
                db.session.commit()
                current_app.logger.info(f"Applied {len(fixes_applied)} data fixes")
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to apply data fixes: {str(e)}")
            fixes_applied.append(f"Error applying fixes: {str(e)}")
        
        return fixes_applied


def run_database_validation():
    """Run comprehensive database validation."""
    validator = DatabaseValidator()
    return validator.run_full_validation()


def fix_database_issues():
    """Fix common database issues."""
    validator = DatabaseValidator()
    return validator.fix_data_inconsistencies()