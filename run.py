#!/usr/bin/env python
"""
Simple run script for Cibozer
"""

import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set development environment if not set
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'development'

# Import and run the app
from app import app

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Cibozer Development Server")
    print("=" * 60)
    print()
    print("  Main App:    http://localhost:5001")
    print("  Admin Panel: http://localhost:5001/admin")
    print()
    print("  Admin Login: admin / (--F#.A8xzYlTn/3")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    try:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5001,
            use_reloader=False  # Disable reloader to prevent double startup
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        sys.exit(0)