#!/usr/bin/env python
"""Debug script to check meal macro data structure."""
import os
import sys
import json

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer

print("=== DEBUGGING MEAL MACRO DATA ===\n")

app = create_app()

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    
    # Generate a single meal
    meals, metrics = optimizer.generate_single_day_plan({
        'diet': 'standard',
        'calories': 2000,
        'pattern': 'standard',
        'restrictions': [],
        'cuisines': ['all'],
        'cooking_methods': ['all'],
        'measurement_system': 'US',
        'allow_substitutions': True,
        'timestamp': '2025-07-29'
    })
    
    print("Meal structure:")
    for meal_type, meal_data in meals.items():
        print(f"\n{meal_type}:")
        print(f"  Keys: {list(meal_data.keys())}")
        
        # Check if macros exist
        if 'macros' in meal_data:
            print(f"  Macros: {meal_data['macros']}")
        else:
            # Check if macros are at top level
            print(f"  Protein: {meal_data.get('protein', 'NOT FOUND')}")
            print(f"  Carbs: {meal_data.get('carbs', 'NOT FOUND')}")
            print(f"  Fat: {meal_data.get('fat', 'NOT FOUND')}")