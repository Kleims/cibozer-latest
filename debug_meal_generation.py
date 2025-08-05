#!/usr/bin/env python
"""
Debug meal generation directly
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def debug_meal_generation():
    """Test meal generation directly without API"""
    print("=== DEBUGGING MEAL GENERATION ===")
    
    try:
        # Test import
        print("1. Testing meal_optimizer import...")
        import meal_optimizer
        print("SUCCESS: meal_optimizer imported")
        
        # Test class creation
        print("2. Testing MealPlanOptimizer creation...")
        optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
        print("SUCCESS: MealPlanOptimizer created")
        
        # Test meal generation
        print("3. Testing meal plan generation...")
        from datetime import datetime
        
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
        
        day_meals, metrics = optimizer.generate_single_day_plan(preferences)
        print("SUCCESS: Single day plan generated")
        print(f"Generated {len(day_meals)} meals")
        
        for i, meal in enumerate(day_meals):
            print(f"  Meal {i+1}: {meal.get('name', 'Unknown')} - {meal.get('calories', 0)} cal")
        
        print("\n4. Testing API structure creation...")
        all_days = []
        total_calories = 0
        days = 7
        
        for day_num in range(1, days + 1):
            day_meals, metrics = optimizer.generate_single_day_plan(preferences)
            day_calories = sum(meal.get('calories', 0) for meal in day_meals)
            total_calories += day_calories
            
            all_days.append({
                'day': day_num,
                'meals': day_meals,
                'total_calories': day_calories,
                'macros': {
                    'protein': sum(meal.get('macros', {}).get('protein', 0) for meal in day_meals),
                    'carbs': sum(meal.get('macros', {}).get('carbs', 0) for meal in day_meals),
                    'fat': sum(meal.get('macros', {}).get('fat', 0) for meal in day_meals)
                }
            })
        
        meal_plan = {
            'days': all_days,
            'total_calories': total_calories,
            'diet_type': 'standard',
            'summary': {
                'total_days': days,
                'total_meals': len(all_days) * (len(all_days[0]['meals']) if all_days else 0),
                'average_daily_calories': total_calories / days if days > 0 else 0
            }
        }
        
        print(f"SUCCESS: {days}-day meal plan created")
        print(f"Total calories: {total_calories}")
        print(f"Average daily calories: {total_calories / days}")
        print(f"Total meals: {len(all_days) * len(all_days[0]['meals'])}")
        
        print("\n=== MEAL GENERATION DEBUG COMPLETE - ALL WORKING ===")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = debug_meal_generation()
    if success:
        print("\nMeal generation logic is working perfectly!")
        print("The issue must be in the API route or authentication.")
    else:
        print("\nMeal generation logic has issues that need fixing.")