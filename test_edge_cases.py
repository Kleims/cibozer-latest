#!/usr/bin/env python
"""Test edge cases and special diets."""
import os
import sys
import json
from datetime import datetime

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer

print("=== EDGE CASE TESTING ===\n")

# Edge case test scenarios
edge_cases = [
    {
        "name": "Very Low Calorie - 1200 cal",
        "params": {
            "diet": "standard",
            "calories": 1200,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Very High Calorie - 4000 cal",
        "params": {
            "diet": "standard", 
            "calories": 4000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Vegan + Gluten Free",
        "params": {
            "diet": "vegan",
            "calories": 2000,
            "days": 1,
            "pattern": "standard",
            "restrictions": ["gluten"]
        }
    },
    {
        "name": "Keto + Dairy Free",
        "params": {
            "diet": "keto",
            "calories": 2000,
            "days": 1,
            "pattern": "standard", 
            "restrictions": ["dairy"]
        }
    },
    {
        "name": "Mediterranean Diet",
        "params": {
            "diet": "mediterranean",
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Paleo Diet",
        "params": {
            "diet": "paleo",
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Vegetarian + Nut Allergy",
        "params": {
            "diet": "vegetarian",
            "calories": 2000,
            "days": 1,
            "pattern": "standard",
            "restrictions": ["nuts"]
        }
    },
    {
        "name": "Pescatarian Diet",
        "params": {
            "diet": "pescatarian",
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Multiple Restrictions",
        "params": {
            "diet": "standard",
            "calories": 2000,
            "days": 1,
            "pattern": "standard",
            "restrictions": ["dairy", "gluten", "nuts"]
        }
    },
    {
        "name": "Athletic Pattern - 3000 cal",
        "params": {
            "diet": "standard",
            "calories": 3000,
            "days": 1,
            "pattern": "athletic"
        }
    }
]

results = []
app = create_app()

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    
    for scenario in edge_cases:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 50)
        
        try:
            params = scenario['params']
            restrictions = params.get('restrictions', [])
            
            # Generate meal plan
            meals, metrics = optimizer.generate_single_day_plan({
                'diet': params['diet'],
                'calories': params['calories'],
                'pattern': params.get('pattern', 'standard'),
                'restrictions': restrictions,
                'cuisines': ['all'],
                'cooking_methods': ['all'],
                'measurement_system': 'US',
                'allow_substitutions': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Check results
            total_calories = sum(m.get('calories', 0) for m in meals.values())
            calorie_accuracy = 100 - abs(total_calories - params['calories']) / params['calories'] * 100
            
            # Check restrictions compliance
            restriction_violations = []
            for meal in meals.values():
                for ingredient in meal.get('ingredients', []):
                    if isinstance(ingredient, dict):
                        item = ingredient.get('item', '')
                        
                        # Check each restriction
                        for restriction in restrictions:
                            if restriction == 'gluten' and any(g in item.lower() for g in ['wheat', 'bread', 'pasta']):
                                restriction_violations.append(f"{item} contains gluten")
                            elif restriction == 'dairy' and any(d in item.lower() for d in ['milk', 'cheese', 'yogurt', 'butter', 'cream']):
                                restriction_violations.append(f"{item} contains dairy")
                            elif restriction == 'nuts' and any(n in item.lower() for n in ['almond', 'walnut', 'cashew', 'peanut', 'nut']):
                                restriction_violations.append(f"{item} contains nuts")
            
            # Validate diet compliance
            diet_violations = []
            for meal in meals.values():
                is_compliant, violations = optimizer.validate_diet_compliance(meal, params['diet'])
                diet_violations.extend(violations)
            
            # Display results
            print(f"Total Calories: {total_calories:.1f} (Target: {params['calories']})")
            print(f"Calorie Accuracy: {calorie_accuracy:.1f}%")
            print(f"Diet Violations: {len(diet_violations)}")
            print(f"Restriction Violations: {len(restriction_violations)}")
            
            success = calorie_accuracy > 80 and len(diet_violations) == 0 and len(restriction_violations) == 0
            status = "PASS" if success else "FAIL"
            print(f"Status: {status}")
            
            if diet_violations:
                print("Diet Issues:")
                for v in diet_violations[:3]:
                    print(f"  - {v}")
            
            if restriction_violations:
                print("Restriction Issues:")
                for v in restriction_violations[:3]:
                    print(f"  - {v}")
            
            results.append({
                "scenario": scenario['name'],
                "success": success,
                "accuracy": calorie_accuracy,
                "diet_violations": len(diet_violations),
                "restriction_violations": len(restriction_violations)
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                "scenario": scenario['name'],
                "success": False,
                "error": str(e)
            })

# Summary
print("\n" + "="*60)
print("EDGE CASE TESTING SUMMARY")
print("="*60)

successful = sum(1 for r in results if r.get('success', False))
print(f"\nSuccess Rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")

print("\nDetailed Results:")
for result in results:
    status = "PASS" if result.get('success', False) else "FAIL"
    accuracy = result.get('accuracy', 0)
    print(f"\n{result['scenario']}: {status}")
    if accuracy > 0:
        print(f"  Calorie Accuracy: {accuracy:.1f}%")
    if result.get('diet_violations', 0) > 0:
        print(f"  Diet Violations: {result['diet_violations']}")
    if result.get('restriction_violations', 0) > 0:
        print(f"  Restriction Violations: {result['restriction_violations']}")
    if 'error' in result:
        print(f"  Error: {result['error']}")

print("\n=== END OF EDGE CASE TESTING ===")