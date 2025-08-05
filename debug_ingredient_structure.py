#!/usr/bin/env python3
"""Debug ingredient structure"""

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
        
        # Make API request
        test_data = {
            "calories": "2000",
            "days": "1",
            "diet": "standard", 
            "meal_structure": "standard"
        }
        
        response = client.post('/api/generate', json=test_data)
        result = response.get_json()
        
        if result and result.get('meal_plan') and result['meal_plan'].get('days'):
            first_day = result['meal_plan']['days'][0]
            first_meal = first_day['meals'][0]
            
            print("=== MEAL STRUCTURE DEBUG ===")
            print(f"Meal keys: {list(first_meal.keys())}")
            print(f"Ingredients type: {type(first_meal.get('ingredients'))}")
            print(f"Ingredients: {first_meal.get('ingredients')}")
            
            if first_meal.get('ingredients'):
                first_ingredient = first_meal['ingredients'][0]
                print(f"First ingredient type: {type(first_ingredient)}")
                print(f"First ingredient: {first_ingredient}")
                if isinstance(first_ingredient, dict):
                    print(f"Ingredient keys: {list(first_ingredient.keys())}")
        else:
            print("No meal plan data found")