"""Database timeout utilities for robust database operations."""
import signal
import time
from contextlib import contextmanager
from functools import wraps
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError
from app.extensions import db


class DatabaseTimeoutError(Exception):
    """Raised when a database operation times out."""
    pass


@contextmanager
def database_timeout(timeout_seconds=30):
    """Context manager that adds timeout to database operations."""
    def timeout_handler(signum, frame):
        raise DatabaseTimeoutError(f"Database operation timed out after {timeout_seconds} seconds")
    
    # Set up timeout signal (Unix only)
    old_handler = None
    try:
        if hasattr(signal, 'SIGALRM'):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
        
        yield
        
    except DatabaseTimeoutError:
        raise
    except (OperationalError, TimeoutError) as e:
        current_app.logger.error(f"Database operation failed: {e}")
        raise DatabaseTimeoutError(f"Database operation failed: {str(e)}")
    finally:
        # Clear timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)


def with_database_timeout(timeout_seconds=30):
    """Decorator that adds timeout to database operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with database_timeout(timeout_seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator


@with_database_timeout(15)
def safe_database_query(query, params=None):
    """Execute a database query with timeout protection."""
    try:
        if params:
            result = db.session.execute(text(query), params)
        else:
            result = db.session.execute(text(query))
        return result
    except DatabaseTimeoutError:
        db.session.rollback()
        current_app.logger.error(f"Database query timed out: {query}")
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database query failed: {query} - {str(e)}")
        raise


@with_database_timeout(30)
def safe_database_commit():
    """Commit database changes with timeout protection."""
    try:
        db.session.commit()
        return True
    except DatabaseTimeoutError:
        db.session.rollback()
        current_app.logger.error("Database commit timed out")
        raise
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database commit failed: {str(e)}")
        raise


class DatabaseOperation:
    """Class for managing database operations with timeouts and retries."""
    
    def __init__(self, timeout_seconds=30, max_retries=3, retry_delay=1):
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute_with_retry(self, operation):
        """Execute a database operation with timeout and retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                with database_timeout(self.timeout_seconds):
                    return operation()
                    
            except DatabaseTimeoutError as e:
                last_error = e
                current_app.logger.warning(
                    f"Database operation attempt {attempt + 1} timed out: {str(e)}"
                )
                
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    current_app.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    
                    # Try to recover connection
                    try:
                        db.session.rollback()
                        db.session.remove()
                    except:
                        pass
                        
            except Exception as e:
                last_error = e
                current_app.logger.error(
                    f"Database operation attempt {attempt + 1} failed: {str(e)}"
                )
                
                # Don't retry for certain errors
                if isinstance(e, (ValueError, TypeError)):
                    break
                    
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    
                    try:
                        db.session.rollback()
                        db.session.remove()
                    except:
                        pass
        
        # All attempts failed
        current_app.logger.error(f"All database operation attempts failed. Last error: {str(last_error)}")
        raise last_error
    
    def query(self, model_class, **filters):
        """Execute a query with timeout and retry protection."""
        def operation():
            return model_class.query.filter_by(**filters).all()
        
        return self.execute_with_retry(operation)
    
    def get(self, model_class, id):
        """Get a single record with timeout and retry protection."""
        def operation():
            return model_class.query.get(id)
        
        return self.execute_with_retry(operation)
    
    def create(self, model_instance):
        """Create a new record with timeout and retry protection."""
        def operation():
            db.session.add(model_instance)
            safe_database_commit()
            return model_instance
        
        return self.execute_with_retry(operation)
    
    def update(self, model_instance, **updates):
        """Update a record with timeout and retry protection."""
        def operation():
            for key, value in updates.items():
                setattr(model_instance, key, value)
            safe_database_commit()
            return model_instance
        
        return self.execute_with_retry(operation)
    
    def delete(self, model_instance):
        """Delete a record with timeout and retry protection."""
        def operation():
            db.session.delete(model_instance)
            safe_database_commit()
            return True
        
        return self.execute_with_retry(operation)


# Global database operation instance
db_ops = DatabaseOperation()


def check_database_health():
    """Check if database is responsive within timeout."""
    try:
        with database_timeout(5):  # Short timeout for health check
            db.session.execute(text('SELECT 1'))
            return True
    except DatabaseTimeoutError:
        current_app.logger.error("Database health check timed out")
        return False
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        return False


def optimize_database_connection():
    """Optimize database connection settings for better timeout handling."""
    try:
        # For SQLAlchemy, we can adjust pool settings dynamically
        engine = db.get_engine()
        
        # Log current pool status
        pool = engine.pool
        current_app.logger.info(f"Database pool status - Size: {pool.size()}, Checked out: {pool.checkedout()}")
        
        # Dispose of old connections if needed
        if pool.checkedout() > pool.size() * 0.8:  # 80% threshold
            current_app.logger.info("Disposing old database connections")
            engine.dispose()
            
    except Exception as e:
        current_app.logger.error(f"Failed to optimize database connection: {str(e)}")