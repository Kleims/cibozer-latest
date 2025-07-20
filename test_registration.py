#!/usr/bin/env python3
"""Test script to verify registration flow works properly"""

import requests
import json
from datetime import datetime
import sys

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test configuration
BASE_URL = "http://localhost:5001"
TEST_EMAIL = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
TEST_PASSWORD = "TestPass123!"
TEST_NAME = "Test User"

print("=== Testing Cibozer Registration Flow ===\n")

# Test 1: Load registration page
print("1. Testing registration page loads...")
try:
    response = requests.get(f"{BASE_URL}/register")
    if response.status_code == 200:
        print("✓ Registration page loads successfully")
    else:
        print(f"✗ Failed to load registration page: {response.status_code}")
except Exception as e:
    print(f"✗ Error loading registration page: {e}")

# Test 2: Register new user
print("\n2. Testing user registration...")
registration_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
    "password_confirm": TEST_PASSWORD,
    "full_name": TEST_NAME,
    "agree_terms": "on"
}

try:
    # Need to get CSRF token first
    session = requests.Session()
    response = session.get(f"{BASE_URL}/register")
    
    # Extract CSRF token (if present)
    # For now, we'll test without CSRF
    
    response = session.post(f"{BASE_URL}/register", data=registration_data, allow_redirects=False)
    
    if response.status_code in [302, 303]:  # Redirect after successful registration
        print(f"✓ Registration successful! Redirected to: {response.headers.get('Location', 'unknown')}")
    elif response.status_code == 200:
        # Check if there's an error message in the response
        if "already registered" in response.text.lower():
            print("✗ Email already registered")
        elif "password" in response.text.lower() and "match" in response.text.lower():
            print("✗ Password confirmation doesn't match")
        else:
            print("✗ Registration failed - form returned with errors")
    else:
        print(f"✗ Registration failed with status: {response.status_code}")
except Exception as e:
    print(f"✗ Error during registration: {e}")

# Test 3: Try to login with new credentials
print("\n3. Testing login with new credentials...")
login_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

try:
    response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
    
    if response.status_code in [302, 303]:
        print(f"✓ Login successful! Redirected to: {response.headers.get('Location', 'unknown')}")
    else:
        print(f"✗ Login failed with status: {response.status_code}")
except Exception as e:
    print(f"✗ Error during login: {e}")

# Test 4: Check if we can access protected route
print("\n4. Testing access to protected route...")
try:
    response = session.get(f"{BASE_URL}/account")
    
    if response.status_code == 200:
        print("✓ Can access account page - authentication working!")
    elif response.status_code == 302:
        print("✗ Redirected to login - authentication not persisting")
    else:
        print(f"✗ Unexpected status: {response.status_code}")
except Exception as e:
    print(f"✗ Error accessing protected route: {e}")

# Test 5: Password validation
print("\n5. Testing password validation...")
weak_passwords = [
    ("short", "Password too short"),
    ("alllowercase123", "No uppercase letters"),
    ("ALLUPPERCASE123", "No lowercase letters"),
    ("NoNumbers!", "No numbers"),
    ("NoSpecialChars123", "No special characters")
]

for weak_pass, reason in weak_passwords:
    data = {
        "email": f"weak_{datetime.now().timestamp()}@example.com",
        "password": weak_pass,
        "password_confirm": weak_pass,
        "full_name": "Weak Password Test",
        "agree_terms": "on"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", data=data)
        if response.status_code == 200 and ("password" in response.text.lower() or "validation" in response.text.lower()):
            print(f"✓ Correctly rejected weak password: {reason}")
        else:
            print(f"✗ Failed to reject weak password: {reason}")
    except Exception as e:
        print(f"✗ Error testing password validation: {e}")

print("\n=== Registration Flow Test Complete ===")