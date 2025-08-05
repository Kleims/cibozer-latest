#!/usr/bin/env python3
"""Test admin login directly"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"ADMIN_USERNAME = {os.getenv('ADMIN_USERNAME')}")
print(f"ADMIN_PASSWORD = {os.getenv('ADMIN_PASSWORD')}")

# Test the admin route directly
from app import create_app
from flask import session

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

with app.test_client() as client:
    # Get the login page
    response = client.get('/admin/login')
    print(f"\nGET /admin/login: {response.status_code}")
    
    # Try to login
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'SecureAdmin2024!MVP'
    })
    print(f"POST /admin/login: {response.status_code}")
    print(f"Response location: {response.location}")
    
    # Check if we're logged in
    with client.session_transaction() as sess:
        print(f"Session is_admin: {sess.get('is_admin')}")