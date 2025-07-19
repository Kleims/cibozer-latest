"""
Request Logger - Comprehensive logging for all user activities
"""

import logging
import time
import json
from datetime import datetime
from flask import request, g
from functools import wraps
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cibozer_requests.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('cibozer_requests')

def log_request_start():
    """Log the start of a request"""
    g.start_time = time.time()
    
    # Get user info
    user_info = "anonymous"
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            user_info = f"user_{current_user.id}_{current_user.email}"
    except Exception as e:
        logger.debug(f"Could not get current user info: {e}")
    
    # Log request details
    logger.info(f"REQUEST_START: {request.method} {request.path} | User: {user_info} | IP: {request.remote_addr}")
    
    # Log form data if present
    if request.form:
        form_data = {k: v for k, v in request.form.items() if 'password' not in k.lower()}
        logger.info(f"FORM_DATA: {json.dumps(form_data, default=str)}")
    
    # Log query parameters
    if request.args:
        logger.info(f"QUERY_PARAMS: {dict(request.args)}")
    
    # Log JSON data if present
    if request.is_json:
        try:
            json_data = request.get_json()
            if json_data:
                logger.info(f"JSON_DATA: {json.dumps(json_data, default=str)}")
        except:
            pass

def log_request_end(response):
    """Log the end of a request"""
    duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
    
    logger.info(f"REQUEST_END: {request.method} {request.path} | Status: {response.status_code} | Duration: {duration:.3f}s")
    
    # Log errors
    if response.status_code >= 400:
        logger.error(f"ERROR_RESPONSE: {response.status_code} - {response.get_data(as_text=True)[:500]}")
    
    return response

def log_exception(error):
    """Log exceptions"""
    logger.error(f"EXCEPTION: {request.method} {request.path} | Error: {str(error)}")
    logger.error(f"TRACEBACK: {traceback.format_exc()}")

def log_user_action(action, details=None):
    """Log specific user actions"""
    user_info = "anonymous"
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            user_info = f"user_{current_user.id}_{current_user.email}"
    except Exception as e:
        logger.debug(f"Could not get current user info: {e}")
    
    logger.info(f"USER_ACTION: {action} | User: {user_info} | Details: {details}")

def logged_route(f):
    """Decorator to log route access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        log_user_action(f"ROUTE_ACCESS: {f.__name__}")
        try:
            result = f(*args, **kwargs)
            log_user_action(f"ROUTE_SUCCESS: {f.__name__}")
            return result
        except Exception as e:
            log_user_action(f"ROUTE_ERROR: {f.__name__}", str(e))
            raise
    return decorated_function

def init_logging(app):
    """Initialize logging for the Flask app"""
    
    @app.before_request
    def before_request():
        log_request_start()
    
    @app.after_request
    def after_request(response):
        return log_request_end(response)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        log_exception(e)
        return "Internal Server Error", 500
    
    logger.info("=== CIBOZER REQUEST LOGGING INITIALIZED ===")
    return app