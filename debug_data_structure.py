#!/usr/bin/env python
"""
Debug the data structure returned by meal optimizer
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def debug_data_structure():
    """Check what the meal optimizer actually returns"""
    print("=== DEBUGGING DATA STRUCTURE ===")
    
    try:
        import meal_optimizer
        from datetime import datetime
        
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
            'timestamp': datetime.now().isoformat()
        }
        
        print("Calling generate_single_day_plan...")
        result = optimizer.generate_single_day_plan(preferences)
        
        print(f"Result type: {type(result)}")
        print(f"Result length: {len(result) if hasattr(result, '__len__') else 'N/A'}")
        
        if isinstance(result, tuple):
            day_meals, metrics = result
            print(f"day_meals type: {type(day_meals)}")
            print(f"day_meals length: {len(day_meals) if hasattr(day_meals, '__len__') else 'N/A'}")
            print(f"metrics type: {type(metrics)}")
            
            if hasattr(day_meals, '__iter__'):
                print("day_meals contents:")
                for i, meal in enumerate(day_meals):
                    print(f"  Meal {i}: {type(meal)} - {repr(meal)[:100]}...")
                    if hasattr(meal, 'keys'):
                        print(f"    Keys: {list(meal.keys())}")
        else:
            print(f"Result: {repr(result)[:200]}...")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_data_structure()