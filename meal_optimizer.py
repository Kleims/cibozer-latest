# meal_optimizer.py - Updated to support Cibozer video generation

import json
import random
import math
import sys
import os
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set
import nutrition_data as nd

class MealPlanOptimizer:
    def __init__(self, cuisine_preferences: List[str] = None, cooking_preferences: List[str] = None):
        """Initialize with enhanced global cuisine support"""
        self.ingredients = nd.INGREDIENTS
        self.diet_profiles = nd.DIET_PROFILES
        self.meal_patterns = nd.MEAL_PATTERNS
        self.templates = nd.MEAL_TEMPLATES
        self.conversions = nd.CONVERSIONS
        self.specific_conversions = nd.INGREDIENT_SPECIFIC_CONVERSIONS
        self.allergen_mapping = nd.ALLERGEN_MAPPING
        
        # Enhanced features
        self.cooking_methods = nd.COOKING_METHODS
        self.substitutions = nd.SUBSTITUTIONS
        self.cuisine_compatibility = nd.CUISINE_DIET_COMPATIBILITY
        self.nutrient_retention = nd.NUTRIENT_RETENTION
        self.regional_measurements = nd.REGIONAL_MEASUREMENTS
        
        # User preferences
        self.cuisine_preferences = cuisine_preferences or ["all"]
        self.cooking_preferences = cooking_preferences or ["all"]
        self.substitution_enabled = True
        
        # Cooking factors (extended)
        self.cooking_factors = {
            'chicken_breast': 0.75,
            'ground_beef': 0.80,
            'salmon': 0.85,
            'pasta': 2.5,
            'rice': 2.8,
            'quinoa': 2.2,
            'tofu': 0.85,
            'tempeh': 0.90,
            'plantain': 0.95,
            'yucca': 0.90,
        }
        
        # Maximum shopping amounts (extended)
        self.max_shopping_amounts = {
            'lettuce': 1000,
            'milk': 2000,
            'eggs': 1000,
            'chicken_breast': 3000,
            'olive_oil': 500,
            'coconut_milk': 1000,
            'rice': 5000,
            'beans': 2000,
        }
        
        # Enhanced optimization parameters
        self.ACCURACY_TARGET = 0.95
        self.MAX_ITERATIONS = 25  # Increased for better convergence
        self.CALORIE_TOLERANCE = 50
        self.MACRO_TOLERANCE = 3
        self.CUISINE_VARIETY_WEIGHT = 0.15  # Bonus for cuisine variety
        
        # Tracking for Cibozer
        self.optimization_steps = []
        self.convergence_history = []
        self.algorithm_metrics = {
            'iterations': 0,
            'constraints_checked': 0,
            'templates_evaluated': 0,
            'substitutions_made': 0,
            'optimization_time': 0,
            'final_accuracy': 0
        }
    
    def generate_single_day_plan(self, preferences: Dict) -> Tuple[Dict, Dict]:
        """Generate a single day meal plan for Cibozer videos"""
        import time
        start_time = time.time()
        
        # Reset tracking
        self.optimization_steps = []
        self.convergence_history = []
        self.algorithm_metrics = {
            'iterations': 0,
            'constraints_checked': 0,
            'templates_evaluated': 0,
            'substitutions_made': 0,
            'optimization_time': 0,
            'final_accuracy': 0
        }
        
        # Generate day meals
        meal_history = {}
        day_meals = self.generate_day_meals_enhanced(preferences, meal_history, 1)
        
        # Track convergence
        self._track_convergence(day_meals, preferences)
        
        # Optimize
        day_meals = self.optimize_day_final(day_meals, preferences)
        self._track_convergence(day_meals, preferences)
        
        # Final rebalancing
        day_meals = self.rebalance_day_nutrients(day_meals, preferences)
        self._track_convergence(day_meals, preferences)
        
        # Calculate final metrics
        totals = self.calculate_day_totals(day_meals)
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        final_score = self.calculate_nutrition_score(totals, preferences['calories'], target_macros)
        
        self.algorithm_metrics['optimization_time'] = time.time() - start_time
        self.algorithm_metrics['final_accuracy'] = final_score
        
        return day_meals, self.algorithm_metrics
    
    def generate_day_with_tracking(self, preferences: Dict) -> Dict:
        """Generate a single day meal plan with optimization tracking for Cibozer"""
        import time
        start_time = time.time()
        
        # Reset tracking
        self.optimization_steps = []
        self.convergence_history = []
        self.algorithm_metrics = {
            'iterations': 0,
            'constraints_checked': 0,
            'templates_evaluated': 0,
            'substitutions_made': 0,
            'optimization_time': 0,
            'final_accuracy': 0
        }
        
        # Add tracking step
        self.optimization_steps.append({
            'code': """optimizer = MealPlanOptimizer()
preferences = convert_params(params)
optimizer.set_constraints(preferences)""",
            'accuracy': 0,
            'iterations': 0
        })
        
        # Generate day meals
        meal_history = {}
        day_meals = self.generate_day_meals_enhanced(preferences, meal_history, 1)
        
        # Track convergence
        self._track_convergence(day_meals, preferences)
        
        # Add optimization step
        self.optimization_steps.append({
            'code': "day_meals = optimizer.generate_meals(preferences)",
            'accuracy': self.convergence_history[-1] if self.convergence_history else 0,
            'iterations': self.algorithm_metrics['iterations']
        })
        
        # Optimize
        day_meals = self.optimize_day_final(day_meals, preferences)
        self._track_convergence(day_meals, preferences)
        
        # Add optimization step
        self.optimization_steps.append({
            'code': "day_meals = optimizer.optimize_day_final(day_meals, preferences)",
            'accuracy': self.convergence_history[-1] if self.convergence_history else 0,
            'iterations': self.algorithm_metrics['iterations']
        })
        
        # Final rebalancing
        day_meals = self.rebalance_day_nutrients(day_meals, preferences)
        self._track_convergence(day_meals, preferences)
        
        # Add final step
        self.optimization_steps.append({
            'code': "day_meals = optimizer.rebalance_nutrients(day_meals)",
            'accuracy': self.convergence_history[-1] if self.convergence_history else 0,
            'iterations': self.algorithm_metrics['iterations']
        })
        
        # Calculate final metrics
        totals = self.calculate_day_totals(day_meals)
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        final_score = self.calculate_nutrition_score(totals, preferences['calories'], target_macros)
        
        self.algorithm_metrics['optimization_time'] = time.time() - start_time
        self.algorithm_metrics['final_accuracy'] = final_score
        self.algorithm_metrics['total_iterations'] = self.algorithm_metrics['iterations']
        self.algorithm_metrics['time_seconds'] = time.time() - start_time
        
        # Final tracking step
        self.optimization_steps.append({
            'code': "# Optimization complete!",
            'accuracy': final_score,
            'iterations': self.algorithm_metrics['iterations']
        })
        
        return {
            'meals': day_meals,
            'totals': totals,
            'steps': self.optimization_steps,
            'final_accuracy': final_score,
            'total_iterations': self.algorithm_metrics['iterations'],
            'time_seconds': self.algorithm_metrics['optimization_time'],
            'constraints_satisfied': 'ALL' if final_score >= 95 else 'PARTIAL'
        }
    
    def get_optimization_steps(self) -> List[Dict]:
        """Return optimization steps for animation"""
        return self.optimization_steps
    
    def get_convergence_history(self) -> List[float]:
        """Return convergence history for visualization"""
        return self.convergence_history
    
    def get_algorithm_metrics(self) -> Dict:
        """Return algorithm performance metrics"""
        return self.algorithm_metrics
    
    def _track_convergence(self, day_meals: Dict, preferences: Dict):
        """Track convergence for visualization"""
        totals = self.calculate_day_totals(day_meals)
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        score = self.calculate_nutrition_score(totals, preferences['calories'], target_macros)
        self.convergence_history.append(score)
        self.algorithm_metrics['iterations'] += 1
    
    def _log_optimization_step(self, step_name: str, details: str):
        """Log optimization step for visualization"""
        self.optimization_steps.append({
            'step': step_name,
            'details': details,
            'iteration': self.algorithm_metrics['iterations']
        })
    
    def get_cibozer_format(self, day_meals: Dict, totals: Dict) -> Dict:
        """Convert meal plan to Cibozer expected format"""
        return {
            'meals': day_meals,
            'macros': {
                'Protein': totals['protein'],
                'Carbs': totals['carbs'],
                'Fat': totals['fat']
            },
            'total_protein': totals['protein'],
            'total_calories': totals['calories']
        }
    
    # Add support for high_protein diet profile
    def _add_high_protein_profile(self):
        """Add high protein diet profile if not exists"""
        if "high_protein" not in self.diet_profiles:
            self.diet_profiles["high_protein"] = {
                "name": "High Protein",
                "macros": {"protein": 40, "fat": 30, "carbs": 30},
                "rules": {"min_protein_per_meal": 30},
                "meal_tags": ["standard", "carnivore"],
                "description": "Optimized for muscle building and satiety",
                "daily_fiber_min": 25,
                "daily_protein_min": 150
            }
    
    def get_user_preferences_enhanced(self) -> Dict:
        """Enhanced preference gathering with cuisine and cooking method options"""
        try:
            print("\n" + "="*60)
            print("🍽️  GLOBAL CUISINE MEAL PLAN OPTIMIZER v4.0")
            print("="*60 + "\n")
            
            # Check for saved preferences
            if os.path.exists('saved_preferences_v4.json'):
                if input("Load previous preferences? (y/n): ").lower() == 'y':
                    with open('saved_preferences_v4.json', 'r') as f:
                        return json.load(f)
            
            # Diet selection (same as before)
            print("📋 SELECT DIET TYPE:")
            print("-" * 30)
            diets = list(self.diet_profiles.keys())
            for i, diet in enumerate(diets, 1):
                profile = self.diet_profiles[diet]
                print(f"[{i}] {profile['name']}")
                print(f"    {profile['description']}")
            
            diet_choice = self._get_choice("diet", diets)
            
            # Cuisine preferences (NEW)
            print("\n\n🌍 SELECT CUISINE PREFERENCES:")
            print("-" * 30)
            cuisines = ["All Cuisines", "Asian", "Latin American", "Mediterranean", 
                       "Middle Eastern", "African", "European", "American", "Mixed"]
            
            for i, cuisine in enumerate(cuisines, 1):
                print(f"[{i}] {cuisine}")
            
            print("\nSelect multiple (comma-separated) or 0 for all:")
            cuisine_input = input("Your choices: ").strip()
            
            if cuisine_input == "0" or cuisine_input == "":
                cuisine_choices = ["all"]
            else:
                cuisine_indices = [int(x.strip()) for x in cuisine_input.split(",")]
                cuisine_choices = [cuisines[i-1].lower().replace(" ", "_") 
                                  for i in cuisine_indices if 1 <= i <= len(cuisines)]
            
            # Cooking method preferences (NEW)
            print("\n\n👨‍🍳 PREFERRED COOKING METHODS:")
            print("-" * 30)
            methods = ["All Methods", "Grilled", "Baked", "Steamed", "Stir-fried", 
                      "Slow-cooked", "Raw", "Pan-fried", "Roasted"]
            
            for i, method in enumerate(methods, 1):
                print(f"[{i}] {method}")
            
            print("\nSelect multiple (comma-separated) or 0 for all:")
            method_input = input("Your choices: ").strip()
            
            if method_input == "0" or method_input == "":
                cooking_methods = ["all"]
            else:
                method_indices = [int(x.strip()) for x in method_input.split(",")]
                cooking_methods = [methods[i-1].lower().replace(" ", "_").replace("-", "_")
                                 for i in method_indices if 1 <= i <= len(methods)]
            
            # Meal pattern selection
            print("\n\n⏰ SELECT MEAL PATTERN:")
            print("-" * 30)
            patterns = list(self.meal_patterns.keys())
            for i, pattern in enumerate(patterns, 1):
                print(f"[{i}] {self.meal_patterns[pattern]['name']}")
            
            pattern_choice = self._get_choice("pattern", patterns)
            
            # Restrictions
            print("\n\n🚫 DIETARY RESTRICTIONS:")
            print("-" * 30)
            restrictions = self._get_restrictions()
            
            # Calorie target
            print("\n\n🎯 CALORIE TARGET:")
            print("-" * 30)
            calories = self._get_calorie_target()
            
            # Measurement preference (NEW)
            print("\n\n📏 MEASUREMENT PREFERENCE:")
            print("-" * 30)
            regions = list(self.regional_measurements.keys())
            for i, region in enumerate(regions, 1):
                print(f"[{i}] {region} ({', '.join(self.regional_measurements[region][:3])}...)")
            
            measurement_choice = regions[self._get_choice("measurement", regions, raw=True) - 1]
            
            # Substitution preference (NEW)
            allow_substitutions = input("\n\nAllow intelligent ingredient substitutions? (y/n): ").lower() == 'y'
            
            # Summary
            print("\n\n✅ CONFIGURATION SUMMARY:")
            print("-" * 30)
            print(f"Diet: {self.diet_profiles[diet_choice]['name']}")
            print(f"Cuisines: {', '.join(cuisine_choices)}")
            print(f"Cooking Methods: {', '.join(cooking_methods)}")
            print(f"Meal Pattern: {self.meal_patterns[pattern_choice]['name']}")
            print(f"Restrictions: {', '.join(restrictions) if restrictions else 'None'}")
            print(f"Daily Calories: {calories}")
            print(f"Measurements: {measurement_choice}")
            print(f"Allow Substitutions: {'Yes' if allow_substitutions else 'No'}")
            
            if input("\nProceed with these settings? (y/n): ").lower() != 'y':
                return self.get_user_preferences_enhanced()
            
            preferences = {
                'diet': diet_choice,
                'cuisines': cuisine_choices,
                'cooking_methods': cooking_methods,
                'pattern': pattern_choice,
                'restrictions': restrictions,
                'calories': calories,
                'measurement_system': measurement_choice,
                'allow_substitutions': allow_substitutions,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save preferences
            if input("\nSave these preferences for next time? (y/n): ").lower() == 'y':
                with open('saved_preferences_v4.json', 'w') as f:
                    json.dump(preferences, f, indent=2)
            
            return preferences
            
        except Exception as e:
            print(f"\n❌ Error during setup: {e}")
            print("Starting over...")
            return self.get_user_preferences_enhanced()
    
    def get_test_preferences(self) -> Dict:
        """Get test preferences for quick testing"""
        return {
            'diet': 'standard',
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'pattern': 'standard',
            'restrictions': [],
            'calories': 2000,
            'measurement_system': 'US',
            'allow_substitutions': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_meal_plan_for_preferences(self, preferences: Dict) -> Dict:
        """Generate a meal plan for given preferences"""
        print(f"\n📊 Generating meal plan for {preferences['calories']} calories, {preferences['diet']} diet...")
        
        # Initialize meal history
        meal_history = {}
        
        # Generate Week 1
        week1 = self.generate_week_plan_enhanced(preferences, 1, meal_history)
        
        # Generate Week 2
        week2 = self.generate_week_plan_enhanced(preferences, 2, meal_history)
        
        # Validate both weeks
        val1 = self.validate_meal_plan(week1, preferences)
        val2 = self.validate_meal_plan(week2, preferences)
        
        return {
            'preferences': preferences,
            'week1': week1,
            'week2': week2,
            'validation': {
                'week1': val1,
                'week2': val2
            }
        }
    
    def generate_batch_meal_plans(self):
        """Generate meal plans for most common permutations only"""
        import glob
        
        # Create output directory
        os.makedirs("meal_plans", exist_ok=True)
        
        # Define MOST COMMON options only
        calorie_options = [1800, 2000, 2200, 2500]  # Most common calorie targets
        diet_options = ['standard', 'keto', 'vegan']  # Top 3 diets
        cuisine_options = ["all"]  # Keep it simple for now
        pattern_options = ['standard', '16_8_if']  # Two most popular patterns
        
        total_permutations = len(calorie_options) * len(diet_options) * len(cuisine_options) * len(pattern_options)
        
        print(f"\nTotal permutations to generate: {total_permutations}")
        print("This includes the most popular configurations:")
        print(f"  • Calories: {calorie_options}")
        print(f"  • Diets: {diet_options}")
        print(f"  • Patterns: {pattern_options}")
        
        generated = 0
        failed = 0
        
        for calories in calorie_options:
            for diet in diet_options:
                for cuisine in cuisine_options:
                    for pattern in pattern_options:
                        generated += 1
                        
                        # Create filename
                        filename = f"meal_plans/plan_{calories}cal_{diet}_{cuisine}_{pattern}.json"
                        
                        # Skip if already exists
                        if os.path.exists(filename):
                            print(f"  [{generated}/{total_permutations}] Skipping existing: {filename}")
                            continue
                        
                        # Create preferences
                        preferences = {
                            'diet': diet,
                            'cuisines': [cuisine],
                            'cooking_methods': ['all'],
                            'pattern': pattern,
                            'restrictions': [],
                            'calories': calories,
                            'measurement_system': 'US',
                            'allow_substitutions': True,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        try:
                            # Generate meal plan
                            meal_plan = self.generate_meal_plan_for_preferences(preferences)
                            
                            # Save to file
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(meal_plan, f, indent=2, ensure_ascii=False)
                            
                            # Get validation scores
                            avg_score = (meal_plan['validation']['week1']['overall_score'] + 
                                       meal_plan['validation']['week2']['overall_score']) / 2
                            
                            print(f"  [{generated}/{total_permutations}] ✅ Generated: {calories}cal {diet} {cuisine} {pattern} - Score: {avg_score:.1f}%")
                            
                        except Exception as e:
                            failed += 1
                            print(f"  [{generated}/{total_permutations}] ❌ Failed: {calories}cal {diet} {cuisine} {pattern} - Error: {e}")
        
        print(f"\n✅ Batch generation complete!")
        print(f"   Total generated: {generated - failed}")
        print(f"   Failed: {failed}")
        print(f"   Files saved in: meal_plans/")
    
    def _get_choice(self, choice_type: str, options: List[str], raw: bool = False) -> any:
        """Helper to get user choice with validation"""
        while True:
            try:
                choice = int(input(f"\nEnter {choice_type} choice (1-{len(options)}): "))
                if 1 <= choice <= len(options):
                    return choice if raw else options[choice - 1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
    
    def _get_restrictions(self) -> List[str]:
        """Get dietary restrictions from user"""
        restrictions = []
        if input("Do you have any allergies or restrictions? (y/n): ").lower() == 'y':
            print("\nSelect all that apply (enter numbers separated by commas):")
            restriction_options = [
                "Nuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Soy",
                "Sesame", "Fish", "Nightshades", "Legumes"
            ]
            
            for i, r in enumerate(restriction_options, 1):
                print(f"[{i}] {r}")
            
            choices = input("\nYour restrictions (e.g., 1,3,5): ").split(',')
            for choice in choices:
                try:
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(restriction_options):
                        restrictions.append(restriction_options[idx].lower())
                except ValueError:
                    pass
        
        return restrictions
    
    def _get_calorie_target(self) -> int:
        """Get calorie target from user"""
        while True:
            try:
                calories_input = input("Enter daily calorie target (default 2000): ").strip()
                calories = int(calories_input) if calories_input else 2000
                if 1200 <= calories <= 4000:
                    return calories
                else:
                    print("Please enter a value between 1200 and 4000 calories.")
            except ValueError:
                print("Please enter a valid number.")
    
    def apply_cooking_method(self, nutrition: Dict, cooking_method: str) -> Dict:
        """Apply cooking method modifiers to nutrition values"""
        if cooking_method not in self.cooking_methods:
            return nutrition
        
        modifiers = self.cooking_methods[cooking_method]
        
        return {
            'calories': nutrition['calories'] * modifiers['calorie_mult'],
            'protein': nutrition['protein'] * modifiers['protein_mult'],
            'fat': nutrition['fat'] * modifiers['fat_mult'],
            'carbs': nutrition['carbs']  # Carbs generally don't change much
        }
    
    def find_substitution(self, ingredient: str, restrictions: List[str], 
                         diet: str) -> Optional[str]:
        """Find suitable substitution for an ingredient"""
        if not self.substitution_enabled or ingredient not in self.substitutions:
            return None
        
        diet_profile = self.diet_profiles[diet]
        banned = diet_profile.get('banned', [])
        
        for substitute in self.substitutions[ingredient]:
            # Check if substitute exists in our database
            if substitute not in self.ingredients:
                continue
            
            # Check if substitute is banned by diet
            if substitute in banned:
                continue
            
            # Check if substitute violates restrictions
            violates_restriction = False
            for restriction in restrictions:
                if restriction in self.allergen_mapping:
                    if substitute in self.allergen_mapping[restriction]:
                        violates_restriction = True
                        break
            
            if not violates_restriction:
                self.algorithm_metrics['substitutions_made'] += 1
                return substitute
        
        return None
    
    def calculate_meal_nutrition_enhanced(self, meal_template: Dict, 
                                        scale_factor: float = 1.0) -> Dict:
        """Enhanced nutrition calculation with cooking method support"""
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0
        }
        
        # Get cooking method from template
        cooking_method = meal_template.get('cooking_method', 'raw')
        
        for ingredient_info in meal_template['base_ingredients']:
            ingredient = ingredient_info['item']
            amount = ingredient_info['amount'] * scale_factor
            unit = ingredient_info['unit']
            
            if ingredient not in self.ingredients:
                print(f"Warning: Ingredient '{ingredient}' not found in database")
                continue
            
            # Convert to grams
            weight_g = self.convert_unit_to_grams(unit, amount, ingredient)
            
            # Apply cooking factor if applicable
            if ingredient in self.cooking_factors:
                weight_g *= self.cooking_factors[ingredient]
            
            # Get base nutrition per 100g
            base_nutrition = self.ingredients[ingredient]
            
            # Calculate nutrition for actual amount
            multiplier = weight_g / 100.0
            ingredient_nutrition = {
                'calories': base_nutrition['calories'] * multiplier,
                'protein': base_nutrition['protein'] * multiplier,
                'fat': base_nutrition['fat'] * multiplier,
                'carbs': base_nutrition['carbs'] * multiplier
            }
            
            # Apply cooking method modifiers
            if cooking_method != 'raw':
                ingredient_nutrition = self.apply_cooking_method(
                    ingredient_nutrition, cooking_method
                )
            
            # Add to total
            for nutrient in total_nutrition:
                total_nutrition[nutrient] += ingredient_nutrition[nutrient]
        
        return total_nutrition
    
    def filter_templates_by_cuisine(self, templates: List[str], 
                                   cuisine_prefs: List[str]) -> List[str]:
        """Filter templates by cuisine preferences"""
        if "all" in cuisine_prefs:
            return templates
        
        filtered = []
        for template_id in templates:
            template = self.templates[template_id]
            template_cuisine = template.get('cuisine', 'standard')
            
            # Check if cuisine matches preferences
            cuisine_match = False
            for pref in cuisine_prefs:
                if pref in template_cuisine or template_cuisine in pref:
                    cuisine_match = True
                    break
                # Also check tags
                if any(pref in tag for tag in template.get('tags', [])):
                    cuisine_match = True
                    break
            
            if cuisine_match:
                filtered.append(template_id)
        
        # If too few options, gradually expand to include standard options
        if len(filtered) < 5:
            for template_id in templates:
                if template_id not in filtered:
                    template = self.templates[template_id]
                    if 'standard' in template.get('tags', []):
                        filtered.append(template_id)
                        if len(filtered) >= 5:
                            break
        
        return filtered
    
    def filter_templates_by_cooking_method(self, templates: List[str], 
                                         cooking_prefs: List[str]) -> List[str]:
        """Filter templates by cooking method preferences"""
        if "all" in cooking_prefs:
            return templates
        
        filtered = []
        for template_id in templates:
            template = self.templates[template_id]
            template_method = template.get('cooking_method', 'raw')
            
            if template_method in cooking_prefs:
                filtered.append(template_id)
        
        # If too few options, include some alternatives
        if len(filtered) < 3:
            return templates  # Return all if too restrictive
        
        return filtered
    
    def generate_day_meals_enhanced(self, preferences: Dict, meal_history: Dict, 
                                  day_number: int) -> Dict:
        """Enhanced meal generation with cuisine variety"""
        # Add high protein profile if needed
        self._add_high_protein_profile()
        
        diet = preferences['diet']
        pattern = self.meal_patterns[preferences['pattern']]
        daily_calories = preferences['calories']
        restrictions = preferences['restrictions']
        target_macros = self.diet_profiles[diet]['macros']
        cuisine_prefs = preferences.get('cuisines', ['all'])
        cooking_prefs = preferences.get('cooking_methods', ['all'])
        allow_subs = preferences.get('allow_substitutions', True)
        
        meal_history['current_day'] = day_number
        day_meals = {}
        attempts = 0
        max_attempts = 15
        
        # Track cuisines used today for variety
        cuisines_used_today = set()
        
        self._log_optimization_step("MEAL SELECTION", f"Analyzing {len(self.templates)} templates")
        
        while attempts < max_attempts:
            attempts += 1
            day_meals = {}
            cuisines_used_today.clear()
            
            for meal_info in pattern['meals']:
                meal_name = meal_info['name']
                calories_pct = meal_info['calories_pct']
                target_calories = daily_calories * calories_pct / 100
                
                # Map meal names to standard types
                meal_type_map = {
                    'breakfast': 'breakfast',
                    'lunch': 'lunch',
                    'late_lunch': 'lunch',
                    'dinner': 'dinner',
                    'snack': 'snack',
                    'mid_morning': 'snack',
                    'pre_workout': 'snack',
                    'post_workout': 'snack'
                }
                meal_type = meal_type_map.get(meal_name, 'snack')
                
                # Get valid templates
                valid_templates = self.filter_templates_by_diet(diet, meal_type)
                valid_templates = self.filter_templates_by_restrictions(valid_templates, restrictions)
                valid_templates = self.filter_recent_meals(valid_templates, meal_history)
                valid_templates = self.filter_templates_by_cuisine(valid_templates, cuisine_prefs)
                valid_templates = self.filter_templates_by_cooking_method(valid_templates, cooking_prefs)
                
                self.algorithm_metrics['templates_evaluated'] += len(valid_templates)
                
                if not valid_templates:
                    print(f"Warning: No valid templates for {meal_name}")
                    continue
                
                # Rank templates (prefer cuisine variety)
                ranked_templates = self.rank_templates_enhanced(
                    valid_templates, target_macros, meal_type, cuisines_used_today
                )
                
                # Try top candidates
                best_template = None
                best_scale = 1.0
                best_score = 0
                
                for template_id in ranked_templates[:5]:
                    scale = self.optimize_meal_scale_advanced(template_id, target_calories, target_macros)
                    
                    template = self.templates[template_id]
                    nutrition = self.calculate_meal_nutrition_enhanced(template, scale)
                    score = self.calculate_nutrition_score(nutrition, target_calories, target_macros)
                    
                    # Add cuisine variety bonus
                    template_cuisine = template.get('cuisine', 'standard')
                    if template_cuisine not in cuisines_used_today:
                        score += self.CUISINE_VARIETY_WEIGHT * 100
                    
                    if score > best_score:
                        best_score = score
                        best_template = template_id
                        best_scale = scale
                
                if best_template:
                    template = self.templates[best_template].copy()
                    
                    # Apply substitutions if needed and allowed
                    if allow_subs:
                        template = self.apply_substitutions(template, restrictions, diet)
                    
                    # Scale ingredients
                    scaled_ingredients = []
                    for ing in template['base_ingredients']:
                        scaled_ing = ing.copy()
                        scaled_ing['amount'] = round(ing['amount'] * best_scale, 2)
                        scaled_ingredients.append(scaled_ing)
                    
                    # Calculate actual nutrition
                    nutrition = self.calculate_meal_nutrition_enhanced(template, best_scale)
                    
                    # Track cuisine
                    cuisines_used_today.add(template.get('cuisine', 'standard'))
                    
                    day_meals[meal_name] = {
                        'name': template['name'],
                        'ingredients': scaled_ingredients,
                        'calories': nutrition['calories'],
                        'protein': nutrition['protein'],
                        'fat': nutrition['fat'],
                        'carbs': nutrition['carbs'],
                        'prep_time': template.get('prep_time', 15),
                        'cuisine': template.get('cuisine', 'standard'),
                        'cooking_method': template.get('cooking_method', 'raw')
                    }
                    
                    # Track used meals
                    meal_history[template['name']] = day_number
            
            # Check if day totals are acceptable
            totals = self.calculate_day_totals(day_meals)
            score = self.calculate_nutrition_score(totals, daily_calories, target_macros)
            
            self.algorithm_metrics['constraints_checked'] += 1
            
            if score >= 88:  # Slightly lower threshold for more variety
                break
        
        return day_meals
    
    def rank_templates_enhanced(self, templates: List[str], target_macros: Dict, 
                               meal_type: str, cuisines_used: Set[str]) -> List[str]:
        """Enhanced ranking with cuisine variety consideration"""
        template_scores = []
        
        for template_id in templates:
            nutrition = self.calculate_meal_nutrition_enhanced(self.templates[template_id])
            if nutrition['calories'] > 0:
                macros = self.calculate_macro_percentages(nutrition)
                
                # Calculate macro distance
                macro_distance = (
                    abs(macros['protein'] - target_macros['protein']) +
                    abs(macros['fat'] - target_macros['fat']) +
                    abs(macros['carbs'] - target_macros['carbs'])
                )
                
                # Add cuisine variety bonus (lower score is better)
                template = self.templates[template_id]
                cuisine = template.get('cuisine', 'standard')
                if cuisine not in cuisines_used:
                    macro_distance -= 5  # Bonus for new cuisine
                
                template_scores.append((template_id, macro_distance))
        
        # Sort by best fit
        template_scores.sort(key=lambda x: x[1])
        
        return [t[0] for t in template_scores]
    
    def apply_substitutions(self, template: Dict, restrictions: List[str], 
                           diet: str) -> Dict:
        """Apply intelligent substitutions to a meal template"""
        modified_template = template.copy()
        modified_ingredients = []
        
        for ing in template['base_ingredients']:
            ingredient = ing['item']
            
            # Check if ingredient needs substitution
            needs_sub = False
            
            # Check restrictions
            for restriction in restrictions:
                if restriction in self.allergen_mapping:
                    if ingredient in self.allergen_mapping[restriction]:
                        needs_sub = True
                        break
            
            # Check diet compatibility
            diet_profile = self.diet_profiles[diet]
            if ingredient in diet_profile.get('banned', []):
                needs_sub = True
            
            if needs_sub:
                substitute = self.find_substitution(ingredient, restrictions, diet)
                if substitute:
                    new_ing = ing.copy()
                    new_ing['item'] = substitute
                    new_ing['substituted_from'] = ingredient
                    modified_ingredients.append(new_ing)
                    print(f"  Substituted {ingredient} with {substitute}")
                else:
                    # Skip this ingredient if no substitute found
                    print(f"  Warning: Could not substitute {ingredient}, skipping")
            else:
                modified_ingredients.append(ing.copy())
        
        modified_template['base_ingredients'] = modified_ingredients
        return modified_template
    
    def calculate_meal_nutrition(self, meal_template: Dict, scale_factor: float = 1.0) -> Dict:
        """Wrapper for backwards compatibility"""
        return self.calculate_meal_nutrition_enhanced(meal_template, scale_factor)
    
    def optimize_meal_plan_enhanced(self) -> Dict:
        """Main method to generate enhanced meal plan with global cuisine support"""
        # Get enhanced user preferences
        preferences = self.get_user_preferences_enhanced()
        
        print("\n" + "="*60)
        print("🔄 OPTIMIZING GLOBAL CUISINE MEAL PLAN")
        print("="*60)
        
        # Initialize meal history
        meal_history = {}
        
        # Generate Week 1
        week1 = self.generate_week_plan_enhanced(preferences, 1, meal_history)
        
        # Generate Week 2
        week2 = self.generate_week_plan_enhanced(preferences, 2, meal_history)
        
        # Validate both weeks
        print("\n📊 VALIDATING MEAL PLANS")
        print("-" * 30)
        val1 = self.validate_meal_plan(week1, preferences)
        val2 = self.validate_meal_plan(week2, preferences)
        
        print(f"\nWeek 1: {val1['status']}")
        print(f"  Overall Score: {val1['overall_score']:.1f}%")
        print(f"  Calorie Accuracy: {val1['calorie_accuracy']:.1f}%")
        print(f"  Macro Accuracy: {val1['macro_accuracy']:.1f}%")
        print(f"  Cuisine Variety: {val1.get('cuisine_variety', 'N/A')}")
        
        print(f"\nWeek 2: {val2['status']}")
        print(f"  Overall Score: {val2['overall_score']:.1f}%")
        print(f"  Calorie Accuracy: {val2['calorie_accuracy']:.1f}%")
        print(f"  Macro Accuracy: {val2['macro_accuracy']:.1f}%")
        print(f"  Cuisine Variety: {val2.get('cuisine_variety', 'N/A')}")
        
        return {
            'preferences': preferences,
            'week1': week1,
            'week2': week2,
            'validation': {
                'week1': val1,
                'week2': val2
            }
        }
    
    def generate_week_plan_enhanced(self, preferences: Dict, week_num: int, 
                                  meal_history: Dict = None) -> Dict:
        """Generate week plan with enhanced features"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        week_plan = {}
        
        if meal_history is None:
            meal_history = {}
        
        print(f"\n🗓️  Generating Week {week_num} with global cuisine variety...")
        
        cuisines_used_week = set()
        
        for i, day in enumerate(days):
            day_number = (week_num - 1) * 7 + i + 1
            
            # Generate day's meals
            day_meals = self.generate_day_meals_enhanced(preferences, meal_history, day_number)
            
            # Apply optimization passes
            day_meals = self.optimize_day_final(day_meals, preferences)
            day_meals = self.rebalance_day_nutrients(day_meals, preferences)
            
            # Track cuisines
            for meal_data in day_meals.values():
                cuisines_used_week.add(meal_data.get('cuisine', 'standard'))
            
            # Calculate totals
            totals = self.calculate_day_totals(day_meals)
            
            # Calculate accuracy
            diet_profile = self.diet_profiles[preferences['diet']]
            target_macros = diet_profile['macros']
            score = self.calculate_nutrition_score(totals, preferences['calories'], target_macros)
            
            week_plan[day] = {
                'meals': day_meals,
                'totals': totals
            }
            
            # Progress indicator
            cal_accuracy = max(0, 100 - abs(totals['calories'] - preferences['calories']) / 
                             preferences['calories'] * 100)
            macros = self.calculate_macro_percentages(totals)
            
            print(f"  ✓ {day}: {totals['calories']:.0f} cal ({cal_accuracy:.1f}%) | "
                  f"P:{macros['protein']:.0f}% F:{macros['fat']:.0f}% C:{macros['carbs']:.0f}% | "
                  f"Score: {score:.1f}% | Cuisines: {len(set(meal.get('cuisine', 'standard') for meal in day_meals.values()))}")
        
        print(f"  Week {week_num} Cuisine Variety: {len(cuisines_used_week)} different cuisines")
        
        return week_plan
    
    def validate_meal_plan(self, plan: Dict, preferences: Dict) -> Dict:
        """Enhanced validation with cuisine variety tracking"""
        target_calories = preferences['calories']
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        
        issues = []
        scores = []
        calorie_accuracies = []
        macro_accuracies = []
        cuisines_used = set()
        
        for day_name, day_data in plan.items():
            day_issues = []
            totals = day_data['totals']
            
            # Track cuisines
            for meal_data in day_data['meals'].values():
                cuisines_used.add(meal_data.get('cuisine', 'standard'))
            
            # Calculate score
            score = self.calculate_nutrition_score(totals, target_calories, target_macros)
            scores.append(score)
            
            # Calorie accuracy
            cal_diff = abs(totals['calories'] - target_calories)
            cal_accuracy = max(0, 100 - (cal_diff / target_calories * 100))
            calorie_accuracies.append(cal_accuracy)
            
            if cal_diff > self.CALORIE_TOLERANCE:
                day_issues.append(f"Calories off by {cal_diff:.0f}")
            
            # Macro accuracy
            if totals['calories'] > 0:
                current_macros = self.calculate_macro_percentages(totals)
                
                macro_diffs = []
                for macro in ['protein', 'fat', 'carbs']:
                    diff = abs(current_macros[macro] - target_macros[macro])
                    if diff > self.MACRO_TOLERANCE:
                        day_issues.append(f"{macro.capitalize()} {current_macros[macro]:.0f}% "
                                        f"(target: {target_macros[macro]}%)")
                    macro_diffs.append(diff)
                
                macro_accuracy = max(0, 100 - sum(macro_diffs) / 3)
                macro_accuracies.append(macro_accuracy)
            
            if day_issues:
                issues.append(f"{day_name}: {', '.join(day_issues)}")
        
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_cal_accuracy = sum(calorie_accuracies) / len(calorie_accuracies) if calorie_accuracies else 0
        avg_macro_accuracy = sum(macro_accuracies) / len(macro_accuracies) if macro_accuracies else 0
        
        if avg_score >= 95:
            status = "Excellent - Target Achieved!"
        elif avg_score >= 90:
            status = "Very Good"
        elif avg_score >= 85:
            status = "Good"
        else:
            status = "Needs Improvement"
        
        # Cuisine variety assessment
        num_cuisines = len(cuisines_used)
        if num_cuisines >= 5:
            cuisine_variety = f"Excellent ({num_cuisines} cuisines)"
        elif num_cuisines >= 3:
            cuisine_variety = f"Good ({num_cuisines} cuisines)"
        else:
            cuisine_variety = f"Limited ({num_cuisines} cuisines)"
        
        return {
            'overall_score': avg_score,
            'calorie_accuracy': avg_cal_accuracy,
            'macro_accuracy': avg_macro_accuracy,
            'status': status,
            'cuisine_variety': cuisine_variety,
            'cuisines_used': list(cuisines_used),
            'issues': issues[:5]
        }
    
    # Include all other methods from the original MealPlanOptimizer class
    # (calculate_macro_percentages, calculate_nutrition_score, optimize_day_final, etc.)
    # These remain the same as in the original implementation
    
    def convert_unit_to_grams(self, unit: str, amount: float, ingredient: str = "") -> float:
        """Convert various units to grams with cooking factor awareness"""
        unit_lower = unit.lower()
        ingredient_lower = ingredient.lower()
        
        # Check ingredient-specific conversions first
        if ingredient_lower in self.specific_conversions:
            if unit_lower in self.specific_conversions[ingredient_lower]:
                return amount * self.specific_conversions[ingredient_lower][unit_lower]
        
        # Use general conversions
        if unit_lower in self.conversions:
            return amount * self.conversions[unit_lower]
        
        # Default to grams if unit not found
        print(f"Warning: Unknown unit '{unit}' for '{ingredient}', assuming grams")
        return amount
    
    def calculate_macro_percentages(self, nutrition: Dict) -> Dict:
        """Calculate macro percentages from nutrition data"""
        if nutrition['calories'] == 0:
            return {'protein': 0, 'fat': 0, 'carbs': 0}
        
        return {
            'protein': (nutrition['protein'] * 4) / nutrition['calories'] * 100,
            'fat': (nutrition['fat'] * 9) / nutrition['calories'] * 100,
            'carbs': (nutrition['carbs'] * 4) / nutrition['calories'] * 100
        }
    
    def calculate_nutrition_score(self, nutrition: Dict, target_calories: float, 
                                 target_macros: Dict) -> float:
        """Calculate combined score for calories and macro accuracy (0-100)"""
        # Calorie accuracy (40% weight)
        calorie_diff = abs(nutrition['calories'] - target_calories)
        calorie_score = max(0, 100 - (calorie_diff / target_calories * 100)) * 0.4
        
        # Macro accuracy (60% weight)
        current_macros = self.calculate_macro_percentages(nutrition)
        macro_diffs = [
            abs(current_macros['protein'] - target_macros['protein']),
            abs(current_macros['fat'] - target_macros['fat']),
            abs(current_macros['carbs'] - target_macros['carbs'])
        ]
        macro_score = max(0, 100 - sum(macro_diffs) / 3) * 0.6
        
        return calorie_score + macro_score
    
    def filter_templates_by_diet(self, diet: str, meal_type: str = None) -> List[str]:
        """Filter meal templates compatible with selected diet"""
        diet_profile = self.diet_profiles[diet]
        valid_templates = []
        
        for template_id, template in self.templates.items():
            # Check meal type if specified
            if meal_type and template.get('meal_type') != meal_type:
                continue
            
            # Check if any of the template tags match the diet's meal tags
            template_tags = template.get('tags', [])
            diet_tags = diet_profile.get('meal_tags', [diet])
            
            if any(tag in template_tags for tag in diet_tags):
                # Check banned ingredients
                banned = diet_profile.get('banned', [])
                has_banned = False
                
                for ingredient_info in template['base_ingredients']:
                    ingredient = ingredient_info['item']
                    if ingredient in banned:
                        has_banned = True
                        break
                
                if not has_banned:
                    valid_templates.append(template_id)
        
        return valid_templates
    
    def filter_templates_by_restrictions(self, templates: List[str], 
                                       restrictions: List[str]) -> List[str]:
        """Filter out templates containing restricted ingredients"""
        if not restrictions:
            return templates
        
        filtered = []
        for template_id in templates:
            template = self.templates[template_id]
            has_restricted = False
            
            for ingredient_info in template['base_ingredients']:
                ingredient = ingredient_info['item']
                
                # Check each restriction
                for restriction in restrictions:
                    if restriction in self.allergen_mapping:
                        banned_ingredients = self.allergen_mapping[restriction]
                        if ingredient in banned_ingredients:
                            has_restricted = True
                            break
                
                if has_restricted:
                    break
            
            if not has_restricted:
                filtered.append(template_id)
        
        return filtered
    
    def filter_recent_meals(self, valid_templates: List[str], meal_history: Dict[str, int], 
                          days_to_avoid: int = 5) -> List[str]:
        """Enhanced variety tracking - avoid repeating meals within X days"""
        filtered = []
        current_day = meal_history.get('current_day', 0)
        
        for template_id in valid_templates:
            template_name = self.templates[template_id]['name']
            last_used = meal_history.get(template_name, -999)
            
            if current_day - last_used >= days_to_avoid:
                filtered.append(template_id)
        
        # If too few options, gradually reduce the restriction
        if len(filtered) < 3 and days_to_avoid > 2:
            return self.filter_recent_meals(valid_templates, meal_history, days_to_avoid - 1)
        
        return filtered if filtered else valid_templates
    
    def optimize_meal_scale_advanced(self, template_id: str, target_calories: float, 
                                   target_macros: Dict, max_iterations: int = 10) -> float:
        """Advanced scaling using gradient descent to optimize both calories and macros"""
        template = self.templates[template_id]
        
        # Initial scale based on calories
        base_nutrition = self.calculate_meal_nutrition_enhanced(template)
        if base_nutrition['calories'] == 0:
            return 1.0
        
        scale = target_calories / base_nutrition['calories']
        best_scale = scale
        best_score = 0
        
        # Learning rate for gradient descent
        learning_rate = 0.1
        
        for iteration in range(max_iterations):
            # Calculate current nutrition
            current_nutrition = self.calculate_meal_nutrition_enhanced(template, scale)
            
            # Calculate score
            score = self.calculate_nutrition_score(current_nutrition, target_calories, target_macros)
            
            if score > best_score:
                best_score = score
                best_scale = scale
            
            # If we're close enough, stop
            if score >= 95:
                break
            
            # Calculate gradient (simplified)
            # Try slightly higher and lower scales
            scale_up = scale * 1.05
            scale_down = scale * 0.95
            
            nutrition_up = self.calculate_meal_nutrition_enhanced(template, scale_up)
            nutrition_down = self.calculate_meal_nutrition_enhanced(template, scale_down)
            
            score_up = self.calculate_nutrition_score(nutrition_up, target_calories, target_macros)
            score_down = self.calculate_nutrition_score(nutrition_down, target_calories, target_macros)
            
            # Move in the direction of improvement
            if score_up > score and score_up > score_down:
                scale = scale + learning_rate * (scale_up - scale)
            elif score_down > score:
                scale = scale + learning_rate * (scale_down - scale)
            else:
                # Reduce learning rate if no improvement
                learning_rate *= 0.5
            
            # Keep scale in reasonable bounds
            scale = max(0.3, min(2.5, scale))
        
        return best_scale
    
    def calculate_day_totals(self, meals: Dict) -> Dict:
        """Calculate total nutrition for a day"""
        totals = {
            'calories': 0,
            'protein': 0,
            'fat': 0,
            'carbs': 0
        }
        
        for meal in meals.values():
            totals['calories'] += meal['calories']
            totals['protein'] += meal['protein']
            totals['fat'] += meal['fat']
            totals['carbs'] += meal['carbs']
        
        return totals
    
    def optimize_day_final(self, day_meals: Dict, preferences: Dict) -> Dict:
        """Final optimization pass using multi-objective optimization"""
        self._log_optimization_step("MULTI-OBJECTIVE OPTIMIZATION", 
                                   f"Fine-tuning {len(day_meals)} meals")
        
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        target_calories = preferences['calories']
        
        best_meals = {k: v.copy() for k, v in day_meals.items()}
        best_score = 0
        best_scales = {meal_name: 1.0 for meal_name in day_meals.keys()}
        
        # Try different scaling combinations
        meal_names = list(day_meals.keys())
        n_meals = len(meal_names)
        
        # Generate scaling factors to try
        scale_options = [0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15]
        
        # Try systematic combinations (limited to avoid exponential complexity)
        for iteration in range(50):
            # Random perturbation from current best
            test_meals = {}
            scales = {}
            
            for meal_name in meal_names:
                # Small random perturbation
                if iteration == 0:
                    scales[meal_name] = 1.0
                else:
                    scales[meal_name] = best_scales[meal_name] * random.uniform(0.95, 1.05)
                    scales[meal_name] = max(0.7, min(1.3, scales[meal_name]))
                
                meal = best_meals[meal_name]
                test_meal = meal.copy()
                
                # Apply scale
                scale = scales[meal_name]
                test_meal['calories'] = meal['calories'] * scale
                test_meal['protein'] = meal['protein'] * scale
                test_meal['fat'] = meal['fat'] * scale
                test_meal['carbs'] = meal['carbs'] * scale
                
                # Scale ingredients too
                test_meal['ingredients'] = []
                for ing in meal['ingredients']:
                    scaled_ing = ing.copy()
                    scaled_ing['amount'] = round(ing['amount'] * scale, 2)
                    test_meal['ingredients'].append(scaled_ing)
                
                test_meals[meal_name] = test_meal
            
            # Evaluate
            totals = self.calculate_day_totals(test_meals)
            score = self.calculate_nutrition_score(totals, target_calories, target_macros)
            
            if score > best_score:
                best_score = score
                best_meals = test_meals
                best_scales = scales
                
                # If we hit our target, we can stop
                if score >= 95:
                    break
        
        return best_meals
    
    def rebalance_day_nutrients(self, day_meals: Dict, preferences: Dict) -> Dict:
        """Advanced rebalancing using linear algebra to hit both calorie and macro targets"""
        self._log_optimization_step("NUTRIENT REBALANCING", 
                                   "Fine-tuning macro distributions")
        
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        target_calories = preferences['calories']
        
        # Target nutrients in grams
        target_protein = (target_calories * target_macros['protein'] / 100) / 4
        target_fat = (target_calories * target_macros['fat'] / 100) / 9
        target_carbs = (target_calories * target_macros['carbs'] / 100) / 4
        
        meal_names = list(day_meals.keys())
        n_meals = len(meal_names)
        
        if n_meals == 0:
            return day_meals
        
        # Create matrix of current meal nutrients
        A = np.zeros((4, n_meals))
        b = np.array([target_calories, target_protein, target_fat, target_carbs])
        
        for i, meal_name in enumerate(meal_names):
            meal = day_meals[meal_name]
            A[0, i] = meal['calories']
            A[1, i] = meal['protein']
            A[2, i] = meal['fat']
            A[3, i] = meal['carbs']
        
        # Solve for optimal scaling factors
        # We want to find x such that A @ x ≈ b
        # Using least squares with bounds
        try:
            # Initial guess (all meals scaled to 1.0)
            x0 = np.ones(n_meals)
            
            # Bounds for scaling factors
            bounds = [(0.6, 1.4) for _ in range(n_meals)]
            
            # Simple iterative approach
            best_x = x0.copy()
            best_error = float('inf')
            
            for _ in range(100):
                # Random perturbation
                x = best_x + np.random.normal(0, 0.05, n_meals)
                
                # Apply bounds
                x = np.clip(x, 0.6, 1.4)
                
                # Calculate error
                result = A @ x
                error = np.sum((result - b) ** 2)
                
                if error < best_error:
                    best_error = error
                    best_x = x
            
            # Apply the scaling factors
            rebalanced_meals = {}
            for i, meal_name in enumerate(meal_names):
                scale = best_x[i]
                meal = day_meals[meal_name].copy()
                
                # Scale nutrients
                meal['calories'] *= scale
                meal['protein'] *= scale
                meal['fat'] *= scale
                meal['carbs'] *= scale
                
                # Scale ingredients
                meal['ingredients'] = []
                for ing in day_meals[meal_name]['ingredients']:
                    scaled_ing = ing.copy()
                    scaled_ing['amount'] = round(ing['amount'] * scale, 2)
                    meal['ingredients'].append(scaled_ing)
                
                rebalanced_meals[meal_name] = meal
            
            return rebalanced_meals
            
        except Exception as e:
            print(f"Rebalancing failed: {e}")
            return day_meals
    
    def generate_shopping_list(self, meal_plan: Dict) -> Dict:
        """Generate consolidated shopping list with validation"""
        shopping_list = {}
        
        # Process both weeks
        for week_key in ['week1', 'week2']:
            week_data = meal_plan[week_key]
            
            for day_name, day_data in week_data.items():
                for meal_name, meal_data in day_data['meals'].items():
                    for ingredient_info in meal_data['ingredients']:
                        ingredient = ingredient_info['item']
                        amount = ingredient_info['amount']
                        unit = ingredient_info['unit']
                        
                        # Convert to standard units for aggregation
                        weight_g = self.convert_unit_to_grams(unit, amount, ingredient)
                        
                        if ingredient not in shopping_list:
                            shopping_list[ingredient] = {
                                'total_grams': 0,
                                'category': self.ingredients.get(ingredient, {}).get('category', 'other'),
                                'original_units': []
                            }
                        
                        shopping_list[ingredient]['total_grams'] += weight_g
                        shopping_list[ingredient]['original_units'].append(f"{amount} {unit}")
        
        # Validate amounts
        shopping_list = self.validate_shopping_amounts(shopping_list)
        
        # Organize by category
        organized_list = {}
        for ingredient, data in shopping_list.items():
            category = data['category']
            if category not in organized_list:
                organized_list[category] = {}
            
            # Convert back to friendly units
            total_g = data['total_grams']
            if total_g >= 1000:
                display_amount = f"{total_g/1000:.1f} kg"
            else:
                display_amount = f"{total_g:.0f} g"
            
            organized_list[category][ingredient] = display_amount
        
        return organized_list
    
    def validate_shopping_amounts(self, shopping_list: Dict) -> Dict:
        """Validate and cap shopping amounts to reasonable levels"""
        validated_list = shopping_list.copy()
        
        for ingredient, data in validated_list.items():
            # Check against maximum amounts
            if ingredient in self.max_shopping_amounts:
                max_amount = self.max_shopping_amounts[ingredient]
                if data['total_grams'] > max_amount:
                    print(f"Warning: Capping {ingredient} from {data['total_grams']:.0f}g to {max_amount}g")
                    data['total_grams'] = max_amount
            
            # General sanity check - nothing should be more than 5kg
            if data['total_grams'] > 5000:
                print(f"Warning: Capping {ingredient} from {data['total_grams']:.0f}g to 5000g")
                data['total_grams'] = 5000
        
        return validated_list
    
    def save_meal_plan(self, meal_plan: Dict, filename: str = 'meal_plan_enhanced.json'):
        """Save meal plan to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(meal_plan, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Meal plan saved to {filename}")
    
    def create_meal_plan_text(self, meal_plan: Dict, filename: str = 'meal_plan_enhanced.txt'):
        """Create human-readable text version of meal plan"""
        lines = []
        preferences = meal_plan['preferences']
        
        # Header
        lines.append("="*80)
        lines.append("GLOBAL CUISINE MEAL PLAN - 95% ACCURACY TARGET")
        lines.append("="*80)
        lines.append(f"\nDiet Type: {self.diet_profiles[preferences['diet']]['name']}")
        lines.append(f"Cuisines: {', '.join(preferences.get('cuisines', ['all']))}")
        lines.append(f"Cooking Methods: {', '.join(preferences.get('cooking_methods', ['all']))}")
        lines.append(f"Meal Pattern: {self.meal_patterns[preferences['pattern']]['name']}")
        lines.append(f"Daily Calories: {preferences['calories']}")
        lines.append(f"Restrictions: {', '.join(preferences['restrictions']) if preferences['restrictions'] else 'None'}")
        lines.append(f"Substitutions: {'Enabled' if preferences.get('allow_substitutions', True) else 'Disabled'}")
        lines.append(f"Generated: {preferences['timestamp'][:10]}")
        
        # Target macros
        diet_profile = self.diet_profiles[preferences['diet']]
        target_macros = diet_profile['macros']
        lines.append(f"\nTarget Macros:")
        lines.append(f"  Protein: {target_macros['protein']}%")
        lines.append(f"  Fat: {target_macros['fat']}%")
        lines.append(f"  Carbs: {target_macros['carbs']}%")
        
        # Process each week
        for week_num, week_key in enumerate(['week1', 'week2'], 1):
            lines.append(f"\n\n{'='*80}")
            lines.append(f"WEEK {week_num}")
            lines.append("="*80)
            
            week_data = meal_plan[week_key]
            validation = meal_plan['validation'][week_key]
            
            lines.append(f"\nWeek {week_num} Performance:")
            lines.append(f"  Overall Score: {validation['overall_score']:.1f}%")
            lines.append(f"  Calorie Accuracy: {validation['calorie_accuracy']:.1f}%")
            lines.append(f"  Macro Accuracy: {validation['macro_accuracy']:.1f}%")
            lines.append(f"  Cuisine Variety: {validation.get('cuisine_variety', 'N/A')}")
            
            for day_name, day_data in week_data.items():
                lines.append(f"\n\n{day_name.upper()}")
                lines.append("-"*50)
                
                meals = day_data['meals']
                totals = day_data['totals']
                
                # Each meal
                for meal_name, meal in meals.items():
                    lines.append(f"\n{meal_name.replace('_', ' ').title()}:")
                    lines.append(f"  {meal['name']} ({meal.get('cuisine', 'standard').title()} cuisine)")
                    lines.append(f"  Cooking method: {meal.get('cooking_method', 'raw').replace('_', ' ')}")
                    lines.append(f"  {meal['calories']:.0f} cal | P: {meal['protein']:.1f}g | F: {meal['fat']:.1f}g | C: {meal['carbs']:.1f}g")
                    lines.append("  Ingredients:")
                    
                    for ing in meal['ingredients']:
                        if 'substituted_from' in ing:
                            lines.append(f"    - {ing['item']}: {ing['amount']} {ing['unit']} (substituted from {ing['substituted_from']})")
                        else:
                            lines.append(f"    - {ing['item']}: {ing['amount']} {ing['unit']}")
                
                # Day totals
                if totals['calories'] > 0:
                    macros = self.calculate_macro_percentages(totals)
                    score = self.calculate_nutrition_score(totals, preferences['calories'], target_macros)
                    
                    lines.append(f"\nDaily Totals: {totals['calories']:.0f} calories")
                    lines.append(f"Macros: P: {totals['protein']:.1f}g ({macros['protein']:.0f}%) | F: {totals['fat']:.1f}g ({macros['fat']:.0f}%) | C: {totals['carbs']:.1f}g ({macros['carbs']:.0f}%)")
                    lines.append(f"Daily Score: {score:.1f}%")
        
        # Shopping list
        lines.append(f"\n\n{'='*80}")
        lines.append("SHOPPING LIST (2 WEEKS)")
        lines.append("="*80)
        
        shopping_list = self.generate_shopping_list(meal_plan)
        
        for category, items in sorted(shopping_list.items()):
            lines.append(f"\n{category.upper()}:")
            for ingredient, amount in sorted(items.items()):
                lines.append(f"  - {ingredient}: {amount}")
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"📄 Readable meal plan saved to {filename}")


# Main execution
if __name__ == "__main__":
    try:
        # Initialize with enhanced features
        optimizer = MealPlanOptimizer()
        
        # Generate optimized meal plan
        meal_plan = optimizer.optimize_meal_plan_enhanced()
        
        # Save outputs
        optimizer.save_meal_plan(meal_plan, 'meal_plan_enhanced.json')
        optimizer.create_meal_plan_text(meal_plan, 'meal_plan_enhanced.txt')
        
        # Generate shopping list
        print("\n🛒 SHOPPING LIST PREVIEW:")
        print("-" * 30)
        shopping_list = optimizer.generate_shopping_list(meal_plan)
        
        # Show first few items from each category
        for category, items in list(shopping_list.items())[:3]:
            print(f"\n{category.upper()}:")
            for ingredient, amount in list(items.items())[:3]:
                print(f"  - {ingredient}: {amount}")
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more items")
        
        print("\n✅ Enhanced meal plan generation complete!")
        print("\nFiles created:")
        print("  - meal_plan_enhanced.json (data)")
        print("  - meal_plan_enhanced.txt (readable)")
        
        # Final performance summary
        avg_score = (meal_plan['validation']['week1']['overall_score'] + 
                    meal_plan['validation']['week2']['overall_score']) / 2
        
        if avg_score >= 95:
            print(f"\n🎉 SUCCESS! Achieved {avg_score:.1f}% overall accuracy!")
        else:
            print(f"\n📊 Final accuracy: {avg_score:.1f}% (Target: 95%)")
            
    except KeyboardInterrupt:
        print("\n\n👋 Program cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check your inputs and try again.")