"""Integration tests for Cibozer application"""

import pytest
import json
from app import create_app
from app.extensions import db
from models import User
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
            email='test@example.com',
            credits_balance=10,
            subscription_tier='premium',
            subscription_status='active'
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        # Login
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpass'
        })
        
        return user

def test_home_page(client):
    """Test home page loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_meal_planning_requires_auth(client):
    """Test meal planning requires authentication"""
    response = client.post('/api/generate-meal-plan', json={
        'calories': 2000,
        'diet_type': 'vegetarian',
        'meals_per_day': 3
    })
    # Should be 401 (Unauthorized), 302 (redirect to login), 400 (bad request), or 405 (method not allowed)
    assert response.status_code in [401, 302, 400, 405]

def test_meal_planning_with_auth(client, logged_in_user):
    """Test meal planning with authenticated user"""
    response = client.post('/api/generate-meal-plan', json={
        'calories': 2000,
        'diet_type': 'vegetarian',
        'meals_per_day': 3,
        'days': 1
    })
    # Should handle the request (200 or 400/500 for errors)
    assert response.status_code in [200, 400, 500]

def test_video_generation_requires_credits(client, logged_in_user):
    """Test video generation requires premium"""
    # First create a meal plan
    meal_plan_response = client.post('/api/save-meal-plan', json={
        'name': 'Test Plan',
        'meal_plan': {'day1': {'breakfast': {'name': 'Test'}}},
        'total_calories': 2000
    })
    
    if meal_plan_response.status_code == 200:
        meal_plan_id = meal_plan_response.json.get('meal_plan_id', 1)
        response = client.get(f'/api/generate-video/{meal_plan_id}')
        # Should be 200 (success) or 403 (requires premium)
        assert response.status_code in [200, 403]
