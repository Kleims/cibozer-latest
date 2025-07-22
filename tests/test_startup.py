"""
Test script to diagnose startup issues
"""

import sys
import os

print("1. Starting test...")

try:
    print("2. Setting up environment...")
    os.environ['FLASK_ENV'] = 'development'
    
    print("3. Importing Flask...")
    from flask import Flask
    
    print("4. Importing other modules...")
    from dotenv import load_dotenv
    load_dotenv()
    
    print("5. Creating Flask app...")
    test_app = Flask(__name__)
    
    print("6. Importing database...")
    from models import db
    
    print("7. Importing app components...")
    from admin import admin_bp
    from auth import auth_bp
    from payments import payments_bp
    
    print("8. Testing imports complete!")
    
    print("\n9. Now testing full app import...")
    from app import app
    
    print("10. SUCCESS! App imported successfully")
    
    print("\nApp configuration:")
    print(f"  - Debug mode: {app.debug}")
    print(f"  - Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')}")
    
except Exception as e:
    print(f"\nERROR at step: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll imports successful! The app should be able to start.")