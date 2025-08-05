#!/usr/bin/env python3
"""Start the Cibozer server with proper environment loading"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify environment variables are loaded
print("Environment variables loaded:")
print(f"ADMIN_USERNAME = {os.getenv('ADMIN_USERNAME')}")
print(f"ADMIN_PASSWORD = {os.getenv('ADMIN_PASSWORD')}")
print(f"SECRET_KEY = {os.getenv('SECRET_KEY')[:10]}...")

# Import and run the app
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\nStarting Cibozer server...")
    print("Admin login: http://localhost:5000/admin/login")
    print("Username: admin")
    print("Password: SecureAdmin2024!MVP")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )