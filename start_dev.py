#!/usr/bin/env python
"""
Development server startup script
Automatically uses .env.development for local development
"""

import os
import sys
from pathlib import Path

# Set development environment
os.environ['FLASK_ENV'] = 'development'

# Check if .env.development exists
dev_env = Path('.env.development')
if dev_env.exists():
    print("✅ Loading development environment from .env.development")
    # Backup current .env if it exists
    if Path('.env').exists():
        Path('.env').rename('.env.backup')
    # Copy .env.development to .env
    dev_env.read_text()
    Path('.env').write_text(dev_env.read_text())
else:
    print("❌ .env.development not found!")
    print("Please run: cp .env.example .env.development")
    sys.exit(1)

# Import and run the app
try:
    from app import app
    print("\n🚀 Starting Cibozer development server...")
    print("📍 URL: http://localhost:5001")
    print("🔧 Debug mode: ON")
    print("📂 Database: SQLite (development)")
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, host='127.0.0.1', port=5001)
except Exception as e:
    print(f"\n❌ Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    
    # Restore original .env if backed up
    if Path('.env.backup').exists():
        Path('.env').unlink()
        Path('.env.backup').rename('.env')