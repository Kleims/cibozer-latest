#!/usr/bin/env python3
"""Minimal test server to debug login"""
from flask import Flask, request, jsonify
from app import create_app
from app.models import db, User
from app.extensions import login_manager
import traceback

# Create a test app
app = create_app()

@app.route('/test-login', methods=['GET', 'POST'])
def test_login():
    if request.method == 'GET':
        return '''
        <form method="POST">
            <input name="email" placeholder="Email" value="admin@cibozer.com"><br>
            <input name="password" type="password" placeholder="Password" value="SecureAdminPassword123!"><br>
            <button type="submit">Test Login</button>
        </form>
        '''
    
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Debug info
        debug_info = []
        debug_info.append(f"Email received: {email}")
        debug_info.append(f"Password received: {'*' * len(password) if password else 'None'}")
        
        # Try to get user
        user = User.query.filter_by(email=email).first()
        debug_info.append(f"User found: {user is not None}")
        
        if user:
            debug_info.append(f"User ID: {user.id}")
            debug_info.append(f"User active: {user.is_active}")
            debug_info.append(f"Email verified: {user.email_verified}")
            
            # Check password
            password_correct = user.check_password(password)
            debug_info.append(f"Password correct: {password_correct}")
            
            if password_correct:
                # Try login_user
                from flask_login import login_user
                try:
                    result = login_user(user)
                    debug_info.append(f"login_user result: {result}")
                except Exception as e:
                    debug_info.append(f"login_user error: {e}")
                    debug_info.append(traceback.format_exc())
        
        return '<pre>' + '\n'.join(debug_info) + '</pre>'
        
    except Exception as e:
        return f'<pre>ERROR: {e}\n\n{traceback.format_exc()}</pre>'

if __name__ == '__main__':
    print("\nTest server starting...")
    print("Go to: http://localhost:5001/test-login")
    print("\nThis bypasses all middleware to test login directly.")
    app.run(port=5001, debug=True)