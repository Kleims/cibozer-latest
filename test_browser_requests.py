#!/usr/bin/env python3
"""Test browser-like requests to understand the 415 error"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_json_endpoint():
    """Test the /api/test-json endpoint"""
    print("\n=== Testing /api/test-json ===")
    
    data = {
        "test": "data",
        "calories": 2000,
        "diet": "standard"
    }
    
    # Test 1: With proper headers
    print("\n1. With Content-Type: application/json")
    response = requests.post(
        f"{BASE_URL}/api/test-json",
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    # Test 2: Without Content-Type
    print("\n2. Without Content-Type header")
    response = requests.post(
        f"{BASE_URL}/api/test-json",
        data=json.dumps(data)
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")
    
    # Test 3: With wrong Content-Type
    print("\n3. With Content-Type: text/plain")
    response = requests.post(
        f"{BASE_URL}/api/test-json",
        headers={"Content-Type": "text/plain"},
        data=json.dumps(data)
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}")

def test_generate_endpoint():
    """Test the /api/generate endpoint"""
    print("\n=== Testing /api/generate ===")
    
    # First, we need to login
    session = requests.Session()
    
    # Login
    login_data = {
        "email": "admin@cibozer.com",
        "password": "AdminPass123!",
        "remember": "true"
    }
    
    print("\n1. Logging in...")
    response = session.post(
        f"{BASE_URL}/auth/login",
        data=login_data
    )
    print(f"Login status: {response.status_code}")
    
    # Test generate endpoint
    data = {
        "calories": "2000",
        "days": "1",
        "diet": "standard",
        "meal_structure": "standard"
    }
    
    print("\n2. Testing /api/generate with JSON")
    response = session.post(
        f"{BASE_URL}/api/generate",
        headers={"Content-Type": "application/json"},
        data=json.dumps(data)
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")

if __name__ == "__main__":
    print("Testing browser-like requests to Cibozer API")
    print("Make sure the Flask server is running on port 5000")
    
    try:
        test_json_endpoint()
        test_generate_endpoint()
    except requests.exceptions.ConnectionError:
        print("\nERROR: Could not connect to server. Is it running?")
    except Exception as e:
        print(f"\nERROR: {e}")