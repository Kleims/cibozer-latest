#!/usr/bin/env python
"""Test script to verify auth fixes"""

import pytest
from app import create_app
from app.extensions import db

@pytest.fixture
def client():
    """Test client fixture"""
    app = create_app()
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
    response = client.get('/auth/login')
    assert response.status_code == 200, f"Login page returned {response.status_code}"
    
    # Test register page  
    response = client.get('/auth/register')
    assert response.status_code == 200, f"Register page returned {response.status_code}"
    
    # Test logout route (should redirect)
    response = client.get('/auth/logout', follow_redirects=False)
    assert response.status_code in [302, 301], f"/auth/logout returned unexpected {response.status_code}"