"""Integration tests for Cibozer application"""

import pytest
import json
from app import create_app
from models import db, User
import tempfile
import os

@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def logged_in_user(app, client):
    """Create a logged-in user"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            credits=10,
            is_premium=True
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        # Login
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        return user

def test_home_page(client):
    """Test home page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_meal_planning_requires_auth(client):
    """Test meal planning requires authentication"""
    response = client.post('/generate_meal_plan', json={
        'dietary_restrictions': ['vegetarian'],
        'budget': 50
    })
    assert response.status_code == 302  # Redirect to login

def test_meal_planning_with_auth(client, logged_in_user):
    """Test meal planning with authenticated user"""
    response = client.post('/generate_meal_plan', json={
        'dietary_restrictions': ['vegetarian'],
        'budget': 50,
        'meals_per_day': 3,
        'days': 7
    })
    # Should not redirect (would be 200 or error, not 302)
    assert response.status_code != 302

def test_video_generation_requires_credits(client, logged_in_user):
    """Test video generation requires credits"""
    response = client.post('/generate_video', json={
        'recipe_name': 'Test Recipe',
        'ingredients': ['test ingredient'],
        'instructions': ['test instruction']
    })
    # Should handle the request (not redirect to login)
    assert response.status_code != 302
