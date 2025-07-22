#!/usr/bin/env python3
"""
Migrate from SQLite to PostgreSQL
This script prepares the database configuration for PostgreSQL
"""

import os
import sys
from pathlib import Path

def main():
    """Setup PostgreSQL configuration"""
    print("Setting up PostgreSQL configuration...")
    
    # Check if .env file exists
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    if not env_file.exists() and env_template.exists():
        print("Creating .env file from template...")
        # Read template
        with open(env_template, 'r') as f:
            content = f.read()
        
        # Update DATABASE_URL for PostgreSQL
        content = content.replace(
            'DATABASE_URL=sqlite:///instance/cibozer.db',
            '# DATABASE_URL=sqlite:///instance/cibozer.db\n# For production, use PostgreSQL:\n# DATABASE_URL=postgresql://user:password@localhost/cibozer'
        )
        
        # Write to .env
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("Created .env file with PostgreSQL configuration template")
    
    # Create a migration info file
    migration_info = """# PostgreSQL Migration Guide

## Development Setup (SQLite)
For development, you can continue using SQLite by setting:
```
DATABASE_URL=sqlite:///instance/cibozer.db
```

## Production Setup (PostgreSQL)

### 1. Install PostgreSQL
- Windows: Download from https://www.postgresql.org/download/windows/
- Mac: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

### 2. Install Python driver
```
pip install psycopg2-binary
```

### 3. Create database and user
```sql
CREATE DATABASE cibozer;
CREATE USER cibozer_user WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE cibozer TO cibozer_user;
```

### 4. Update .env file
```
DATABASE_URL=postgresql://cibozer_user:your-secure-password@localhost/cibozer
```

### 5. Run migrations
```
python -c "from app import db; db.create_all()"
```

## Data Migration
To migrate existing data from SQLite to PostgreSQL:
1. Export data: `python scripts/export_sqlite_data.py`
2. Switch to PostgreSQL in .env
3. Import data: `python scripts/import_postgres_data.py`
"""
    
    with open('POSTGRESQL_MIGRATION.md', 'w') as f:
        f.write(migration_info)
    
    print("Created POSTGRESQL_MIGRATION.md with detailed instructions")
    print("\nFor development, you can continue using SQLite.")
    print("For production, follow the instructions in POSTGRESQL_MIGRATION.md")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())