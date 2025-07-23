"""Tests for admin.py"""

import pytest
from unittest.mock import patch, MagicMock
from flask import session
from app import create_app
import admin
from admin import admin_required


class TestAdminDecorator:
    """Test the admin_required decorator"""
    
    def test_admin_required_decorator(self):
        """Test admin_required decorator functionality"""
        # Create a mock function
        mock_func = MagicMock(return_value="success")
        mock_func.__name__ = "mock_func"
        
        # Apply the decorator
        decorated = admin_required(mock_func)
        
        # Test that decorator returns a function
        assert callable(decorated)
        assert decorated.__name__ == "mock_func"


class TestAdminRoutes:
    """Test admin route functions using Flask test client"""
    
    def setup_method(self):
        """Set up test client"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    def test_login_get(self):
        """Test GET request to login page"""
        response = self.client.get('/admin/login')
        assert response.status_code == 200
    
    def test_login_post_invalid(self):
        """Test POST request with invalid credentials"""
        response = self.client.post('/admin/login', data={
            'password': 'wrong_password'
        })
        assert response.status_code == 200
        # Check that user is not logged in
        with self.client.session_transaction() as sess:
            assert not sess.get('is_admin')
    
    @patch('admin.os.environ.get')
    def test_login_post_valid(self, mock_environ):
        """Test POST request with valid credentials"""
        mock_environ.return_value = 'test_password'
        
        response = self.client.post('/admin/login', data={
            'password': 'test_password'
        }, follow_redirects=True)
        
        # Should redirect to dashboard
        assert response.status_code == 200
    
    def test_logout(self):
        """Test logout functionality"""
        with self.client:
            # Set admin session
            with self.client.session_transaction() as sess:
                sess['is_admin'] = True
            
            response = self.client.get('/admin/logout')
            assert response.status_code == 302  # Redirect
            
            # Check session is cleared
            with self.client.session_transaction() as sess:
                assert not sess.get('is_admin')
    
    def test_dashboard_without_auth(self):
        """Test dashboard access without authentication"""
        response = self.client.get('/admin/dashboard')
        assert response.status_code == 302  # Redirect to login
    
    def test_dashboard_with_auth(self):
        """Test dashboard access with authentication"""
        with self.client:
            with self.client.session_transaction() as sess:
                sess['is_admin'] = True
            
            with patch('admin.User') as mock_user:
                with patch('admin.SavedMealPlan') as mock_plan:
                    with patch('admin.Payment') as mock_payment:
                        # Mock database queries
                        mock_user.query.count.return_value = 10
                        mock_plan.query.count.return_value = 20
                        mock_payment.query.count.return_value = 5
                        mock_payment.query.filter_by.return_value.with_entities.return_value.scalar.return_value = 100.0
                        
                        response = self.client.get('/admin/dashboard')
                        assert response.status_code == 200
    
    def test_video_generator_without_auth(self):
        """Test video generator access without authentication"""
        response = self.client.get('/admin/video-generator')
        assert response.status_code == 302  # Redirect to login
    
    def test_video_generator_with_auth(self):
        """Test video generator access with authentication"""
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        
        response = self.client.get('/admin/video-generator')
        assert response.status_code == 200
    
    def test_generate_content_video_without_auth(self):
        """Test generate content video without authentication"""
        response = self.client.post('/admin/generate-content-video')
        assert response.status_code == 302  # Redirect to login
    
    @patch('admin.VideoContentGenerator')
    def test_generate_content_video_with_auth(self, mock_generator):
        """Test generate content video with authentication"""
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        
        # Mock the video generator
        mock_instance = MagicMock()
        mock_instance.create_promotional_video.return_value = {
            'success': True,
            'filename': 'test_video.mp4'
        }
        mock_generator.return_value = mock_instance
        
        response = self.client.post('/admin/generate-content-video', json={
            'type': 'benefits',
            'style': 'modern'
        })
        
        assert response.status_code == 200
        assert response.json['success'] is True
    
    def test_batch_generate_without_auth(self):
        """Test batch generate without authentication"""
        response = self.client.post('/admin/batch-generate')
        assert response.status_code == 302  # Redirect to login
    
    def test_analytics_without_auth(self):
        """Test analytics access without authentication"""
        response = self.client.get('/admin/analytics')
        assert response.status_code == 302  # Redirect to login
    
    def test_analytics_with_auth(self):
        """Test analytics access with authentication"""
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        
        with patch('admin.db.session.execute') as mock_execute:
            # Mock the database queries
            mock_execute.return_value.fetchall.return_value = []
            
            response = self.client.get('/admin/analytics')
            assert response.status_code == 200
    
    def test_refill_credits_without_auth(self):
        """Test refill credits without authentication"""
        response = self.client.post('/admin/refill-credits')
        assert response.status_code == 302  # Redirect to login
    
    def test_refill_credits_with_auth(self):
        """Test refill credits with authentication"""
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        
        with patch('admin.User') as mock_user:
            # Mock user query
            mock_user_instance = MagicMock()
            mock_user_instance.email = 'test@example.com'
            mock_user_instance.credits_balance = 50
            mock_user.query.get.return_value = mock_user_instance
            
            with patch('admin.db.session.commit'):
                response = self.client.post('/admin/refill-credits', json={
                    'user_id': 1,
                    'credits': 100
                })
                
                assert response.status_code == 200
                assert response.json['success'] is True
    
    def test_users_without_auth(self):
        """Test users page without authentication"""
        response = self.client.get('/admin/users')
        assert response.status_code == 302  # Redirect to login
    
    def test_users_with_auth(self):
        """Test users page with authentication"""
        with self.client.session_transaction() as sess:
            sess['is_admin'] = True
        
        with patch('admin.User') as mock_user:
            # Mock user query
            mock_user.query.order_by.return_value.all.return_value = []
            
            response = self.client.get('/admin/users')
            assert response.status_code == 200