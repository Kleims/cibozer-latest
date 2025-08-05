#!/usr/bin/env python
"""
Test the meal plan generation API directly
"""
import sys
import os
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_api_generation():
    """Test the API meal generation directly"""
    print("=== TESTING MEAL PLAN API ===")
    
    try:
        from app import create_app
        
        # Create app
        app = create_app()
        
        # Test using test client
        with app.test_client() as client:
            print("Testing meal plan generation API...")
            
            # First, we need to create a user and log in
            # Register a test user
            register_data = {
                'full_name': 'Test User',
                'email': 'test@example.com',
                'password': 'testpass123',
                'password_confirm': 'testpass123'
            }
            
            print("1. Registering test user...")
            response = client.post('/auth/register', data=register_data)
            print(f"Registration: {response.status_code}")
            
            # Now test the API
            print("2. Testing meal plan generation API...")
            api_data = {
                "calories": "2000",
                "days": "7", 
                "diet": "standard",
                "meal_structure": "standard"
            }
            
            response = client.post('/api/generate', 
                                 json=api_data,
                                 content_type='application/json')
            
            print(f"API Response: {response.status_code}")
            
            if response.status_code == 200:
                result = response.get_json()
                print("SUCCESS: API returned 200")
                print(f"Response keys: {list(result.keys())}")
                if 'meal_plan' in result:
                    meal_plan = result['meal_plan']
                    print(f"Meal plan days: {len(meal_plan.get('days', []))}")
                    print(f"Total calories: {meal_plan.get('total_calories', 0)}")
                    print("SUCCESS: Meal plan generated!")
                else:
                    print("WARNING: No meal_plan in response")
                    print(f"Response: {result}")
            else:
                print(f"FAILED: API returned {response.status_code}")
                try:
                    error_data = response.get_json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Error text: {response.data.decode()}")
        
        print("\n=== API TEST COMPLETE ===")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_generation()