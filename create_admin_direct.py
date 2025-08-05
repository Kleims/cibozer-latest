#!/usr/bin/env python3
"""Direct admin user creation without queries"""
import sys
import os
import sqlite3
import getpass
from werkzeug.security import generate_password_hash
from datetime import datetime

# Database path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'cibozer.db')

# Admin credentials from environment or prompt
admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
admin_password = os.environ.get('ADMIN_PASSWORD')
admin_name = os.environ.get('ADMIN_NAME', 'Administrator')

if not admin_password:
    admin_password = getpass.getpass('Enter admin password: ')
    if not admin_password:
        print("Error: Password is required")
        sys.exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if admin already exists
cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
existing = cursor.fetchone()

if existing:
    print(f"Admin user already exists: {admin_email}")
    # Update password
    password_hash = generate_password_hash(admin_password)
    cursor.execute("""
        UPDATE users 
        SET password_hash = ?, 
            subscription_tier = 'premium',
            subscription_status = 'active',
            credits_balance = 1000,
            is_active = 1,
            email_verified = 1
        WHERE email = ?
    """, (password_hash, admin_email))
    print("Admin password updated!")
else:
    # Insert new admin user with minimal required fields
    password_hash = generate_password_hash(admin_password)
    now = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO users (
            email, password_hash, full_name, 
            subscription_tier, subscription_status, credits_balance,
            created_at, is_active, email_verified
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        admin_email, password_hash, admin_name,
        'premium', 'active', 1000,
        now, 1, 1
    ))
    print("Admin user created successfully!")

# Commit changes
conn.commit()
conn.close()

print(f"\n✅ Admin Login Credentials:")
print(f"   Email: {admin_email}")
print(f"   Password: [Set via environment or prompt]")
print(f"\nLogin at: http://localhost:5000/auth/login")