#!/usr/bin/env python3
"""Check if login manager is configured correctly"""
from app import create_app
from app.models import User
from app.extensions import login_manager

def check_login_manager():
    app = create_app()
    
    with app.app_context():
        print("=== LOGIN MANAGER CONFIGURATION ===")
        print(f"Login view: {login_manager.login_view}")
        print(f"Login message: {login_manager.login_message}")
        print(f"Session protection: {login_manager.session_protection}")
        
        # Check user loader
        print("\n=== USER LOADER TEST ===")
        try:
            # Test loading user ID 1
            user = login_manager._user_callback(1)
            if user:
                print(f"User loader works! Loaded: {user.email}")
            else:
                print("User loader returned None for ID 1")
        except Exception as e:
            print(f"User loader error: {e}")
            import traceback
            traceback.print_exc()
            
        # Check if User model has required methods
        print("\n=== USER MODEL METHODS ===")
        user = User.query.first()
        if user:
            print(f"is_authenticated: {hasattr(user, 'is_authenticated')}")
            print(f"is_active property: {hasattr(user, 'is_active')}")
            print(f"is_anonymous: {hasattr(user, 'is_anonymous')}")
            print(f"get_id: {hasattr(user, 'get_id')}")
            
            # Test get_id
            try:
                user_id = user.get_id()
                print(f"get_id() returns: {user_id} (type: {type(user_id)})")
            except Exception as e:
                print(f"get_id() error: {e}")

if __name__ == '__main__':
    check_login_manager()