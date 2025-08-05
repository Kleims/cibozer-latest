#!/usr/bin/env python
"""
Debug configuration to check what's actually being loaded
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from app import create_app

def debug_config():
    """Debug the current configuration"""
    print("=== DEBUGGING FLASK CONFIGURATION ===")
    
    # Check environment variables
    print("Environment Variables:")
    print(f"  FLASK_ENV: {os.environ.get('FLASK_ENV', 'Not Set')}")
    print(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not Set')}")
    print(f"  SECRET_KEY: {os.environ.get('SECRET_KEY', 'Not Set')[:20]}..." if os.environ.get('SECRET_KEY') else "  SECRET_KEY: Not Set")
    print(f"  DEBUG: {os.environ.get('DEBUG', 'Not Set')}")
    print()
    
    try:
        # Create app and check config
        app = create_app()
        
        print("Flask App Configuration:")
        print(f"  DEBUG: {app.config.get('DEBUG')}")
        print(f"  TESTING: {app.config.get('TESTING')}")
        print(f"  SECRET_KEY: {app.config.get('SECRET_KEY', '')[:20]}..." if app.config.get('SECRET_KEY') else "  SECRET_KEY: Not Set")
        print(f"  SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"  WTF_CSRF_ENABLED: {app.config.get('WTF_CSRF_ENABLED', 'Default')}")
        print()
        
        # Check database connection
        with app.app_context():
            from app.extensions import db
            from sqlalchemy import text
            
            try:
                result = db.session.execute(text('SELECT 1')).scalar()
                print(f"Database Connection: SUCCESS")
                
                # Check tables
                tables = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
                print(f"Database Tables: {len(tables)} found")
                for table in tables[:5]:  # Show first 5
                    print(f"  - {table[0]}")
                
            except Exception as e:
                print(f"Database Connection: FAILED - {e}")
        
        # Check CSRF
        print(f"CSRF Protection: {'Enabled' if hasattr(app, 'csrf') else 'Not Found'}")
        
        # Check if secret key is set properly for CSRF
        if app.config.get('SECRET_KEY'):
            print("Secret Key: ✓ SET")
        else:
            print("Secret Key: ✗ MISSING")
            
    except Exception as e:
        print(f"App Creation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_config()