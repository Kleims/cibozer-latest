"""Security middleware for request/response processing"""
from flask import request, abort, current_app
from functools import wraps
import hmac
import hashlib
from datetime import datetime

class SecurityMiddleware:
    """Security middleware for Flask application"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process request before handling"""
        
        # Check for suspicious patterns
        if self._is_suspicious_request():
            current_app.logger.warning(f"Suspicious request blocked: {request.url}")
            abort(400)
        
        # Validate content length
        if request.content_length and request.content_length > 50 * 1024 * 1024:  # 50MB
            abort(413)  # Request Entity Too Large
        
        # Add request ID for tracking
        request.request_id = self._generate_request_id()
    
    def after_request(self, response):
        """Process response after handling"""
        
        # Add request ID to response
        if hasattr(request, 'request_id'):
            response.headers['X-Request-ID'] = request.request_id
        
        # Remove server header
        response.headers.pop('Server', None)
        
        # Add cache headers for static content
        if request.path.startswith('/static/'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        return response
    
    def _is_suspicious_request(self):
        """Check if request contains suspicious patterns"""
        
        suspicious_patterns = [
            '../',  # Directory traversal
            '..\\',  # Windows directory traversal
            '<script',  # XSS attempt
            'javascript:',  # XSS attempt
            'onerror=',  # XSS attempt
            'onclick=',  # XSS attempt
            'SELECT%20',  # SQL injection
            'UNION%20',  # SQL injection
            'DROP%20',  # SQL injection
            '%3Cscript',  # Encoded XSS
            '%00',  # Null byte
            '\x00',  # Null byte
        ]
        
        # Check URL
        url = request.url.lower()
        for pattern in suspicious_patterns:
            if pattern.lower() in url:
                return True
        
        # Check common attack vectors in form data
        if request.form:
            for value in request.form.values():
                for pattern in suspicious_patterns:
                    if pattern.lower() in str(value).lower():
                        return True
        
        return False
    
    def _generate_request_id(self):
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())

def require_https(f):
    """Decorator to require HTTPS in production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_app.config.get('ENV') == 'production' and not request.is_secure:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function

def validate_json_request(f):
    """Decorator to validate JSON requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'PATCH']:
            if not request.is_json:
                abort(400, 'Content-Type must be application/json')
            
            # Validate JSON size
            if request.content_length > 1024 * 1024:  # 1MB limit for JSON
                abort(413, 'JSON payload too large')
        
        return f(*args, **kwargs)
    return decorated_function
