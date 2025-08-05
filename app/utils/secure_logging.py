"""Secure logging configuration"""
import logging
import re
from logging.handlers import RotatingFileHandler, SysLogHandler

# Patterns to redact from logs
REDACT_PATTERNS = [
    (r'password["']?:\s*["']?[^"'\s]+', 'password: [REDACTED]'),
    (r'token["']?:\s*["']?[^"'\s]+', 'token: [REDACTED]'),
    (r'api_key["']?:\s*["']?[^"'\s]+', 'api_key: [REDACTED]'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
    (r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b', '[CARD_REDACTED]'),
]

class SecurityFilter(logging.Filter):
    """Filter to redact sensitive information from logs"""
    
    def filter(self, record):
        # Redact sensitive data from log messages
        message = record.getMessage()
        for pattern, replacement in REDACT_PATTERNS:
            message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
        record.msg = message
        record.args = ()
        return True

def configure_secure_logging(app):
    """Configure secure logging for the application"""
    
    # Remove default handlers
    app.logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    
    # File handler with rotation
    if not app.debug:
        file_handler = RotatingFileHandler(
            'logs/cibozer.log',
            maxBytes=10485760,  # 10MB
            backupCount=30
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.INFO)
        file_handler.addFilter(SecurityFilter())
        app.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = RotatingFileHandler(
            'logs/cibozer_errors.log',
            maxBytes=10485760,  # 10MB
            backupCount=30
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(SecurityFilter())
        app.logger.addHandler(error_handler)
    
    # Syslog handler for production
    if app.config.get('ENV') == 'production' and app.config.get('SYSLOG_ADDRESS'):
        syslog_handler = SysLogHandler(address=app.config['SYSLOG_ADDRESS'])
        syslog_handler.setFormatter(detailed_formatter)
        syslog_handler.addFilter(SecurityFilter())
        app.logger.addHandler(syslog_handler)
    
    # Set log level
    app.logger.setLevel(logging.INFO)
    
    # Log security events
    app.logger.info('Secure logging configured')
    
    return app
