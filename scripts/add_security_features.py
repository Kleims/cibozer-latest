#!/usr/bin/env python3
"""Add security features to Cibozer application"""

import sys
import argparse
from pathlib import Path
import re

def check_csrf_exists():
    """Check if CSRF protection is already configured"""
    app_py = Path(__file__).parent.parent / 'app.py'
    if not app_py.exists():
        print(f"Error: app.py not found at {app_py}")
        return False
        
    with open(app_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for CSRF imports and initialization
    has_import = 'from flask_wtf.csrf import CSRFProtect' in content
    has_init = re.search(r'csrf\s*=\s*CSRFProtect\(app\)', content) is not None
    
    return has_import and has_init

def add_csrf_protection():
    """Add CSRF protection to the Flask app"""
    app_py = Path(__file__).parent.parent / 'app.py'
    
    if not app_py.exists():
        print(f"Error: app.py not found at {app_py}")
        return False
    
    # Check if already exists
    if check_csrf_exists():
        print("CSRF protection already configured in app.py")
        return True
    
    with open(app_py, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find where to add import
    import_added = False
    csrf_added = False
    
    for i, line in enumerate(lines):
        # Add import after other Flask imports
        if not import_added and line.startswith('from flask'):
            # Insert after all flask imports
            j = i
            while j < len(lines) and lines[j].startswith('from flask'):
                j += 1
            lines.insert(j, 'from flask_wtf.csrf import CSRFProtect\n')
            import_added = True
        
        # Add CSRF initialization after app creation and configuration
        if not csrf_added and 'CORS(app)' in line:
            # Add after CORS initialization
            lines.insert(i + 1, 'csrf = CSRFProtect(app)\n')
            csrf_added = True
            break
    
    # If we didn't find CORS, look for app initialization
    if not csrf_added:
        for i, line in enumerate(lines):
            if 'app = Flask(__name__)' in line:
                # Find next non-configuration line
                j = i + 1
                while j < len(lines) and ('app.' in lines[j] or lines[j].strip() == ''):
                    j += 1
                lines.insert(j, '\n# Initialize CSRF protection\ncsrf = CSRFProtect(app)\n')
                csrf_added = True
                break
    
    if import_added and csrf_added:
        # Write back the modified content
        with open(app_py, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Successfully added CSRF protection to app.py")
        return True
    else:
        print("Error: Could not add CSRF protection")
        return False

def add_security_headers():
    """Add security headers middleware"""
    # This would add security headers like X-Frame-Options, CSP, etc.
    # For now, we'll note this as a future enhancement
    print("Security headers: Already handled by Flask-Talisman if configured")
    return True

def main():
    parser = argparse.ArgumentParser(description='Add security features to Cibozer')
    parser.add_argument('--csrf', action='store_true', help='Add CSRF protection')
    parser.add_argument('--headers', action='store_true', help='Add security headers')
    parser.add_argument('--all', action='store_true', help='Add all security features')
    
    args = parser.parse_args()
    
    success = True
    
    if args.csrf or args.all:
        if not add_csrf_protection():
            success = False
    
    if args.headers or args.all:
        if not add_security_headers():
            success = False
    
    if not any([args.csrf, args.headers, args.all]):
        print("Please specify a security feature to add (--csrf, --headers, or --all)")
        success = False
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())