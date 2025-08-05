#!/usr/bin/env python3
"""
Add security fields to database
Run this script to add the new security fields to existing database
"""

import sqlite3
import sys
from datetime import datetime

def add_security_fields():
    """Add security fields to users table"""
    
    # Connect to database
    conn = sqlite3.connect('instance/cibozer.db')
    cursor = conn.cursor()
    
    # Check which columns already exist
    cursor.execute("PRAGMA table_info(users)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns
    columns_to_add = [
        ('failed_login_attempts', 'INTEGER DEFAULT 0'),
        ('locked_until', 'DATETIME'),
        ('last_failed_login', 'DATETIME'),
        ('password_changed_at', 'DATETIME'),
        ('api_key', 'VARCHAR(64)'),
        ('is_admin', 'BOOLEAN DEFAULT 0'),
    ]
    
    for column_name, column_def in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_def}")
                print(f"✓ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e):
                    print(f"✗ Error adding column {column_name}: {e}")
        else:
            print(f"- Column already exists: {column_name}")
    
    # Set default password_changed_at for existing users
    cursor.execute("""
        UPDATE users 
        SET password_changed_at = created_at 
        WHERE password_changed_at IS NULL
    """)
    
    # Commit changes
    conn.commit()
    
    # Create indexes for performance
    indexes = [
        ('idx_users_email_active', 'users', 'email, is_active'),
        ('idx_users_failed_login', 'users', 'email, failed_login_attempts'),
        ('idx_users_api_key', 'users', 'api_key'),
    ]
    
    for index_name, table_name, columns in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns})")
            print(f"✓ Created index: {index_name}")
        except sqlite3.OperationalError as e:
            print(f"✗ Error creating index {index_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nDatabase security fields added successfully!")

if __name__ == '__main__':
    add_security_fields()