#!/usr/bin/env python3
"""Setup database while Flask is running"""
import requests
import time

# Send a request to Flask to trigger database creation
print("Setting up database in running Flask app...")

try:
    # First check if Flask is running
    response = requests.get('http://localhost:5000/', timeout=5)
    print("Flask is responding")
    
    # Create a special endpoint request to setup database
    setup_code = """
from app.models import db, User

# Create all tables
db.create_all()

# Create admin user
admin = User.query.filter_by(email='admin@cibozer.com').first()
if not admin:
    admin = User(
        email='admin@cibozer.com',
        full_name='Administrator',
        subscription_tier='premium',
        subscription_status='active',
        credits_balance=1000,
        is_active=True,
        email_verified=True
    )
    admin.set_password('Admin123!')
    db.session.add(admin)
    db.session.commit()
    result = 'Admin user created'
else:
    admin.set_password('Admin123!')
    db.session.commit()
    result = 'Admin password updated'

print(result)
"""
    
    # We'll create this as a temp file and execute it in Flask context
    with open('temp_db_setup.py', 'w') as f:
        f.write(setup_code)
    
    print("Database setup script created.")
    print("\nNow we need to execute this in Flask context...")
    
except requests.exceptions.RequestException as e:
    print(f"Flask not responding: {e}")
    print("Please start Flask first with: python wsgi.py")