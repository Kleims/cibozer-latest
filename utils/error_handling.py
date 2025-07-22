"""Centralized error handling utilities for the application"""

import logging
from functools import wraps
from flask import jsonify, render_template, request, current_app
from werkzeug.exceptions import HTTPException


logger = logging.getLogger(__name__)


class CibozerError(Exception):
    """Base exception class for Cibozer-specific errors"""
    
    def __init__(self, message, error_code=None, status_code=400):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class ValidationError(CibozerError):
    """Raised when input validation fails"""
    
    def __init__(self, message, field=None):
        super().__init__(message, error_code='VALIDATION_ERROR', status_code=400)
        self.field = field


class AuthenticationError(CibozerError):
    """Raised when authentication fails"""
    
    def __init__(self, message):
        super().__init__(message, error_code='AUTH_ERROR', status_code=401)


class InsufficientCreditsError(CibozerError):
    """Raised when user has insufficient credits"""
    
    def __init__(self, required_credits, available_credits):
        message = f"Insufficient credits. Required: {required_credits}, Available: {available_credits}"
        super().__init__(message, error_code='INSUFFICIENT_CREDITS', status_code=403)
        self.required_credits = required_credits
        self.available_credits = available_credits


def handle_error(error):
    """Generic error handler that returns appropriate response format"""
    
    # Log the error
    logger.error(f"Error occurred: {str(error)}", exc_info=True)
    
    # Extract error details
    if isinstance(error, CibozerError):
        message = error.message
        status_code = error.status_code
        error_code = error.error_code
    elif isinstance(error, HTTPException):
        message = error.description or str(error)
        status_code = error.code
        error_code = error.name.upper()
    else:
        message = "An unexpected error occurred"
        status_code = 500
        error_code = "INTERNAL_SERVER_ERROR"
    
    # Return JSON for API requests, HTML for web requests
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({
            'error': {
                'message': message,
                'code': error_code,
                'status': status_code
            }
        }), status_code
    else:
        return render_template('error.html', 
                             error_message=message, 
                             error_code=status_code), status_code


def with_error_handling(func):
    """Decorator to wrap functions with centralized error handling"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            return handle_error(e)
    
    return wrapper


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present and not empty"""
    
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            empty_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    if empty_fields:
        raise ValidationError(f"Empty required fields: {', '.join(empty_fields)}")
    
    return True


def safe_execute(func, *args, **kwargs):
    """Safely execute a function and return result or None on error"""
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Safe execution failed for {func.__name__}: {str(e)}")
        return None


def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(CibozerError)
    def handle_cibozer_error(e):
        return handle_error(e)
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return handle_error(e)
    
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(e):
        return handle_error(e)
    
    @app.errorhandler(InsufficientCreditsError)
    def handle_credits_error(e):
        return handle_error(e)
    
    @app.errorhandler(404)
    def handle_not_found(e):
        return handle_error(e)
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        return handle_error(e)
    
    @app.errorhandler(Exception)
    def handle_general_exception(e):
        return handle_error(e)