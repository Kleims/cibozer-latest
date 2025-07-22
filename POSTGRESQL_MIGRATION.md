# PostgreSQL Migration Guide

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
