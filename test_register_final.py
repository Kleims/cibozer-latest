import requests
from datetime import datetime
from bs4 import BeautifulSoup
import sys
import io

# Fix Windows Unicode issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Create a session to maintain cookies
session = requests.Session()

# First, GET the registration page to get CSRF token
print("1. Getting registration page...")
response = session.get("http://localhost:5001/register")
print(f"   Status: {response.status_code}")

# Parse the HTML to find CSRF token
soup = BeautifulSoup(response.text, 'html.parser')
csrf_input = soup.find('input', {'name': 'csrf_token'})

if not csrf_input:
    print("   ERROR: No CSRF token found!")
    exit(1)

csrf_token = csrf_input.get('value')
print(f"   CSRF token: {csrf_token[:20]}...")

# Now POST with the CSRF token
print("\n2. Submitting registration...")
data = {
    "email": f"test_{datetime.now().timestamp()}@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "full_name": "Test User",
    "csrf_token": csrf_token
}

response = session.post("http://localhost:5001/register", data=data, allow_redirects=False)
print(f"   Status: {response.status_code}")

if response.status_code == 302:
    print(f"   Success! Redirected to: {response.headers.get('Location')}")
    
    # Follow the redirect
    response = session.get(response.headers.get('Location'))
    print(f"   Final page status: {response.status_code}")
else:
    print("   Registration failed")
    # Check for error messages
    soup = BeautifulSoup(response.text, 'html.parser')
    alerts = soup.find_all('div', class_='alert')
    for alert in alerts:
        print(f"   Alert: {alert.text.strip()}")

print("\n✅ Registration can be completed successfully with CSRF token!")