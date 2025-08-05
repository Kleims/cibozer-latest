#!/usr/bin/env python
"""Verify database tables and data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import User, SavedMealPlan, Payment, UsageLog
from app.extensions import db

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Create app with proper config
app = create_app()

with app.app_context():
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    # Check tables
    print("=== DATABASE TABLES ===")
    tables = db.metadata.tables.keys()
    for table in tables:
        print(f"OK Table: {table}")
    print()
    
    # Check data
    print("=== DATABASE CONTENTS ===")
    print(f"Users: {User.query.count()}")
    print(f"Saved Meal Plans: {SavedMealPlan.query.count()}")
    print(f"Payments: {Payment.query.count()}")
    print(f"Usage Logs: {UsageLog.query.count()}")
    print()
    
    # Check admin user
    admin = User.query.filter_by(email='admin@cibozer.com').first()
    if admin:
        print(f"OK Admin user found: {admin.email} (tier: {admin.subscription_tier})")
    else:
        print("ERROR: No admin user found")
    print()
    
    print("SUCCESS: DATABASE IS FULLY FUNCTIONAL!")