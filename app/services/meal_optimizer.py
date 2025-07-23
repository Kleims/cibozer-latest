"""Meal optimization service."""
import random
from typing import Dict, List, Any
from app.core.nutrition_data import MEAL_DATABASE, NUTRITION_TARGETS


class MealOptimizer:
    """Service for generating optimized meal plans."""
    
    def __init__(self):
        self.meal_database = MEAL_DATABASE
        self.nutrition_targets = NUTRITION_TARGETS
    
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
        Generate a meal plan based on user preferences.
        
        Args:
            target_calories: Daily calorie target
            diet_type: Type of diet (keto, paleo, vegan, etc.)
            meals_per_day: Number of meals per day
            days: Number of days to plan
            restrictions: List of dietary restrictions
            cuisine_preference: Preferred cuisine type
            
        Returns:
            Dictionary containing the meal plan
        """
        restrictions = restrictions or []
        meal_plan = {
            'days': [],
            'total_calories': 0,
            'diet_type': diet_type,
            'summary': {}
        }
        
        # Calculate calories per meal
        calories_per_meal = target_calories // meals_per_day
        
        for day in range(1, days + 1):
            day_plan = {
                'day': day,
                'meals': [],
                'total_calories': 0,
                'macros': {'protein': 0, 'carbs': 0, 'fat': 0}
            }
            
            # Generate meals for the day
            for meal_num in range(meals_per_day):
                meal_type = self._get_meal_type(meal_num, meals_per_day)
                meal = self._generate_meal(
                    calories_per_meal,
                    diet_type,
                    meal_type,
                    restrictions,
                    cuisine_preference
                )
                
                day_plan['meals'].append(meal)
                day_plan['total_calories'] += meal['calories']
                
                # Update macros
                for macro in ['protein', 'carbs', 'fat']:
                    day_plan['macros'][macro] += meal['macros'][macro]
            
            meal_plan['days'].append(day_plan)
            meal_plan['total_calories'] += day_plan['total_calories']
        
        # Add summary
        meal_plan['summary'] = self._generate_summary(meal_plan)
        
        return meal_plan
    
    def _get_meal_type(self, meal_num: int, meals_per_day: int) -> str:
        """Determine meal type based on meal number and total meals."""
        if meals_per_day == 1:
            return 'dinner'
        elif meals_per_day == 2:
            return 'lunch' if meal_num == 0 else 'dinner'
        elif meals_per_day == 3:
            meal_types = ['breakfast', 'lunch', 'dinner']
            return meal_types[meal_num] if meal_num < 3 else 'snack'
        else:
            # For more than 3 meals, include snacks
            base_meals = ['breakfast', 'lunch', 'dinner']
            if meal_num < len(base_meals):
                return base_meals[meal_num]
            return 'snack'
    
    def _generate_meal(
        self,
        target_calories: int,
        diet_type: str,
        meal_type: str,
        restrictions: List[str],
        cuisine_preference: str = None
    ) -> Dict[str, Any]:
        """Generate a single meal."""
        # Filter available meals
        available_meals = self._filter_meals(
            diet_type,
            meal_type,
            restrictions,
            cuisine_preference
        )
        
        if not available_meals:
            # Fallback to a basic meal if no matches
            return self._create_basic_meal(target_calories, meal_type)
        
        # Select a meal close to target calories
        selected_meal = self._select_meal_by_calories(
            available_meals,
            target_calories
        )
        
        # Adjust portion size if needed
        portion_multiplier = target_calories / selected_meal['calories']
        
        meal = {
            'name': selected_meal['name'],
            'type': meal_type,
            'calories': int(selected_meal['calories'] * portion_multiplier),
            'macros': {
                'protein': int(selected_meal['macros']['protein'] * portion_multiplier),
                'carbs': int(selected_meal['macros']['carbs'] * portion_multiplier),
                'fat': int(selected_meal['macros']['fat'] * portion_multiplier)
            },
            'ingredients': selected_meal.get('ingredients', []),
            'instructions': selected_meal.get('instructions', []),
            'prep_time': selected_meal.get('prep_time', 20),
            'cook_time': selected_meal.get('cook_time', 30)
        }
        
        return meal
    
    def _filter_meals(
        self,
        diet_type: str,
        meal_type: str,
        restrictions: List[str],
        cuisine_preference: str = None
    ) -> List[Dict[str, Any]]:
        """Filter meals based on criteria."""
        filtered_meals = []
        
        for meal in self.meal_database:
            # Check diet type
            if diet_type != 'standard' and diet_type not in meal.get('diet_types', []):
                continue
            
            # Check meal type
            if meal_type not in meal.get('meal_types', []):
                continue
            
            # Check restrictions
            if any(restriction in meal.get('contains', []) for restriction in restrictions):
                continue
            
            # Check cuisine preference
            if cuisine_preference and cuisine_preference != meal.get('cuisine'):
                continue
            
            filtered_meals.append(meal)
        
        return filtered_meals
    
    def _select_meal_by_calories(
        self,
        meals: List[Dict[str, Any]],
        target_calories: int
    ) -> Dict[str, Any]:
        """Select meal closest to target calories."""
        if not meals:
            return None
        
        # Sort by calorie difference
        sorted_meals = sorted(
            meals,
            key=lambda m: abs(m['calories'] - target_calories)
        )
        
        # Add some randomness to avoid repetition
        top_choices = sorted_meals[:5]
        return random.choice(top_choices)
    
    def _create_basic_meal(
        self,
        calories: int,
        meal_type: str
    ) -> Dict[str, Any]:
        """Create a basic meal as fallback."""
        return {
            'name': f'Custom {meal_type.title()}',
            'type': meal_type,
            'calories': calories,
            'macros': {
                'protein': int(calories * 0.3 / 4),  # 30% from protein, 4 cal/g
                'carbs': int(calories * 0.4 / 4),    # 40% from carbs, 4 cal/g
                'fat': int(calories * 0.3 / 9)       # 30% from fat, 9 cal/g
            },
            'ingredients': ['Customized ingredients based on your preferences'],
            'instructions': ['Prepare according to your dietary needs'],
            'prep_time': 15,
            'cook_time': 20
        }
    
    def _generate_summary(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate meal plan summary."""
        total_meals = sum(len(day['meals']) for day in meal_plan['days'])
        avg_calories = meal_plan['total_calories'] / len(meal_plan['days'])
        
        # Calculate average macros
        total_macros = {'protein': 0, 'carbs': 0, 'fat': 0}
        for day in meal_plan['days']:
            for macro in total_macros:
                total_macros[macro] += day['macros'][macro]
        
        avg_macros = {
            macro: total_macros[macro] / len(meal_plan['days'])
            for macro in total_macros
        }
        
        return {
            'total_days': len(meal_plan['days']),
            'total_meals': total_meals,
            'average_daily_calories': int(avg_calories),
            'average_daily_macros': {
                macro: int(value) for macro, value in avg_macros.items()
            }
        }