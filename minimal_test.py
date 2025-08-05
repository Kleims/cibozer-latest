#!/usr/bin/env python
"""
Minimal Flask app test to isolate the issue
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'test-key')
app.config['DEBUG'] = True

@app.route('/')
def test_home():
    return "MINIMAL TEST: Flask is working!"

@app.route('/test-db')
def test_db():
    try:
        # Test basic imports
        from app.extensions import db
        from app import create_app
        
        real_app = create_app()
        with real_app.app_context():
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).scalar()
            return f"DATABASE TEST: Success - {result}"
    except Exception as e:
        return f"DATABASE TEST: Failed - {str(e)}"

if __name__ == '__main__':
    print("Starting minimal test server...")
    app.run(host='127.0.0.1', port=5001, debug=True)