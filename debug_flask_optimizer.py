#!/usr/bin/env python3
"""Debug the enhanced optimizer in Flask context"""
from app import create_app

def debug_optimizer():
    app = create_app()
    
    with app.app_context():
        print("=== TESTING ENHANCED OPTIMIZER IN FLASK ===")
        
        try:
            from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
            print("✓ Enhanced optimizer imported")
            
            optimizer = EnhancedMealOptimizer()
            print("✓ Enhanced optimizer initialized")
            
            meal_plan = optimizer.generate_meal_plan(
                target_calories=2000,
                diet_type='standard',
                meals_per_day=3,
                days=2
            )
            
            print(f"✓ Meal plan generated successfully")
            print(f"   Days: {len(meal_plan['days'])}")
            print(f"   Variety score: {meal_plan['variety_score']}")
            
            # Show first few meals
            if meal_plan['days']:
                day1 = meal_plan['days'][0]
                print(f"\n   Day 1 meals:")
                for i, meal in enumerate(day1['meals'], 1):
                    print(f"     {i}. {meal['name']} - {meal['calories']} cal")
            
            return True
            
        except ImportError as e:
            print(f"✗ Import error: {e}")
            return False
        except Exception as e:
            print(f"✗ Other error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    debug_optimizer()