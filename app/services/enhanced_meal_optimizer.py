"""Enhanced meal optimization service using comprehensive nutrition database."""
import random
import sys
import os
from typing import Dict, List, Any, Set
from copy import deepcopy

# Add root directory to path to import nutrition_data
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    import nutrition_data as nd
except ImportError:
    print("Warning: Could not import comprehensive nutrition_data. Using fallback.")
    nd = None


class EnhancedMealOptimizer:
    """Enhanced service for generating diverse, accurate meal plans."""
    
    def __init__(self):
        """Initialize with comprehensive nutrition database."""
        if nd is None:
            raise ImportError("Comprehensive nutrition database not available")
            
        self.ingredients = nd.INGREDIENTS
        self.meal_templates = nd.MEAL_TEMPLATES
        self.diet_profiles = nd.DIET_PROFILES
        
        # Track meal history to prevent repetition
        self.recent_meals = set()
        self.used_templates = set()
        
    def generate_meal_plan(
        self,
        target_calories: int,
        diet_type: str,
        meals_per_day: int = 3,
        days: int = 1,
        restrictions: List[str] = None,
        cuisine_preference: str = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive meal plan with variety and accurate portions.
        
        Args:
            target_calories: Daily calorie target
            diet_type: Type of diet (standard, keto, paleo, vegan, etc.)
            meals_per_day: Number of meals per day
            days: Number of days to plan
            restrictions: List of dietary restrictions
            cuisine_preference: Preferred cuisine type
            
        Returns:
            Dictionary containing the detailed meal plan
        """
        restrictions = restrictions or []
        
        # Reset meal tracking for new plan
        self.recent_meals = set()
        self.used_templates = set()
        
        meal_plan = {
            'days': [],
            'total_calories': 0,
            'diet_type': diet_type,
            'summary': {},
            'variety_score': 0
        }
        
        # Calculate calories per meal with some variation
        base_calories_per_meal = target_calories // meals_per_day
        
        for day in range(1, days + 1):
            day_plan = {
                'day': day,
                'meals': [],
                'total_calories': 0,
                'macros': {'protein': 0, 'carbs': 0, 'fat': 0}
            }
            
            # Generate varied meals for the day
            day_calories_remaining = target_calories
            
            for meal_num in range(meals_per_day):
                meal_type = self._get_meal_type(meal_num, meals_per_day)
                
                # Adjust target calories for this meal
                if meal_num == meals_per_day - 1:  # Last meal gets remaining calories
                    meal_target_calories = max(200, day_calories_remaining)
                else:
                    # Add some variation to meal sizes
                    variation = random.randint(-100, 100)
                    meal_target_calories = max(200, base_calories_per_meal + variation)
                
                meal = self._generate_diverse_meal(
                    meal_target_calories,
                    diet_type,
                    meal_type,
                    restrictions,
                    cuisine_preference,
                    day
                )
                
                day_plan['meals'].append(meal)
                day_plan['total_calories'] += meal['calories']
                day_calories_remaining -= meal['calories']
                
                # Update macros
                for macro in ['protein', 'carbs', 'fat']:
                    day_plan['macros'][macro] += meal['macros'][macro]
            
            meal_plan['days'].append(day_plan)
            meal_plan['total_calories'] += day_plan['total_calories']
        
        # Calculate variety score and summary
        meal_plan['variety_score'] = len(self.used_templates)
        meal_plan['summary'] = self._generate_enhanced_summary(meal_plan)
        
        return meal_plan
    
    def _get_meal_type(self, meal_num: int, meals_per_day: int) -> str:
        """Determine meal type based on meal number."""
        meal_types_map = {
            1: ['dinner'],
            2: ['lunch', 'dinner'],
            3: ['breakfast', 'lunch', 'dinner'],
            4: ['breakfast', 'lunch', 'snack', 'dinner'],
            5: ['breakfast', 'snack', 'lunch', 'snack', 'dinner']
        }
        
        meal_types = meal_types_map.get(meals_per_day, ['breakfast', 'lunch', 'dinner'])
        return meal_types[meal_num] if meal_num < len(meal_types) else 'snack'
    
    def _generate_diverse_meal(
        self,
        target_calories: int,
        diet_type: str,
        meal_type: str,
        restrictions: List[str],
        cuisine_preference: str,
        day: int
    ) -> Dict[str, Any]:
        """Generate a meal with anti-repetition logic."""
        
        # Get suitable meal templates
        suitable_templates = self._filter_meal_templates(
            diet_type, meal_type, restrictions, cuisine_preference
        )
        
        if not suitable_templates:
            return self._create_fallback_meal(target_calories, meal_type)
        
        # Select template with anti-repetition logic
        selected_template = self._select_diverse_template(suitable_templates)
        
        if selected_template is None:
            return self._create_fallback_meal(target_calories, meal_type)
        
        # Generate meal from template with accurate portions
        meal = self._build_meal_from_template(selected_template, target_calories, meal_type)
        
        # Track this meal to prevent repetition
        self.recent_meals.add(meal['name'])
        self.used_templates.add(selected_template['name'])
        
        return meal
    
    def _filter_meal_templates(
        self,
        diet_type: str,
        meal_type: str,
        restrictions: List[str],
        cuisine_preference: str
    ) -> List[Dict[str, Any]]:
        """Filter meal templates based on criteria."""
        suitable_templates = []
        
        for template_name, template in self.meal_templates.items():
            # Check meal type
            if template.get('meal_type') != meal_type:
                continue
            
            # Check diet compatibility
            template_tags = template.get('tags', [])
            if diet_type != 'standard':
                if diet_type not in template_tags:
                    continue
            
            # Check restrictions
            if any(restriction in template_tags for restriction in restrictions):
                continue
            
            # Check cuisine preference
            if cuisine_preference and template.get('cuisine') != cuisine_preference:
                continue
            
            suitable_templates.append(template)
        
        return suitable_templates
    
    def _select_diverse_template(self, templates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select template with preference for unused ones."""
        
        # Prefer unused templates
        unused_templates = [t for t in templates if t.get('name') not in self.used_templates]
        
        if unused_templates:
            return random.choice(unused_templates)
        elif templates:
            # If all templates used, pick least recently used
            return random.choice(templates)
        
        return None
    
    def _build_meal_from_template(
        self, 
        template: Dict[str, Any], 
        target_calories: int, 
        meal_type: str
    ) -> Dict[str, Any]:
        """Build meal from template with accurate calorie calculation."""
        
        # Calculate template's base calories
        base_calories = 0
        template_macros = {'protein': 0, 'carbs': 0, 'fat': 0}
        
        for ingredient in template.get('base_ingredients', []):
            item_name = ingredient['item']
            amount = ingredient['amount']
            unit = ingredient['unit']
            
            if item_name in self.ingredients:
                item_data = self.ingredients[item_name]
                
                # Convert to 100g basis for calculation
                if unit == 'g':
                    calories_per_100g = item_data['calories']
                    actual_calories = (amount / 100) * calories_per_100g
                elif unit == 'ml':
                    # Assume 1ml = 1g for liquids (close enough)
                    calories_per_100g = item_data['calories']
                    actual_calories = (amount / 100) * calories_per_100g
                else:
                    actual_calories = item_data['calories'] * 0.5  # Rough estimate
                
                base_calories += actual_calories
                
                # Calculate macros
                if unit in ['g', 'ml']:
                    factor = amount / 100
                    template_macros['protein'] += item_data['protein'] * factor
                    template_macros['carbs'] += item_data['carbs'] * factor
                    template_macros['fat'] += item_data['fat'] * factor
        
        # Calculate scaling factor
        if base_calories > 0:
            scale_factor = target_calories / base_calories
            # Limit extreme scaling
            scale_factor = max(0.5, min(3.0, scale_factor))
        else:
            scale_factor = 1.0
        
        # Build scaled ingredient list
        scaled_ingredients = []
        for ingredient in template.get('base_ingredients', []):
            item_name = ingredient['item']
            amount = ingredient['amount']
            unit = ingredient['unit']
            
            scaled_amount = amount * scale_factor
            
            # Format nicely
            if item_name in self.ingredients:
                display_name = item_name.replace('_', ' ').title()
                
                if unit == 'g':
                    if scaled_amount >= 100:
                        display_amount = f"{scaled_amount:.0f}g"
                    else:
                        display_amount = f"{scaled_amount:.0f}g"
                elif unit == 'ml':
                    display_amount = f"{scaled_amount:.0f}ml"
                else:
                    display_amount = f"{scaled_amount:.1f} {unit}"
                
                scaled_ingredients.append(f"{display_amount} {display_name}")
        
        # Calculate final macros
        final_macros = {
            'protein': int(template_macros['protein'] * scale_factor),
            'carbs': int(template_macros['carbs'] * scale_factor),
            'fat': int(template_macros['fat'] * scale_factor)
        }
        
        meal = {
            'name': template.get('name', 'Custom Meal'),
            'type': meal_type,
            'calories': int(base_calories * scale_factor),
            'macros': final_macros,
            'ingredients': scaled_ingredients,
            'prep_time': template.get('prep_time', 15),
            'cooking_method': template.get('cooking_method', 'mixed'),
            'cuisine': template.get('cuisine', 'standard')
        }
        
        return meal
    
    def _create_fallback_meal(self, calories: int, meal_type: str) -> Dict[str, Any]:
        """Create a basic fallback meal when no templates match."""
        fallback_meals = {
            'breakfast': {
                'name': 'Simple Breakfast',
                'ingredients': ['2 eggs', '1 slice toast', '1 tbsp butter']
            },
            'lunch': {
                'name': 'Quick Lunch',
                'ingredients': ['Protein of choice', 'Mixed vegetables', 'Rice or quinoa']
            },
            'dinner': {
                'name': 'Basic Dinner',
                'ingredients': ['Lean protein', 'Steamed vegetables', 'Complex carbs']
            },
            'snack': {
                'name': 'Healthy Snack',
                'ingredients': ['Nuts', 'Fruit', 'Greek yogurt']
            }
        }
        
        fallback = fallback_meals.get(meal_type, fallback_meals['lunch'])
        
        return {
            'name': fallback['name'],
            'type': meal_type,
            'calories': calories,
            'macros': {'protein': calories//20, 'carbs': calories//15, 'fat': calories//25},
            'ingredients': fallback['ingredients'],
            'prep_time': 15,
            'cooking_method': 'varied',
            'cuisine': 'standard'
        }
    
    def _generate_enhanced_summary(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive meal plan summary."""
        total_days = len(meal_plan['days'])
        total_meals = sum(len(day['meals']) for day in meal_plan['days'])
        unique_meals = len(self.used_templates)
        
        avg_calories_per_day = meal_plan['total_calories'] / total_days if total_days > 0 else 0
        
        return {
            'total_days': total_days,
            'total_meals': total_meals,
            'unique_meals': unique_meals,
            'variety_percentage': round((unique_meals / total_meals) * 100, 1) if total_meals > 0 else 0,
            'avg_calories_per_day': round(avg_calories_per_day),
            'diet_type': meal_plan['diet_type']
        }