"""Performance tests for critical endpoints"""

import pytest
import time
from app import create_app
from app.extensions import db
from models import User

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

def test_home_page_performance(client):
    """Test home page loads within acceptable time"""
    start_time = time.time()
    response = client.get('/')
    end_time = time.time()
    
    assert response.status_code == 200
    assert (end_time - start_time) < 2.0  # Should load in under 2 seconds

def test_api_response_time(client):
    """Test API endpoints respond quickly"""
    start_time = time.time()
    response = client.get('/api/health')
    end_time = time.time()
    
    # API should respond in under 1 second
    assert (end_time - start_time) < 1.0
