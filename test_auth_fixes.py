#!/usr/bin/env python
"""Test script to verify auth fixes"""

import pytest
from app import app
from models import db

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_auth_routes(client):
    """Test that auth routes are accessible"""
    # Test login page
    response = client.get('/login')
    assert response.status_code == 200, f"Login page returned {response.status_code}"
    
    # Test register page
    response = client.get('/register')
    assert response.status_code == 200, f"Register page returned {response.status_code}"
    
    # Test that /auth/login returns 404 or redirects
    response = client.get('/auth/login', follow_redirects=False)
    assert response.status_code in [404, 302, 301], f"/auth/login returned unexpected {response.status_code}"