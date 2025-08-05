#!/usr/bin/env python3
"""Test the enhanced meal optimizer"""
from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer

def test_enhanced_optimizer():
    try:
        optimizer = EnhancedMealOptimizer()
        print("Enhanced optimizer initialized successfully!")
        
        # Generate a test meal plan
        meal_plan = optimizer.generate_meal_plan(
            target_calories=2000,
            diet_type='standard',
            meals_per_day=3,
            days=3
        )
        
        print(f"\nGenerated meal plan:")
        print(f"Days: {len(meal_plan['days'])}")
        print(f"Total calories: {meal_plan['total_calories']}")
        print(f"Variety score: {meal_plan['variety_score']}")
        
        # Show first day meals
        if meal_plan['days']:
            day1 = meal_plan['days'][0]
            print(f"\nDay 1 meals ({len(day1['meals'])} meals):")
            for i, meal in enumerate(day1['meals'], 1):
                print(f"  {i}. {meal['name']} - {meal['calories']} calories")
                print(f"     Ingredients: {', '.join(meal['ingredients'][:3])}...")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_enhanced_optimizer()