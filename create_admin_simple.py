#!/usr/bin/env python3
"""Simple admin creation with minimal fields"""
import sqlite3
from werkzeug.security import generate_password_hash
import os
import sys
import getpass

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cibozer.db')

# Admin credentials from environment or prompt
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
admin_password = os.environ.get('ADMIN_PASSWORD')

if not admin_password:
    admin_password = getpass.getpass('Enter admin password: ')
    if not admin_password:
        print("Error: Password is required")
        sys.exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Delete existing admin if present
cursor.execute("DELETE FROM users WHERE email = ?", (admin_email,))

# Insert admin with only the columns that exist
password_hash = generate_password_hash(admin_password)
cursor.execute("""
    INSERT INTO users (
        email, password_hash, full_name,
        subscription_tier, subscription_status, credits_balance,
        is_active, email_verified
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (
    admin_email, password_hash, 'Administrator',
    'premium', 'active', 1000,
    1, 1
))

conn.commit()
conn.close()

print(f"✅ Admin user created!")
print(f"   Email: {admin_email}")
print(f"   Password: [Set via environment or prompt]")
print(f"\nLogin at: http://localhost:5000/auth/login")