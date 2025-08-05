#!/usr/bin/env python
"""
Restart the server with better error logging
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def restart_server():
    """Restart the server with enhanced error logging"""
    print("=== RESTARTING CIBOZER SERVER WITH ERROR LOGGING ===")
    
    try:
        from app import create_app
        
        # Create app
        app = create_app()
        print("App created successfully")
        print("Enhanced error logging enabled")
        print("")
        print("Starting server on http://127.0.0.1:5002")
        print("When you test meal generation, detailed errors will show in this console")
        print("Press CTRL+C to stop")
        print("")
        
        # Start server
        app.run(
            host='127.0.0.1', 
            port=5002, 
            debug=True,
            use_reloader=False
        )
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    restart_server()