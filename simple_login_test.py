#!/usr/bin/env python3
"""Simple login test"""

import requests
from bs4 import BeautifulSoup

# Create session
session = requests.Session()

# Get login page
print("Getting login page...")
response = session.get('http://localhost:5000/auth/login')
soup = BeautifulSoup(response.text, 'html.parser')

# Find CSRF token
csrf_input = soup.find('input', {'name': 'csrf_token'})
if csrf_input:
    csrf_token = csrf_input['value']
    print(f"CSRF token: {csrf_token}")
else:
    print("No CSRF token found!")
    exit(1)

# Try to login
print("\nAttempting login...")
login_data = {
    'email': 'admin@cibozer.com',
    'password': 'SecureAdmin2024!MVP',
    'csrf_token': csrf_token
}

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'http://localhost:5000/auth/login'
}

response = session.post('http://localhost:5000/auth/login', data=login_data, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 400:
    print("Error response:")
    print(response.text)
elif response.status_code == 302:
    print(f"Redirected to: {response.headers.get('Location')}")
elif response.status_code == 200:
    # Check for error messages
    soup = BeautifulSoup(response.text, 'html.parser')
    alerts = soup.find_all('div', class_='alert')
    if alerts:
        print("Alerts found:")
        for alert in alerts:
            print(f"  - {alert.text.strip()}")
    else:
        print("No obvious errors, checking if we're still on login page...")
        if 'Sign In' in response.text:
            print("Still on login page")
        else:
            print("Possibly logged in")
            
# Check cookies
print("\nCookies:")
for cookie in session.cookies:
    print(f"  {cookie.name}: {cookie.value[:20]}...")