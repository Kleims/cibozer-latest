#!/usr/bin/env python
"""
Test Flask app startup without running full server
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

def test_app_startup():
    """Test if Flask app can start without errors"""
    print("=== TESTING FLASK APP STARTUP ===")
    
    try:
        from app import create_app
        
        # Create app
        print("Creating Flask app...")
        app = create_app()
        print("SUCCESS: Flask app created successfully")
        
        # Test app context
        with app.app_context():
            print("SUCCESS: App context working")
            
            # Test database
            from app.extensions import db
            from sqlalchemy import text
            
            try:
                result = db.session.execute(text('SELECT 1')).scalar()
                print("SUCCESS: Database connection working")
                
                # Test a simple route
                with app.test_client() as client:
                    print("Testing routes...")
                    
                    # Test homepage
                    response = client.get('/')
                    print(f"Homepage (GET /): {response.status_code}")
                    
                    # Test auth pages
                    response = client.get('/auth/login')
                    print(f"Login page (GET /auth/login): {response.status_code}")
                    
                    response = client.get('/auth/register')
                    print(f"Register page (GET /auth/register): {response.status_code}")
                    
                    # Test actual registration (POST)
                    response = client.post('/auth/register', data={
                        'full_name': 'Test User',
                        'email': 'test@example.com',
                        'password': 'testpass123',
                        'password_confirm': 'testpass123'
                    }, follow_redirects=True)
                    print(f"Registration (POST /auth/register): {response.status_code}")
                    
                    if response.status_code != 200:
                        print(f"Registration failed. Response data: {response.data.decode()[:200]}...")
                    else:
                        print("SUCCESS: Registration working!")
                
            except Exception as e:
                print(f"FAILED: Database test failed: {e}")
                return False
        
        print("SUCCESS: All tests passed!")
        return True
        
    except Exception as e:
        print(f"FAILED: App startup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_app_startup()
    sys.exit(0 if success else 1)