#!/usr/bin/env python3
"""Test API directly to understand the issue"""

import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User

app = create_app()

with app.app_context():
    # Get admin user
    user = User.query.filter_by(email='admin@cibozer.com').first()
    if not user:
        print("Admin user not found!")
        exit(1)
    
    print(f"Testing with user: {user.email}")
    
    # Test with different Content-Type scenarios
    with app.test_client() as client:
        # Login first
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
        
        test_data = {
            "calories": "2000",
            "days": "7", 
            "diet": "standard",
            "meal_structure": "standard"
        }
        
        print("\n1. Testing with correct Content-Type...")
        response = client.post('/api/generate',
                             data=json.dumps(test_data),
                             headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.data.decode()[:200]}")
        
        print("\n2. Testing with no Content-Type...")
        response = client.post('/api/generate',
                             data=json.dumps(test_data))
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.data.decode()[:200]}")
        
        print("\n3. Testing with json parameter...")
        response = client.post('/api/generate', json=test_data)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.data.decode()[:200]}")
            
        print("\n4. Testing without CSRF exempt...")
        # Get CSRF token
        from flask_wtf.csrf import generate_csrf
        with client.session_transaction() as sess:
            csrf_token = generate_csrf()
            
        response = client.post('/api/generate',
                             json=test_data,
                             headers={'X-CSRF-Token': csrf_token})
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.data.decode()[:200]}")