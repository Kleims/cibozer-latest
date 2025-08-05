#!/usr/bin/env python3
"""Test login through web interface"""

import requests
from bs4 import BeautifulSoup
import re

# Test credentials
email = "admin@cibozer.com"
password = "SecureAdmin2024!MVP"

print("Testing Cibozer Web Login")
print("=" * 50)

# Create a session to maintain cookies
session = requests.Session()

# Step 1: GET the login page
print("\n1. Fetching login page...")
login_page = session.get('http://localhost:5000/auth/login')
print(f"   Status: {login_page.status_code}")

# Parse the login page
soup = BeautifulSoup(login_page.text, 'html.parser')

# Find the CSRF token from the form
csrf_token = None
form = soup.find('form', {'action': re.compile('login')})
if form:
    csrf_input = form.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"   Found CSRF token: {csrf_token[:20]}...")

if not csrf_token:
    print("   ERROR: No CSRF token found!")
    exit(1)

# Step 2: POST login credentials
print("\n2. Submitting login form...")
login_data = {
    'email': email,
    'password': password,
    'csrf_token': csrf_token,
    'remember': 'on'  # Check remember me
}

# Submit login
login_response = session.post(
    'http://localhost:5000/auth/login',
    data=login_data,
    allow_redirects=False  # Don't follow redirects automatically
)

print(f"   Status: {login_response.status_code}")
print(f"   Headers: {dict(login_response.headers)}")

# Check for redirect (successful login)
if login_response.status_code == 302:
    redirect_location = login_response.headers.get('Location', '')
    print(f"   Redirected to: {redirect_location}")
    
    # Follow the redirect
    dashboard = session.get('http://localhost:5000' + redirect_location)
    print(f"   Dashboard status: {dashboard.status_code}")
    
    # Check if we're logged in
    if 'dashboard' in dashboard.url:
        print("\n✅ Login successful!")
        print(f"   Logged in as: {email}")
    else:
        print("\n❌ Login failed - redirected to wrong page")
        
elif login_response.status_code == 200:
    # Still on login page - check for errors
    soup = BeautifulSoup(login_response.text, 'html.parser')
    
    # Look for flash messages
    flash_messages = soup.find_all('div', class_='alert')
    if flash_messages:
        print("\n❌ Login failed with errors:")
        for msg in flash_messages:
            print(f"   - {msg.text.strip()}")
    else:
        print("\n❌ Login failed - no redirect occurred")
        
else:
    print(f"\n❌ Unexpected response: {login_response.status_code}")

# Step 3: Verify authentication state
print("\n3. Verifying authentication...")
profile_check = session.get('http://localhost:5000/dashboard')
if profile_check.status_code == 200 and 'dashboard' in profile_check.url:
    print("   ✅ Authenticated - can access dashboard")
    
    # Check user info in the page
    soup = BeautifulSoup(profile_check.text, 'html.parser')
    user_info = soup.find(text=re.compile(email))
    if user_info:
        print(f"   ✅ User email found in dashboard: {email}")
else:
    print("   ❌ Not authenticated - cannot access dashboard")

# Step 4: Test admin panel access
print("\n4. Testing admin panel access...")
admin_check = session.get('http://localhost:5000/admin')
if admin_check.status_code == 200:
    print("   ✅ Can access admin panel (user login)")
elif admin_check.status_code == 401:
    print("   ⚠️  Admin panel requires separate authentication")
else:
    print(f"   Admin panel status: {admin_check.status_code}")

print("\n" + "=" * 50)
print("Test complete!")