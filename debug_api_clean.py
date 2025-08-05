#!/usr/bin/env python
"""
Clean API endpoint debugging without unicode issues
"""
import sys
import os

# Fix encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
                print(f"   FAILED: API blueprint import failed: {e}")
                return
            
            print("\n2. Testing meal optimizer import in API context...")
            try:
                import meal_optimizer
                print("   SUCCESS: meal_optimizer imported")
            except Exception as e:
                print(f"   FAILED: meal_optimizer import failed: {e}")
                return
            
            print("\n3. Testing helper functions...")
            
            # Test format_meal_plan_for_frontend
            try:
                from app.routes.api import format_meal_plan_for_frontend
                test_plan = {'test': 'data'}
                result = format_meal_plan_for_frontend(test_plan)
                print(f"   SUCCESS: format_meal_plan_for_frontend works - returns: {type(result)}")
            except Exception as e:
                print(f"   FAILED: format_meal_plan_for_frontend failed: {e}")
            
            print("\n4. Checking if any users exist...")
            from app.models.user import User
            user_count = User.query.count()
            print(f"   Found {user_count} users in database")
            
            if user_count == 0:
                print("   Creating a test user...")
                test_user = User(
                    email='debugtest@example.com',
                    full_name='Debug Test User',
                    credits_balance=10
                )
                test_user.set_password('testpass123')
                db.session.add(test_user)
                db.session.commit()
                print("   Test user created!")
            else:
                test_user = User.query.first()
                print(f"   Using existing user: {test_user.email}")
            
            print("\n5. Testing the API route...")
            with app.test_client() as client:
                # Login
                login_data = {
                    'email': test_user.email,
                    'password': 'testpass123' if test_user.email == 'debugtest@example.com' else 'unknown'
                }
                
                # If login fails, try creating account
                login_response = client.post('/auth/login', data=login_data)
                print(f"   Login attempt: {login_response.status_code}")
                
                if login_response.status_code != 302:  # 302 is redirect after successful login
                    print("   Login failed, trying with session...")
                    # Force login for testing
                    with client.session_transaction() as sess:
                        sess['_user_id'] = str(test_user.id)
                
                # Now test the API
                print("\n   Testing /api/generate endpoint...")
                api_data = {
                    "calories": "2000",
                    "days": "1",
                    "diet": "standard",
                    "meal_structure": "standard"
                }
                
                try:
                    response = client.post('/api/generate', 
                                         json=api_data,
                                         content_type='application/json')
                    
                    print(f"   API Response Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.get_json()
                        print(f"   SUCCESS! Response keys: {list(data.keys())}")
                        if 'meal_plan' in data:
                            meal_plan = data['meal_plan']
                            print(f"   Meal plan has {len(meal_plan.get('days', []))} days")
                    else:
                        error_data = response.get_json()
                        print(f"   ERROR Response: {error_data}")
                        
                except Exception as e:
                    print(f"   API call exception: {e}")
                    import traceback
                    traceback.print_exc()
            
            print("\n6. Testing direct function components...")
            
            # Test if we can generate a meal plan directly
            try:
                print("   Testing meal plan generation directly...")
                optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
                
                preferences = {
                    'diet': 'standard',
                    'calories': 2000,
                    'pattern': 'standard',
                    'restrictions': [],
                    'cuisines': ['all'],
                    'cooking_methods': ['all'],
                    'measurement_system': 'US',
                    'allow_substitutions': True,
                    'timestamp': '2024-01-01T00:00:00'
                }
                
                day_meals, metrics = optimizer.generate_single_day_plan(preferences)
                meals_list = list(day_meals.values())
                print(f"   Direct generation SUCCESS: {len(meals_list)} meals generated")
                
            except Exception as e:
                print(f"   Direct generation FAILED: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_api_endpoint()