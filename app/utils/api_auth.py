"""API authentication utilities"""
import secrets
from functools import wraps
from flask import request, jsonify, current_app
from app.models import User
from app.extensions import db

def generate_api_key():
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def require_api_key(f):
    """Decorator to require API key for endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (implement based on your storage method)
        user = User.query.filter_by(api_key=api_key).first()
        
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Add user to request context
        request.api_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_api_request_signature(f):
    """Validate request signature for extra security"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Implement HMAC signature validation if needed
        return f(*args, **kwargs)
    
    return decorated_function
