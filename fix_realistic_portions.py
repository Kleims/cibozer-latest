#!/usr/bin/env python3
"""Fix meal plans to have realistic portions and kitchen measurements"""

import json

# Kitchen measurement conversion system
KITCHEN_MEASUREMENTS = {
    # Volume conversions (ml to kitchen units)
    'ml_to_kitchen': {
        5: '1 tsp',
        15: '1 tbsp', 
        30: '2 tbsp',
        60: '1/4 cup',
        125: '1/2 cup',
        250: '1 cup',
        500: '2 cups',
        750: '3 cups',
        1000: '4 cups'
    },
    
    # Weight conversions (g to kitchen units)
    'g_to_kitchen': {
        # Common ingredient conversions
        'flour': {30: '1/4 cup', 60: '1/2 cup', 125: '1 cup'},
        'sugar': {50: '1/4 cup', 100: '1/2 cup', 200: '1 cup'},
        'oats': {40: '1/2 cup', 80: '1 cup', 160: '2 cups'},
        'rice': {50: '1/4 cup', 95: '1/2 cup', 190: '1 cup'},
        'quinoa': {50: '1/4 cup', 85: '1/2 cup', 170: '1 cup'},
        
        # Proteins (more realistic portions)
        'chicken': {113: '4 oz', 170: '6 oz', 225: '8 oz'},
        'tofu': {85: '3 oz', 140: '5 oz', 225: '8 oz'},
        'fish': {113: '4 oz', 170: '6 oz', 225: '8 oz'},
        
        # Vegetables (reasonable portions)
        'broccoli': {85: '1/2 cup', 150: '1 cup', 300: '2 cups'},
        'bell_pepper': {75: '1/2 medium', 120: '1 medium', 240: '2 medium'},
        'onion': {60: '1/2 small', 110: '1 medium', 150: '1 large'},
        'carrot': {60: '1 small', 85: '1 medium', 125: '1 large'},
        
        # Nuts and seeds
        'almonds': {15: '1 tbsp', 30: '1/4 cup', 60: '1/2 cup'},
        'tahini': {15: '1 tbsp', 30: '2 tbsp', 60: '1/4 cup'},
        
        # General weight guidelines
        'default': {15: '1 tbsp', 30: '2 tbsp', 60: '1/4 cup', 125: '1/2 cup', 250: '1 cup'}
    }
}

# Realistic portion limits per meal
REALISTIC_PORTIONS = {
    # Proteins (grams)
    'tofu': {'min': 75, 'max': 150, 'ideal': 110},
    'chicken': {'min': 85, 'max': 170, 'ideal': 113},
    'fish': {'min': 85, 'max': 170, 'ideal': 113},
    'eggs': {'min': 50, 'max': 150, 'ideal': 100},  # ~2 eggs
    'chickpeas': {'min': 80, 'max': 160, 'ideal': 120},
    
    # Vegetables (grams)
    'broccoli': {'min': 75, 'max': 200, 'ideal': 125},
    'bell_pepper': {'min': 50, 'max': 120, 'ideal': 85},
    'onion': {'min': 30, 'max': 110, 'ideal': 70},
    'kale': {'min': 50, 'max': 100, 'ideal': 75},
    
    # Grains (grams dry weight)
    'oats': {'min': 30, 'max': 80, 'ideal': 50},
    'quinoa': {'min': 40, 'max': 85, 'ideal': 60},
    'rice': {'min': 45, 'max': 95, 'ideal': 70},
    
    # Oils and sauces (ml)
    'olive_oil': {'min': 5, 'max': 15, 'ideal': 10},
    'sesame_oil': {'min': 5, 'max': 15, 'ideal': 10},
    'soy_sauce': {'min': 10, 'max': 30, 'ideal': 15},
    
    # Dairy
    'milk': {'min': 150, 'max': 300, 'ideal': 240},  # ~1 cup
    'cheese': {'min': 15, 'max': 60, 'ideal': 30},
}

