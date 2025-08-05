#!/usr/bin/env python3
"""
Database Optimization and Integrity Checks for Cibozer
Adds indexes, constraints, and optimizes queries
"""

import sqlite3
import os
from datetime import datetime

class DatabaseOptimizer:
    def __init__(self, db_path='instance/cibozer.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.optimizations = []
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
    
    def log_optimization(self, action, details):
        """Log optimization action"""
        self.optimizations.append({
            'action': action,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✓ {action}: {details}")
    
    def add_indexes(self):
        """Add database indexes for performance"""
        indexes = [
            # User indexes
            ('idx_users_email', 'users', 'email'),
            ('idx_users_email_active', 'users', 'email, is_active'),
            ('idx_users_stripe_customer', 'users', 'stripe_customer_id'),
            ('idx_users_subscription', 'users', 'subscription_status, subscription_tier'),
            
            # Usage log indexes
            ('idx_usage_logs_user_action', 'usage_logs', 'user_id, action, created_at'),
            ('idx_usage_logs_created', 'usage_logs', 'created_at'),
            
            # Payment indexes
            ('idx_payments_user', 'payments', 'user_id'),
            ('idx_payments_status', 'payments', 'status'),
            ('idx_payments_stripe', 'payments', 'stripe_payment_intent_id'),
            
            # Meal plan indexes
            ('idx_meal_plans_user', 'saved_meal_plans', 'user_id'),
            ('idx_meal_plans_created', 'saved_meal_plans', 'created_at'),
            ('idx_meal_plans_user_created', 'saved_meal_plans', 'user_id, created_at'),
            
            # Shared meal plan indexes
            ('idx_shared_plans_token', 'shared_meal_plans', 'share_token'),
            ('idx_shared_plans_user', 'shared_meal_plans', 'user_id'),
        ]
        
        for index_name, table_name, columns in indexes:
            try:
                self.cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})")
                self.log_optimization("Index created", f"{index_name} on {table_name}({columns})")
            except Exception as e:
                print(f"✗ Failed to create index {index_name}: {e}")
    
    def add_constraints(self):
        """Add database constraints for data integrity"""
        # Note: SQLite doesn't support adding constraints to existing tables
        # We'll check for constraint violations instead
        
        # Check for duplicate emails
        self.cursor.execute("""
            SELECT email, COUNT(*) as count 
            FROM users 
            GROUP BY email 
            HAVING count > 1
        """)
        duplicates = self.cursor.fetchall()
        
        if duplicates:
            print(f"⚠ Found {len(duplicates)} duplicate emails - manual cleanup required")
            for email, count in duplicates:
                print(f"  - {email}: {count} occurrences")
        else:
            self.log_optimization("Constraint check", "No duplicate emails found")
        
        # Check for orphaned records
        orphan_checks = [
            ('usage_logs', 'user_id', 'users', 'id'),
            ('payments', 'user_id', 'users', 'id'),
            ('saved_meal_plans', 'user_id', 'users', 'id'),
            ('shared_meal_plans', 'user_id', 'users', 'id'),
        ]
        
        for child_table, child_col, parent_table, parent_col in orphan_checks:
            self.cursor.execute(f"""
                SELECT COUNT(*) FROM {child_table} 
                WHERE {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
            """)
            orphan_count = self.cursor.fetchone()[0]
            
            if orphan_count > 0:
                print(f"⚠ Found {orphan_count} orphaned records in {child_table}")
                # Clean up orphans
                self.cursor.execute(f"""
                    DELETE FROM {child_table} 
                    WHERE {child_col} NOT IN (SELECT {parent_col} FROM {parent_table})
                """)
                self.log_optimization("Cleanup", f"Removed {orphan_count} orphaned records from {child_table}")
            else:
                self.log_optimization("Integrity check", f"No orphaned records in {child_table}")
    
    def optimize_settings(self):
        """Optimize SQLite settings"""
        optimizations = [
            ("PRAGMA journal_mode = WAL", "Enable Write-Ahead Logging"),
            ("PRAGMA synchronous = NORMAL", "Set synchronous mode to NORMAL"),
            ("PRAGMA cache_size = -64000", "Set cache size to 64MB"),
            ("PRAGMA temp_store = MEMORY", "Use memory for temporary tables"),
            ("PRAGMA mmap_size = 268435456", "Enable memory-mapped I/O (256MB)"),
            ("PRAGMA optimize", "Run ANALYZE optimization"),
        ]
        
        for pragma, description in optimizations:
            try:
                self.cursor.execute(pragma)
                self.log_optimization("SQLite setting", description)
            except Exception as e:
                print(f"✗ Failed to set {pragma}: {e}")
    
    def analyze_slow_queries(self):
        """Identify potentially slow queries"""
        # Check table sizes
        tables = ['users', 'usage_logs', 'payments', 'saved_meal_plans', 'shared_meal_plans']
        
        print("\nTable Statistics:")
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  {table}: {count} rows")
            except:
                pass
        
        # Check for missing indexes on foreign keys
        self.cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        """)
        
        tables_sql = self.cursor.fetchall()
        foreign_keys = []
        
        for table_sql in tables_sql:
            sql = table_sql[0]
            # Simple regex to find foreign key references
            import re
            fk_matches = re.findall(r'(\w+)\s+.*REFERENCES\s+(\w+)\((\w+)\)', sql, re.IGNORECASE)
            foreign_keys.extend(fk_matches)
        
        if foreign_keys:
            print("\nForeign keys that should have indexes:")
            for col, ref_table, ref_col in foreign_keys:
                print(f"  - {col} -> {ref_table}.{ref_col}")
    
    def add_triggers(self):
        """Add triggers for automatic timestamp updates"""
        triggers = [
            # Auto-update updated_at timestamp
            (
                'update_user_timestamp',
                """
                CREATE TRIGGER IF NOT EXISTS update_user_timestamp 
                AFTER UPDATE ON users
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
                """
            ),
            # Cascade soft deletes
            (
                'cascade_user_soft_delete',
                """
                CREATE TRIGGER IF NOT EXISTS cascade_user_soft_delete
                AFTER UPDATE OF is_active ON users
                WHEN NEW.is_active = 0
                BEGIN
                    UPDATE saved_meal_plans SET is_deleted = 1 WHERE user_id = NEW.id;
                    UPDATE shared_meal_plans SET is_active = 0 WHERE user_id = NEW.id;
                END
                """
            ),
        ]
        
        for trigger_name, trigger_sql in triggers:
            try:
                self.cursor.execute(trigger_sql)
                self.log_optimization("Trigger created", trigger_name)
            except Exception as e:
                if "no such column" not in str(e):
                    print(f"✗ Failed to create trigger {trigger_name}: {e}")
    
    def vacuum_database(self):
        """Vacuum database to reclaim space and optimize"""
        try:
            # Get size before vacuum
            file_size_before = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            
            self.cursor.execute("VACUUM")
            
            # Get size after vacuum
            file_size_after = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            
            space_saved = file_size_before - file_size_after
            self.log_optimization("Database vacuumed", f"Saved {space_saved:.2f}MB")
        except Exception as e:
            print(f"✗ Failed to vacuum database: {e}")
    
    def create_views(self):
        """Create useful database views"""
        views = [
            (
                'user_stats',
                """
                CREATE VIEW IF NOT EXISTS user_stats AS
                SELECT 
                    u.id,
                    u.email,
                    u.subscription_tier,
                    COUNT(DISTINCT ul.id) as total_actions,
                    COUNT(DISTINCT smp.id) as saved_plans,
                    COUNT(DISTINCT p.id) as payments_made,
                    MAX(ul.created_at) as last_activity
                FROM users u
                LEFT JOIN usage_logs ul ON u.id = ul.user_id
                LEFT JOIN saved_meal_plans smp ON u.id = smp.user_id
                LEFT JOIN payments p ON u.id = p.user_id
                GROUP BY u.id
                """
            ),
            (
                'daily_usage',
                """
                CREATE VIEW IF NOT EXISTS daily_usage AS
                SELECT 
                    DATE(created_at) as date,
                    action,
                    COUNT(*) as count
                FROM usage_logs
                GROUP BY DATE(created_at), action
                """
            ),
        ]
        
        for view_name, view_sql in views:
            try:
                self.cursor.execute(view_sql)
                self.log_optimization("View created", view_name)
            except Exception as e:
                print(f"✗ Failed to create view {view_name}: {e}")
    
    def run_all_optimizations(self):
        """Run all database optimizations"""
        print("Starting Database Optimization...")
        print("="*60)
        
        self.connect()
        
        try:
            # Run optimizations
            self.optimize_settings()
            print()
            self.add_indexes()
            print()
            self.add_constraints()
            print()
            self.add_triggers()
            print()
            self.create_views()
            print()
            self.analyze_slow_queries()
            print()
            self.vacuum_database()
            
            # Commit all changes
            self.conn.commit()
            
            print("\n" + "="*60)
            print(f"Database optimization complete!")
            print(f"Total optimizations applied: {len(self.optimizations)}")
            
            # Save optimization report
            import json
            with open('database_optimization_report.json', 'w') as f:
                json.dump(self.optimizations, f, indent=2)
            
            print("Report saved to: database_optimization_report.json")
            
        except Exception as e:
            print(f"\n✗ Error during optimization: {e}")
            self.conn.rollback()
        finally:
            self.disconnect()

def main():
    optimizer = DatabaseOptimizer()
    optimizer.run_all_optimizations()

if __name__ == '__main__':
    main()