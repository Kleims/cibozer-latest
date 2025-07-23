"""Custom decorators for the application."""
from functools import wraps
from flask import jsonify, redirect, url_for, flash
from flask_login import current_user


def check_credits_or_premium(f):
    """Check if user has credits or premium subscription."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not current_user.is_premium() and not current_user.has_credits():
            return jsonify({
                'error': 'No credits available. Please purchase credits or upgrade to premium.',
                'credits_remaining': 0
            }), 402
        
        return f(*args, **kwargs)
    return decorated_function


def premium_required(f):
    """Require premium subscription."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this feature.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_premium():
            flash('This feature requires a premium subscription.', 'error')
            return redirect(url_for('main.pricing'))
        
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Require admin access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        # Check if user is admin (you might want to add an is_admin field to User model)
        if current_user.email not in ['admin@cibozer.com']:  # Replace with proper admin check
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function


def api_key_required(f):
    """Require valid API key for API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        from app.models import APIKey
        
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        key = APIKey.query.filter_by(key=api_key).first()
        
        if not key or not key.is_valid():
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Increment usage
        key.increment_usage()
        
        # Add key to kwargs for use in view
        kwargs['api_key'] = key
        
        return f(*args, **kwargs)
    return decorated_function