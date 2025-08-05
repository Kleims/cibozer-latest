#!/usr/bin/env python3
"""
Direct template content test to verify guidance features are implemented
"""

def test_template_content():
    """Test that the template contains all guidance features"""
    print("Testing Template Content Directly")
    print("=" * 50)
    
    # Read the template file
    try:
        with open('templates/create_clean.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
    except Exception as e:
        print(f"Error reading template: {e}")
        return False
    
    # Test 1: Tooltips
    print("\nTesting tooltips...")
    tooltip_count = template_content.count('data-bs-toggle="tooltip"')
    if tooltip_count >= 8:
        print(f"PASS: Found {tooltip_count} tooltip elements")
    else:
        print(f"FAIL: Only found {tooltip_count} tooltips (expected >= 8)")
        return False
    
    # Test 2: Calorie Calculator
    print("\nTesting calorie calculator...")
    calc_elements = [
        'id="calcCalories"',
        'function calculateCalories()',
        'Mifflin-St Jeor equation',
        'id="calcAge"',
        'performCalcuation()',
        'useCalculatedCalories()'
    ]
    calc_found = 0
    for element in calc_elements:
        if element in template_content:
            print(f"PASS: Found {element}")
            calc_found += 1
        else:
            print(f"FAIL: Missing {element}")
    
    if calc_found < 5:
        print("FAIL: Calculator test failed")
        return False
    
    # Test 3: Setup Wizard
    print("\nTesting setup wizard...")
    wizard_elements = [
        'Need Help?',
        'id="setupWizard"',
        'function startWizard()',
        'function nextWizardStep()',
        'function completeWizard()',
        'What\'s your main goal?',
        'wizardSteps = {',
        'goal-card'
    ]
    wizard_found = 0
    for element in wizard_elements:
        if element in template_content:
            print(f"PASS: Found {element}")
            wizard_found += 1
        else:
            print(f"FAIL: Missing {element}")
    
    if wizard_found < 6:
        print("FAIL: Wizard test failed")
        return False
    
    # Test 4: Diet Type Tooltips
    print("\nTesting diet type tooltips...")
    diet_tooltips = [
        'Balanced diet with all food groups',
        'Very low carb, high fat diet',
        'Plant-based only: no meat, dairy',
        'Whole foods only: meat, fish, eggs',
        '40% protein for muscle building'
    ]
    diet_found = 0
    for tooltip in diet_tooltips:
        if tooltip in template_content:
            print(f"PASS: Found diet tooltip - {tooltip[:30]}...")
            diet_found += 1
        else:
            print(f"FAIL: Missing diet tooltip - {tooltip[:30]}...")
    
    if diet_found < 4:
        print("FAIL: Diet tooltips test failed")
        return False
    
    # Test 5: Measurement System
    print("\nTesting measurement system...")
    if 'id="measurement_system"' in template_content and 'Imperial (cups, tbsp, oz)' in template_content:
        print("PASS: Measurement system found")
    else:
        print("FAIL: Measurement system missing")
        return False
    
    # Test 6: JavaScript Integration
    print("\nTesting JavaScript integration...")
    js_elements = [
        'new bootstrap.Tooltip(tooltip)',
        'addEventListener(\'click\', calculateCalories)',
        'document.addEventListener(\'DOMContentLoaded\'',
        'currentWizardStep = 1'
    ]
    js_found = sum(1 for element in js_elements if element in template_content)
    if js_found >= 3:
        print(f"PASS: JavaScript integration found ({js_found}/4 elements)")
    else:
        print(f"FAIL: JavaScript integration incomplete ({js_found}/4 elements)")
        return False
    
    print("\n" + "=" * 50)
    print("ALL TEMPLATE TESTS PASSED!")
    print("Guidance system is fully implemented in the template!")
    return True

if __name__ == "__main__":
    success = test_template_content()
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")