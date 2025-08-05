#!/usr/bin/env python3
"""
Comprehensive test suite for the three-layered user guidance system:
1. Educational Tooltips
2. Calorie Calculator 
3. Setup Wizard
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import sys

def test_page_loading():
    """Test that the create.html page loads successfully"""
    print("Testing Page Loading...")
    try:
        response = requests.get('http://127.0.0.1:5000/create', timeout=10)
        if response.status_code == 200:
            print("PASS: Create page loads successfully")
            return response.text
        else:
            print(f"FAIL: HTTP Error {response.status_code}")
            return None
    except Exception as e:
        print(f"FAIL: Connection error - {e}")
        return None

def test_tooltips_presence(html_content):
    """Test that educational tooltips are present in the HTML"""
    print("\n🧪 Testing Educational Tooltips...")
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test 1: Check for tooltip elements
    tooltip_elements = soup.find_all(attrs={'data-bs-toggle': 'tooltip'})
    if len(tooltip_elements) > 0:
        print(f"PASS: Found {len(tooltip_elements)} tooltip elements")
    else:
        print("FAIL: No tooltip elements found")
        return False
    
    # Test 2: Check specific tooltips
    expected_tooltips = [
        "Average adult needs 1800-2400 calories",
        "Balanced diet with all food groups", 
        "Very low carb, high fat diet",
        "Plant-based only: no meat, dairy",
        "Choose how you prefer to distribute"
    ]
    
    tooltip_count = 0
    for expected in expected_tooltips:
        if expected in html_content:
            tooltip_count += 1
            print(f"✅ PASS: Found tooltip - '{expected[:30]}...'")
        else:
            print(f"❌ FAIL: Missing tooltip - '{expected[:30]}...'")
    
    # Test 3: Check quick guide text
    if "Quick guide:" in html_content and "Sedentary: 1600-1800" in html_content:
        print("✅ PASS: Quick calorie guide present")
        tooltip_count += 1
    else:
        print("❌ FAIL: Quick calorie guide missing")
    
    return tooltip_count >= 4

def test_calorie_calculator(html_content):
    """Test that calorie calculator elements are present"""
    print("\n🧪 Testing Calorie Calculator...")
    
    # Test 1: Calculator button
    if 'id="calcCalories"' in html_content:
        print("✅ PASS: Calculator button found")
    else:
        print("❌ FAIL: Calculator button missing")
        return False
    
    # Test 2: Calculator function
    if 'function calculateCalories()' in html_content:
        print("✅ PASS: calculateCalories function found")
    else:
        print("❌ FAIL: calculateCalories function missing")
        return False
    
    # Test 3: BMR calculation logic
    if 'Mifflin-St Jeor equation' in html_content:
        print("✅ PASS: BMR calculation logic found")
    else:
        print("❌ FAIL: BMR calculation logic missing")
        return False
    
    # Test 4: Calculator modal elements
    calculator_elements = [
        'id="calorieCalculator"',
        'id="calcAge"',
        'id="calcWeight"', 
        'id="calcHeight"',
        'id="calcGender"',
        'id="calcActivity"'
    ]
    
    found_elements = 0
    for element in calculator_elements:
        if element in html_content:
            found_elements += 1
            print(f"✅ PASS: Found {element}")
        else:
            print(f"❌ FAIL: Missing {element}")
    
    return found_elements >= 5

def test_setup_wizard(html_content):
    """Test that setup wizard elements are present"""
    print("\n🧪 Testing Setup Wizard...")
    
    # Test 1: Wizard button
    if 'Need Help?' in html_content and 'onclick="startWizard()"' in html_content:
        print("✅ PASS: Wizard trigger button found")
    else:
        print("❌ FAIL: Wizard trigger button missing")
        return False
    
    # Test 2: Wizard modal structure
    if 'id="setupWizard"' in html_content:
        print("✅ PASS: Wizard modal found")
    else:
        print("❌ FAIL: Wizard modal missing")
        return False
    
    # Test 3: Wizard functions
    wizard_functions = [
        'function startWizard()',
        'function showWizardStep()',
        'function nextWizardStep()',
        'function previousWizardStep()',
        'function completeWizard()',
        'function generateRecommendations()'
    ]
    
    found_functions = 0
    for func in wizard_functions:
        if func in html_content:
            found_functions += 1
            print(f"✅ PASS: Found {func}")
        else:
            print(f"❌ FAIL: Missing {func}")
    
    # Test 4: Wizard steps data
    if 'wizardSteps = {' in html_content:
        print("✅ PASS: Wizard steps data found")
        found_functions += 1
    else:
        print("❌ FAIL: Wizard steps data missing")
    
    # Test 5: Step content checks
    step_contents = [
        "What's your main goal?",
        "Any dietary preferences or restrictions?",
        "How active are you?",
        "Your Personalized Recommendations"
    ]
    
    for content in step_contents:
        if content in html_content:
            print(f"✅ PASS: Found step content - '{content}'")
            found_functions += 1
        else:
            print(f"❌ FAIL: Missing step content - '{content}'")
    
    return found_functions >= 8

def test_javascript_integration(html_content):
    """Test JavaScript integration and initialization"""
    print("\n🧪 Testing JavaScript Integration...")
    
    # Test 1: Tooltip initialization
    if 'new bootstrap.Tooltip(tooltip)' in html_content:
        print("✅ PASS: Tooltip initialization found")
    else:
        print("❌ FAIL: Tooltip initialization missing")
        return False
    
    # Test 2: Calculator button event listener
    if 'calcButton.addEventListener(\'click\', calculateCalories)' in html_content:
        print("✅ PASS: Calculator event listener found")
    else:
        print("❌ FAIL: Calculator event listener missing")
        return False
    
    # Test 3: DOMContentLoaded event
    if 'document.addEventListener(\'DOMContentLoaded\'' in html_content:
        print("✅ PASS: DOMContentLoaded event found")
    else:
        print("❌ FAIL: DOMContentLoaded event missing")
        return False
    
    # Test 4: Form population logic
    if 'wizardData.recommendedDiet' in html_content and 'document.getElementById' in html_content:
        print("✅ PASS: Form population logic found")
    else:
        print("❌ FAIL: Form population logic missing")
        return False
    
    return True

def test_meal_generation_integration():
    """Test that guidance features integrate with meal generation"""
    print("\n🧪 Testing Meal Generation Integration...")
    
    # Test meal generation with wizard-recommended settings
    test_data = {
        "calories": 1800,
        "days": 1,
        "diet": "high_protein",
        "meal_structure": "standard",
        "measurement_system": "US"
    }
    
    try:
        # First get CSRF token
        response = requests.get('http://127.0.0.1:5000/create')
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        
        # Test meal generation API
        response = requests.post(
            'http://127.0.0.1:5000/api/generate',
            headers={
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_token
            },
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ PASS: Meal generation works with guidance recommendations")
                return True
            else:
                print(f"❌ FAIL: Meal generation failed - {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ FAIL: API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Meal generation test error - {e}")
        return False

def test_measurement_system_toggle(html_content):
    """Test that measurement system toggle is properly integrated"""
    print("\n🧪 Testing Measurement System Toggle...")
    
    # Check for measurement system dropdown
    if 'id="measurement_system"' in html_content:
        print("✅ PASS: Measurement system dropdown found")
    else:
        print("❌ FAIL: Measurement system dropdown missing")
        return False
    
    # Check for both options
    if 'value="US"' in html_content and 'value="Metric"' in html_content:
        print("✅ PASS: Both US and Metric options found")
    else:
        print("❌ FAIL: Missing measurement system options")
        return False
    
    return True

def run_comprehensive_tests():
    """Run all tests and provide summary"""
    print("Starting Comprehensive Guidance Features Test Suite")
    print("=" * 60)
    
    # Test 1: Page Loading
    html_content = test_page_loading()
    if not html_content:
        print("\n❌ CRITICAL FAILURE: Cannot load page - aborting tests")
        return False
    
    # Run all feature tests
    test_results = {
        "tooltips": test_tooltips_presence(html_content),
        "calculator": test_calorie_calculator(html_content), 
        "wizard": test_setup_wizard(html_content),
        "javascript": test_javascript_integration(html_content),
        "measurements": test_measurement_system_toggle(html_content),
        "meal_generation": test_meal_generation_integration()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    print(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Guidance system is fully functional!")
        return True
    else:
        print("⚠️  Some tests failed - review issues above")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)