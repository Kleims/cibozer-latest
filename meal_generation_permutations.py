#!/usr/bin/env python
"""Calculate all possible meal generation permutations."""
import os
import sys

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import nutrition_data as nd

print("=== MEAL GENERATION PERMUTATIONS ANALYSIS ===\n")

# Load all options
app = create_app()

with app.app_context():
    # Get all available options
    diets = list(nd.DIET_PROFILES.keys())
    patterns = list(nd.MEAL_PATTERNS.keys())
    
    # Common calorie levels
    calorie_levels = [1200, 1500, 1800, 2000, 2200, 2500, 3000, 3500, 4000]
    
    # Days options
    days_options = [1, 3, 7, 14, 30]
    
    # Restrictions (from ALLERGEN_MAPPING)
    restrictions = list(nd.ALLERGEN_MAPPING.keys())
    
    # Cuisine preferences
    cuisine_options = []
    if hasattr(nd, 'CUISINE_PROFILES'):
        cuisine_options = list(nd.CUISINE_PROFILES.keys())
    else:
        # Common cuisines
        cuisine_options = ['all', 'american', 'asian', 'mediterranean', 'mexican', 'italian', 'indian']
    
    # Cooking methods
    cooking_methods = []
    if hasattr(nd, 'COOKING_METHODS'):
        cooking_methods = list(nd.COOKING_METHODS.keys())
    else:
        cooking_methods = ['all', 'baked', 'grilled', 'pan_fried', 'steamed', 'raw', 'boiled']
    
    # Measurement systems
    measurement_systems = ['US', 'Metric']
    
    # Boolean options
    allow_substitutions = [True, False]
    
    print("AVAILABLE OPTIONS:")
    print(f"Diets: {len(diets)} - {diets}")
    print(f"Meal Patterns: {len(patterns)} - {patterns}")
    print(f"Calorie Levels: {len(calorie_levels)} - {calorie_levels}")
    print(f"Days Options: {len(days_options)} - {days_options}")
    print(f"Restrictions: {len(restrictions)} - {restrictions}")
    print(f"Cuisines: {len(cuisine_options)} - {cuisine_options}")
    print(f"Cooking Methods: {len(cooking_methods)} - {cooking_methods}")
    print(f"Measurement Systems: {len(measurement_systems)} - {measurement_systems}")
    print(f"Allow Substitutions: {len(allow_substitutions)} - {allow_substitutions}")
    
    print("\n" + "="*60 + "\n")
    
    # Calculate basic permutations (without restrictions combinations)
    basic_permutations = (
        len(diets) * 
        len(patterns) * 
        len(calorie_levels) * 
        len(days_options) * 
        len(cuisine_options) * 
        len(cooking_methods) * 
        len(measurement_systems) * 
        len(allow_substitutions)
    )
    
    print(f"BASIC PERMUTATIONS (without restrictions): {basic_permutations:,}")
    print(f"  = {len(diets)} diets")
    print(f"  × {len(patterns)} patterns")
    print(f"  × {len(calorie_levels)} calorie levels")
    print(f"  × {len(days_options)} day options")
    print(f"  × {len(cuisine_options)} cuisines")
    print(f"  × {len(cooking_methods)} cooking methods")
    print(f"  × {len(measurement_systems)} measurement systems")
    print(f"  × {len(allow_substitutions)} substitution options")
    
    # Calculate restriction combinations (power set)
    # Total combinations = 2^n (each restriction can be present or absent)
    restriction_combinations = 2 ** len(restrictions)
    
    print(f"\nRESTRICTION COMBINATIONS: {restriction_combinations:,}")
    print(f"  = 2^{len(restrictions)} (power set of {len(restrictions)} restrictions)")
    
    # Total permutations
    total_permutations = basic_permutations * restriction_combinations
    
    print(f"\nTOTAL PERMUTATIONS: {total_permutations:,}")
    
    # Additional analysis
    print("\n" + "="*60 + "\n")
    print("ADDITIONAL ANALYSIS:")
    
    # Most common use cases
    print("\nMost Common Permutations (estimate):")
    common_diets = ['standard', 'vegan', 'keto', 'vegetarian']
    common_calories = [1500, 2000, 2500]
    common_days = [1, 7]
    common_restrictions_count = 5  # No restrictions + 4 common single restrictions
    
    common_permutations = (
        len(common_diets) * 
        1 *  # standard pattern
        len(common_calories) * 
        len(common_days) * 
        1 *  # all cuisines
        1 *  # all cooking methods
        2 *  # both measurement systems
        1 *  # allow substitutions = True
        common_restrictions_count
    )
    
    print(f"Common use cases: ~{common_permutations:,}")
    print(f"  = {len(common_diets)} common diets (standard, vegan, keto, vegetarian)")
    print(f"  × 1 pattern (standard)")
    print(f"  × {len(common_calories)} common calories (1500, 2000, 2500)")
    print(f"  × {len(common_days)} common days (1, 7)")
    print(f"  × 5 common restriction scenarios")
    
    # Generate sample permutations
    print("\n" + "="*60 + "\n")
    print("SAMPLE PERMUTATIONS:")
    
    sample_count = 10
    import random
    
    for i in range(sample_count):
        diet = random.choice(diets)
        pattern = random.choice(patterns)
        calories = random.choice(calorie_levels)
        days = random.choice(days_options)
        num_restrictions = random.randint(0, 3)  # 0-3 restrictions
        selected_restrictions = random.sample(restrictions, num_restrictions) if num_restrictions > 0 else []
        cuisine = random.choice(cuisine_options)
        cooking = random.choice(cooking_methods)
        measurement = random.choice(measurement_systems)
        substitutions = random.choice(allow_substitutions)
        
        print(f"\n{i+1}. Diet: {diet}, Pattern: {pattern}, Calories: {calories}, Days: {days}")
        print(f"   Restrictions: {selected_restrictions if selected_restrictions else 'None'}")
        print(f"   Cuisine: {cuisine}, Cooking: {cooking}, Units: {measurement}, Substitutions: {substitutions}")
    
    # Calculate some interesting statistics
    print("\n" + "="*60 + "\n")
    print("INTERESTING STATISTICS:")
    
    # Time to generate all permutations
    avg_generation_time = 0.5  # seconds per meal plan (estimate)
    total_time_seconds = total_permutations * avg_generation_time
    total_time_hours = total_time_seconds / 3600
    total_time_days = total_time_hours / 24
    total_time_years = total_time_days / 365
    
    print(f"\nIf we generated all {total_permutations:,} permutations:")
    print(f"  At {avg_generation_time}s per plan: {total_time_years:,.1f} years")
    print(f"  At 100 plans/second: {total_permutations/100/3600/24/365:,.1f} years")
    print(f"  At 1000 plans/second: {total_permutations/1000/3600/24/365:,.1f} years")
    
    # Storage requirements
    avg_plan_size = 10_000  # bytes (10KB estimate)
    total_storage_bytes = total_permutations * avg_plan_size
    total_storage_gb = total_storage_bytes / (1024**3)
    total_storage_tb = total_storage_gb / 1024
    total_storage_pb = total_storage_tb / 1024
    
    print(f"\nStorage requirements:")
    print(f"  At {avg_plan_size/1000}KB per plan: {total_storage_pb:,.1f} PB (petabytes)")
    
    # Practical subset
    print("\n" + "="*60 + "\n")
    print("PRACTICAL SUBSET:")
    
    # Most diets don't combine with many restrictions
    practical_restriction_combos = 20  # No restrictions + common singles + few doubles
    practical_permutations = (
        len(diets) * 
        2 *  # standard and 16:8 IF patterns mostly
        5 *  # 5 common calorie levels
        3 *  # 1, 7, 30 days
        3 *  # all, mediterranean, asian cuisines
        2 *  # all, grilled
        2 *  # US, Metric
        1 *  # allow substitutions = True
        practical_restriction_combos
    )
    
    print(f"Practical permutations: ~{practical_permutations:,}")
    print(f"This covers ~95% of real-world use cases")

print("\n=== END OF PERMUTATION ANALYSIS ===")