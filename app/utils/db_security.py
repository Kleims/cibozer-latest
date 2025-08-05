"""Database security utilities"""
from sqlalchemy import event
from sqlalchemy.pool import Pool
from app.extensions import db

def configure_db_security(app):
    """Configure database security settings"""
    
    # Set connection pool settings for production
    if app.config.get('ENV') == 'production':
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            'pool_pre_ping': True,  # Verify connections before using
            'max_overflow': 20,
            'connect_args': {
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000'  # 30 second statement timeout
            }
        }
    
    # Add event listeners for security
    @event.listens_for(Pool, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas for better security and performance"""
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    
    # Add query logging in debug mode only
    if app.debug:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def create_indexes():
    """Create database indexes for performance and security"""
    from app.models import User, SavedMealPlan, Payment, UsageLog
    
    # This would be better done in migrations, but adding here for completeness
    indexes = [
        ('ix_users_email_active', User.__table__, ['email', 'is_active']),
        ('ix_users_stripe_customer', User.__table__, ['stripe_customer_id']),
        ('ix_usage_logs_user_action', UsageLog.__table__, ['user_id', 'action', 'created_at']),
        ('ix_payments_user_status', Payment.__table__, ['user_id', 'status']),
        ('ix_meal_plans_user_created', SavedMealPlan.__table__, ['user_id', 'created_at']),
    ]
    
    # Note: In production, use Alembic migrations instead
    return indexes
