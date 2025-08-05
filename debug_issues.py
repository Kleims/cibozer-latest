#!/usr/bin/env python
"""Debug remaining issues."""
import os
import sys
from datetime import datetime

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
import meal_optimizer
import nutrition_data as nd

print("=== DEBUGGING REMAINING ISSUES ===\n")

app = create_app()

with app.app_context():
    optimizer = meal_optimizer.MealPlanOptimizer(skip_validation=True)
    
    # Test 1: Check if high_protein diet exists
    print("1. HIGH PROTEIN DIET CHECK:")
    print(f"Available diets: {list(nd.DIET_PROFILES.keys())}")
    if 'high_protein' in nd.DIET_PROFILES:
        print("PASS - high_protein diet profile exists")
        print(f"  Tags: {nd.DIET_PROFILES['high_protein']['meal_tags']}")
        
        # Check templates with these tags
        templates_with_tags = []
        for tid, template in nd.MEAL_TEMPLATES.items():
            template_tags = template.get('tags', [])
            if any(tag in nd.DIET_PROFILES['high_protein']['meal_tags'] for tag in template_tags):
                templates_with_tags.append(tid)
        
        print(f"  Templates with matching tags: {len(templates_with_tags)}")
        if templates_with_tags:
            print(f"  Sample templates: {templates_with_tags[:5]}")
        else:
            print("  FAIL - No templates have high_protein or standard tags!")
    else:
        print("FAIL - high_protein diet profile not found")
    
    print("\n2. GLUTEN-FREE FILTERING CHECK:")
    
    # Check gluten allergen mapping
    print(f"Gluten allergens: {nd.ALLERGEN_MAPPING.get('gluten', 'NOT FOUND')}")
    
    # Test restriction filtering
    all_templates = list(nd.MEAL_TEMPLATES.keys())
    print(f"Total templates: {len(all_templates)}")
    
    gluten_free_templates = optimizer.filter_templates_by_restrictions(all_templates, ['gluten'])
    print(f"Gluten-free templates: {len(gluten_free_templates)}")
    
    # Find templates that should be filtered out
    filtered_out = set(all_templates) - set(gluten_free_templates)
    print(f"Filtered out templates: {len(filtered_out)}")
    
    if filtered_out:
        print("Sample filtered templates:")
        for tid in list(filtered_out)[:3]:
            template = nd.MEAL_TEMPLATES[tid]
            print(f"  {tid}: {template['name']}")
            for ing in template['base_ingredients']:
                item = ing['item']
                if item in nd.ALLERGEN_MAPPING.get('gluten', []):
                    print(f"    - Contains gluten: {item}")
    
    # Test actual meal generation with gluten restriction
    print("\n3. TESTING GLUTEN-FREE MEAL GENERATION:")
    try:
        meals, metrics = optimizer.generate_single_day_plan({
            'diet': 'standard',
            'calories': 2000,
            'pattern': 'standard',
            'restrictions': ['gluten'],
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'measurement_system': 'US',
            'allow_substitutions': True,
            'timestamp': datetime.now().isoformat()
        })
        
        print("Generated meals successfully!")
        
        # Check for gluten violations
        violations = []
        for meal_name, meal in meals.items():
            print(f"\n{meal_name}: {meal['name']}")
            for ing in meal.get('ingredients', []):
                if isinstance(ing, dict):
                    item = ing.get('item', '')
                    print(f"  - {item}")
                    if item in nd.ALLERGEN_MAPPING.get('gluten', []):
                        violations.append(f"{meal_name}: {item} contains gluten")
        
        if violations:
            print(f"\nFAIL - Found {len(violations)} gluten violations:")
            for v in violations:
                print(f"  - {v}")
        else:
            print(f"\nPASS - No gluten violations found!")
            
    except Exception as e:
        print(f"FAIL - Error generating gluten-free meals: {e}")

print("\n=== END OF DEBUG ===")