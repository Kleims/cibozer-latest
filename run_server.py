#!/usr/bin/env python
"""
Production-ready development server for Cibozer
Handles port conflicts, proper shutdown, and logging
"""

import os
import sys
import socket
import signal
import time
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

def check_port(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except:
        return False

def find_available_port(start_port=5001):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 10):
        if check_port(port):
            return port
    return None

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n\nShutting down server...')
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    os.environ['DEBUG'] = 'True'
    
    # Find available port
    preferred_port = 5001
    port = find_available_port(preferred_port)
    
    if not port:
        print("ERROR: No available ports found!")
        print("Please stop other running instances.")
        return 1
    
    # Import app here to avoid import issues
    try:
        from app import app
    except Exception as e:
        print(f"ERROR: Failed to import app: {e}")
        return 1
    
    # Display startup banner
    print("\n" + "=" * 60)
    print("  Cibozer Development Server")
    print("=" * 60)
    print()
    
    if port != preferred_port:
        print(f"  NOTE: Port {preferred_port} was busy, using port {port}")
        print()
    
    print(f"  Main App:    http://localhost:{port}")
    print(f"  Admin Panel: http://localhost:{port}/admin")
    print()
    print("  Admin Credentials:")
    print("     Username: admin")
    print("     Password: (--F#.A8xzYlTn/3")
    print()
    print("  Tips:")
    print("     - Press Ctrl+C to stop the server")
    print("     - Check logs/ folder for application logs")
    print("     - Visit /health for system status")
    print()
    print("=" * 60)
    print()
    
    # Start the server
    try:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=port,
            use_reloader=False,  # Disable reloader to prevent double startup
            threaded=True       # Enable threading for better performance
        )
    except Exception as e:
        print(f"\nERROR: Server failed to start: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())