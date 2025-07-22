#!/usr/bin/env python3
"""
Test script to verify meal plan generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from meal_optimizer import MealPlanOptimizer

def test_meal_generation():
    """Test basic meal plan generation"""
    print("Testing meal plan generation...")
    
    try:
        # Initialize optimizer
        optimizer = MealPlanOptimizer()
        print("[OK] Optimizer initialized successfully")
        
        # Create test preferences
        preferences = {
            'diet': 'standard',
            'calories': 2000,
            'pattern': 'standard',
            'restrictions': [],
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'measurement_system': 'metric',
            'allow_substitutions': True
        }
        
        print("\nGenerating single day meal plan...")
        print(f"Preferences: {preferences}")
        
        # Generate single day plan
        day_meals, metrics = optimizer.generate_single_day_plan(preferences)
        
        print(f"\n[OK] Meal plan generated successfully!")
        print(f"Metrics: {metrics}")
        
        # Display meals
        print("\nGenerated Meals:")
        print("-" * 50)
        for meal_name, meal_data in day_meals.items():
            print(f"\n{meal_name.upper()}:")
            print(f"  Name: {meal_data.get('name', 'Unknown')}")
            print(f"  Calories: {meal_data.get('calories', 0)}")
            print(f"  Protein: {meal_data.get('protein', 0)}g")
            print(f"  Carbs: {meal_data.get('carbs', 0)}g")
            print(f"  Fat: {meal_data.get('fat', 0)}g")
            print(f"  Ingredients:")
            for ingredient in meal_data.get('ingredients', []):
                if isinstance(ingredient, dict):
                    print(f"    - {ingredient['item']}: {ingredient['amount']}{ingredient.get('unit', 'g')}")
                else:
                    print(f"    - {ingredient}")
        
        # Calculate totals
        totals = optimizer.calculate_day_totals(day_meals)
        print(f"\nDaily Totals:")
        print(f"  Calories: {totals['calories']}")
        print(f"  Protein: {totals['protein']}g")
        print(f"  Carbs: {totals['carbs']}g")
        print(f"  Fat: {totals['fat']}g")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_meal_generation()
    sys.exit(0 if success else 1)