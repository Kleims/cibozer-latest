#!/usr/bin/env python3
"""Test login functionality"""

import requests
from bs4 import BeautifulSoup

# Start a session to handle cookies
session = requests.Session()

# Step 1: Get the login page to obtain CSRF token
print("Getting login page...")
response = session.get('http://localhost:5000/auth/login')
print(f"Status: {response.status_code}")

# Parse the HTML to find the CSRF token
soup = BeautifulSoup(response.text, 'html.parser')
csrf_token = None

# Look for CSRF token in meta tag
meta_tag = soup.find('meta', {'name': 'csrf-token'})
if meta_tag:
    csrf_token = meta_tag.get('content')
    print(f"Found CSRF token in meta tag: {csrf_token}")

# Look for CSRF token in form input
if not csrf_token:
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"Found CSRF token in form input: {csrf_token}")

if not csrf_token:
    print("ERROR: Could not find CSRF token!")
    exit(1)

# Step 2: Attempt login with credentials
print("\nAttempting login...")
login_data = {
    'email': 'admin@cibozer.com',
    'password': 'SecureAdmin2024!MVP',
    'csrf_token': csrf_token
}

response = session.post('http://localhost:5000/auth/login', data=login_data)
print(f"Login status: {response.status_code}")

# Check if we were redirected (successful login)
if response.history:
    print("Login successful! Redirected to:", response.url)
else:
    # Check for error messages
    soup = BeautifulSoup(response.text, 'html.parser')
    error_messages = soup.find_all('div', class_='alert')
    if error_messages:
        print("Login failed with errors:")
        for msg in error_messages:
            print(f"  - {msg.text.strip()}")
    else:
        print("Login response:")
        print(response.text[:500])

# Step 3: Try to access dashboard to verify login
print("\nChecking dashboard access...")
dashboard_response = session.get('http://localhost:5000/dashboard')
if dashboard_response.status_code == 200:
    print("Successfully accessed dashboard!")
elif dashboard_response.status_code == 302:
    print("Redirected from dashboard (not logged in)")
else:
    print(f"Dashboard status: {dashboard_response.status_code}")