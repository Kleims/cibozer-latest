"""
Simplified tests for app functionality
"""
import pytest
import json
from app import create_app
from app.extensions import db
from models import User


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def init_db(app):
    """Initialize database"""
    with app.app_context():
        # Import models to ensure they're registered
        from models import User, SavedMealPlan, Payment, UsageLog
        db.create_all()
        yield db
        db.drop_all()


def test_index_page(client):
    """Test main landing page loads"""
    rv = client.get('/')
    assert rv.status_code == 200


def test_health_check(client):
    """Test health check endpoint"""
    rv = client.get('/api/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'status' in data


def test_auth_routes(client):
    """Test auth routes are accessible"""
    # Login page
    rv = client.get('/auth/login')
    assert rv.status_code == 200
    
    # Register page
    rv = client.get('/auth/register')
    assert rv.status_code == 200


def test_static_files(client):
    """Test static files are served"""
    rv = client.get('/static/css/style.css')
    assert rv.status_code in [200, 304]  # 304 = Not Modified


def test_404_page(client):
    """Test 404 error page"""
    rv = client.get('/nonexistent-page')
    assert rv.status_code == 404


def test_create_page_requires_auth(client):
    """Test create page requires authentication"""
    rv = client.get('/create')
    assert rv.status_code == 302  # Redirect to login


def test_api_requires_auth(client):
    """Test API endpoints require authentication"""
    rv = client.post('/api/generate-meal-plan', json={
        'calories': 2000,
        'diet_type': 'balanced'
    })
    assert rv.status_code in [401, 302, 400]  # Unauthorized or redirect