"""
Production WSGI server entry point for Cibozer
Use this for production deployments with Gunicorn/uWSGI
"""

import os
import sys
from pathlib import Path

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    # Try to load production environment first
    if os.path.exists('.env.production'):
        load_dotenv('.env.production')
        print("OK: Loaded .env.production")
    elif os.path.exists('.env'):
        load_dotenv('.env')
        print("OK: Loaded .env (fallback)")
    else:
        print("INFO: No .env file found, using system environment")
except ImportError:
    print("WARNING: python-dotenv not installed, using system environment only")

# Import the Flask app factory
from app import create_app

# Determine environment
flask_env = os.environ.get('FLASK_ENV', 'production')

# Create application instance
app = create_app()

# Production environment validation
if flask_env == 'production':
    # Ensure all critical environment variables are set
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL', 
        'MAIL_SERVER',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        error_msg = f"Missing required environment variables for production: {', '.join(missing_vars)}"
        print(f"ERROR: {error_msg}")
        raise ValueError(error_msg)
    
    print("OK: Production environment validation passed")

# WSGI application object (required by deployment platforms)
application = app

# Log startup information
print(f"INFO: Cibozer WSGI application started")
print(f"   Environment: {flask_env}")
print(f"   Debug: {app.config.get('DEBUG', False)}")
print(f"   Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')[:20]}...")

if __name__ == "__main__":
    # Development server (only for testing WSGI setup)
    print("WARNING: Using development server. For production, use Gunicorn or similar.")
    print("   Example: gunicorn wsgi:app --bind 0.0.0.0:5000")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)