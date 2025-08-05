#!/usr/bin/env python
"""
Test the main Cibozer app's request handling
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_main_app_routes():
    """Test the main app's routes using test client"""
    print("=== TESTING MAIN APP ROUTES ===")
    
    try:
        from app import create_app
        
        # Create the real app
        app = create_app()
        print("SUCCESS: Main app created successfully")
        
        # Test using test client (simulates HTTP requests)
        with app.test_client() as client:
            print("\nTesting routes with test client:")
            
            # Test homepage
            try:
                response = client.get('/')
                print(f"Homepage (GET /): {response.status_code}")
                if response.status_code != 200:
                    print(f"Homepage error: {response.data.decode()[:200]}...")
                else:
                    print("SUCCESS: Homepage working!")
            except Exception as e:
                print(f"Homepage failed: {e}")
            
            # Test auth pages  
            try:
                response = client.get('/auth/login')
                print(f"Login page (GET /auth/login): {response.status_code}")
                if response.status_code != 200:
                    print(f"Login error: {response.data.decode()[:200]}...")
            except Exception as e:
                print(f"Login page failed: {e}")
                
            # Test register page
            try:
                response = client.get('/auth/register') 
                print(f"Register page (GET /auth/register): {response.status_code}")
                if response.status_code != 200:
                    print(f"Register error: {response.data.decode()[:200]}...")
            except Exception as e:
                print(f"Register page failed: {e}")
        
        print("\n=== TEST COMPLETE ===")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_main_app_routes()