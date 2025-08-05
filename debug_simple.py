#!/usr/bin/env python3
"""Simple debug of optimizer"""
from app import create_app

def debug_simple():
    app = create_app()
    
    with app.app_context():
        print("Testing enhanced optimizer in Flask...")
        
        try:
            from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
            print("SUCCESS: Enhanced optimizer imported")
            
            optimizer = EnhancedMealOptimizer()
            print("SUCCESS: Enhanced optimizer initialized")
            
            meal_plan = optimizer.generate_meal_plan(
                target_calories=2000,
                diet_type='standard',
                meals_per_day=3,
                days=1
            )
            
            print("SUCCESS: Meal plan generated")
            print(f"Variety score: {meal_plan['variety_score']}")
            
            # Show meals
            day1 = meal_plan['days'][0]
            print(f"Day 1 meals ({len(day1['meals'])}):")  
            for i, meal in enumerate(day1['meals'], 1):
                print(f"  {i}. {meal['name']} - {meal['calories']} cal")
            
            return True
            
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = debug_simple()
    if success:
        print("\nEnhanced optimizer is working properly!")
    else:
        print("\nEnhanced optimizer has issues!")
