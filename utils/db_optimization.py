"""Database optimization utilities for improved performance"""

import logging
from sqlalchemy import event
from sqlalchemy.pool import Pool
from sqlalchemy.engine import Engine
from datetime import datetime


logger = logging.getLogger(__name__)


def setup_connection_pool(app):
    """Configure database connection pooling for better performance"""
    
    # Set optimal pool settings based on environment
    if app.config.get('TESTING'):
        # Test environment: smaller pool
        app.config['SQLALCHEMY_POOL_SIZE'] = 5
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = 10
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 300
    elif app.config.get('ENV') == 'production':
        # Production: larger pool for concurrent requests
        app.config['SQLALCHEMY_POOL_SIZE'] = 20
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600
        app.config['SQLALCHEMY_MAX_OVERFLOW'] = 40
    else:
        # Development: moderate pool
        app.config['SQLALCHEMY_POOL_SIZE'] = 10
        app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 1800
    
    # Enable connection pool pre-ping to verify connections
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': app.config.get('SQLALCHEMY_POOL_RECYCLE', 3600),
    }
    
    logger.info(f"Database connection pool configured: size={app.config.get('SQLALCHEMY_POOL_SIZE')}")


def setup_query_logging(app, threshold_ms=100):
    """Log slow queries for performance monitoring"""
    
    if app.config.get('TESTING'):
        return  # Don't log queries during tests
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(datetime.now())
        if app.debug:
            logger.debug(f"Executing query: {statement[:100]}...")
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total = (datetime.now() - conn.info['query_start_time'].pop(-1)).total_seconds() * 1000
        if total > threshold_ms:
            logger.warning(f"Slow query detected ({total:.1f}ms): {statement[:200]}...")


def optimize_database_indexes(db):
    """Create database indexes for common query patterns"""
    
    index_definitions = [
        # User lookups
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_tier, subscription_status);",
        
        # Payment queries
        "CREATE INDEX IF NOT EXISTS idx_payments_user_date ON payments(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);",
        
        # Meal plan queries
        "CREATE INDEX IF NOT EXISTS idx_meal_plans_user_date ON meal_plans(user_id, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_meal_plans_shared ON meal_plans(is_public, share_token);",
    ]
    
    created = 0
    for index_sql in index_definitions:
        try:
            db.engine.execute(index_sql)
            created += 1
        except Exception as e:
            # Index might already exist or table doesn't exist yet
            logger.debug(f"Could not create index: {e}")
    
    if created > 0:
        logger.info(f"Created {created} database indexes for optimization")


def enable_query_cache(app):
    """Enable query result caching for frequently accessed data"""
    
    # Configure Flask-Caching if available
    try:
        from flask_caching import Cache
        
        cache_config = {
            'CACHE_TYPE': 'simple' if app.config.get('TESTING') else 'filesystem',
            'CACHE_DIR': 'cache',
            'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes
            'CACHE_THRESHOLD': 500
        }
        
        cache = Cache(app, config=cache_config)
        app.cache = cache
        logger.info("Query caching enabled")
        return cache
    except ImportError:
        logger.debug("Flask-Caching not available, skipping query cache")
        return None


def vacuum_database(db):
    """Run VACUUM to optimize SQLite database"""
    
    if 'sqlite' in db.engine.url.drivername:
        try:
            db.engine.execute("VACUUM")
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.warning(f"Could not vacuum database: {e}")


def get_database_stats(db):
    """Get database performance statistics"""
    
    stats = {
        'pool_size': db.engine.pool.size(),
        'checked_in_connections': db.engine.pool.checkedin(),
        'overflow': db.engine.pool.overflow(),
        'total': db.engine.pool.checkedout()
    }
    
    if 'sqlite' in db.engine.url.drivername:
        # SQLite specific stats
        result = db.engine.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()").first()
        stats['database_size_bytes'] = result[0] if result else 0
        stats['database_size_mb'] = round(stats['database_size_bytes'] / (1024 * 1024), 2)
    
    return stats