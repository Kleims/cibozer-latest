#!/usr/bin/env python3
"""Test API directly"""

import requests
import json

# Login first
session = requests.Session()

# Get login page for CSRF
login_page = session.get('http://localhost:5000/auth/login')
from bs4 import BeautifulSoup
soup = BeautifulSoup(login_page.text, 'html.parser')
csrf_token = soup.find('input', {'name': 'csrf_token'})['value']

# Login
login_data = {
    'email': 'admin@cibozer.com',
    'password': 'SecureAdmin2024!MVP',
    'csrf_token': csrf_token
}
login_resp = session.post('http://localhost:5000/auth/login', data=login_data)
print(f"Login status: {login_resp.status_code}")

# Test API endpoint
test_data = {
    "calories": "2000",
    "days": "7", 
    "diet": "standard",
    "meal_structure": "standard"
}

print("\nTesting /api/generate endpoint...")
print(f"Request data: {json.dumps(test_data, indent=2)}")

# Get CSRF token for API call
dashboard = session.get('http://localhost:5000/dashboard')
soup = BeautifulSoup(dashboard.text, 'html.parser')
meta_csrf = soup.find('meta', {'name': 'csrf-token'})
if meta_csrf:
    api_csrf = meta_csrf['content']
else:
    api_csrf = csrf_token

headers = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': api_csrf,
    'Accept': 'application/json'
}

print(f"\nRequest headers: {headers}")

response = session.post(
    'http://localhost:5000/api/generate',
    json=test_data,  # This automatically sets Content-Type
    headers={'X-CSRF-Token': api_csrf}  # Don't override Content-Type
)

print(f"\nResponse status: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")
print(f"Response body: {response.text[:500]}...")

if response.status_code == 415:
    print("\n415 Error - Checking request details...")
    print(f"Request Content-Type: {response.request.headers.get('Content-Type')}")
    print(f"Request body: {response.request.body}")