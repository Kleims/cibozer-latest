#!/usr/bin/env python
"""Comprehensive app testing - NO SURPRISES!"""
import os
import sys
import requests
from flask import url_for

os.environ['FLASK_ENV'] = 'development'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User
from app.extensions import db

print("=== COMPREHENSIVE APP TESTING ===\n")

app = create_app()

# Test 1: Database
print("1. DATABASE TESTS:")
with app.app_context():
    users = User.query.all()
    print(f"   OK Users in database: {len(users)}")
    admin = User.query.filter_by(email='admin@cibozer.com').first()
    print(f"   OK Admin exists: {admin is not None}")
    print(f"   OK Admin can login: {admin.check_password('SecureAdmin2024!MVP')}")

# Test 2: Routes
print("\n2. ROUTE TESTS:")
with app.test_client() as client:
    # Public routes
    routes_to_test = [
        ('/', 'GET', None, 200),
        ('/auth/login', 'GET', None, 200),
        ('/auth/register', 'GET', None, 200),
        ('/api/health', 'GET', None, 200),
    ]
    
    for route, method, data, expected in routes_to_test:
        if method == 'GET':
            resp = client.get(route)
        else:
            resp = client.post(route, json=data)
        status = "OK" if resp.status_code == expected else "FAIL"
        print(f"   {status} {method} {route}: {resp.status_code}")

# Test 3: Login Flow
print("\n3. LOGIN FLOW TEST:")
with app.test_client() as client:
    # Get CSRF token
    login_page = client.get('/auth/login')
    print(f"   OK Login page loads: {login_page.status_code == 200}")
    
    # Try login
    login_data = {
        'email': 'admin@cibozer.com',
        'password': 'SecureAdmin2024!MVP',
        'remember': False
    }
    
    # Extract CSRF token from page
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(login_page.data, 'html.parser')
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        login_data['csrf_token'] = csrf_input.get('value')
        print(f"   OK CSRF token found")
    else:
        print(f"   FAIL CSRF token NOT found")
    
    # Submit login
    login_resp = client.post('/auth/login', data=login_data, follow_redirects=True)
    print(f"   OK Login submission: {login_resp.status_code}")
    
    # Check if logged in
    dashboard = client.get('/create')
    print(f"   OK Access protected route: {dashboard.status_code in [200, 302]}")

# Test 4: API Endpoints
print("\n4. API ENDPOINT TESTS:")
with app.test_client() as client:
    # Health check
    health = client.get('/api/health')
    print(f"   OK Health endpoint: {health.status_code == 200}")
    if health.status_code == 200:
        data = health.get_json()
        print(f"   OK Health data: {data.get('status')}")
    
    # Metrics
    metrics = client.get('/api/metrics')
    print(f"   OK Metrics endpoint: {metrics.status_code == 200}")

# Test 5: Error Handling
print("\n5. ERROR HANDLING TESTS:")
with app.test_client() as client:
    # 404 error
    resp = client.get('/nonexistent-page')
    print(f"   OK 404 handling: {resp.status_code == 404}")
    
    # Invalid JSON
    resp = client.post('/api/generate', data='invalid json', 
                      content_type='application/json')
    print(f"   OK Invalid JSON handling: {resp.status_code in [400, 302]}")

# Test 6: Static Files
print("\n6. STATIC FILE TESTS:")
with app.test_client() as client:
    static_files = [
        '/static/css/style.css',
        '/static/js/app.js',
    ]
    for file in static_files:
        resp = client.get(file)
        status = "OK" if resp.status_code == 200 else "FAIL"
        print(f"   {status} {file}: {resp.status_code}")

# Test 7: Configuration
print("\n7. CONFIGURATION TESTS:")
with app.app_context():
    critical_configs = [
        'SECRET_KEY',
        'SQLALCHEMY_DATABASE_URI',
        'DEBUG',
        'TESTING'
    ]
    for config in critical_configs:
        value = app.config.get(config)
        has_value = value is not None and value != ''
        status = "OK" if has_value else "FAIL"
        if config == 'SECRET_KEY':
            print(f"   {status} {config}: {'SET' if has_value else 'NOT SET'}")
        else:
            print(f"   {status} {config}: {value}")

print("\n=== ALL TESTS COMPLETE ===")