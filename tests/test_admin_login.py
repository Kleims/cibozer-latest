"""
Tests for admin login functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db
from models import User


class TestAdminLogin:
    """Test admin login functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def teardown_method(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_create_admin_user(self):
        """Test creating an admin user"""
        with self.app.app_context():
            # Create admin user
            admin = User(
                email='admin@test.com',
                full_name='Admin User',
                subscription_tier='pro',
                credits_balance=100
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            
            # Verify user was created
            user = User.query.filter_by(email='admin@test.com').first()
            assert user is not None
            assert user.full_name == 'Admin User'
            assert user.check_password('admin123')
    
    def test_admin_login_success(self):
        """Test successful admin login"""
        with self.app.app_context():
            # Create test admin user
            admin = User(
                email='admin@test.com',
                full_name='Admin User'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Test login
        response = self.client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_admin_login_failure(self):
        """Test failed admin login with wrong password"""
        with self.app.app_context():
            # Create test admin user
            admin = User(
                email='admin@test.com',
                full_name='Admin User'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Test login with wrong password
        response = self.client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200  # Stays on login page
        assert b'Invalid email or password' in response.data or b'error' in response.data.lower()