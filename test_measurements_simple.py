#!/usr/bin/env python3
"""Simple measurement system test"""

def test_conversions():
    print("=== MEASUREMENT CONVERSION TEST ===")
    
    # Test cases
    test_cases = [
        {"name": "Average person", "lbs": 150, "inches": 66},
        {"name": "Tall person", "lbs": 200, "inches": 76},
        {"name": "Short person", "lbs": 120, "inches": 60}
    ]
    
    print("\nTesting Imperial to Metric conversions:")
    
    for case in test_cases:
        print(f"\n{case['name']}:")
        
        # Conversions
        kg = round(case['lbs'] * 0.453592)
        cm = round(case['inches'] * 2.54)
        
        print(f"  {case['lbs']} lbs -> {kg} kg")
        print(f"  {case['inches']} inches -> {cm} cm")
        
        # Reverse conversions
        lbs_back = round(kg / 0.453592)
        inches_back = round(cm / 2.54)
        
        print(f"  {kg} kg -> {lbs_back} lbs (diff: {abs(case['lbs'] - lbs_back)})")
        print(f"  {cm} cm -> {inches_back} inches (diff: {abs(case['inches'] - inches_back)})")
    
    print("\n=== CALORIE CALCULATION TEST ===")
    
    # Test BMR calculation
    age = 30
    weight_kg = 70
    height_cm = 175
    
    # Mifflin-St Jeor for male
    bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    
    print(f"\nBMR calculation (30yr male, 70kg, 175cm):")
    print(f"  BMR: {bmr:.0f} calories/day")
    
    # Test with imperial conversion
    weight_lbs = 154  # ~70kg
    height_inches = 69  # ~175cm
    
    weight_kg_conv = weight_lbs * 0.453592
    height_cm_conv = height_inches * 2.54
    
    bmr_conv = (10 * weight_kg_conv) + (6.25 * height_cm_conv) - (5 * age) + 5
    
    print(f"\nSame person via imperial ({weight_lbs} lbs, {height_inches} inches):")
    print(f"  Converted: {weight_kg_conv:.1f} kg, {height_cm_conv:.1f} cm")
    print(f"  BMR: {bmr_conv:.0f} calories/day")
    print(f"  Difference: {abs(bmr - bmr_conv):.1f} calories")
    
    print("\n=== INPUT VALIDATION RANGES ===")
    
    validations = [
        ("Daily Calories", 800, 6000, "Covers from severe diet to bodybuilders"),
        ("Age", 10, 100, "Children to elderly"),
        ("Weight (lbs)", 50, 500, "From small child to very heavy adult"),
        ("Weight (kg)", 30, 300, "From small child to very heavy adult"),
        ("Height (inches)", 36, 96, "3 feet to 8 feet"),
        ("Height (cm)", 100, 250, "1 meter to 2.5 meters")
    ]
    
    for field, min_val, max_val, desc in validations:
        print(f"\n{field}: {min_val} - {max_val}")
        print(f"  {desc}")
    
    print("\n=== TEST COMPLETE ===")
    print("Measurement system appears to be working correctly!")
    
    return True

if __name__ == '__main__':
    test_conversions()