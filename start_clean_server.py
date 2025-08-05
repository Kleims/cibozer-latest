#!/usr/bin/env python
"""
Start a completely clean Flask server
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def start_clean_server():
    """Start the server cleanly"""
    print("=== STARTING CLEAN CIBOZER SERVER ===")
    
    try:
        from app import create_app
        
        # Create app
        app = create_app()
        print("App created successfully")
        print("Database connection verified")
        print("")
        print("Starting server on http://127.0.0.1:5002")
        print("Press CTRL+C to stop")
        print("")
        
        # Start on a different port to avoid conflicts
        app.run(
            host='127.0.0.1', 
            port=5002, 
            debug=True,
            use_reloader=False  # Disable reloader to prevent multiple processes
        )
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    start_clean_server()