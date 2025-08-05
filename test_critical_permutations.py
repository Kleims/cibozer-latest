#!/usr/bin/env python
"""Comprehensive testing of critical meal generation permutations."""
import os
import sys
import json
import time
import statistics
from datetime import datetime
from collections import defaultdict

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer
import nutrition_data as nd

print("=== CRITICAL PERMUTATION TESTING ===\n")

# Define critical test scenarios - the most important real-world use cases
CRITICAL_SCENARIOS = [
    # Standard diets for different lifestyles
    {
        "name": "Office Worker Standard",
        "description": "Typical sedentary adult",
        "params": {
            "diet": "standard",
            "calories": 2000,
            "pattern": "standard",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "protein_g_min": 50,
            "protein_g_max": 100,
            "fiber_g_min": 25,
            "meal_prep_time_max": 30,
            "ingredient_variety_min": 30
        }
    },
    {
        "name": "Weight Loss Female",
        "description": "Calorie-restricted for weight loss",
        "params": {
            "diet": "standard",
            "calories": 1500,
            "pattern": "standard",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "protein_g_min": 60,  # Higher protein for satiety
            "fiber_g_min": 25,
            "portion_satisfaction": True,
            "hunger_management": True
        }
    },
    {
        "name": "Athletic Male Bulk",
        "description": "High calorie for muscle gain",
        "params": {
            "diet": "high_protein",
            "calories": 3500,
            "pattern": "3_plus_2",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "protein_g_min": 175,  # 2g/kg for 87kg person
            "protein_g_max": 280,  # Not excessive
            "meal_timing_appropriate": True,
            "pre_post_workout_meals": True
        }
    },
    
    # Special diets
    {
        "name": "Strict Vegan Balanced",
        "description": "Plant-based with complete nutrition",
        "params": {
            "diet": "vegan",
            "calories": 2000,
            "pattern": "standard",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "b12_supplementation_noted": True,
            "protein_complete": True,
            "iron_adequate": True,
            "no_animal_products": True,
            "calcium_adequate": True
        }
    },
    {
        "name": "Therapeutic Keto",
        "description": "Medical ketogenic diet",
        "params": {
            "diet": "keto",
            "calories": 2000,
            "pattern": "standard",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "net_carbs_max": 20,
            "fat_percent_min": 70,
            "ketone_producing": True,
            "electrolyte_adequate": True
        }
    },
    
    # Common restrictions
    {
        "name": "Gluten-Free Family",
        "description": "Celiac-safe family meals",
        "params": {
            "diet": "standard",
            "calories": 2200,
            "pattern": "standard",
            "days": 7,
            "restrictions": ["gluten"]
        },
        "expectations": {
            "zero_gluten": True,
            "no_cross_contamination_risk": True,
            "grain_alternatives_used": True
        }
    },
    {
        "name": "Dairy-Free Vegetarian",
        "description": "Lactose intolerant vegetarian",
        "params": {
            "diet": "vegetarian",
            "calories": 2000,
            "pattern": "standard",
            "days": 7,
            "restrictions": ["dairy"]
        },
        "expectations": {
            "zero_dairy": True,
            "calcium_from_plants": True,
            "protein_adequate": True
        }
    },
    {
        "name": "Multiple Allergies Child",
        "description": "Child with multiple food allergies",
        "params": {
            "diet": "standard",
            "calories": 1500,
            "pattern": "3_plus_2",
            "days": 7,
            "restrictions": ["nuts", "dairy", "eggs"]
        },
        "expectations": {
            "zero_allergens": True,
            "kid_friendly_meals": True,
            "fun_variety": True,
            "nutrient_dense": True
        }
    },
    
    # Lifestyle patterns
    {
        "name": "Intermittent Fasting Executive",
        "description": "Busy professional doing 16:8 IF",
        "params": {
            "diet": "standard",
            "calories": 2000,
            "pattern": "2_meals",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "eating_window_respected": True,
            "meal_size_appropriate": True,
            "energy_sustained": True
        }
    },
    {
        "name": "Mediterranean Longevity",
        "description": "Heart-healthy Mediterranean diet",
        "params": {
            "diet": "mediterranean",
            "calories": 2000,
            "pattern": "standard",
            "days": 7,
            "restrictions": []
        },
        "expectations": {
            "olive_oil_primary_fat": True,
            "fish_twice_weekly": True,
            "red_meat_limited": True,
            "whole_grains_emphasized": True
        }
    },
    
    # Edge cases that should work
    {
        "name": "Ultra-Low Calorie Medical",
        "description": "Medically supervised very low calorie",
        "params": {
            "diet": "standard",
            "calories": 1200,
            "pattern": "standard",
            "days": 3,
            "restrictions": []
        },
        "expectations": {
            "nutritionally_complete": True,
            "protein_sparing": True,
            "vitamin_adequate": True
        }
    },
    {
        "name": "Vegan Keto Challenge",
        "description": "Most restrictive practical combination",
        "params": {
            "diet": "vegan",
            "calories": 2000,
            "pattern": "standard",
            "days": 3,
            "restrictions": ["gluten"]
        },
        "expectations": {
            "achievable": True,  # Should be possible but limited
            "fat_from_plants": True,
            "protein_adequate": True
        }
    }
]

