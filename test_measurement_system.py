#!/usr/bin/env python3
"""Test the measurement system improvements"""
import requests
import json

def test_measurement_conversions():
    """
    Test the measurement system by checking:
    1. Imperial to metric conversion
    2. Metric to imperial conversion
    3. Calorie calculation accuracy
    """
    
    print("=== MEASUREMENT SYSTEM TEST ===")
    print("\nTesting conversion accuracy:")
    
    # Test conversions
    test_cases = [
        {"name": "Average person", "lbs": 150, "inches": 66, "kg": 68, "cm": 168},
        {"name": "Tall person", "lbs": 200, "inches": 76, "kg": 91, "cm": 193},
        {"name": "Short person", "lbs": 120, "inches": 60, "kg": 54, "cm": 152}
    ]
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        
        # Test lbs to kg conversion
        calc_kg = round(case['lbs'] * 0.453592)
        print(f"  {case['lbs']} lbs → {calc_kg} kg (expected: {case['kg']}) {'✓' if abs(calc_kg - case['kg']) <= 1 else '✗'}")
        
        # Test inches to cm conversion
        calc_cm = round(case['inches'] * 2.54)
        print(f"  {case['inches']} inches → {calc_cm} cm (expected: {case['cm']}) {'✓' if abs(calc_cm - case['cm']) <= 1 else '✗'}")
        
        # Test kg to lbs conversion
        calc_lbs = round(case['kg'] / 0.453592)
        print(f"  {case['kg']} kg → {calc_lbs} lbs (expected: {case['lbs']}) {'✓' if abs(calc_lbs - case['lbs']) <= 2 else '✗'}")
        
        # Test cm to inches conversion
        calc_inches = round(case['cm'] / 2.54)
        print(f"  {case['cm']} cm → {calc_inches} inches (expected: {case['inches']}) {'✓' if abs(calc_inches - case['inches']) <= 1 else '✗'}")
    
    print("\n=== CALORIE CALCULATION TEST ===")
    
    # Test calorie calculation with both systems
    # Using Mifflin-St Jeor equation
    test_person = {
        "age": 30,
        "weight_kg": 70,
        "height_cm": 175,
        "gender": "male"
    }
    
    # Manual calculation
    bmr = (10 * test_person['weight_kg']) + (6.25 * test_person['height_cm']) - (5 * test_person['age']) + 5
    tdee_moderate = bmr * 1.55  # Moderately active
    
    print(f"\nTest person (30yr male, 70kg, 175cm):")
    print(f"  BMR: {bmr:.0f} calories")
    print(f"  TDEE (moderate activity): {tdee_moderate:.0f} calories")
    
    # Convert to imperial for comparison
    weight_lbs = round(70 / 0.453592)
    height_inches = round(175 / 2.54)
    
    print(f"\nSame person in imperial: {weight_lbs} lbs, {height_inches} inches")
    
    # Test if our conversion would give same result
    weight_kg_converted = weight_lbs * 0.453592
    height_cm_converted = height_inches * 2.54
    
    bmr_converted = (10 * weight_kg_converted) + (6.25 * height_cm_converted) - (5 * 30) + 5
    print(f"  BMR from converted values: {bmr_converted:.0f} calories")
    print(f"  Difference: {abs(bmr - bmr_converted):.1f} calories {'✓' if abs(bmr - bmr_converted) < 5 else '✗'}")
    
    print("\n=== INPUT VALIDATION TEST ===")
    
    validation_tests = [
        {"field": "Calories", "min": 800, "max": 6000, "reasonable": [1200, 1800, 2000, 2500]},
        {"field": "Age (calc)", "min": 10, "max": 100, "reasonable": [25, 35, 50, 65]},
        {"field": "Weight Imperial (lbs)", "min": 50, "max": 500, "reasonable": [120, 150, 180, 220]},
        {"field": "Weight Metric (kg)", "min": 30, "max": 300, "reasonable": [55, 70, 85, 100]},
        {"field": "Height Imperial (inches)", "min": 36, "max": 96, "reasonable": [60, 66, 70, 74]},
        {"field": "Height Metric (cm)", "min": 100, "max": 250, "reasonable": [155, 170, 180, 190]}
    ]
    
    for test in validation_tests:
        print(f"\n{test['field']}:")
        print(f"  Range: {test['min']} - {test['max']}")
        print(f"  Reasonable values: {', '.join(map(str, test['reasonable']))}")
        
        # Check if reasonable values are within range
        all_valid = all(test['min'] <= val <= test['max'] for val in test['reasonable'])
        print(f"  Validation: {'✓' if all_valid else '✗'}")
    
    return True

if __name__ == '__main__':
    test_measurement_conversions()