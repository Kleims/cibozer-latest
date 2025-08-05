#!/usr/bin/env python3
"""Test to understand and fix the 415 error"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User

app = create_app()

# Test direct API call
with app.app_context():
    # Get admin user
    user = User.query.filter_by(email='admin@cibozer.com').first()
    if not user:
        print("Admin user not found!")
        exit(1)
    
    print(f"Testing with user: {user.email}")
    
    with app.test_client() as client:
        # Login
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
        
        # Test the actual endpoint
        import json
        test_data = {
            "calories": "2000",
            "days": "1",
            "diet": "standard",
            "meal_structure": "standard"
        }
        
        print("\nTesting /api/generate endpoint...")
        
        # Method 1: Using json parameter (Flask's preferred way)
        print("\n1. Using json= parameter:")
        response = client.post('/api/generate', json=test_data)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.status_code == 415:
            print(f"   ERROR Response: {response.data.decode()}")
        else:
            print(f"   Success! Response: {response.data.decode()[:200]}...")
        
        # Method 2: Manual JSON with headers
        print("\n2. Using manual JSON with Content-Type header:")
        response = client.post('/api/generate',
                             data=json.dumps(test_data),
                             headers={'Content-Type': 'application/json'})
        print(f"   Status: {response.status_code}")
        if response.status_code == 415:
            print(f"   ERROR Response: {response.data.decode()}")
        else:
            print(f"   Success! Response: {response.data.decode()[:200]}...")
        
        # Method 3: Without Content-Type (should work with force=True)
        print("\n3. Without Content-Type header (testing force=True):")
        response = client.post('/api/generate',
                             data=json.dumps(test_data))
        print(f"   Status: {response.status_code}")
        if response.status_code == 415:
            print(f"   ERROR Response: {response.data.decode()}")
        else:
            print(f"   Success! Response: {response.data.decode()[:200]}...")

print("\nTest complete. Check the output above to understand the 415 error.")