class ComprehensiveMealTester:
    """Test meal plans from all angles."""
    
    def __init__(self, optimizer):
        self.optimizer = optimizer
        self.results = []
        
    def test_scenario(self, scenario):
        """Run comprehensive tests on a scenario."""
        print(f"\n{'='*70}")
        print(f"Testing: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Parameters: {json.dumps(scenario['params'], indent=2)}")
        print(f"{'='*70}\n")
        
        result = {
            "scenario": scenario['name'],
            "tests": {},
            "issues": [],
            "score": 0
        }
        
        try:
            # Generate meal plan
            start_time = time.time()
            meals, metrics = self.optimizer.generate_single_day_plan({
                'diet': scenario['params']['diet'],
                'calories': scenario['params']['calories'],
                'pattern': scenario['params']['pattern'],
                'restrictions': scenario['params']['restrictions'],
                'cuisines': ['all'],
                'cooking_methods': ['all'],
                'measurement_system': 'US',
                'allow_substitutions': True,
                'timestamp': datetime.now().isoformat()
            })
            generation_time = time.time() - start_time
            
            # If multi-day, generate full week
            if scenario['params']['days'] > 1:
                week_meals = {1: meals}
                for day in range(2, scenario['params']['days'] + 1):
                    day_meals, _ = self.optimizer.generate_single_day_plan({
                        'diet': scenario['params']['diet'],
                        'calories': scenario['params']['calories'],
                        'pattern': scenario['params']['pattern'],
                        'restrictions': scenario['params']['restrictions'],
                        'cuisines': ['all'],
                        'cooking_methods': ['all'],
                        'measurement_system': 'US',
                        'allow_substitutions': True,
                        'timestamp': datetime.now().isoformat()
                    })
                    week_meals[day] = day_meals
            else:
                week_meals = {1: meals}
            
            # Run all tests
            result['tests']['generation'] = self.test_generation_performance(generation_time, metrics)
            result['tests']['nutrition'] = self.test_nutritional_accuracy(week_meals, scenario)
            result['tests']['optimization'] = self.test_optimization_quality(metrics)
            result['tests']['cooking'] = self.test_cooking_feasibility(week_meals)
            result['tests']['reality'] = self.test_real_world_practicality(week_meals, scenario)
            result['tests']['math'] = self.test_mathematical_accuracy(week_meals, scenario['params']['calories'])
            result['tests']['ingredients'] = self.test_ingredient_quality(week_meals)
            result['tests']['portions'] = self.test_portion_sizes(week_meals)
            result['tests']['compliance'] = self.test_diet_compliance(week_meals, scenario)
            result['tests']['cost'] = self.test_cost_analysis(week_meals)
            
            # Calculate overall score
            total_tests = sum(len(test_results) for test_results in result['tests'].values())
            passed_tests = sum(
                sum(1 for r in test_results.values() if r.get('passed', False))
                for test_results in result['tests'].values()
            )
            result['score'] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Collect issues
            for test_category, test_results in result['tests'].items():
                for test_name, test_result in test_results.items():
                    if not test_result.get('passed', False):
                        result['issues'].append(f"{test_category}.{test_name}: {test_result.get('reason', 'Failed')}")
            
        except Exception as e:
            result['error'] = str(e)
            result['score'] = 0
            
        self.results.append(result)
        self._print_test_summary(result)
        return result
    
    def test_generation_performance(self, generation_time, metrics):
        """Test generation performance metrics."""
        tests = {}
        
        # Generation speed
        tests['speed'] = {
            'value': generation_time,
            'passed': generation_time < 2.0,
            'reason': f"Generation took {generation_time:.2f}s"
        }
        
        # Convergence
        tests['convergence'] = {
            'value': metrics.get('final_accuracy', 0),
            'passed': metrics.get('final_accuracy', 0) > 85,
            'reason': f"Final accuracy: {metrics.get('final_accuracy', 0):.1f}%"
        }
        
        # Iterations
        tests['efficiency'] = {
            'value': metrics.get('iterations', 0),
            'passed': metrics.get('iterations', 999) < 25,
            'reason': f"Used {metrics.get('iterations', 0)} iterations"
        }
        
        return tests
    
    def test_nutritional_accuracy(self, week_meals, scenario):
        """Test nutritional accuracy and balance."""
        tests = {}
        
        # Calculate weekly averages
        total_days = len(week_meals)
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        total_fiber = 0
        
        for day_meals in week_meals.values():
            for meal in day_meals.values():
                total_calories += meal.get('calories', 0)
                total_protein += meal.get('protein', 0)
                total_fat += meal.get('fat', 0)
                total_carbs += meal.get('carbs', 0)
                total_fiber += meal.get('fiber', 0) if meal.get('fiber') is not None else 0
        
        avg_calories = total_calories / total_days
        avg_protein = total_protein / total_days
        avg_fat = total_fat / total_days
        avg_carbs = total_carbs / total_days
        avg_fiber = total_fiber / total_days
        
        # Calorie accuracy
        target_calories = scenario['params']['calories']
        calorie_diff = abs(avg_calories - target_calories)
        tests['calorie_accuracy'] = {
            'value': avg_calories,
            'passed': calorie_diff < target_calories * 0.05,  # Within 5%
            'reason': f"Average {avg_calories:.0f} vs target {target_calories}"
        }
        
        # Protein adequacy
        expectations = scenario.get('expectations', {})
        if 'protein_g_min' in expectations:
            tests['protein_minimum'] = {
                'value': avg_protein,
                'passed': avg_protein >= expectations['protein_g_min'],
                'reason': f"Average {avg_protein:.1f}g vs minimum {expectations['protein_g_min']}g"
            }
        
        if 'protein_g_max' in expectations:
            tests['protein_maximum'] = {
                'value': avg_protein,
                'passed': avg_protein <= expectations['protein_g_max'],
                'reason': f"Average {avg_protein:.1f}g vs maximum {expectations['protein_g_max']}g"
            }
        
        # Fiber adequacy
        if 'fiber_g_min' in expectations:
            tests['fiber_minimum'] = {
                'value': avg_fiber,
                'passed': avg_fiber >= expectations['fiber_g_min'],
                'reason': f"Average {avg_fiber:.1f}g vs minimum {expectations['fiber_g_min']}g"
            }
        
        # Macro balance
        if avg_calories > 0:
            protein_pct = (avg_protein * 4) / avg_calories * 100
            carbs_pct = (avg_carbs * 4) / avg_calories * 100
            fat_pct = (avg_fat * 9) / avg_calories * 100
            
            tests['macro_balance'] = {
                'value': {'protein': protein_pct, 'carbs': carbs_pct, 'fat': fat_pct},
                'passed': abs(protein_pct + carbs_pct + fat_pct - 100) < 5,
                'reason': f"P:{protein_pct:.1f}% C:{carbs_pct:.1f}% F:{fat_pct:.1f}%"
            }
            
            # Diet-specific macro checks
            if scenario['params']['diet'] == 'keto':
                tests['keto_macros'] = {
                    'value': carbs_pct,
                    'passed': carbs_pct < 10 and fat_pct > 65,
                    'reason': f"Carbs {carbs_pct:.1f}% (need <10%), Fat {fat_pct:.1f}% (need >65%)"
                }
        
        return tests
    
    def test_optimization_quality(self, metrics):
        """Test optimization algorithm quality."""
        tests = {}
        
        # Constraint satisfaction
        tests['constraints_checked'] = {
            'value': metrics.get('constraints_checked', 0),
            'passed': metrics.get('constraints_checked', 0) > 0,
            'reason': f"Checked {metrics.get('constraints_checked', 0)} constraints"
        }
        
        # Template evaluation
        tests['templates_evaluated'] = {
            'value': metrics.get('templates_evaluated', 0),
            'passed': metrics.get('templates_evaluated', 0) > 10,
            'reason': f"Evaluated {metrics.get('templates_evaluated', 0)} templates"
        }
        
        # Substitutions
        if metrics.get('substitutions_made', 0) > 0:
            tests['substitutions'] = {
                'value': metrics.get('substitutions_made', 0),
                'passed': True,
                'reason': f"Made {metrics.get('substitutions_made', 0)} substitutions"
            }
        
        return tests
    
    def test_cooking_feasibility(self, week_meals):
        """Test cooking method feasibility and time."""
        tests = {}
        
        total_prep_time = 0
        cooking_methods = defaultdict(int)
        meal_count = 0
        
        for day_meals in week_meals.values():
            for meal in day_meals.values():
                prep_time = meal.get('prep_time', 15)
                total_prep_time += prep_time
                cooking_methods[meal.get('cooking_method', 'none')] += 1
                meal_count += 1
        
        avg_prep_time = total_prep_time / meal_count if meal_count > 0 else 0
        
        # Average prep time
        tests['avg_prep_time'] = {
            'value': avg_prep_time,
            'passed': avg_prep_time <= 30,
            'reason': f"Average prep time: {avg_prep_time:.0f} minutes"
        }
        
        # Cooking method variety
        tests['cooking_variety'] = {
            'value': len(cooking_methods),
            'passed': len(cooking_methods) >= 3,
            'reason': f"Uses {len(cooking_methods)} different cooking methods"
        }
        
        # No excessive frying
        fried_meals = cooking_methods.get('deep_fried', 0) + cooking_methods.get('pan_fried', 0)
        tests['healthy_cooking'] = {
            'value': fried_meals,
            'passed': fried_meals < meal_count * 0.3,  # Less than 30% fried
            'reason': f"{fried_meals}/{meal_count} meals are fried"
        }
        
        return tests
    
    def test_real_world_practicality(self, week_meals, scenario):
        """Test real-world practicality."""
        tests = {}
        
        # Ingredient availability
        all_ingredients = set()
        exotic_ingredients = []
        shopping_trips = 0
        
        for day_meals in week_meals.values():
            daily_ingredients = set()
            for meal in day_meals.values():
                for ing in meal.get('ingredients', []):
                    if isinstance(ing, dict):
                        item = ing.get('item', '')
                        all_ingredients.add(item)
                        daily_ingredients.add(item)
                        
                        # Check for exotic ingredients
                        exotic = ['dragon_fruit', 'durian', 'saffron', 'truffle', 'caviar']
                        if any(e in item.lower() for e in exotic):
                            exotic_ingredients.append(item)
            
            # Assume shopping for fresh ingredients every 3 days
            if len(daily_ingredients) > 0:
                shopping_trips += 1
        
        tests['ingredient_availability'] = {
            'value': len(exotic_ingredients),
            'passed': len(exotic_ingredients) == 0,
            'reason': f"Found {len(exotic_ingredients)} exotic ingredients"
        }
        
        # Shopping frequency
        tests['shopping_practical'] = {
            'value': shopping_trips,
            'passed': shopping_trips <= len(week_meals) / 3,
            'reason': f"Requires {shopping_trips} shopping trips for {len(week_meals)} days"
        }
        
        # Meal complexity
        complex_meals = 0
        for day_meals in week_meals.values():
            for meal in day_meals.values():
                if len(meal.get('ingredients', [])) > 10:
                    complex_meals += 1
        
        tests['meal_complexity'] = {
            'value': complex_meals,
            'passed': complex_meals < len(week_meals) * 0.2,  # Less than 20% complex
            'reason': f"{complex_meals} overly complex meals"
        }
        
        return tests
    
    def test_mathematical_accuracy(self, week_meals, target_calories):
        """Test mathematical calculations."""
        tests = {}
        
        # Daily calorie totals
        daily_calories = []
        calculation_errors = []
        
        for day, day_meals in week_meals.items():
            day_total = 0
            day_calculated = 0
            
            for meal_name, meal in day_meals.items():
                meal_calories = meal.get('calories', 0)
                day_total += meal_calories
                
                # Recalculate from ingredients
                calculated_calories = 0
                for ing in meal.get('ingredients', []):
                    if isinstance(ing, dict):
                        item = ing.get('item', '')
                        amount = ing.get('amount', 0)
                        unit = ing.get('unit', 'g')
                        
                        # Convert to grams if needed
                        if unit == 'g':
                            grams = amount
                        elif unit == 'ml':
                            grams = amount  # Assume 1ml = 1g for simplicity
                        else:
                            # Use conversion if available
                            grams = amount * 100  # Rough estimate
                        
                        # Get nutrition data
                        if item in nd.INGREDIENTS:
                            cal_per_100g = nd.INGREDIENTS[item].get('calories', 0)
                            calculated_calories += (grams / 100) * cal_per_100g
                
                day_calculated += calculated_calories
                
                # Check calculation accuracy
                if calculated_calories > 0:
                    calc_diff = abs(meal_calories - calculated_calories) / calculated_calories
                    if calc_diff > 0.1:  # More than 10% difference
                        calculation_errors.append({
                            'meal': meal_name,
                            'stated': meal_calories,
                            'calculated': calculated_calories
                        })
            
            daily_calories.append(day_total)
        
        # Daily consistency
        if daily_calories:
            avg_daily = sum(daily_calories) / len(daily_calories)
            max_deviation = max(abs(dc - avg_daily) for dc in daily_calories)
            
            tests['daily_consistency'] = {
                'value': max_deviation,
                'passed': max_deviation < target_calories * 0.1,  # Within 10%
                'reason': f"Max daily deviation: {max_deviation:.0f} calories"
            }
        
        # Calculation accuracy
        tests['calculation_accuracy'] = {
            'value': len(calculation_errors),
            'passed': len(calculation_errors) == 0,
            'reason': f"{len(calculation_errors)} calculation errors found"
        }
        
        # Rounding errors
        has_excessive_decimals = False
        for day_meals in week_meals.values():
            for meal in day_meals.values():
                if len(str(meal.get('calories', 0)).split('.')[-1]) > 2:
                    has_excessive_decimals = True
                    break
        
        tests['rounding_appropriate'] = {
            'value': has_excessive_decimals,
            'passed': not has_excessive_decimals,
            'reason': "Calorie values properly rounded"
        }
        
        return tests
    
    def test_ingredient_quality(self, week_meals):
        """Test ingredient quality and variety."""
        tests = {}
        
        # Collect all ingredients
        all_ingredients = defaultdict(float)
        ingredient_days = defaultdict(set)
        processed_foods = []
        whole_foods = []
        
        for day, day_meals in week_meals.items():
            for meal in day_meals.values():
                for ing in meal.get('ingredients', []):
                    if isinstance(ing, dict):
                        item = ing.get('item', '')
                        amount = ing.get('amount', 0)
                        all_ingredients[item] += amount
                        ingredient_days[item].add(day)
                        
                        # Categorize ingredients
                        processed = ['sausage', 'bacon', 'deli', 'chip', 'cookie', 'soda']
                        if any(p in item.lower() for p in processed):
                            processed_foods.append(item)
                        else:
                            whole_foods.append(item)
        
        # Variety score
        tests['ingredient_variety'] = {
            'value': len(all_ingredients),
            'passed': len(all_ingredients) >= 20,
            'reason': f"Uses {len(all_ingredients)} different ingredients"
        }
        
        # Processed vs whole foods
        if len(processed_foods) + len(whole_foods) > 0:
            processed_ratio = len(processed_foods) / (len(processed_foods) + len(whole_foods))
            tests['whole_foods_emphasis'] = {
                'value': processed_ratio,
                'passed': processed_ratio < 0.2,  # Less than 20% processed
                'reason': f"{processed_ratio*100:.0f}% processed foods"
            }
        
        # Ingredient rotation
        overused = []
        for item, days in ingredient_days.items():
            if len(days) > len(week_meals) * 0.7:  # Used more than 70% of days
                overused.append(item)
        
        tests['ingredient_rotation'] = {
            'value': len(overused),
            'passed': len(overused) < 5,
            'reason': f"{len(overused)} ingredients overused"
        }
        
        return tests
    
    def test_portion_sizes(self, week_meals):
        """Test portion size appropriateness."""
        tests = {}
        
        extreme_portions = []
        tiny_portions = []
        
        for day_meals in week_meals.values():
            for meal_name, meal in day_meals.values():
                meal_total_g = 0
                
                for ing in meal.get('ingredients', []):
                    if isinstance(ing, dict):
                        amount = ing.get('amount', 0)
                        unit = ing.get('unit', 'g')
                        item = ing.get('item', '')
                        
                        # Convert to grams
                        if unit == 'g':
                            grams = amount
                        elif unit == 'ml':
                            grams = amount * 0.9  # Rough density
                        else:
                            grams = amount * 100  # Rough estimate
                        
                        meal_total_g += grams
                        
                        # Check individual portions
                        if grams > 500:  # More than 500g of one ingredient
                            extreme_portions.append(f"{amount}{unit} {item}")
                        elif grams < 5 and unit == 'g':  # Less than 5g
                            tiny_portions.append(f"{amount}{unit} {item}")
                
                # Check total meal size
                if meal_name in ['breakfast', 'lunch', 'dinner']:
                    if meal_total_g > 1000:  # More than 1kg
                        extreme_portions.append(f"{meal_name}: {meal_total_g:.0f}g total")
                    elif meal_total_g < 200:  # Less than 200g
                        tiny_portions.append(f"{meal_name}: {meal_total_g:.0f}g total")
        
        tests['portion_sizes_reasonable'] = {
            'value': len(extreme_portions),
            'passed': len(extreme_portions) == 0,
            'reason': f"{len(extreme_portions)} extreme portions found"
        }
        
        tests['portion_sizes_adequate'] = {
            'value': len(tiny_portions),
            'passed': len(tiny_portions) < 5,  # Allow some small portions (spices, etc)
            'reason': f"{len(tiny_portions)} tiny portions found"
        }
        
        return tests
    
    def test_diet_compliance(self, week_meals, scenario):
        """Test diet compliance thoroughly."""
        tests = {}
        
        diet = scenario['params']['diet']
        restrictions = scenario['params']['restrictions']
        violations = []
        
        for day_meals in week_meals.values():
            for meal in day_meals.values():
                # Check diet compliance
                is_compliant, meal_violations = self.optimizer.validate_diet_compliance(meal, diet)
                violations.extend(meal_violations)
                
                # Check restrictions
                for restriction in restrictions:
                    if restriction in nd.ALLERGEN_MAPPING:
                        banned = nd.ALLERGEN_MAPPING[restriction]
                        for ing in meal.get('ingredients', []):
                            if isinstance(ing, dict):
                                item = ing.get('item', '')
                                if item in banned:
                                    violations.append(f"{item} violates {restriction} restriction")
        
        tests['diet_compliance'] = {
            'value': len(violations),
            'passed': len(violations) == 0,
            'reason': f"{len(violations)} compliance violations"
        }
        
        # Diet-specific checks
        expectations = scenario.get('expectations', {})
        
        if diet == 'vegan' and 'no_animal_products' in expectations:
            tests['vegan_strict'] = {
                'value': len(violations),
                'passed': len(violations) == 0,
                'reason': "All animal products excluded"
            }
        
        if diet == 'keto' and 'net_carbs_max' in expectations:
            total_net_carbs = 0
            for day_meals in week_meals.values():
                for meal in day_meals.values():
                    carbs = meal.get('carbs', 0)
                    fiber = meal.get('fiber', 0) or 0
                    total_net_carbs += (carbs - fiber)
            
            avg_net_carbs = total_net_carbs / len(week_meals)
            tests['keto_net_carbs'] = {
                'value': avg_net_carbs,
                'passed': avg_net_carbs <= expectations['net_carbs_max'],
                'reason': f"Average net carbs: {avg_net_carbs:.1f}g"
            }
        
        return tests
    
    def test_cost_analysis(self, week_meals):
        """Test cost estimates."""
        tests = {}
        
        # Rough cost estimates per 100g
        cost_estimates = {
            'chicken_breast': 0.8,
            'salmon': 2.5,
            'beef': 1.5,
            'eggs': 0.3,
            'vegetables': 0.4,  # Average
            'fruits': 0.5,
            'grains': 0.2,
            'nuts': 1.5,
            'oils': 0.3
        }
        
        total_cost = 0
        meal_costs = []
        
        for day_meals in week_meals.values():
            day_cost = 0
            for meal in day_meals.values():
                meal_cost = 0
                for ing in meal.get('ingredients', []):
                    if isinstance(ing, dict):
                        item = ing.get('item', '')
                        amount = ing.get('amount', 0)
                        unit = ing.get('unit', 'g')
                        
                        # Convert to grams
                        if unit == 'g':
                            grams = amount
                        elif unit == 'ml':
                            grams = amount
                        else:
                            grams = amount * 100
                        
                        # Estimate cost
                        item_cost = 0.4  # Default
                        for category, cost in cost_estimates.items():
                            if category in item.lower():
                                item_cost = cost
                                break
                        
                        meal_cost += (grams / 100) * item_cost
                
                meal_costs.append(meal_cost)
                day_cost += meal_cost
            total_cost += day_cost
        
        avg_daily_cost = total_cost / len(week_meals) if week_meals else 0
        
        tests['daily_cost_reasonable'] = {
            'value': avg_daily_cost,
            'passed': avg_daily_cost < 15,  # Less than $15/day
            'reason': f"Average daily cost: ${avg_daily_cost:.2f}"
        }
        
        # Cost variance
        if meal_costs:
            max_meal_cost = max(meal_costs)
            min_meal_cost = min(meal_costs)
            cost_variance = max_meal_cost - min_meal_cost
            
            tests['cost_balance'] = {
                'value': cost_variance,
                'passed': cost_variance < 10,  # Less than $10 difference
                'reason': f"Meal cost variance: ${cost_variance:.2f}"
            }
        
        return tests
    
    def _print_test_summary(self, result):
        """Print test summary for a scenario."""
        print(f"\nTest Results for: {result['scenario']}")
        print(f"Overall Score: {result['score']:.1f}%")
        
        if 'error' in result:
            print(f"ERROR: {result['error']}")
            return
        
        print("\nTest Categories:")
        for category, tests in result['tests'].items():
            passed = sum(1 for t in tests.values() if t.get('passed', False))
            total = len(tests)
            print(f"  {category}: {passed}/{total} passed")
            
            for test_name, test_result in tests.items():
                status = "PASS" if test_result.get('passed', False) else "FAIL"
                print(f"    {status} {test_name}: {test_result.get('reason', 'N/A')}")
        
        if result['issues']:
            print(f"\nTop Issues ({len(result['issues'])} total):")
            for issue in result['issues'][:5]:
                print(f"  - {issue}")
    
    def generate_report(self):
        """Generate comprehensive report."""
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST REPORT")
        print("="*70)
        
        # Overall statistics
        total_scenarios = len(self.results)
        passed_scenarios = sum(1 for r in self.results if r['score'] >= 80)
        
        print(f"\nScenarios Tested: {total_scenarios}")
        print(f"Passed (>=80%): {passed_scenarios}")
        print(f"Success Rate: {passed_scenarios/total_scenarios*100:.1f}%")
        
        # Category analysis
        category_scores = defaultdict(list)
        for result in self.results:
            if 'tests' in result:
                for category, tests in result['tests'].items():
                    passed = sum(1 for t in tests.values() if t.get('passed', False))
                    total = len(tests)
                    if total > 0:
                        category_scores[category].append(passed / total * 100)
        
        print("\nCategory Performance:")
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            print(f"  {category}: {avg_score:.1f}% average")
        
        # Common issues
        all_issues = []
        for result in self.results:
            all_issues.extend(result.get('issues', []))
        
        issue_counts = defaultdict(int)
        for issue in all_issues:
            issue_type = issue.split(':')[0]
            issue_counts[issue_type] += 1
        
        print("\nMost Common Issues:")
        for issue_type, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {issue_type}: {count} occurrences")
        
        # Best and worst scenarios
        sorted_results = sorted(self.results, key=lambda x: x['score'], reverse=True)
        
        print("\nBest Performing Scenarios:")
        for result in sorted_results[:3]:
            print(f"  {result['scenario']}: {result['score']:.1f}%")
        
        print("\nWorst Performing Scenarios:")
        for result in sorted_results[-3:]:
            print(f"  {result['scenario']}: {result['score']:.1f}%")

# Run the tests
app = create_app()

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    tester = ComprehensiveMealTester(optimizer)
    
    # Test all critical scenarios
    for scenario in CRITICAL_SCENARIOS:
        tester.test_scenario(scenario)
    
    # Generate final report
    tester.generate_report()
    
    # Save results
    with open('critical_permutation_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'scenarios_tested': len(CRITICAL_SCENARIOS),
            'results': tester.results
        }, f, indent=2)
    
    print("\n\nResults saved to critical_permutation_results.json")

print("\n=== END OF CRITICAL PERMUTATION TESTING ===")