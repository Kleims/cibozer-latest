#!/usr/bin/env python
"""Test script to verify auth fixes"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_auth_routes():
    """Test that auth routes are accessible"""
    print("Testing Auth Routes:")
    print("-" * 50)
    
    # Test login page
    response = requests.get(f"{BASE_URL}/login")
    print(f"GET /login: {response.status_code}")
    if response.status_code == 200:
        print("  [OK] Login page accessible")
    else:
        print(f"  [ERROR] Login page returned {response.status_code}")
    
    # Test register page
    response = requests.get(f"{BASE_URL}/register")
    print(f"\nGET /register: {response.status_code}")
    if response.status_code == 200:
        print("  [OK] Register page accessible")
    else:
        print(f"  [ERROR] Register page returned {response.status_code}")
    
    # Test that /auth/login redirects or 404s
    response = requests.get(f"{BASE_URL}/auth/login", allow_redirects=False)
    print(f"\nGET /auth/login: {response.status_code}")
    if response.status_code == 404:
        print("  [OK] /auth/login correctly returns 404")
    else:
        print(f"  [WARNING] /auth/login returned {response.status_code}")
    
    print("\nAuth route test complete!")

if __name__ == "__main__":
    test_auth_routes()