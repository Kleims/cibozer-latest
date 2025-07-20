"""
Centralized logging setup for Cibozer application
Provides consistent logging configuration across all modules
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from functools import wraps
import time

from app_config import get_app_config

# Get configuration
config = get_app_config()

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_obj['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_obj['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_obj['duration'] = record.duration
        if hasattr(record, 'ip_address'):
            log_obj['ip_address'] = record.ip_address
            
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_obj)


class RequestIdFilter(logging.Filter):
    """Add request ID to log records"""
    
    def filter(self, record):
        # Try to get request ID from Flask g object
        try:
            from flask import g
            record.request_id = getattr(g, 'request_id', 'no-request')
        except:
            record.request_id = 'no-request'
        return True


def setup_logging(
    name: Optional[str] = None,
    log_level: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """
    Set up logging for a module
    
    Args:
        name: Logger name (defaults to root logger)
        log_level: Log level (defaults to config value)
        use_json: Whether to use JSON formatting
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name) if name else logging.getLogger()
    
    # Clear existing handlers to avoid duplication
    logger.handlers.clear()
    
    # Set log level
    level = getattr(logging, log_level or config.logging.LOG_LEVEL)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    if use_json:
        console_formatter = StructuredFormatter()
    else:
        console_formatter = logging.Formatter(config.logging.LOG_FORMAT)
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.logging.LOG_TO_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.logging.LOG_FILE_PATH,
            maxBytes=config.logging.LOG_FILE_MAX_BYTES,
            backupCount=config.logging.LOG_FILE_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # Always use JSON for file logs
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    # Add request ID filter
    request_filter = RequestIdFilter()
    for handler in logger.handlers:
        handler.addFilter(request_filter)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger
    """
    return setup_logging(name)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time
    
    Args:
        logger: Logger instance (creates one if not provided)
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
            
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"{func.__name__} completed",
                    extra={'duration': duration}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed",
                    extra={'duration': duration},
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


def log_database_operation(operation: str, model: str, **kwargs):
    """
    Log database operations consistently
    
    Args:
        operation: Type of operation (create, update, delete, query)
        model: Model name
        **kwargs: Additional context
    """
    logger = get_logger('database')
    logger.info(
        f"Database {operation}: {model}",
        extra={
            'operation': operation,
            'model': model,
            **kwargs
        }
    )


def log_security_event(event_type: str, **kwargs):
    """
    Log security-related events
    
    Args:
        event_type: Type of security event
        **kwargs: Event details
    """
    logger = get_logger('security')
    logger.warning(
        f"Security event: {event_type}",
        extra={
            'event_type': event_type,
            **kwargs
        }
    )


def log_payment_event(event_type: str, **kwargs):
    """
    Log payment-related events
    
    Args:
        event_type: Type of payment event
        **kwargs: Event details
    """
    logger = get_logger('payments')
    logger.info(
        f"Payment event: {event_type}",
        extra={
            'event_type': event_type,
            **kwargs
        }
    )


def setup_app_logging(app):
    """
    Set up logging for Flask application
    
    Args:
        app: Flask application instance
    """
    # Set up main app logger
    app.logger = setup_logging('app', use_json=not app.debug)
    
    # Set up Werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)
    
    # Log application startup
    app.logger.info(
        f"{config.APP_NAME} v{config.APP_VERSION} starting",
        extra={
            'debug': app.debug,
            'testing': app.testing,
            'environment': os.getenv('FLASK_ENV', 'development')
        }
    )
    
    return app.logger


# Audit logger for compliance
class AuditLogger:
    """Separate audit logger for compliance and security tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Audit logs go to separate file
        audit_handler = logging.handlers.RotatingFileHandler(
            filename='logs/audit.log',
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        
        audit_formatter = StructuredFormatter()
        audit_handler.setFormatter(audit_formatter)
        
        self.logger.addHandler(audit_handler)
        self.logger.propagate = False
    
    def log(self, action: str, user_id: Optional[int] = None, **kwargs):
        """Log an audit event"""
        self.logger.info(
            f"Audit: {action}",
            extra={
                'action': action,
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat(),
                **kwargs
            }
        )


# Global audit logger instance
audit_logger = AuditLogger()


if __name__ == '__main__':
    # Test logging setup
    test_logger = setup_logging('test', 'DEBUG')
    test_logger.debug("Debug message")
    test_logger.info("Info message")
    test_logger.warning("Warning message")
    test_logger.error("Error message")
    
    try:
        raise ValueError("Test exception")
    except Exception:
        test_logger.exception("Exception test")
    
    # Test audit logger
    audit_logger.log('test_action', user_id=1, ip_address='127.0.0.1')
    
    print("\nLogging setup complete. Check logs/ directory for output.")