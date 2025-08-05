#!/usr/bin/env python3
"""Compare old vs enhanced optimizer output"""
from app import create_app

def compare_optimizers():
    app = create_app()
    
    with app.app_context():
        print("=== OPTIMIZER COMPARISON ===")
        
        # Test old optimizer
        print("\n1. Testing OLD optimizer:")
        try:
            from app.services.meal_optimizer import MealOptimizer
            old_optimizer = MealOptimizer()
            old_plan = old_optimizer.generate_meal_plan(
                target_calories=2000,
                diet_type='standard',
                meals_per_day=3,
                days=2
            )
            
            print(f"   Days: {len(old_plan['days'])}")
            print(f"   Variety score: {old_plan.get('variety_score', 'N/A')}")
            
            # Show meals from both days
            for day_idx, day in enumerate(old_plan['days'][:2], 1):
                print(f"   Day {day_idx} meals:")
                for meal in day['meals']:
                    print(f"     - {meal['name']} ({meal['calories']} cal)")
                    
        except Exception as e:
            print(f"   ERROR: {e}")
        
        # Test enhanced optimizer
        print("\n2. Testing ENHANCED optimizer:")
        try:
            from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
            enhanced_optimizer = EnhancedMealOptimizer()
            enhanced_plan = enhanced_optimizer.generate_meal_plan(
                target_calories=2000,
                diet_type='standard',
                meals_per_day=3,
                days=2
            )
            
            print(f"   Days: {len(enhanced_plan['days'])}")
            print(f"   Variety score: {enhanced_plan.get('variety_score', 'N/A')}")
            
            # Show meals from both days
            for day_idx, day in enumerate(enhanced_plan['days'][:2], 1):
                print(f"   Day {day_idx} meals:")
                for meal in day['meals']:
                    print(f"     - {meal['name']} ({meal['calories']} cal)")
                    
        except Exception as e:
            print(f"   ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== COMPARISON COMPLETE ===")
        
        # Check what the web interface would use
        print("\n3. Testing what main.py route imports:")
        try:
            from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
            web_optimizer = EnhancedMealOptimizer()
            print(f"   Route will use: {type(web_optimizer).__name__}")
        except Exception as e:
            print(f"   Route import ERROR: {e}")

if __name__ == '__main__':
    compare_optimizers()