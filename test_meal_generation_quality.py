#!/usr/bin/env python
"""Comprehensive meal generation testing and evaluation."""
import os
import sys
import json
from datetime import datetime

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer

print("=== MEAL GENERATION QUALITY TESTING ===\n")

# Test configurations
test_scenarios = [
    {
        "name": "Standard Diet - 2000 cal",
        "params": {
            "diet": "standard",
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Vegan Diet - 2000 cal", 
        "params": {
            "diet": "vegan",
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Keto Diet - 2000 cal",
        "params": {
            "diet": "keto", 
            "calories": 2000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "Low Calorie - 1500 cal",
        "params": {
            "diet": "standard",
            "calories": 1500,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "High Calorie - 3000 cal",
        "params": {
            "diet": "standard",
            "calories": 3000,
            "days": 1,
            "pattern": "standard"
        }
    },
    {
        "name": "7-Day Vegan Plan",
        "params": {
            "diet": "vegan",
            "calories": 2000,
            "days": 7,
            "pattern": "standard"
        }
    }
]

def evaluate_meal_plan(meal_plan, target_calories, diet_type):
    """Evaluate quality of generated meal plan."""
    evaluation = {
        "calorie_accuracy": 0,
        "macro_balance": {},
        "portion_realism": True,
        "ingredient_variety": 0,
        "diet_compliance": True,
        "issues": []
    }
    
    # Check if plan exists
    if not meal_plan or 'days' not in meal_plan:
        evaluation["issues"].append("No meal plan generated")
        return evaluation
    
    # Calorie accuracy
    total_calories = 0
    all_ingredients = set()
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    
    for day in meal_plan.get('days', []):
        day_calories = 0
        
        for meal in day.get('meals', []):
            meal_calories = meal.get('calories', 0)
            day_calories += meal_calories
            
            # Collect macros (stored directly in meal object)
            total_protein += meal.get('protein', 0)
            total_carbs += meal.get('carbs', 0)
            total_fat += meal.get('fat', 0)
            
            # Check portions
            for ingredient in meal.get('ingredients', []):
                if isinstance(ingredient, dict):
                    all_ingredients.add(ingredient.get('item', ''))
                    amount = ingredient.get('amount', 0)
                    
                    # Check for unrealistic portions
                    if amount > 500:  # More than 500g of single ingredient
                        evaluation["issues"].append(f"Large portion: {amount}g of {ingredient.get('item')}")
                    if amount < 5 and ingredient.get('unit') == 'g':  # Less than 5g
                        evaluation["issues"].append(f"Tiny portion: {amount}g of {ingredient.get('item')}")
        
        total_calories += day_calories
    
    # Calculate evaluation metrics
    days = len(meal_plan.get('days', []))
    if days > 0:
        avg_daily_calories = total_calories / days
        calorie_difference = abs(avg_daily_calories - target_calories)
        evaluation["calorie_accuracy"] = max(0, 100 - (calorie_difference / target_calories * 100))
        
        # Macro balance (as percentage of calories)
        if total_calories > 0:
            protein_pct = (total_protein * 4) / total_calories * 100
            carbs_pct = (total_carbs * 4) / total_calories * 100
            fat_pct = (total_fat * 9) / total_calories * 100
            
            evaluation["macro_balance"] = {
                "protein_pct": round(protein_pct, 1),
                "carbs_pct": round(carbs_pct, 1),
                "fat_pct": round(fat_pct, 1)
            }
            
            # Check macro balance based on diet type
            if diet_type == "keto":
                if carbs_pct > 10:
                    evaluation["issues"].append(f"Keto diet but carbs are {carbs_pct:.1f}% (should be <10%)")
            elif diet_type == "standard":
                if protein_pct < 10 or protein_pct > 35:
                    evaluation["issues"].append(f"Protein {protein_pct:.1f}% outside healthy range (10-35%)")
    
    # Ingredient variety
    evaluation["ingredient_variety"] = len(all_ingredients)
    if len(all_ingredients) < 10:
        evaluation["issues"].append("Low ingredient variety")
    
    # Diet compliance check
    if diet_type == "vegan":
        non_vegan = ["chicken", "beef", "fish", "egg", "milk", "cheese", "yogurt"]
        for ingredient in all_ingredients:
            if any(item in ingredient.lower() for item in non_vegan):
                evaluation["diet_compliance"] = False
                evaluation["issues"].append(f"Non-vegan ingredient: {ingredient}")
    
    return evaluation

# Run tests
results = []
app = create_app()

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    
    for scenario in test_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 50)
        
        try:
            # Generate meal plan
            params = scenario['params']
            
            if params['days'] == 1:
                # Single day generation
                meals, metrics = optimizer.generate_single_day_plan({
                    'diet': params['diet'],
                    'calories': params['calories'],
                    'pattern': params['pattern'],
                    'restrictions': [],
                    'cuisines': ['all'],
                    'cooking_methods': ['all'],
                    'measurement_system': 'US',
                    'allow_substitutions': True,
                    'timestamp': datetime.now().isoformat()
                })
                
                meal_plan = {
                    'days': [{
                        'day': 1,
                        'meals': list(meals.values()),
                        'total_calories': sum(m.get('calories', 0) for m in meals.values())
                    }],
                    'diet_type': params['diet']
                }
            else:
                # Multi-day generation
                all_days = []
                for day in range(1, params['days'] + 1):
                    meals, metrics = optimizer.generate_single_day_plan({
                        'diet': params['diet'],
                        'calories': params['calories'],
                        'pattern': params['pattern'],
                        'restrictions': [],
                        'cuisines': ['all'],
                        'cooking_methods': ['all'],
                        'measurement_system': 'US',
                        'allow_substitutions': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    all_days.append({
                        'day': day,
                        'meals': list(meals.values()),
                        'total_calories': sum(m.get('calories', 0) for m in meals.values())
                    })
                
                meal_plan = {
                    'days': all_days,
                    'diet_type': params['diet']
                }
            
            # Evaluate the plan
            evaluation = evaluate_meal_plan(meal_plan, params['calories'], params['diet'])
            
            # Display results
            print(f"Calorie Accuracy: {evaluation['calorie_accuracy']:.1f}%")
            print(f"Macros: P:{evaluation['macro_balance'].get('protein_pct', 0):.1f}% " +
                  f"C:{evaluation['macro_balance'].get('carbs_pct', 0):.1f}% " +
                  f"F:{evaluation['macro_balance'].get('fat_pct', 0):.1f}%")
            print(f"Ingredient Variety: {evaluation['ingredient_variety']} unique items")
            print(f"Diet Compliance: {'PASS' if evaluation['diet_compliance'] else 'FAIL'}")
            
            if evaluation['issues']:
                print("Issues Found:")
                for issue in evaluation['issues'][:5]:  # Show first 5 issues
                    print(f"  - {issue}")
            
            # Sample meal output
            if meal_plan['days']:
                first_meal = meal_plan['days'][0]['meals'][0]
                print(f"\nSample Meal: {first_meal.get('name', 'Unnamed')}")
                print(f"Calories: {first_meal.get('calories', 0)}")
                print("Ingredients:")
                for ing in first_meal.get('ingredients', [])[:5]:
                    if isinstance(ing, dict):
                        print(f"  - {ing.get('amount', 0)}{ing.get('unit', '')} {ing.get('item', '')}")
            
            results.append({
                "scenario": scenario['name'],
                "evaluation": evaluation,
                "success": evaluation['calorie_accuracy'] > 80 and evaluation['diet_compliance']
            })
            
        except Exception as e:
            print(f"ERROR: {str(e)}")
            results.append({
                "scenario": scenario['name'],
                "evaluation": {"issues": [str(e)]},
                "success": False
            })

# Summary
print("\n" + "="*60)
print("OVERALL RESULTS SUMMARY")
print("="*60)

successful = sum(1 for r in results if r['success'])
print(f"\nSuccess Rate: {successful}/{len(results)} ({successful/len(results)*100:.0f}%)")

print("\nDetailed Results:")
for result in results:
    status = "PASS" if result['success'] else "FAIL"
    print(f"\n{result['scenario']}: {status}")
    if not result['success'] and result['evaluation'].get('issues'):
        print(f"  Main issue: {result['evaluation']['issues'][0]}")

print("\n=== END OF MEAL GENERATION TESTING ===")