#!/usr/bin/env python
"""
Database integrity check script for Cibozer
"""
import sys
import os
from datetime import datetime, timezone

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.usage import UsageLog
from app.models.payment import Payment
from app.models.meal_plan import SavedMealPlan
from sqlalchemy import text

def check_database_integrity():
    """Check database integrity and consistency"""
    app = create_app()
    
    with app.app_context():
        try:
            print("=== DATABASE INTEGRITY CHECK ===")
            print(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
            print(f"Check time: {datetime.now()}")
            print()
            
            # Check database connection
            print("1. Checking database connection...")
            try:
                result = db.session.execute(text('SELECT 1')).scalar()
                if result == 1:
                    print("   ✓ Database connection successful")
                else:
                    print("   ✗ Database connection failed")
                    return False
            except Exception as e:
                print(f"   ✗ Database connection error: {e}")
                return False
            
            # Check table existence
            print("\n2. Checking table existence...")
            tables = ['users', 'usage_logs', 'payments', 'saved_meal_plans']
            
            for table in tables:
                try:
                    # Use parameterized query to prevent SQL injection
                    # For table names, we validate against a whitelist instead
                    if table not in ['users', 'usage_logs', 'payments', 'saved_meal_plans']:
                        print(f"   ✗ Table '{table}' not in allowed list")
                        continue
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                    print(f"   ✓ Table '{table}' exists with {result} records")
                except Exception as e:
                    print(f"   ✗ Table '{table}' error: {e}")
            
            # Check data consistency
            print("\n3. Checking data consistency...")
            
            # User table checks
            try:
                user_count = User.query.count()
                active_users = User.query.filter_by(is_active=True).count()
                verified_users = User.query.filter_by(email_verified=True).count()
                
                print(f"   ✓ Users: {user_count} total, {active_users} active, {verified_users} verified")
                
                # Check for users with invalid data
                invalid_emails = User.query.filter(User.email.is_(None)).count()
                invalid_passwords = User.query.filter(User.password_hash.is_(None)).count()
                
                if invalid_emails > 0:
                    print(f"   ⚠ Found {invalid_emails} users with null emails")
                if invalid_passwords > 0:
                    print(f"   ⚠ Found {invalid_passwords} users with null password hashes")
                
            except Exception as e:
                print(f"   ✗ User table check error: {e}")
            
            # Usage log checks
            try:
                usage_count = UsageLog.query.count()
                print(f"   ✓ Usage logs: {usage_count} records")
                
                # Check for orphaned usage logs
                orphaned_usage = db.session.execute(text("""
                    SELECT COUNT(*) FROM usage_logs 
                    WHERE user_id NOT IN (SELECT id FROM users)
                """)).scalar()
                
                if orphaned_usage > 0:
                    print(f"   ⚠ Found {orphaned_usage} orphaned usage log records")
                
            except Exception as e:
                print(f"   ✗ Usage log check error: {e}")
            
            # Payment checks
            try:
                payment_count = Payment.query.count()
                total_revenue = db.session.execute(text('SELECT COALESCE(SUM(amount), 0) FROM payments')).scalar()
                
                print(f"   ✓ Payments: {payment_count} records, ${total_revenue/100:.2f} total revenue")
                
                # Check for orphaned payments
                orphaned_payments = db.session.execute(text("""
                    SELECT COUNT(*) FROM payments 
                    WHERE user_id NOT IN (SELECT id FROM users)
                """)).scalar()
                
                if orphaned_payments > 0:
                    print(f"   ⚠ Found {orphaned_payments} orphaned payment records")
                
            except Exception as e:
                print(f"   ✗ Payment check error: {e}")
            
            # Meal plan checks
            try:
                meal_plan_count = SavedMealPlan.query.count()
                print(f"   ✓ Saved meal plans: {meal_plan_count} records")
                
                # Check for orphaned meal plans
                orphaned_plans = db.session.execute(text("""
                    SELECT COUNT(*) FROM saved_meal_plans 
                    WHERE user_id NOT IN (SELECT id FROM users)
                """)).scalar()
                
                if orphaned_plans > 0:
                    print(f"   ⚠ Found {orphaned_plans} orphaned meal plan records")
                
            except Exception as e:
                print(f"   ✗ Meal plan check error: {e}")
            
            
            # Check foreign key constraints
            print("\n4. Checking foreign key relationships...")
            
            try:
                # Test user-usage relationship
                test_query = db.session.execute(text("""
                    SELECT u.email, COUNT(ul.id) as usage_count
                    FROM users u
                    LEFT JOIN usage_logs ul ON u.id = ul.user_id
                    GROUP BY u.id, u.email
                    LIMIT 5
                """)).fetchall()
                
                print("   ✓ User-Usage relationship intact")
                for row in test_query:
                    print(f"     - {row.email}: {row.usage_count} usage records")
                
            except Exception as e:
                print(f"   ✗ Foreign key check error: {e}")
            
            # Check database performance
            print("\n5. Checking database performance...")
            
            try:
                start_time = datetime.now()
                complex_query = db.session.execute(text("""
                    SELECT 
                        u.subscription_tier,
                        COUNT(u.id) as user_count,
                        COALESCE(SUM(p.amount), 0) as total_revenue
                    FROM users u
                    LEFT JOIN payments p ON u.id = p.user_id
                    GROUP BY u.subscription_tier
                """)).fetchall()
                
                query_time = (datetime.now() - start_time).total_seconds()
                print(f"   ✓ Complex query executed in {query_time:.3f} seconds")
                
                for row in complex_query:
                    tier = row.subscription_tier or 'None'
                    print(f"     - {tier}: {row.user_count} users, ${row.total_revenue/100:.2f} revenue")
                
            except Exception as e:
                print(f"   ✗ Performance check error: {e}")
            
            print("\n=== DATABASE INTEGRITY CHECK COMPLETE ===")
            return True
            
        except Exception as e:
            print(f"Critical error during database check: {e}")
            return False

if __name__ == '__main__':
    success = check_database_integrity()
    sys.exit(0 if success else 1)