#!/usr/bin/env python3
"""
Test Core User Flow for MVP Week 1
Tests: Registration -> Login -> Create Meal Plan -> Save -> View
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_homepage():
    """Test if homepage loads"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Homepage loads successfully")
            return True
        else:
            print(f"❌ Homepage failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Homepage error: {e}")
        return False

def test_registration():
    """Test user registration"""
    test_user = {
        "email": f"test_mvp_{int(time.time())}@example.com",
        "password": "TestPassword123!",
        "full_name": "MVP Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            data=test_user,
            allow_redirects=False
        )
        if response.status_code in [200, 302]:
            print(f"✅ Registration successful for {test_user['email']}")
            return test_user
        else:
            print(f"❌ Registration failed: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return None

def test_login(user_data):
    """Test user login"""
    session = requests.Session()
    
    try:
        response = session.post(
            f"{BASE_URL}/auth/login",
            data={
                "email": user_data["email"],
                "password": user_data["password"]
            },
            allow_redirects=False
        )
        if response.status_code in [200, 302]:
            print(f"✅ Login successful for {user_data['email']}")
            return session
        else:
            print(f"❌ Login failed: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_meal_plan_generation(session):
    """Test meal plan generation"""
    meal_data = {
        "diet_type": "balanced",
        "calories": "2000",
        "meals": "3"
    }
    
    try:
        response = session.post(
            f"{BASE_URL}/api/generate-meal-plan",
            json=meal_data
        )
        if response.status_code == 200:
            result = response.json()
            if "meal_plan" in result or "meals" in result:
                print("✅ Meal plan generated successfully")
                return result
            else:
                print(f"❌ Meal plan response missing data: {result}")
                return None
        else:
            print(f"❌ Meal plan generation failed: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Meal plan generation error: {e}")
        return None

def test_save_meal_plan(session, meal_plan):
    """Test saving meal plan"""
    try:
        response = session.post(
            f"{BASE_URL}/api/save-meal-plan",
            json={"meal_plan": meal_plan}
        )
        if response.status_code == 200:
            print("✅ Meal plan saved successfully")
            return True
        else:
            print(f"❌ Save meal plan failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Save meal plan error: {e}")
        return False

def test_view_saved_plans(session):
    """Test viewing saved meal plans"""
    try:
        response = session.get(f"{BASE_URL}/saved-plans")
        if response.status_code == 200:
            print("✅ Saved plans page loads successfully")
            return True
        else:
            print(f"❌ Saved plans page failed: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Saved plans page error: {e}")
        return False

def run_mvp_tests():
    """Run all MVP Week 1 core tests"""
    print("\n" + "="*60)
    print("🎯 MVP WEEK 1: CORE USER FLOW TEST")
    print("="*60)
    print(f"Testing at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*60)
    
    results = {
        "homepage": False,
        "registration": False,
        "login": False,
        "meal_generation": False,
        "save_plan": False,
        "view_plans": False
    }
    
    # Test 1: Homepage
    print("\n1️⃣ Testing Homepage...")
    results["homepage"] = test_homepage()
    
    if not results["homepage"]:
        print("\n⚠️ Server may not be running. Please start with: python app.py")
        return results
    
    # Test 2: Registration
    print("\n2️⃣ Testing Registration...")
    user_data = test_registration()
    results["registration"] = user_data is not None
    
    if not user_data:
        print("⚠️ Cannot continue without registration")
        return results
    
    # Test 3: Login
    print("\n3️⃣ Testing Login...")
    session = test_login(user_data)
    results["login"] = session is not None
    
    if not session:
        print("⚠️ Cannot continue without login")
        return results
    
    # Test 4: Meal Plan Generation
    print("\n4️⃣ Testing Meal Plan Generation...")
    meal_plan = test_meal_plan_generation(session)
    results["meal_generation"] = meal_plan is not None
    
    if not meal_plan:
        print("⚠️ Cannot test save without meal plan")
    else:
        # Test 5: Save Meal Plan
        print("\n5️⃣ Testing Save Meal Plan...")
        results["save_plan"] = test_save_meal_plan(session, meal_plan)
    
    # Test 6: View Saved Plans
    print("\n6️⃣ Testing View Saved Plans...")
    results["view_plans"] = test_view_saved_plans(session)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {test_name.replace('_', ' ').title()}: {'PASSED' if passed else 'FAILED'}")
    
    print("-"*60)
    print(f"Overall: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 ALL CORE FEATURES WORKING! Ready for deployment!")
    elif passed >= 4:
        print("\n⚠️ Most features working. Fix remaining issues before deployment.")
    else:
        print("\n❌ Critical issues found. Fix before proceeding.")
    
    print("="*60)
    
    return results

if __name__ == "__main__":
    results = run_mvp_tests()
    
    # Update MVP tracker
    if all(results.values()):
        print("\n📝 Updating MVP tracker...")
        import json
        from pathlib import Path
        
        tracker_file = Path(".sprint/mvp_tracker.json")
        if tracker_file.exists():
            with open(tracker_file, 'r') as f:
                tracker = json.load(f)
            
            # Update Week 1 success metrics
            tracker["weekly_goals"]["week1"]["success_metrics"]["signup_to_save_flow"] = True
            tracker["weekly_goals"]["week1"]["success_metrics"]["forms_work"] = True
            
            with open(tracker_file, 'w') as f:
                json.dump(tracker, f, indent=2)
            
            print("✅ MVP tracker updated!")