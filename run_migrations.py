"""
Database migration runner for Cibozer
Handles both Alembic migrations and custom SQL migrations
"""

import os
import sys
from flask import Flask
from flask_migrate import Migrate, upgrade as alembic_upgrade
from models import db
from app_config import get_app_config
import sqlite3
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_custom_migrations():
    """Run custom SQL migrations for indexes and constraints"""
    config = get_app_config()
    
    # For SQLite, we need to run raw SQL
    if config.database.DATABASE_URL.startswith('sqlite'):
        db_path = config.database.DATABASE_URL.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if indexes already exist
            existing_indexes = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
            existing_index_names = [idx[0] for idx in existing_indexes]
            
            # Define indexes to create
            indexes = [
                ("idx_usage_logs_user_id", "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_id ON usage_logs(user_id)"),
                ("idx_usage_logs_user_timestamp", "CREATE INDEX IF NOT EXISTS idx_usage_logs_user_timestamp ON usage_logs(user_id, timestamp)"),
                ("idx_payments_user_id", "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)"),
                ("idx_payments_user_created", "CREATE INDEX IF NOT EXISTS idx_payments_user_created ON payments(user_id, created_at)"),
                ("idx_payments_subscription_id", "CREATE INDEX IF NOT EXISTS idx_payments_subscription_id ON payments(stripe_subscription_id)"),
                ("idx_saved_meal_plans_user_id", "CREATE INDEX IF NOT EXISTS idx_saved_meal_plans_user_id ON saved_meal_plans(user_id)"),
                ("idx_saved_meal_plans_user_created", "CREATE INDEX IF NOT EXISTS idx_saved_meal_plans_user_created ON saved_meal_plans(user_id, created_at)"),
                ("idx_users_subscription_tier", "CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier)"),
                ("idx_users_subscription_status", "CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status)"),
                ("idx_users_active_tier", "CREATE INDEX IF NOT EXISTS idx_users_active_tier ON users(is_active, subscription_tier)")
            ]
            
            # Create indexes
            for index_name, create_sql in indexes:
                if index_name not in existing_index_names:
                    logger.info(f"Creating index: {index_name}")
                    cursor.execute(create_sql)
                else:
                    logger.info(f"Index already exists: {index_name}")
            
            conn.commit()
            logger.info("Custom migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Error running custom migrations: {str(e)}")
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        # For PostgreSQL or other databases, use the migration file
        logger.info("For non-SQLite databases, use Alembic migrations")

def main():
    """Main migration runner"""
    # Create Flask app
    app = Flask(__name__)
    config = get_app_config()
    app.config.update(config.to_flask_config())
    
    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)
    
    with app.app_context():
        # Run Alembic migrations if available
        try:
            logger.info("Running Alembic migrations...")
            alembic_upgrade()
            logger.info("Alembic migrations completed")
        except Exception as e:
            logger.warning(f"No Alembic migrations to run or error: {str(e)}")
        
        # Run custom migrations
        logger.info("Running custom index migrations...")
        run_custom_migrations()
        
        # Verify indexes were created
        if config.database.DATABASE_URL.startswith('sqlite'):
            db_path = config.database.DATABASE_URL.replace('sqlite:///', '')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            indexes = cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()
            
            logger.info(f"Created indexes: {[idx[0] for idx in indexes]}")
            conn.close()
    
    logger.info("All migrations completed successfully!")

if __name__ == "__main__":
    main()