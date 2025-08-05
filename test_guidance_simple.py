#!/usr/bin/env python3
"""
Simple test suite for the three-layered user guidance system
"""

import requests
import json
import time
from bs4 import BeautifulSoup
import sys

def test_all_features():
    """Test all guidance features"""
    print("Starting Guidance Features Test")
    print("=" * 50)
    
    # Test 1: Page Loading
    print("\nTesting page loading...")
    try:
        response = requests.get('http://127.0.0.1:5000/', timeout=10)
        if response.status_code == 200:
            print("PASS: Page loads successfully")
            html = response.text
        else:
            print(f"FAIL: HTTP Error {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Connection error - {e}")
        return False
    
    # Test 2: Tooltips
    print("\nTesting tooltips...")
    tooltip_count = html.count('data-bs-toggle="tooltip"')
    if tooltip_count >= 5:
        print(f"PASS: Found {tooltip_count} tooltips")
    else:
        print(f"FAIL: Only found {tooltip_count} tooltips")
        return False
    
    # Test 3: Calculator
    print("\nTesting calorie calculator...")
    calc_tests = [
        'id="calcCalories"',
        'function calculateCalories()',
        'Mifflin-St Jeor equation'
    ]
    calc_passed = 0
    for test in calc_tests:
        if test in html:
            print(f"PASS: Found {test}")
            calc_passed += 1
        else:
            print(f"FAIL: Missing {test}")
    
    if calc_passed < 3:
        print("FAIL: Calculator test failed")
        return False
    
    # Test 4: Wizard
    print("\nTesting setup wizard...")
    wizard_tests = [
        'Need Help?',
        'id="setupWizard"',
        'function startWizard()',
        'function nextWizardStep()',
        'What\'s your main goal?'
    ]
    wizard_passed = 0
    for test in wizard_tests:
        if test in html:
            print(f"PASS: Found {test}")
            wizard_passed += 1
        else:
            print(f"FAIL: Missing {test}")
    
    if wizard_passed < 4:
        print("FAIL: Wizard test failed")
        return False
    
    # Test 5: JavaScript Integration
    print("\nTesting JavaScript integration...")
    js_tests = [
        'new bootstrap.Tooltip(tooltip)',
        'addEventListener(\'click\', calculateCalories)',
        'DOMContentLoaded'
    ]
    js_passed = 0
    for test in js_tests:
        if test in html:
            print(f"PASS: Found {test}")
            js_passed += 1
        else:
            print(f"FAIL: Missing {test}")
    
    if js_passed < 2:
        print("FAIL: JavaScript integration failed")
        return False
    
    # Test 6: Measurement System
    print("\nTesting measurement system...")
    if 'id="measurement_system"' in html and 'value="US"' in html and 'value="Metric"' in html:
        print("PASS: Measurement system toggle found")
    else:
        print("FAIL: Measurement system toggle missing")
        return False
    
    # Test 7: Meal Generation Integration
    print("\nTesting meal generation integration...")
    try:
        # Get CSRF token
        soup = BeautifulSoup(html, 'html.parser')
        csrf_token_elem = soup.find('input', {'name': 'csrf_token'})
        if not csrf_token_elem:
            print("FAIL: No CSRF token found")
            return False
        csrf_token = csrf_token_elem['value']
        
        # Test with high_protein diet (wizard recommendation)
        response = requests.post(
            'http://127.0.0.1:5000/api/generate',
            headers={
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrf_token
            },
            json={
                "calories": 1800,
                "days": 1,
                "diet": "high_protein",
                "meal_structure": "standard",
                "measurement_system": "US"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("PASS: Meal generation works with guidance recommendations")
            else:
                print(f"FAIL: Meal generation failed - {result.get('error', 'Unknown')}")
                return False
        else:
            print(f"FAIL: API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"FAIL: Meal generation test error - {e}")
        return False
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("Guidance system is fully functional!")
    return True

if __name__ == "__main__":
    success = test_all_features()
    if success:
        print("\nTest completed successfully")
    else:
        print("\nSome tests failed")
    sys.exit(0 if success else 1)