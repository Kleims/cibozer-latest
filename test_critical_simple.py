#!/usr/bin/env python
"""Simple critical scenario testing."""
import os
import sys
import json
from datetime import datetime

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer

print("=== CRITICAL SCENARIO TESTING (SIMPLIFIED) ===\n")

# Most important scenarios
CRITICAL_TESTS = [
    {
        "name": "Standard 2000 cal",
        "diet": "standard", 
        "calories": 2000,
        "restrictions": []
    },
    {
        "name": "Vegan 2000 cal",
        "diet": "vegan",
        "calories": 2000, 
        "restrictions": []
    },
    {
        "name": "Keto 2000 cal",
        "diet": "keto",
        "calories": 2000,
        "restrictions": []
    },
    {
        "name": "Weight Loss 1500 cal",
        "diet": "standard",
        "calories": 1500,
        "restrictions": []
    },
    {
        "name": "High Protein 3000 cal", 
        "diet": "high_protein",
        "calories": 3000,
        "restrictions": []
    },
    {
        "name": "Gluten-Free Standard",
        "diet": "standard",
        "calories": 2000,
        "restrictions": ["gluten"]
    },
    {
        "name": "Multiple Allergies",
        "diet": "standard",
        "calories": 2000,
        "restrictions": ["nuts", "dairy", "eggs"]
    }
]

app = create_app()
results = []

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    
    for test in CRITICAL_TESTS:
        print(f"\nTesting: {test['name']}")
        print("-" * 50)
        
        try:
            # Generate 7-day plan
            all_days = []
            total_calories = 0
            total_protein = 0
            total_carbs = 0
            total_fat = 0
            violations = []
            ingredient_count = set()
            
            for day in range(1, 8):
                meals, metrics = optimizer.generate_single_day_plan({
                    'diet': test['diet'],
                    'calories': test['calories'],
                    'pattern': 'standard',
                    'restrictions': test['restrictions'],
                    'cuisines': ['all'],
                    'cooking_methods': ['all'],
                    'measurement_system': 'US',
                    'allow_substitutions': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Calculate daily totals
                day_calories = sum(m.get('calories', 0) for m in meals.values())
                day_protein = sum(m.get('protein', 0) for m in meals.values())
                day_carbs = sum(m.get('carbs', 0) for m in meals.values())
                day_fat = sum(m.get('fat', 0) for m in meals.values())
                
                total_calories += day_calories
                total_protein += day_protein
                total_carbs += day_carbs
                total_fat += day_fat
                
                # Check compliance
                for meal in meals.values():
                    # Diet compliance
                    is_compliant, meal_violations = optimizer.validate_diet_compliance(meal, test['diet'])
                    violations.extend(meal_violations)
                    
                    # Restriction compliance
                    for ing in meal.get('ingredients', []):
                        if isinstance(ing, dict):
                            ingredient_count.add(ing.get('item', ''))
                            
                            # Check restrictions
                            item = ing.get('item', '').lower()
                            for restriction in test['restrictions']:
                                if restriction == 'gluten' and any(g in item for g in ['wheat', 'bread', 'pasta']):
                                    violations.append(f"{ing.get('item')} contains gluten")
                                elif restriction == 'dairy' and any(d in item for d in ['milk', 'cheese', 'butter', 'cream']):
                                    violations.append(f"{ing.get('item')} contains dairy")
                                elif restriction == 'nuts' and any(n in item.split('_') for n in ['almond', 'walnut', 'cashew', 'pecan', 'macadamia', 'pistachio', 'brazil', 'hazelnut', 'pine', 'peanut']):
                                    violations.append(f"{ing.get('item')} contains nuts")
                                elif restriction == 'eggs' and 'egg' in item:
                                    violations.append(f"{ing.get('item')} contains eggs")
                
                all_days.append({
                    'day': day,
                    'calories': day_calories,
                    'accuracy': 100 - abs(day_calories - test['calories']) / test['calories'] * 100
                })
            
            # Calculate averages
            avg_calories = total_calories / 7
            avg_protein = total_protein / 7
            avg_carbs = total_carbs / 7
            avg_fat = total_fat / 7
            
            # Calculate metrics
            calorie_accuracy = 100 - abs(avg_calories - test['calories']) / test['calories'] * 100
            
            # Macro percentages
            if avg_calories > 0:
                protein_pct = (avg_protein * 4) / avg_calories * 100
                carbs_pct = (avg_carbs * 4) / avg_calories * 100
                fat_pct = (avg_fat * 9) / avg_calories * 100
            else:
                protein_pct = carbs_pct = fat_pct = 0
            
            # Print results
            print(f"\n7-Day Averages:")
            print(f"  Calories: {avg_calories:.0f} (target: {test['calories']})")
            print(f"  Accuracy: {calorie_accuracy:.1f}%")
            print(f"  Protein: {avg_protein:.1f}g ({protein_pct:.1f}%)")
            print(f"  Carbs: {avg_carbs:.1f}g ({carbs_pct:.1f}%)")
            print(f"  Fat: {avg_fat:.1f}g ({fat_pct:.1f}%)")
            print(f"  Ingredient Variety: {len(ingredient_count)} unique items")
            print(f"  Violations: {len(violations)}")
            
            if violations:
                print(f"\n  Sample Violations:")
                for v in list(set(violations))[:5]:
                    print(f"    - {v}")
            
            # Diet-specific checks
            if test['diet'] == 'keto':
                if carbs_pct > 10:
                    print(f"  WARNING: Carbs too high for keto ({carbs_pct:.1f}% > 10%)")
                if fat_pct < 65:
                    print(f"  WARNING: Fat too low for keto ({fat_pct:.1f}% < 65%)")
            
            # Save result
            results.append({
                'test': test['name'],
                'success': calorie_accuracy > 95 and len(violations) == 0,
                'accuracy': calorie_accuracy,
                'violations': len(violations),
                'macros': {'protein': protein_pct, 'carbs': carbs_pct, 'fat': fat_pct},
                'variety': len(ingredient_count)
            })
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
            results.append({
                'test': test['name'],
                'success': False,
                'error': str(e)
            })

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)

successful = sum(1 for r in results if r.get('success', False))
print(f"\nSuccess Rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")

print("\nDetailed Results:")
for result in results:
    status = "PASS" if result.get('success', False) else "FAIL"
    print(f"\n{result['test']}: {status}")
    if 'accuracy' in result:
        print(f"  Calorie Accuracy: {result['accuracy']:.1f}%")
        print(f"  Violations: {result.get('violations', 0)}")
        print(f"  Variety: {result.get('variety', 0)} ingredients")
        macros = result.get('macros', {})
        print(f"  Macros: P:{macros.get('protein', 0):.1f}% C:{macros.get('carbs', 0):.1f}% F:{macros.get('fat', 0):.1f}%")
    if 'error' in result:
        print(f"  Error: {result['error']}")

print("\n=== END OF TESTING ===")