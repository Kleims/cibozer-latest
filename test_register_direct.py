from app import app
from auth import auth_bp
from flask import Flask
from werkzeug.test import Client
from werkzeug.serving import WSGIRequestHandler
from datetime import datetime

# Create test client
with app.test_client() as client:
    # Test GET request first
    print("Testing GET /register...")
    response = client.get('/register')
    print(f"GET Status: {response.status_code}")
    
    # Test POST request
    print("\nTesting POST /register...")
    data = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "TestPass123",
        "password_confirm": "TestPass123",
        "full_name": "Test User"
    }
    
    response = client.post('/register', data=data)
    print(f"POST Status: {response.status_code}")
    
    # Check for flashed messages
    with client.session_transaction() as sess:
        flashed = sess.get('_flashes', [])
        if flashed:
            print("\nFlashed messages:")
            for category, message in flashed:
                print(f"  [{category}] {message}")