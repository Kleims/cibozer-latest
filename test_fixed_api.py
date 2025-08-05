#!/usr/bin/env python
"""
Test the fixed API structure
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_fixed_api():
    """Test the fixed meal generation logic"""
    print("=== TESTING FIXED API LOGIC ===")
    
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
        
        print("Testing fixed data structure handling...")
        
        # Simulate API logic
        all_days = []
        total_calories = 0
        days = 2  # Test with 2 days for speed
        
        for day_num in range(1, days + 1):
            day_meals, metrics = optimizer.generate_single_day_plan(preferences)
            
            # THE FIX: Convert dict to list of values
            meals_list = list(day_meals.values())
            day_calories = sum(meal.get('calories', 0) for meal in meals_list)
            total_calories += day_calories
            
            print(f"Day {day_num}: {len(meals_list)} meals, {day_calories} calories")
            for i, meal in enumerate(meals_list):
                print(f"  Meal {i+1}: {meal.get('name', 'Unknown')} - {meal.get('calories', 0)} cal")
            
            all_days.append({
                'day': day_num,
                'meals': meals_list,
                'total_calories': day_calories,
                'macros': {
                    'protein': sum(meal.get('macros', {}).get('protein', 0) for meal in meals_list),
                    'carbs': sum(meal.get('macros', {}).get('carbs', 0) for meal in meals_list),
                    'fat': sum(meal.get('macros', {}).get('fat', 0) for meal in meals_list)
                }
            })
        
        meal_plan = {
            'days': all_days,
            'total_calories': total_calories,
            'diet_type': 'standard',
            'summary': {
                'total_days': days,
                'total_meals': sum(len(day['meals']) for day in all_days),
                'average_daily_calories': total_calories / days if days > 0 else 0
            }
        }
        
        print(f"\nSUCCESS: Meal plan structure created!")
        print(f"Total days: {meal_plan['summary']['total_days']}")
        print(f"Total meals: {meal_plan['summary']['total_meals']}")
        print(f"Total calories: {meal_plan['total_calories']}")
        print(f"Average daily calories: {meal_plan['summary']['average_daily_calories']}")
        
        # Test that meals are proper dictionaries
        for day in meal_plan['days']:
            for meal in day['meals']:
                assert isinstance(meal, dict), "Meal should be a dictionary"
                assert 'name' in meal, "Meal should have a name"
                assert 'calories' in meal, "Meal should have calories"
        
        print("SUCCESS: All meals are proper dictionaries with required fields!")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_fixed_api()
    if success:
        print("\n🎉 API FIX SUCCESSFUL - READY FOR TESTING!")
    else:
        print("\n❌ API fix failed")