def convert_to_kitchen_measurement(amount, unit, item):
    """Convert amounts to practical kitchen measurements"""
    
    # Round to practical amounts first
    if unit == 'g':
        # Get realistic portion for this ingredient
        if item in REALISTIC_PORTIONS:
            limits = REALISTIC_PORTIONS[item]
            # Clamp to realistic range
            amount = max(limits['min'], min(limits['max'], amount))
        
        # Convert to kitchen measurement
        if item in KITCHEN_MEASUREMENTS['g_to_kitchen']:
            conversions = KITCHEN_MEASUREMENTS['g_to_kitchen'][item]
        else:
            conversions = KITCHEN_MEASUREMENTS['g_to_kitchen']['default']
        
        # Find closest kitchen measurement
        for weight, measurement in sorted(conversions.items()):
            if amount <= weight * 1.2:  # Allow 20% tolerance
                return measurement
        
        # If too large, use largest measurement
        largest = max(conversions.keys())
        return conversions[largest]
    
    elif unit == 'ml':
        # Clamp to realistic range for liquids
        if item in REALISTIC_PORTIONS:
            limits = REALISTIC_PORTIONS[item]
            amount = max(limits['min'], min(limits['max'], amount))
        
        # Convert to kitchen measurement
        conversions = KITCHEN_MEASUREMENTS['ml_to_kitchen']
        for volume, measurement in sorted(conversions.items()):
            if amount <= volume * 1.2:  # Allow 20% tolerance
                return measurement
        
        # If too large, use largest measurement
        largest = max(conversions.keys())
        return conversions[largest]
    
    # Fallback: round to reasonable decimal places
    if amount >= 100:
        return f"{int(round(amount))}{unit}"
    elif amount >= 10:
        return f"{round(amount, 1)}{unit}"
    else:
        return f"{round(amount, 1)}{unit}"

def fix_meal_portions(meal_plan):
    """Fix meal plan to have realistic portions and kitchen measurements"""
    
    if not meal_plan or 'days' not in meal_plan:
        return meal_plan
    
    for day in meal_plan['days']:
        if 'meals' not in day:
            continue
            
        for meal in day['meals']:
            if 'ingredients' not in meal:
                continue
            
            # Fix each ingredient
            for ingredient in meal['ingredients']:
                if not isinstance(ingredient, dict):
                    continue
                
                amount = ingredient.get('amount', 0)
                unit = ingredient.get('unit', 'g')
                item = ingredient.get('item', '').lower()
                
                # Apply realistic portions
                if item in REALISTIC_PORTIONS:
                    limits = REALISTIC_PORTIONS[item]
                    
                    # If amount is way too high, scale it down
                    if amount > limits['max'] * 2:
                        scale_factor = limits['ideal'] / amount
                        ingredient['amount'] = limits['ideal']
                        print(f"WARNING: Scaled down {item}: {amount:.1f}{unit} -> {limits['ideal']}{unit}")
                    elif amount > limits['max']:
                        ingredient['amount'] = limits['max']
                        print(f"WARNING: Capped {item}: {amount:.1f}{unit} -> {limits['max']}{unit}")
                    elif amount < limits['min']:
                        ingredient['amount'] = limits['min']
                        print(f"WARNING: Increased {item}: {amount:.1f}{unit} -> {limits['min']}{unit}")
                
                # Convert to kitchen measurements
                kitchen_measurement = convert_to_kitchen_measurement(
                    ingredient['amount'], unit, item
                )
                
                # Store both for flexibility
                ingredient['kitchen_measurement'] = kitchen_measurement
                ingredient['original_amount'] = amount
                ingredient['original_unit'] = unit
    
    return meal_plan

# Test the system
if __name__ == "__main__":
    # Test conversion
    test_ingredients = [
        {'amount': 321.4, 'unit': 'g', 'item': 'tofu'},
        {'amount': 276.9, 'unit': 'g', 'item': 'bell_pepper'},
        {'amount': 47.7, 'unit': 'ml', 'item': 'soy_sauce'},
        {'amount': 77.8, 'unit': 'g', 'item': 'oats'},
        {'amount': 311, 'unit': 'ml', 'item': 'milk'},
    ]
    
    print("=== PORTION FIXING TEST ===")
    for ing in test_ingredients:
        original = f"{ing['amount']}{ing['unit']} {ing['item']}"
        kitchen = convert_to_kitchen_measurement(ing['amount'], ing['unit'], ing['item'])
        print(f"{original:25} -> {kitchen}")