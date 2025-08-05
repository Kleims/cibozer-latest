#!/usr/bin/env python3
"""
Test file with hardcoded secret for APEX to find and fix
"""

def setup_test_user():
    """Create test user with hardcoded password"""
    password = 'hardcoded123'  # This should be found by APEX
    secret = 'my-secret-key'   # This too
    
    print(f"Creating user with password: {password}")
    print(f"Using secret: {secret}")
    
    return True

if __name__ == '__main__':
    setup_test_user()