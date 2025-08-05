#!/usr/bin/env python3
"""Minimal working Flask app to test login"""
import os
import sqlite3
from flask import Flask, request, session, redirect
from werkzeug.security import check_password_hash

# Create minimal Flask app
app = Flask(__name__)
app.secret_key = 'test-secret-key-12345'

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'dev_cibozer.db')

@app.route('/')
def index():
    if 'user_email' in session:
        return f'<h1>Logged in as: {session["user_email"]}</h1><br><a href="/logout">Logout</a>'
    return '<h1>Not logged in</h1><br><a href="/login">Login</a>'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
        <h2>Simple Login Test</h2>
        <form method="POST">
            Email: <input name="email" value="admin@cibozer.com"><br>
            Password: <input type="password" name="password" value="Admin123!"><br>
            <button type="submit">Login</button>
        </form>
        '''
    
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Direct database query
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT email, password_hash FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if row and check_password_hash(row[1], password):
            session['user_email'] = email
            return redirect('/')
        else:
            return 'Login failed. <a href="/login">Try again</a>'
            
    except Exception as e:
        import traceback
        return f'<pre>ERROR: {e}\n\n{traceback.format_exc()}</pre>'

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect('/')

if __name__ == '__main__':
    print("\n" + "="*50)
    print("MINIMAL TEST APP")
    print("="*50)
    print(f"Database: {DB_PATH}")
    print(f"URL: http://localhost:8888")
    print("\nThis bypasses ALL Flask extensions and middleware.")
    print("If this works, the issue is with Flask configuration.")
    print("If this fails, the issue is with the database.")
    print("="*50)
    app.run(port=8888, debug=False)  # No debug to avoid reloading