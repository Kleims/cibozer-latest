#!/usr/bin/env python3
"""Test the realistic meal plan with kitchen measurements"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
import json

app = create_app()

with app.app_context():
    user = User.query.filter_by(email='admin@cibozer.com').first()
    
    with app.test_client() as client:
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
        
        # Test meal plan generation
        test_data = {
            "calories": "2000",
            "days": "1",
            "diet": "standard", 
            "meal_structure": "standard"
        }
        
        response = client.post('/api/generate', json=test_data)
        result = response.get_json()
        
        if result and result.get('meal_plan') and result['meal_plan'].get('days'):
            day = result['meal_plan']['days'][0]
            
            print("=== REALISTIC MEAL PLAN TEST ===")
            print(f"Day {day['day']} - Total Calories: {day.get('total_calories', 'N/A')}")
            print()
            
            for i, meal in enumerate(day['meals'], 1):
                print(f"MEAL {i}: {meal.get('name', 'Unknown')}")
                print(f"Calories: {round(meal.get('calories', 0))}")
                print("Ingredients:")
                
                for ingredient in meal.get('ingredients', []):
                    amount = ingredient.get('amount', 0)
                    unit = ingredient.get('unit', '')
                    item = ingredient.get('item', '')
                    kitchen = ingredient.get('kitchen_measurement', 'No kitchen measurement')
                    
                    print(f"  - {item}: {amount:.1f}{unit} -> {kitchen}")
                
                print()
        else:
            print("No meal plan data received")
            print(f"Response: {result}")