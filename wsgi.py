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

# Import the Flask app
from app import app

# Configure for production
if __name__ != "__main__":
    # Production settings
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    
    # Ensure all required environment variables are set
    required_vars = ['SECRET_KEY', 'DATABASE_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# WSGI application object
application = app

if __name__ == "__main__":
    # Development server (only for testing)
    print("WARNING: Using development server. For production, use Gunicorn or similar.")
    app.run(host='127.0.0.1', port=5001, debug=False)