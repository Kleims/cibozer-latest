#!/usr/bin/env python3
"""Check if PostgreSQL is properly configured and accessible"""

import os
import sys
from pathlib import Path

def check_postgres_connection():
    """Actually check PostgreSQL connection"""
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
    except ImportError:
        print("FAIL: psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    
    # Get database URL from environment or .env
    database_url = os.environ.get('DATABASE_URL', '')
    
    # If not in environment, try to load from .env
    if not database_url:
        env_file = Path(__file__).parent.parent / '.env'
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        database_url = line.split('=', 1)[1].strip()
                        break
    
    # Check if it's still pointing to SQLite (not PostgreSQL)
    if 'sqlite' in database_url.lower():
        print("FAIL: Still using SQLite. PostgreSQL not configured.")
        print(f"Current DATABASE_URL: {database_url}")
        print("Expected format: postgresql://user:password@localhost/dbname")
        return False
    
    # If no PostgreSQL URL found
    if not database_url or 'postgresql://' not in database_url:
        print("FAIL: PostgreSQL DATABASE_URL not configured")
        print("Set DATABASE_URL=postgresql://user:password@localhost/dbname")
        return False
    
    # Try to actually connect
    try:
        # Parse the connection string
        conn = psycopg2.connect(database_url)
        conn.close()
        print("OK")
        return True
    except psycopg2.OperationalError as e:
        print(f"FAIL: Cannot connect to PostgreSQL: {str(e)}")
        print("Make sure PostgreSQL is running and credentials are correct")
        return False
    except Exception as e:
        print(f"FAIL: Unexpected error: {str(e)}")
        return False

def main():
    """Main function"""
    success = check_postgres_connection()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())