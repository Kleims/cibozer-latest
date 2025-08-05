"""API routes for Cibozer."""
import os
import json
import time
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from sqlalchemy import text
from app.models import User, UsageLog, SavedMealPlan
# Import from root directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import meal_optimizer
from app.services.pdf_generator import PDFGenerator
from app.services.video_generator import VideoGenerator
from app.extensions import db, csrf
from app.utils.decorators import check_credits_or_premium
from app.utils.validators import sanitize_input, validate_diet_type
from app.services.email_service import email_service
from app.services.monitoring_service import monitoring_service, monitor_errors, monitor_performance

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Input validation helpers
def validate_calories(calories):
    """Validate calorie input"""
    try:
        cal = int(calories)
        return 1200 <= cal <= 5000  # Reasonable range
    except (ValueError, TypeError):
        return False

def validate_days(days):
    """Validate days input"""
    try:
        d = int(days)
        return 1 <= d <= 30  # Max 30 days
    except (ValueError, TypeError):
        return False

def validate_meal_structure(structure):
    """Validate meal structure"""
    allowed = ['standard', 'two_meals', 'omad', 'five_small']
    return structure in allowed

# Kitchen measurement conversion system for realistic portions
REALISTIC_PORTIONS = {
    # Proteins
    'tofu': {'min': 75, 'max': 150, 'ideal': 110},
    'eggs': {'min': 50, 'max': 200, 'ideal': 100},
    'bacon': {'min': 15, 'max': 60, 'ideal': 30},
    'chicken_breast': {'min': 85, 'max': 225, 'ideal': 113},
    'ribeye_steak': {'min': 85, 'max': 225, 'ideal': 140},
    'salmon': {'min': 85, 'max': 170, 'ideal': 113},
    
    # Vegetables
    'bell_pepper': {'min': 50, 'max': 120, 'ideal': 85},
    'broccoli': {'min': 75, 'max': 200, 'ideal': 125},
    'kale': {'min': 50, 'max': 100, 'ideal': 75},
    'lettuce': {'min': 100, 'max': 300, 'ideal': 200},
    'tomato': {'min': 50, 'max': 150, 'ideal': 100},
    'cucumber': {'min': 50, 'max': 150, 'ideal': 100},
    'cauliflower': {'min': 75, 'max': 150, 'ideal': 100},
    'spinach': {'min': 30, 'max': 100, 'ideal': 50},
    'mushrooms': {'min': 30, 'max': 100, 'ideal': 50},
    'avocado': {'min': 50, 'max': 150, 'ideal': 75},
    
    # Grains & Legumes
    'oats': {'min': 30, 'max': 80, 'ideal': 50},
    'quinoa': {'min': 40, 'max': 85, 'ideal': 60},
    'chickpeas': {'min': 80, 'max': 160, 'ideal': 120},
    'whole_wheat_bread': {'min': 25, 'max': 75, 'ideal': 50},
    
    # Fats & Oils
    'butter': {'min': 5, 'max': 20, 'ideal': 10},
    'olive_oil': {'min': 5, 'max': 30, 'ideal': 15},
    'sesame_oil': {'min': 5, 'max': 15, 'ideal': 10},
    'coconut_oil': {'min': 5, 'max': 15, 'ideal': 10},
    
    # Condiments & Seasonings
    'soy_sauce': {'min': 10, 'max': 30, 'ideal': 15},
    'tahini': {'min': 15, 'max': 45, 'ideal': 25},
    'honey': {'min': 10, 'max': 25, 'ideal': 15},
    'maple_syrup': {'min': 10, 'max': 30, 'ideal': 15},
    'balsamic_vinegar': {'min': 10, 'max': 30, 'ideal': 15},
    'garlic': {'min': 3, 'max': 12, 'ideal': 6},
    'nutritional_yeast': {'min': 5, 'max': 15, 'ideal': 5},
    
    # Dairy & Alternatives
    'milk': {'min': 150, 'max': 300, 'ideal': 240},
    'almond_milk': {'min': 150, 'max': 300, 'ideal': 240},
    'heavy_cream': {'min': 30, 'max': 120, 'ideal': 60},
    'parmesan_cheese': {'min': 15, 'max': 30, 'ideal': 20},
    'cheddar_cheese': {'min': 30, 'max': 60, 'ideal': 30},
    
    # Fruits & Nuts
    'blueberries': {'min': 50, 'max': 150, 'ideal': 75},
    'apple': {'min': 150, 'max': 200, 'ideal': 150},
    'lemon': {'min': 20, 'max': 40, 'ideal': 20},
    'almond_butter': {'min': 15, 'max': 30, 'ideal': 15},
    'macadamia_nuts': {'min': 15, 'max': 30, 'ideal': 20},
}

