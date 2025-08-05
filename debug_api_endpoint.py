#!/usr/bin/env python
"""
Comprehensive API endpoint debugging
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def debug_api_endpoint():
    """Debug every part of the API endpoint"""
    print("=== COMPREHENSIVE API ENDPOINT DEBUGGING ===\n")
    
    try:
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            print("1. Testing imports...")
            try:
                from app.routes.api import api_bp
                print("   SUCCESS: API blueprint imported")
            except Exception as e:
                print(f"   ✗ API blueprint import failed: {e}")
                return
            
            print("\n2. Testing meal optimizer import in API context...")
            try:
                import meal_optimizer
                print("   ✓ meal_optimizer imported")
            except Exception as e:
                print(f"   ✗ meal_optimizer import failed: {e}")
                return
            
            print("\n3. Testing helper functions...")
            
            # Test format_meal_plan_for_frontend
            try:
                from app.routes.api import format_meal_plan_for_frontend
                test_plan = {'test': 'data'}
                result = format_meal_plan_for_frontend(test_plan)
                print(f"   ✓ format_meal_plan_for_frontend works - returns: {type(result)}")
            except Exception as e:
                print(f"   ✗ format_meal_plan_for_frontend failed: {e}")
            
            # Test log_usage
            print("\n4. Testing log_usage function...")
            try:
                # Create a test user
                from app.models.user import User
                test_user = User.query.first()
                if test_user:
                    print(f"   Found test user: {test_user.email}")
                    
                    # Try to simulate log_usage
                    from flask_login import login_user
                    login_user(test_user)
                    
                    from app.routes.api import log_usage
                    # This will fail without request context, but we can see if function exists
                    print("   ✓ log_usage function exists")
                else:
                    print("   ⚠ No users in database to test with")
            except Exception as e:
                print(f"   ✗ log_usage test failed: {e}")
            
            print("\n5. Testing actual API route logic...")
            with app.test_client() as client:
                # First create and login a user
                print("   Creating test user...")
                from app.models.user import User
                
                # Check if test user exists
                test_user = User.query.filter_by(email='apitest@example.com').first()
                if not test_user:
                    test_user = User(
                        email='apitest@example.com',
                        full_name='API Test User',
                        credits_balance=5
                    )
                    test_user.set_password('testpass123')
                    db.session.add(test_user)
                    db.session.commit()
                    print("   ✓ Test user created")
                else:
                    print("   ✓ Test user already exists")
                
                # Login
                login_response = client.post('/auth/login', data={
                    'email': 'apitest@example.com',
                    'password': 'testpass123'
                })
                print(f"   Login response: {login_response.status_code}")
                
                # Test API with minimal data
                print("\n   Testing API endpoint...")
                api_data = {
                    "calories": "2000",
                    "days": "1",  # Just 1 day for testing
                    "diet": "standard",
                    "meal_structure": "standard"
                }
                
                response = client.post('/api/generate', 
                                     json=api_data,
                                     content_type='application/json')
                
                print(f"   API Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    try:
                        error_data = response.get_json()
                        print(f"   API Error Response: {error_data}")
                    except:
                        print(f"   API Error Text: {response.data.decode()[:500]}...")
                else:
                    data = response.get_json()
                    print(f"   API Success! Response keys: {list(data.keys())}")
                    if 'meal_plan' in data:
                        print(f"   Meal plan generated successfully!")
            
            print("\n6. Testing direct route function call...")
            try:
                # Import the actual function
                from app.routes.api import generate_meal_plan
                
                # Create a mock request context
                with app.test_request_context('/api/generate', 
                                              method='POST',
                                              json={
                                                  "calories": "2000",
                                                  "days": "1",
                                                  "diet": "standard",
                                                  "meal_structure": "standard"
                                              }):
                    # Mock current_user
                    from flask_login import login_user
                    if test_user:
                        login_user(test_user)
                        
                        # Try calling the function directly
                        print("   Calling generate_meal_plan directly...")
                        try:
                            result = generate_meal_plan()
                            print(f"   Direct call result: {result}")
                        except Exception as e:
                            print(f"   Direct call error: {e}")
                            import traceback
                            traceback.print_exc()
                
            except Exception as e:
                print(f"   ✗ Direct function test failed: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_api_endpoint()