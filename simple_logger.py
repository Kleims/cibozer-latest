"""
Simple logging implementation for Cibozer
"""
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cibozer_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('cibozer')

def log_info(message):
    """Log info message"""
    logger.info(message)
    print(f"[INFO] {datetime.now().strftime('%H:%M:%S')} - {message}")

def log_error(message):
    """Log error message"""
    logger.error(message)
    print(f"[ERROR] {datetime.now().strftime('%H:%M:%S')} - {message}")

def log_request(method, path, status_code=None, user=None):
    """Log request details"""
    user_info = f"User: {user}" if user else "User: anonymous"
    if status_code:
        message = f"{method} {path} -> {status_code} | {user_info}"
    else:
        message = f"{method} {path} | {user_info}"
    log_info(message)

def log_form_data(form_data):
    """Log form data"""
    # Filter out sensitive data
    safe_data = {k: v for k, v in form_data.items() if 'password' not in k.lower()}
    log_info(f"Form data: {safe_data}")