KITCHEN_MEASUREMENTS = {
    # Proteins & Meats (by ounces and pieces)
    'eggs': {50: '1 large egg', 100: '2 large eggs', 150: '3 large eggs', 200: '4 large eggs'},
    'egg_whites': {30: '1 egg white', 60: '2 egg whites', 90: '3 egg whites'},
    'bacon': {15: '1 strip', 30: '2 strips', 45: '3 strips', 60: '4 strips'},
    'chicken_breast': {85: '3 oz', 113: '4 oz', 170: '6 oz', 225: '8 oz'},
    'chicken_thigh': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'ground_beef': {85: '3 oz', 113: '4 oz', 170: '6 oz', 225: '8 oz'},
    'ground_turkey': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'ribeye_steak': {85: '3 oz', 113: '4 oz', 170: '6 oz', 225: '8 oz'},
    'beef_sirloin': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'pork_chops': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'lamb_chops': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'salmon': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'cod': {85: '3 oz', 113: '4 oz', 170: '6 oz'},
    'tuna': {85: '3 oz', 113: '4 oz'},
    'shrimp': {85: '3 oz', 113: '4 oz'},
    'tofu': {110: '4 oz', 150: '5 oz'},
    'tempeh': {85: '3 oz', 113: '4 oz'},
    
    # Vegetables (natural portions)
    'avocado': {75: '1/2 medium', 100: '2/3 medium', 150: '1 medium'},
    'bell_pepper': {85: '1 medium', 120: '1 large'},
    'broccoli': {125: '1 cup chopped', 200: '1.5 cups chopped'},
    'cauliflower': {100: '1 cup chopped', 150: '1.5 cups chopped'},
    'carrot': {75: '1 medium', 100: '1 large', 150: '2 medium'},
    'celery': {40: '1 stalk', 80: '2 stalks'},
    'cucumber': {100: '1/2 medium', 150: '3/4 medium'},
    'eggplant': {200: '1/2 medium', 400: '1 medium'},
    'garlic': {3: '1 clove', 6: '2 cloves', 9: '3 cloves', 12: '4 cloves'},
    'ginger': {5: '1 tsp minced', 10: '2 tsp minced', 15: '1 tbsp minced'},
    'kale': {75: '2 cups chopped', 100: '3 cups chopped'},
    'lettuce': {100: '2 cups chopped', 200: '4 cups chopped'},
    'mushrooms': {50: '1/2 cup sliced', 100: '1 cup sliced', 150: '1.5 cups sliced'},
    'onion': {50: '1/2 small', 75: '1 small', 110: '1 medium', 150: '1 large'},
    'potato': {100: '1 small', 150: '1 medium', 200: '1 large'},
    'sweet_potato': {100: '1 small', 150: '1 medium', 200: '1 large'},
    'spinach': {50: '2 cups fresh', 100: '4 cups fresh'},
    'tomato': {75: '1/2 medium', 100: '1 medium', 150: '1 large'},
    'zucchini': {100: '1/2 medium', 150: '3/4 medium', 200: '1 medium'},
    
    # Fruits (by piece and cups)
    'apple': {150: '1 medium', 200: '1 large'},
    'banana': {100: '1 small', 118: '1 medium', 140: '1 large'},
    'orange': {150: '1 medium', 180: '1 large'},
    'lemon': {20: '1/2 lemon juice', 40: '1 lemon juice', 60: 'juice of 1.5 lemons'},
    'lime': {15: '1/2 lime juice', 30: '1 lime juice'},
    'strawberries': {75: '1/2 cup', 150: '1 cup'},
    'blueberries': {75: '1/2 cup', 150: '1 cup'},
    'raspberries': {60: '1/2 cup', 120: '1 cup'},
    'blackberries': {75: '1/2 cup', 150: '1 cup'},
    'grapes': {75: '1/2 cup', 150: '1 cup'},
    'pineapple': {80: '1/2 cup chunks', 160: '1 cup chunks'},
    'mango': {100: '1/2 cup diced', 200: '1 cup diced'},
    
    # Grains & Legumes (cups and servings)
    'oats': {40: '1/2 cup dry', 50: '2/3 cup dry', 80: '1 cup dry'},
    'quinoa': {60: '1/3 cup dry', 85: '1/2 cup dry', 170: '1 cup dry'},
    'brown_rice': {50: '1/4 cup dry', 95: '1/2 cup dry', 190: '1 cup dry'},
    'white_rice': {50: '1/4 cup dry', 95: '1/2 cup dry', 190: '1 cup dry'},
    'pasta': {55: '2 oz dry', 85: '3 oz dry', 115: '4 oz dry'},
    'whole_wheat_bread': {25: '1 slice', 50: '2 slices', 75: '3 slices'},
    'white_bread': {25: '1 slice', 50: '2 slices'},
    'chickpeas': {80: '1/2 cup', 120: '3/4 cup', 160: '1 cup'},
    'black_beans': {85: '1/2 cup', 130: '3/4 cup', 170: '1 cup'},
    'lentils': {50: '1/4 cup dry', 100: '1/2 cup dry', 200: '1 cup dry'},
    'kidney_beans': {85: '1/2 cup', 170: '1 cup'},
    
    # Nuts & Seeds (tablespoons and handfuls)
    'almonds': {15: '1 tbsp', 30: '2 tbsp', 45: '3 tbsp', 28: '1 oz'},
    'walnuts': {15: '1 tbsp chopped', 30: '2 tbsp chopped', 28: '1 oz'},
    'cashews': {15: '1 tbsp', 30: '2 tbsp', 28: '1 oz'},
    'pecans': {15: '1 tbsp chopped', 30: '2 tbsp chopped'},
    'pine_nuts': {10: '1 tbsp', 20: '2 tbsp'},
    'macadamia_nuts': {15: '1 tbsp', 30: '2 tbsp'},
    'pistachios': {15: '1 tbsp', 30: '2 tbsp'},
    'sunflower_seeds': {15: '1 tbsp', 30: '2 tbsp'},
    'pumpkin_seeds': {15: '1 tbsp', 30: '2 tbsp'},
    'chia_seeds': {12: '1 tbsp', 24: '2 tbsp'},
    'flax_seeds': {7: '1 tbsp ground', 14: '2 tbsp ground'},
    'sesame_seeds': {8: '1 tbsp', 16: '2 tbsp'},
    
    # Nut & Seed Butters
    'almond_butter': {15: '1 tbsp', 30: '2 tbsp'},
    'peanut_butter': {15: '1 tbsp', 30: '2 tbsp'},
    'cashew_butter': {15: '1 tbsp', 30: '2 tbsp'},
    'sunflower_butter': {15: '1 tbsp', 30: '2 tbsp'},
    'tahini': {15: '1 tbsp', 30: '2 tbsp'},
    
    # Fats & Oils (teaspoons and tablespoons)
    'butter': {5: '1 tsp', 10: '2 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'ghee': {5: '1 tsp', 15: '1 tbsp'},
    'olive_oil': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'coconut_oil': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'avocado_oil': {5: '1 tsp', 15: '1 tbsp'},
    'sesame_oil': {5: '1 tsp', 10: '2 tsp', 15: '1 tbsp'},
    'vegetable_oil': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'canola_oil': {5: '1 tsp', 15: '1 tbsp'},
    
    # Dairy & Alternatives (cups and ounces)
    'milk': {240: '1 cup', 360: '1.5 cups', 480: '2 cups'},
    'almond_milk': {240: '1 cup', 360: '1.5 cups'},
    'oat_milk': {240: '1 cup', 360: '1.5 cups'},
    'coconut_milk': {240: '1 cup', 400: 'canned (13.5 oz)'},
    'heavy_cream': {60: '1/4 cup', 120: '1/2 cup', 240: '1 cup'},
    'half_and_half': {60: '1/4 cup', 120: '1/2 cup'},
    'greek_yogurt': {125: '1/2 cup', 250: '1 cup'},
    'cottage_cheese': {125: '1/2 cup', 250: '1 cup'},
    'cream_cheese': {15: '1 tbsp', 30: '2 tbsp'},
    'sour_cream': {15: '1 tbsp', 30: '2 tbsp'},
    
    # Cheeses (ounces and cups)
    'cheddar_cheese': {28: '1 oz', 56: '2 oz', 60: '1/4 cup shredded'},
    'mozzarella_cheese': {28: '1 oz', 60: '1/4 cup shredded'},
    'parmesan_cheese': {5: '1 tbsp grated', 15: '3 tbsp grated', 30: '1/4 cup grated'},
    'feta_cheese': {28: '1 oz', 75: '1/3 cup crumbled'},
    'goat_cheese': {28: '1 oz', 60: '2 oz'},
    'swiss_cheese': {28: '1 oz', 56: '2 oz'},
    
    # Sweeteners (tablespoons and teaspoons)
    'honey': {7: '1/2 tbsp', 15: '1 tbsp', 30: '2 tbsp'},
    'maple_syrup': {15: '1 tbsp', 30: '2 tbsp', 60: '1/4 cup'},
    'agave_nectar': {15: '1 tbsp', 30: '2 tbsp'},
    'brown_sugar': {12: '1 tbsp', 15: '1 tbsp packed', 30: '2 tbsp'},
    'white_sugar': {12: '1 tbsp', 25: '2 tbsp'},
    'coconut_sugar': {12: '1 tbsp', 25: '2 tbsp'},
    
    # Condiments & Sauces
    'soy_sauce': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'tamari': {5: '1 tsp', 15: '1 tbsp'},
    'balsamic_vinegar': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'apple_cider_vinegar': {5: '1 tsp', 15: '1 tbsp'},
    'rice_vinegar': {5: '1 tsp', 15: '1 tbsp'},
    'lemon_juice': {15: '1 tbsp', 30: '2 tbsp', 60: '1/4 cup'},
    'lime_juice': {15: '1 tbsp', 30: '2 tbsp'},
    'hot_sauce': {2.5: '1/2 tsp', 5: '1 tsp'},
    'sriracha': {5: '1 tsp', 15: '1 tbsp'},
    'dijon_mustard': {5: '1 tsp', 15: '1 tbsp'},
    'mayonnaise': {15: '1 tbsp', 30: '2 tbsp'},
    'ketchup': {15: '1 tbsp', 30: '2 tbsp'},
    
    # Herbs & Spices (teaspoons and tablespoons)
    'basil': {1: '1/2 tsp dried', 2: '1 tsp dried', 5: '1 tbsp fresh'},
    'oregano': {1: '1/2 tsp', 2: '1 tsp'},
    'thyme': {1: '1/2 tsp', 2: '1 tsp'},
    'rosemary': {1: '1/2 tsp', 2: '1 tsp'},
    'cilantro': {3: '1 tbsp chopped', 6: '2 tbsp chopped'},
    'parsley': {3: '1 tbsp chopped', 6: '2 tbsp chopped'},
    'dill': {1: '1 tsp dried', 3: '1 tbsp fresh'},
    'mint': {2: '1 tsp dried', 6: '2 tbsp fresh'},
    'cinnamon': {2: '1 tsp', 4: '2 tsp'},
    'cumin': {2: '1 tsp', 4: '2 tsp'},
    'paprika': {2: '1 tsp', 4: '2 tsp'},
    'chili_powder': {2: '1 tsp', 4: '2 tsp'},
    'turmeric': {2: '1 tsp', 4: '2 tsp'},
    'black_pepper': {1: '1/2 tsp', 2: '1 tsp'},
    'cayenne_pepper': {0.5: '1/4 tsp', 1: '1/2 tsp'},
    'nutmeg': {1: '1/2 tsp', 2: '1 tsp'},
    'vanilla': {5: '1 tsp extract', 15: '1 tbsp extract'},
    
    # Special Ingredients
    'nutritional_yeast': {5: '1 tsp', 15: '1 tbsp', 30: '2 tbsp'},
    'cocoa_powder': {5: '1 tbsp', 15: '3 tbsp', 30: '1/4 cup'},
    'protein_powder_whey': {30: '1 scoop', 60: '2 scoops'},
    'chia_seeds': {12: '1 tbsp', 24: '2 tbsp'},
    'gelatin': {7: '1 packet', 15: '1 tbsp'},
    'baking_powder': {4: '1 tsp', 8: '2 tsp'},
    'baking_soda': {4: '1 tsp', 8: '2 tsp'},
}

def convert_to_kitchen_measurement(amount, unit, item):
    """Convert to practical kitchen measurements"""
    item = item.lower().replace(' ', '_')
    
    # Handle specific ingredient conversions
    if item in KITCHEN_MEASUREMENTS:
        conversions = KITCHEN_MEASUREMENTS[item]
        # Find closest measurement 
        best_match = min(conversions.keys(), key=lambda x: abs(x - amount))
        difference_percent = abs(best_match - amount) / best_match
        
        if difference_percent < 0.15:  # Within 15% - exact match
            return conversions[best_match]
        elif difference_percent < 0.35:  # Within 35% - show approximate
            return f"~{conversions[best_match]}"
        # If difference is too large, fall through to other logic
    
    # Special handling for common ingredient types
    if 'egg' in item:
        egg_count = amount / 50  # ~50g per large egg
        # Round to nearest practical whole number
        rounded_eggs = round(egg_count)
        if rounded_eggs == 0:
            rounded_eggs = 1  # Always at least 1 egg
        return f'{rounded_eggs} large egg{"s" if rounded_eggs > 1 else ""}'
    
    if item in ['butter', 'margarine'] and unit == 'g':
        if amount <= 5: return '1 tsp'
        elif amount <= 10: return '2 tsp'
        elif amount <= 15: return '1 tbsp'
        elif amount <= 30: return '2 tbsp'
        else: return f'{round(amount/15)} tbsp'
    
    if 'garlic' in item and unit == 'g':
        cloves = amount / 3  # ~3g per clove
        rounded_cloves = round(cloves)
        if rounded_cloves == 0:
            rounded_cloves = 1  # Always at least 1 clove
        return f'{rounded_cloves} clove{"s" if rounded_cloves > 1 else ""}'
    
    if 'bacon' in item and unit == 'g':
        strips = amount / 15  # ~15g per strip
        rounded_strips = round(strips)  
        if rounded_strips == 0:
            rounded_strips = 1  # Always at least 1 strip
        return f'{rounded_strips} strip{"s" if rounded_strips > 1 else ""} bacon'
    
    # Fallback to standard measurements
    if unit == 'ml':
        if amount <= 2.5: return '1/2 tsp'
        elif amount <= 5: return '1 tsp'
        elif amount <= 10: return '2 tsp'
        elif amount <= 15: return '1 tbsp'
        elif amount <= 30: return '2 tbsp'
        elif amount <= 60: return '1/4 cup'
        elif amount <= 125: return '1/2 cup'
        elif amount <= 250: return '1 cup'
        else: return f'{round(amount/250, 1)} cups'
    elif unit == 'g':
        # For solids, use more natural presentations
        if amount >= 450: return f'{round(amount/454)} lb'  # Convert to pounds for large amounts
        elif amount >= 100: return f'{round(amount)}g'
        elif amount >= 10: return f'{round(amount)}g'
        else: return f'{round(amount, 1)}g'
    
    return f'{round(amount, 1)}{unit}'

def get_practical_portion(amount, unit, item, measurement_system='US'):
    """Convert to practical portions and return both adjusted amount and display text.
    
    Applies variability thresholds to prevent excessive nutritional deviations:
    - General ingredients: 25% max deviation
    - Calorie-dense fats/oils: 20% max deviation  
    - High-protein items: 25% max deviation
    - Discrete items (eggs, cloves): 25% max deviation
    
    Args:
        amount: Original amount in grams/ml
        unit: Original unit ('g' or 'ml')  
        item: Ingredient name
        measurement_system: 'US' for imperial, 'Metric' for metric
    
    If threshold exceeded, falls back to precise amounts with descriptive text.
    """
    item = item.lower().replace(' ', '_')
    
    def check_deviation_threshold(original_amount, practical_amount, max_deviation=0.25):
        """Check if practical amount exceeds deviation threshold."""
        if original_amount == 0:
            return True
        deviation = abs(practical_amount - original_amount) / original_amount
        return deviation <= max_deviation
    
    def convert_to_imperial_weight(grams):
        """Convert grams to imperial weight (oz/lb)."""
        if grams >= 454:  # 1 pound
            pounds = grams / 454
            if pounds >= 2:
                return f'{pounds:.1f} lbs'
            else:
                return f'{pounds:.1f} lb'
        else:
            oz = grams / 28.35
            return f'{oz:.1f} oz'
    
    def get_metric_display(amount, unit, item_name):
        """Get metric display format."""
        if unit == 'ml':
            if amount >= 1000:
                return f'{amount/1000:.1f}L {item_name}'
            else:
                return f'{round(amount)}ml {item_name}'
        else:  # grams
            if amount >= 1000:
                return f'{amount/1000:.1f}kg {item_name}'
            else:
                return f'{round(amount)}g {item_name}'
    
    # Handle discrete items that need whole numbers
    if 'egg' in item:
        egg_count = amount / 50  # ~50g per large egg
        rounded_eggs = round(egg_count)
        if rounded_eggs == 0:
            rounded_eggs = 1
        practical_amount = rounded_eggs * 50  # Convert back to grams
        
        # Check deviation threshold
        if not check_deviation_threshold(amount, practical_amount):
            # If deviation too high, use precise amount with descriptive text
            if measurement_system == 'Metric':
                display = f'{round(amount)}g eggs (~{amount/50:.1f} eggs)'
            else:
                display = f'{convert_to_imperial_weight(amount)} eggs (~{amount/50:.1f} eggs)'
            return amount, display
        
        # Eggs are universal - use count for both systems with size indicator
        if measurement_system == 'Metric':
            display = f'{rounded_eggs} large egg{"s" if rounded_eggs > 1 else ""} ({practical_amount}g)'
        else:
            display = f'{rounded_eggs} large egg{"s" if rounded_eggs > 1 else ""}'
        return practical_amount, display
    
    if 'garlic' in item and unit == 'g':
        cloves = amount / 3  # ~3g per clove
        rounded_cloves = round(cloves)
        if rounded_cloves == 0:
            rounded_cloves = 1
        practical_amount = rounded_cloves * 3  # Convert back to grams
        display = f'{rounded_cloves} clove{"s" if rounded_cloves > 1 else ""}'
        return practical_amount, display
    
    if 'bacon' in item and unit == 'g':
        strips = amount / 15  # ~15g per strip
        rounded_strips = round(strips)
        if rounded_strips == 0:
            rounded_strips = 1
        practical_amount = rounded_strips * 15  # Convert back to grams
        display = f'{rounded_strips} strip{"s" if rounded_strips > 1 else ""} bacon'
        return practical_amount, display
    
    # Handle butter and oils - round to practical teaspoons/tablespoons
    if item in ['butter', 'olive_oil', 'coconut_oil', 'vegetable_oil', 'sesame_oil'] and unit == 'g':
        # Convert grams to ml (roughly 1:1 for oils, butter ~0.9)
        ml_amount = amount * 0.9 if 'butter' in item else amount
        
        # Determine practical measurement
        if ml_amount <= 3:  # Round to 1 tsp (5ml)
            practical_amount = 5
            display = '1 tsp'
        elif ml_amount <= 8:  # Round to 1.5 tsp
            practical_amount = 7.5
            display = '1.5 tsp'  
        elif ml_amount <= 12:  # Round to 1 tbsp (15ml)
            practical_amount = 15
            display = '1 tbsp'
        elif ml_amount <= 22:  # Round to 1.5 tbsp
            practical_amount = 22.5
            display = '1.5 tbsp'
        elif ml_amount <= 37:  # Round to 2 tbsp (30ml)
            practical_amount = 30
            display = '2 tbsp'
        else:
            # Round to nearest tablespoon
            tbsp_count = round(ml_amount / 15)
            practical_amount = tbsp_count * 15
            display = f'{tbsp_count} tbsp'
        
        # Check deviation threshold - oils/fats are calorie-dense, be strict
        if not check_deviation_threshold(amount, practical_amount, max_deviation=0.20):
            # If deviation too high, use precise amount in requested system
            item_name = item.replace("_", " ")
            if measurement_system == 'Metric':
                display = get_metric_display(amount, unit, item_name)
            else:
                display = convert_to_imperial_weight(amount) + f' {item_name}'
            return amount, display
        
        # Convert back to grams for butter (ml * 1.1) or keep as grams for oils
        final_amount = practical_amount * 1.1 if 'butter' in item else practical_amount
        
        # US system uses tablespoons/teaspoons, Metric uses ml/grams
        if measurement_system == 'Metric':
            if 'butter' in item:
                display = f'{round(final_amount)}g {item.replace("_", " ")}'
            else:
                display = f'{round(practical_amount)}ml {item.replace("_", " ")}'
        # else use the original US display (already set above)
        
        return final_amount, display
    
    # Handle vegetables - allow some flexibility but round to reasonable amounts
    if item in ['onion', 'bell_pepper', 'carrot', 'tomato', 'potato', 'sweet_potato']:
        if item == 'onion':
            if amount <= 60:  # Small onion (~50g)
                return 50, '1 small onion'
            elif amount <= 90:  # Medium onion (~75g) 
                return 75, '1 medium onion'
            else:  # Large onion (~110g)
                return 110, '1 large onion'
        
        elif item == 'bell_pepper':
            if amount <= 90:  # Medium pepper (~85g)
                return 85, '1 medium bell pepper'
            else:  # Large pepper (~120g)
                return 120, '1 large bell pepper'
        
        # Add more vegetables as needed...
    
    # For measured items in KITCHEN_MEASUREMENTS, round to practical amounts
    if item in KITCHEN_MEASUREMENTS:
        conversions = KITCHEN_MEASUREMENTS[item]
        best_match = min(conversions.keys(), key=lambda x: abs(x - amount))
        difference_percent = abs(best_match - amount) / best_match
        
        if difference_percent < 0.3:  # Within 30% - round to practical amount
            return best_match, conversions[best_match]
    
    # For everything else, use the convert function but keep original amount
    # Apply measurement system preference for fallback cases
    if measurement_system == 'Metric':
        item_name = item.replace('_', ' ')
        display = get_metric_display(amount, unit, item_name)
    else:
        # Check if it's a weight ingredient that should use imperial
        if unit == 'g' and item not in ['garlic', 'bacon'] and amount >= 20:
            item_name = item.replace('_', ' ')
            display = convert_to_imperial_weight(amount) + f' {item_name}'
        else:
            display = convert_to_kitchen_measurement(amount, unit, item)
    
    return amount, display

def fix_meal_plan_portions(meal_plan, measurement_system='US'):
    """Fix meal plan to have realistic portions"""
    if not meal_plan or 'days' not in meal_plan:
        return meal_plan
    
    for day in meal_plan['days']:
        if 'meals' not in day:
            continue
            
        for meal in day['meals']:
            if 'ingredients' not in meal:
                continue
            
            for ingredient in meal['ingredients']:
                if not isinstance(ingredient, dict):
                    continue
                
                amount = ingredient.get('amount', 0)
                unit = ingredient.get('unit', 'g')
                item = ingredient.get('item', '').lower()
                
                # Apply realistic portions
                if item in REALISTIC_PORTIONS:
                    limits = REALISTIC_PORTIONS[item]
                    if amount > limits['max'] * 1.5:  # Way too much
                        ingredient['amount'] = limits['ideal']
                    elif amount > limits['max']:
                        ingredient['amount'] = limits['max']
                    elif amount < limits['min']:
                        ingredient['amount'] = limits['min']
                
                # Round to practical portions and adjust amounts
                original_amount = ingredient['amount']
                practical_amount, kitchen_measurement = get_practical_portion(
                    original_amount, unit, item, measurement_system
                )
                
                # Update the actual amount to match the display
                ingredient['amount'] = practical_amount
                ingredient['kitchen_measurement'] = kitchen_measurement
    
    return meal_plan

# Rate limiting helper
def rate_limit_check(user_id, action='api_call', limit=10, window=3600):
    """Check if user has exceeded rate limit."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window)
    recent_count = UsageLog.query.filter(
        UsageLog.user_id == user_id,
        UsageLog.action == action,
        UsageLog.created_at > cutoff
    ).count()
    return recent_count < limit

@api_bp.route('/generate', methods=['POST'])
@login_required
@check_credits_or_premium
@monitor_performance('meal_plan_generation')
@monitor_errors('error')
@csrf.exempt  # API endpoints should be exempt from CSRF - must be last decorator
def generate_meal_plan():
    """Generate a meal plan based on user preferences."""
    try:
        # Comprehensive debug logging
        print("\n" + "="*60)
        print(f"[DEBUG] REQUEST RECEIVED at {datetime.now()}")
        print(f"[DEBUG] Request method: {request.method}")
        print(f"[DEBUG] Request URL: {request.url}")
        print(f"[DEBUG] Request endpoint: {request.endpoint}")
        print(f"[DEBUG] Request remote_addr: {request.remote_addr}")
        print(f"[DEBUG] Request headers:")
        for header, value in request.headers:
            print(f"  {header}: {value}")
        print(f"[DEBUG] Request content_type: {request.content_type}")
        print(f"[DEBUG] Request mimetype: {request.mimetype}")
        print(f"[DEBUG] Request is_json: {request.is_json}")
        print(f"[DEBUG] Request data length: {len(request.data)} bytes")
        print(f"[DEBUG] Request data (first 500 chars): {request.data[:500]}")
        print(f"[DEBUG] User authenticated: {current_user.is_authenticated}")
        print(f"[DEBUG] User email: {current_user.email if current_user.is_authenticated else 'Not authenticated'}")
        print("="*60 + "\n")
        
        # Rate limiting
        if not current_user.is_premium() and not rate_limit_check(current_user.id, 'meal_generation'):
            return jsonify({
                'error': 'Rate limit exceeded. Please try again later.',
                'rate_limit': True
            }), 429
        
        # Try to get JSON data with force=True to bypass Content-Type check
        data = request.get_json(force=True)
        
        if not data:
            print(f"[DEBUG] No data received. Request data: {request.data}")
            return jsonify({'error': 'No data received'}), 400
        
        print(f"[DEBUG] Successfully parsed data: {data}")
        
        # Validate and sanitize input (match frontend parameter names)
        calories = data.get('calories', 2000)
        if not validate_calories(calories):
            return jsonify({'error': 'Invalid calorie amount. Must be between 1200 and 5000.'}), 400
        calories = int(calories)
        
        diet_type = sanitize_input(data.get('diet', 'standard'))  # Frontend sends 'diet'
        if not validate_diet_type(diet_type):
            return jsonify({'error': 'Invalid diet type'}), 400
            
        meal_structure = data.get('meal_structure', 'standard')   # Frontend sends 'meal_structure'
        if not validate_meal_structure(meal_structure):
            return jsonify({'error': 'Invalid meal structure'}), 400
            
        days = data.get('days', 1)
        if not validate_days(days):
            return jsonify({'error': 'Invalid number of days. Must be between 1 and 30.'}), 400
        days = int(days)
        
        restrictions = data.get('restrictions', [])
        if not isinstance(restrictions, list):
            return jsonify({'error': 'Restrictions must be a list'}), 400
            
        cuisine = sanitize_input(data.get('cuisine_preference'))
        measurement_system = data.get('measurement_system', 'US')  # 'US' or 'Metric'
        
        if measurement_system not in ['US', 'Metric']:
            measurement_system = 'US'
        
        # Convert meal_structure to meals_per_day
        meals_per_day = 3  # Default
        if meal_structure == 'standard':
            meals_per_day = 3
        
        # Initialize optimizer (using the global meal_optimizer module)
        optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
        
        # Generate meal plan for each day
        all_days = []
        total_calories = 0
        
        for day_num in range(1, days + 1):
            day_meals, metrics = optimizer.generate_single_day_plan({
                'diet': diet_type,
                'calories': calories,
                'pattern': meal_structure,
                'restrictions': restrictions,
                'cuisines': ['all'],
                'cooking_methods': ['all'],
                'measurement_system': 'US',
                'allow_substitutions': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Convert day_meals dict to list of meal dictionaries
            meals_list = list(day_meals.values())
            day_calories = sum(meal.get('calories', 0) for meal in meals_list)
            total_calories += day_calories
            
            all_days.append({
                'day': day_num,
                'meals': meals_list,
                'total_calories': day_calories,
                'macros': {
                    'protein': sum(meal.get('macros', {}).get('protein', 0) for meal in meals_list),
                    'carbs': sum(meal.get('macros', {}).get('carbs', 0) for meal in meals_list),
                    'fat': sum(meal.get('macros', {}).get('fat', 0) for meal in meals_list)
                }
            })
        
        # Create meal plan structure
        meal_plan = {
            'days': all_days,
            'total_calories': total_calories,
            'diet_type': diet_type,
            'summary': {
                'total_days': days,
                'total_meals': sum(len(day['meals']) for day in all_days),
                'average_daily_calories': total_calories / days if days > 0 else 0
            }
        }
        
        # Fix portions to be realistic and kitchen-friendly
        realistic_plan = fix_meal_plan_portions(meal_plan, measurement_system)
        
        # Format for frontend
        formatted_plan = format_meal_plan_for_frontend(realistic_plan)
        
        # Deduct credits if not premium
        if not current_user.is_premium():
            current_user.use_credits(1)
            db.session.commit()
        
        # Log usage
        log_usage('meal_generation', {
            'calories': calories,
            'diet_type': diet_type,
            'days': days,
            'meal_structure': meal_structure
        })
        
        # Check if this is user's first meal plan and send celebration email
        user_plans_count = UsageLog.query.filter_by(
            user_id=current_user.id,
            action='meal_generation'
        ).count()
        
        if user_plans_count == 1:  # This is their first meal plan
            meal_plan_info = {
                'days': days,
                'calories': calories,
                'diet_type': diet_type
            }
            email_service.send_first_meal_plan_celebration(
                current_user.email, 
                current_user.full_name, 
                meal_plan_info
            )
        
        return jsonify({
            'success': True,
            'meal_plan': formatted_plan,
            'credits_remaining': current_user.credits_balance
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Error generating meal plan: {str(e)}")
        current_app.logger.error(f"Full traceback: {error_details}")
        print(f"MEAL PLAN ERROR: {str(e)}")
        print(f"FULL TRACEBACK: {error_details}")
        return jsonify({'error': f'Failed to generate meal plan: {str(e)}'}), 500

@api_bp.route('/export-grocery-list', methods=['POST'])
@login_required
@csrf.exempt
def export_grocery_list():
    """Export grocery list from meal plan."""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Extract and categorize ingredients
        grocery_list = categorize_grocery_items(meal_plan)
        
        # Create text file
        grocery_text = generate_grocery_list_text(grocery_list)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(grocery_text)
        temp_file.close()
        
        # Log usage
        log_usage('grocery_export')
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'grocery_list_{datetime.now().strftime("%Y%m%d")}.txt',
            mimetype='text/plain'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting grocery list: {str(e)}")
        return jsonify({'error': 'Failed to export grocery list'}), 500

@api_bp.route('/save-meal-plan', methods=['POST'])
@login_required
@monitor_performance('save_meal_plan')
@monitor_errors('error')
@csrf.exempt
def save_meal_plan():
    """Save meal plan to database."""
    try:
        data = request.get_json()
        
        name = sanitize_input(data.get('name', 'Untitled Meal Plan'), max_length=200)
        meal_plan_data = data.get('meal_plan')
        
        if not meal_plan_data:
            return jsonify({'error': 'No meal plan data provided'}), 400
        
        # Validate meal plan structure
        if not isinstance(meal_plan_data, dict) or 'days' not in meal_plan_data:
            return jsonify({'error': 'Invalid meal plan format'}), 400
        
        # Create saved meal plan
        saved_plan = SavedMealPlan(
            user_id=current_user.id,
            name=name,
            meal_plan_data=meal_plan_data,
            total_calories=meal_plan_data.get('total_calories'),
            diet_type=meal_plan_data.get('diet_type'),
            days=len(meal_plan_data.get('days', []))
        )
        
        db.session.add(saved_plan)
        db.session.commit()
        
        # Log usage
        try:
            log_usage('meal_plan_saved', {'plan_id': saved_plan.id})
        except Exception as log_error:
            current_app.logger.warning(f"Failed to log usage: {str(log_error)}")
        
        return jsonify({
            'success': True,
            'id': saved_plan.id,
            'message': 'Meal plan saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving meal plan: {str(e)}")
        monitoring_service.log_error('save_meal_plan_error', {
            'error': str(e),
            'user_id': current_user.id if current_user.is_authenticated else None
        })
        return jsonify({'error': 'Failed to save meal plan'}), 500

@api_bp.route('/load-meal-plans', methods=['GET'])
@login_required
def load_meal_plans():
    """Load user's saved meal plans."""
    try:
        plans = SavedMealPlan.query.filter_by(
            user_id=current_user.id
        ).order_by(SavedMealPlan.created_at.desc()).all()
        
        plans_data = [{
            'id': plan.id,
            'name': plan.name,
            'created_at': plan.created_at.isoformat(),
            'total_calories': plan.total_calories,
            'diet_type': plan.diet_type,
            'days': plan.days
        } for plan in plans]
        
        return jsonify({
            'success': True,
            'meal_plans': plans_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading meal plans: {str(e)}")
        return jsonify({'error': 'Failed to load meal plans'}), 500

@api_bp.route('/load-meal-plan/<int:plan_id>', methods=['GET'])
@login_required
def load_meal_plan(plan_id):
    """Load specific meal plan."""
    try:
        plan = SavedMealPlan.query.filter_by(
            id=plan_id,
            user_id=current_user.id
        ).first()
        
        if not plan:
            return jsonify({'error': 'Meal plan not found'}), 404
        
        return jsonify({
            'success': True,
            'meal_plan': plan.meal_plan_data,
            'name': plan.name
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading meal plan: {str(e)}")
        return jsonify({'error': 'Failed to load meal plan'}), 500

@api_bp.route('/delete-meal-plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_meal_plan(plan_id):
    """Delete saved meal plan."""
    try:
        plan = SavedMealPlan.query.filter_by(
            id=plan_id,
            user_id=current_user.id
        ).first()
        
        if not plan:
            return jsonify({'error': 'Meal plan not found'}), 404
        
        # Delete associated files if they exist
        if plan.pdf_url:
            try:
                os.remove(plan.pdf_url)
            except:
                pass
        
        if plan.video_url:
            try:
                os.remove(plan.video_url)
            except:
                pass
        
        db.session.delete(plan)
        db.session.commit()
        
        # Log usage
        log_usage('meal_plan_deleted', {'plan_id': plan_id})
        
        return jsonify({
            'success': True,
            'message': 'Meal plan deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting meal plan: {str(e)}")
        return jsonify({'error': 'Failed to delete meal plan'}), 500

@api_bp.route('/export-pdf', methods=['POST'])
@login_required
@monitor_performance('pdf_export')
@monitor_errors('error')
@csrf.exempt
def export_pdf():
    """Export meal plan as PDF."""
    try:
        if not current_user.is_premium():
            return jsonify({'error': 'PDF export requires a premium subscription'}), 403
        
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        title = sanitize_input(data.get('title', 'My Meal Plan'))
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        pdf_path = pdf_generator.generate_meal_plan_pdf(meal_plan, title)
        
        # Log usage
        log_usage('pdf_export')
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'meal_plan_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting PDF: {str(e)}")
        return jsonify({'error': 'Failed to export PDF'}), 500

@api_bp.route('/generate-video', methods=['POST'])
@login_required
@csrf.exempt
def generate_video():
    """Generate video from meal plan."""
    try:
        if not current_user.is_premium():
            return jsonify({'error': 'Video generation requires a premium subscription'}), 403
        
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        platform = data.get('platform', 'youtube')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate video
        video_generator = VideoGenerator()
        video_url = video_generator.generate_meal_plan_video(
            meal_plan,
            platform=platform
        )
        
        # Log usage
        log_usage('video_generation', {'platform': platform})
        
        return jsonify({
            'success': True,
            'video_url': video_url
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating video: {str(e)}")
        return jsonify({'error': 'Failed to generate video'}), 500

@api_bp.route('/user-status', methods=['GET'])
@login_required
def user_status():
    """Get current user status."""
    return jsonify({
        'email': current_user.email,
        'subscription_tier': current_user.subscription_tier,
        'is_premium': current_user.is_premium(),
        'credits_balance': current_user.credits_balance,
        'subscription_status': current_user.subscription_status
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint."""
    start_time = time.time()
    checks = []
    
    # Database health check
    try:
        db.session.execute(text('SELECT 1'))
        db_healthy = True
        checks.append({
            'name': 'database',
            'status': 'healthy',
            'response_time_ms': round((time.time() - start_time) * 1000)
        })
    except Exception as e:
        db_healthy = False
        checks.append({
            'name': 'database',
            'status': 'unhealthy',
            'error': 'Database connection failed',
            'response_time_ms': round((time.time() - start_time) * 1000)
        })
    
    # Memory health check
    try:
        import psutil
        memory = psutil.virtual_memory()
        memory_healthy = memory.percent < 90
        checks.append({
            'name': 'memory',
            'status': 'healthy' if memory_healthy else 'warning',
            'usage_percent': memory.percent,
            'response_time_ms': round((time.time() - start_time) * 1000)
        })
    except ImportError:
        memory_healthy = True  # Skip if psutil not available
        checks.append({
            'name': 'memory',
            'status': 'unknown',
            'message': 'psutil not available'
        })
    except Exception:
        memory_healthy = True
        checks.append({
            'name': 'memory',
            'status': 'unknown',
            'message': 'Unable to check memory'
        })
    
    # Determine overall status
    if db_healthy and memory_healthy:
        overall_status = 'healthy'
    elif db_healthy:
        overall_status = 'degraded'
    else:
        overall_status = 'unhealthy'
    
    total_time = round((time.time() - start_time) * 1000)
    
    return jsonify({
        'status': overall_status,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0',
        'response_time_ms': total_time,
        'checks': checks
    })

@api_bp.route('/test-simple', methods=['POST'])
@csrf.exempt
def test_simple_endpoint():
    """Very simple JSON test endpoint"""
    print(f"\n[SIMPLE] Content-Type: {request.content_type}")
    print(f"[SIMPLE] Data: {request.data}")
    
    try:
        data = request.get_json(force=True)
        return jsonify({'success': True, 'received': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@api_bp.route('/test-json', methods=['POST'])
@csrf.exempt
def test_json_endpoint():
    """Test endpoint to debug JSON handling."""
    print("\n" + "="*60)
    print("[TEST] Request received")
    print(f"[TEST] Method: {request.method}")
    print(f"[TEST] Content-Type: {request.content_type}")
    print(f"[TEST] Headers: {dict(request.headers)}")
    print(f"[TEST] Data: {request.data[:500] if request.data else 'No data'}")
    print("="*60 + "\n")
    
    # Try multiple ways to get data
    try:
        # Method 1: get_json with force
        data1 = request.get_json(force=True)
        print(f"[TEST] get_json(force=True): {data1}")
    except Exception as e:
        print(f"[TEST] get_json(force=True) failed: {e}")
        data1 = None
    
    try:
        # Method 2: get_json without force
        data2 = request.get_json()
        print(f"[TEST] get_json(): {data2}")
    except Exception as e:
        print(f"[TEST] get_json() failed: {e}")
        data2 = None
    
    try:
        # Method 3: parse manually
        import json
        data3 = json.loads(request.data) if request.data else None
        print(f"[TEST] json.loads(request.data): {data3}")
    except Exception as e:
        print(f"[TEST] json.loads failed: {e}")
        data3 = None
    
    return jsonify({
        'success': True,
        'method': request.method,
        'content_type': request.content_type,
        'data_received': data1 or data2 or data3,
        'data_length': len(request.data) if request.data else 0
    })

@api_bp.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint."""
    try:
        # Get basic metrics
        user_count = User.query.count()
        meal_plan_count = SavedMealPlan.query.count()
        
        return jsonify({
            'users': user_count,
            'meal_plans': meal_plan_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except:
        return jsonify({'error': 'Failed to get metrics'}), 500

# Helper functions
def format_meal_plan_for_frontend(meal_plan):
    """Format meal plan for frontend consumption with natural ingredient presentations."""
    if not meal_plan or 'days' not in meal_plan:
        return meal_plan
    
    # Process each day
    for day in meal_plan['days']:
        if 'meals' not in day:
            continue
            
        # Process each meal
        for meal in day['meals']:
            if 'ingredients' not in meal:
                continue
            
            # Convert ingredients to display-friendly format
            formatted_ingredients = []
            for ingredient in meal['ingredients']:
                if not isinstance(ingredient, dict):
                    # Handle string ingredients (fallback)
                    formatted_ingredients.append(str(ingredient))
                    continue
                
                item = ingredient.get('item', '').replace('_', ' ').title()
                
                # Use kitchen measurement if available, otherwise format naturally
                if 'kitchen_measurement' in ingredient and ingredient['kitchen_measurement']:
                    display_text = f"{ingredient['kitchen_measurement']} {item}"
                else:
                    # Fallback formatting
                    amount = ingredient.get('amount', 0)
                    unit = ingredient.get('unit', 'g')
                    kitchen_measurement = convert_to_kitchen_measurement(amount, unit, item)
                    display_text = f"{kitchen_measurement} {item}"
                
                formatted_ingredients.append(display_text)
            
            # Replace ingredients list with formatted strings
            meal['ingredients'] = formatted_ingredients
    
    return meal_plan

def categorize_grocery_items(meal_plan):
    """Categorize grocery items by store section."""
    categories = {
        'produce': [],
        'meat': [],
        'dairy': [],
        'pantry': [],
        'frozen': [],
        'other': []
    }
    
    # Extract ingredients from meal plan
    for day in meal_plan.get('days', []):
        for meal in day.get('meals', []):
            for ingredient in meal.get('ingredients', []):
                # Simple categorization logic
                # In production, this would be more sophisticated
                categories['other'].append(ingredient)
    
    return categories

def generate_grocery_list_text(grocery_list):
    """Generate formatted grocery list text."""
    text = "GROCERY LIST\n"
    text += "=" * 40 + "\n\n"
    
    for category, items in grocery_list.items():
        if items:
            text += f"{category.upper()}\n"
            text += "-" * 20 + "\n"
            for item in items:
                text += f"• {item}\n"
            text += "\n"
    
    return text

def log_usage(action, metadata=None):
    """Log user action."""
    try:
        usage_log = UsageLog(
            user_id=current_user.id,
            action=action,
            metadata=metadata or {},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            endpoint=request.endpoint,
            method=request.method
        )
        db.session.add(usage_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to log usage: {str(e)}")