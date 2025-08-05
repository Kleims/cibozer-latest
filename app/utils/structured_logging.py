"""Structured logging configuration with correlation IDs"""
import logging
import json
import uuid
from datetime import datetime
from flask import g, request, has_request_context
from pythonjsonlogger import jsonlogger
import traceback

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all log records"""
    
    def filter(self, record):
        if has_request_context():
            record.correlation_id = getattr(g, 'correlation_id', 'no-correlation-id')
            record.request_id = getattr(g, 'request_id', 'no-request-id')
            record.user_id = getattr(g, 'user_id', 'anonymous')
            record.session_id = getattr(g, 'session_id', 'no-session')
        else:
            record.correlation_id = 'no-correlation-id'
            record.request_id = 'no-request-id'
            record.user_id = 'system'
            record.session_id = 'no-session'
        
        return True

class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add location info
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add correlation IDs
        log_record['correlation_id'] = getattr(record, 'correlation_id', 'unknown')
        log_record['request_id'] = getattr(record, 'request_id', 'unknown')
        log_record['user_id'] = getattr(record, 'user_id', 'unknown')
        log_record['session_id'] = getattr(record, 'session_id', 'unknown')
        
        # Add request context if available
        if has_request_context():
            log_record['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'unknown')
            }
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

class AuditLogger:
    """Specialized logger for audit events"""
    
    def __init__(self):
        self.logger = logging.getLogger('cibozer.audit')
        
        # Create audit handler
        handler = logging.handlers.RotatingFileHandler(
            'logs/audit.log',
            maxBytes=10485760,  # 10MB
            backupCount=30
        )
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_event(self, event_type, user_id, details, status='success'):
        """Log audit event"""
        self.logger.info(
            'audit_event',
            extra={
                'event_type': event_type,
                'user_id': user_id,
                'status': status,
                'details': details,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_access(self, user_id, resource, action, allowed):
        """Log access control decision"""
        self.log_event(
            'access_control',
            user_id,
            {
                'resource': resource,
                'action': action,
                'allowed': allowed
            },
            'allowed' if allowed else 'denied'
        )
    
    def log_data_change(self, user_id, model, record_id, changes):
        """Log data modification"""
        self.log_event(
            'data_change',
            user_id,
            {
                'model': model,
                'record_id': record_id,
                'changes': changes
            }
        )
    
    def log_authentication(self, email, event, success, ip_address=None):
        """Log authentication events"""
        self.log_event(
            f'auth_{event}',
            email,
            {
                'email': email,
                'ip_address': ip_address or 'unknown',
                'success': success
            },
            'success' if success else 'failed'
        )

class PerformanceLogger:
    """Specialized logger for performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('cibozer.performance')
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/performance.log',
            maxBytes=10485760,
            backupCount=10
        )
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_operation(self, operation, duration_ms, metadata=None):
        """Log operation performance"""
        self.logger.info(
            'performance_metric',
            extra={
                'operation': operation,
                'duration_ms': duration_ms,
                'metadata': metadata or {},
                'slow': duration_ms > 1000  # Flag slow operations
            }
        )
    
    def log_db_query(self, query, duration_ms, rows_affected=None):
        """Log database query performance"""
        self.log_operation(
            'db_query',
            duration_ms,
            {
                'query': query[:500],  # Truncate long queries
                'rows_affected': rows_affected,
                'slow_query': duration_ms > 100
            }
        )
    
    def log_api_call(self, endpoint, method, duration_ms, status_code):
        """Log API call performance"""
        self.log_operation(
            'api_call',
            duration_ms,
            {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'success': 200 <= status_code < 300
            }
        )

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('cibozer.security')
        
        handler = logging.handlers.RotatingFileHandler(
            'logs/security.log',
            maxBytes=10485760,
            backupCount=30
        )
        handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.WARNING)
    
    def log_suspicious_activity(self, activity_type, user_id, details):
        """Log suspicious activity"""
        self.logger.warning(
            'suspicious_activity',
            extra={
                'activity_type': activity_type,
                'user_id': user_id,
                'details': details,
                'ip_address': request.remote_addr if has_request_context() else 'unknown'
            }
        )
    
    def log_failed_authentication(self, email, reason, ip_address):
        """Log failed authentication attempts"""
        self.logger.warning(
            'auth_failure',
            extra={
                'email': email,
                'reason': reason,
                'ip_address': ip_address,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
    
    def log_rate_limit_exceeded(self, user_id, endpoint, limit):
        """Log rate limit violations"""
        self.logger.warning(
            'rate_limit_exceeded',
            extra={
                'user_id': user_id,
                'endpoint': endpoint,
                'limit': limit,
                'ip_address': request.remote_addr if has_request_context() else 'unknown'
            }
        )

def configure_structured_logging(app):
    """Configure structured logging for the application"""
    
    # Remove existing handlers
    app.logger.handlers = []
    
    # Create formatters
    json_formatter = StructuredFormatter()
    correlation_filter = CorrelationIdFilter()
    
    # Console handler (development)
    if app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(json_formatter)
        console_handler.addFilter(correlation_filter)
        app.logger.addHandler(console_handler)
    
    # File handlers
    handlers = [
        ('app.log', logging.INFO),
        ('errors.log', logging.ERROR),
        ('warnings.log', logging.WARNING)
    ]
    
    for filename, level in handlers:
        handler = logging.handlers.RotatingFileHandler(
            f'logs/{filename}',
            maxBytes=10485760,  # 10MB
            backupCount=30
        )
        handler.setFormatter(json_formatter)
        handler.addFilter(correlation_filter)
        handler.setLevel(level)
        app.logger.addHandler(handler)
    
    # Set application log level
    app.logger.setLevel(logging.INFO)
    
    # Initialize specialized loggers
    app.audit_logger = AuditLogger()
    app.performance_logger = PerformanceLogger()
    app.security_logger = SecurityLogger()
    
    # Add request hooks for correlation IDs
    @app.before_request
    def before_request():
        # Generate correlation ID for request tracing
        g.correlation_id = str(uuid.uuid4())
        g.request_id = str(uuid.uuid4())
        g.request_start_time = datetime.utcnow()
        
        # Set user context
        from flask_login import current_user
        if hasattr(current_user, 'id') and current_user.is_authenticated:
            g.user_id = str(current_user.id)
        else:
            g.user_id = 'anonymous'
        
        # Log request start
        app.logger.info(
            'request_started',
            extra={
                'method': request.method,
                'path': request.path,
                'query_string': request.query_string.decode('utf-8')
            }
        )
    
    @app.after_request
    def after_request(response):
        # Calculate request duration
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds() * 1000
            
            # Log request completion
            app.logger.info(
                'request_completed',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'duration_ms': duration,
                    'content_length': response.content_length
                }
            )
            
            # Log slow requests
            if duration > 1000:  # Slower than 1 second
                app.performance_logger.log_operation(
                    'slow_request',
                    duration,
                    {
                        'method': request.method,
                        'path': request.path,
                        'status_code': response.status_code
                    }
                )
        
        # Add correlation ID to response headers
        if hasattr(g, 'correlation_id'):
            response.headers['X-Correlation-ID'] = g.correlation_id
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    # Log application startup
    app.logger.info(
        'application_started',
        extra={
            'environment': app.config.get('ENV'),
            'debug': app.debug,
            'version': '1.0.0'
        }
    )
    
    return app

# Logging utilities
def log_with_context(logger, level, message, **kwargs):
    """Log with request context"""
    extra = {}
    
    if has_request_context():
        extra.update({
            'correlation_id': getattr(g, 'correlation_id', 'unknown'),
            'user_id': getattr(g, 'user_id', 'unknown'),
            'request_path': request.path,
            'request_method': request.method
        })
    
    extra.update(kwargs)
    
    getattr(logger, level)(message, extra=extra)

def get_logger(name):
    """Get a logger with correlation ID filter"""
    logger = logging.getLogger(name)
    logger.addFilter(CorrelationIdFilter())
    return logger