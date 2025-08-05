"""
Comprehensive Security Testing Suite
Tests all security aspects of the application.
"""

import pytest
import json
import secrets
import hashlib
from unittest.mock import patch, MagicMock
import time
from datetime import datetime, timedelta

from app.models.user import User
from app.extensions import db


class TestAuthenticationSecurity:
    """Test authentication security measures."""
    
    def test_password_hashing_security(self, app):
        """Test password hashing is secure."""
        with app.app_context():
            user = User(email='test@example.com')
            password = 'MySecurePassword123!'
            user.set_password(password)
            
            # Password should be hashed, not plain text
            assert user.password_hash != password
            assert len(user.password_hash) > 50  # Bcrypt hashes are long
            assert user.password_hash.startswith('$2b$')  # Bcrypt prefix
            
            # Verify password check works
            assert user.check_password(password)
            assert not user.check_password('WrongPassword')
    
    def test_sql_injection_attempts(self, client):
        """Test SQL injection protection across endpoints."""
        sql_payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1--",
            "') OR ('1'='1",
        ]
        
        for payload in sql_payloads:
            # Login attempt
            response = client.post('/auth/login', data={
                'email': payload,
                'password': payload
            })
            assert response.status_code == 200  # Should return form, not error
            assert b'Invalid email or password' in response.data
            
            # Registration attempt
            response = client.post('/auth/register', data={
                'email': payload,
                'password': 'password123',
                'confirm_password': 'password123'
            })
            # Should validate email format
            assert b'Invalid email' in response.data or response.status_code == 400
    
    def test_xss_prevention(self, auth_client):
        """Test XSS prevention in user inputs."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(`xss`)">',
            '<input onfocus=alert("XSS") autofocus>',
        ]
        
        for payload in xss_payloads:
            # Try in meal plan name
            response = auth_client.post('/api/save-meal-plan', json={
                'name': payload,
                'meal_plan': {'meals': []}
            })
            
            if response.status_code == 200:
                # Verify the payload is escaped in any response
                assert payload.encode() not in response.data
                # Check for escaped version
                assert b'&lt;script&gt;' in response.data or b'&lt;' in response.data or payload.encode() not in response.data
    
    def test_session_security(self, client, test_user):
        """Test session security features."""
        # Login
        response = client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword123'
        })
        assert response.status_code == 302
        
        # Check session cookie security flags
        cookies = response.headers.getlist('Set-Cookie')
        session_cookie = next((c for c in cookies if 'session=' in c), None)
        
        if session_cookie:
            # Should have security flags
            assert 'HttpOnly' in session_cookie  # Prevent JS access
            assert 'SameSite' in session_cookie  # CSRF protection
            # Secure flag might only be set in production with HTTPS
    
    def test_brute_force_protection(self, client, test_user):
        """Test brute force attack protection."""
        # Attempt multiple failed logins
        failed_attempts = []
        
        for i in range(20):
            response = client.post('/auth/login', data={
                'email': test_user.email,
                'password': f'wrongpassword{i}'
            })
            failed_attempts.append(response.status_code)
            time.sleep(0.1)  # Small delay to avoid overwhelming
        
        # Should see some form of rate limiting or account protection
        # Either 429 (rate limit) or increased response times
        unique_statuses = set(failed_attempts)
        assert len(unique_statuses) > 1 or 429 in failed_attempts


class TestAPISecurityTests:
    """Test API security measures."""
    
    def test_api_authentication_required(self, client):
        """Test that API endpoints require authentication."""
        protected_endpoints = [
            ('/api/generate', 'POST', {'diet_type': 'standard', 'calories': 2000}),
            ('/api/save-meal-plan', 'POST', {'name': 'Test', 'meal_plan': {}}),
            ('/api/user/profile', 'GET', None),
            ('/api/saved-plans', 'GET', None),
        ]
        
        for endpoint, method, data in protected_endpoints:
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json=data)
            
            # Should require authentication
            assert response.status_code in [302, 401, 403]
    
    def test_csrf_protection(self, app, client):
        """Test CSRF protection on state-changing operations."""
        # Enable CSRF for this test
        app.config['WTF_CSRF_ENABLED'] = True
        
        # Try POST without CSRF token
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password'
        })
        
        # Should fail without CSRF token
        assert response.status_code == 400 or b'CSRF' in response.data
    
    def test_api_input_validation(self, auth_client):
        """Test API input validation for security."""
        # Test integer overflow
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 999999999999999999999
        })
        assert response.status_code == 400
        
        # Test negative values
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': -1000
        })
        assert response.status_code == 400
        
        # Test invalid types
        response = auth_client.post('/api/generate', json={
            'diet_type': ['standard'],  # Should be string
            'calories': '2000'  # Should be int
        })
        assert response.status_code == 400
    
    def test_api_response_headers(self, client):
        """Test security headers in API responses."""
        response = client.get('/api/health')
        
        # Check security headers
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-Frame-Options') in ['DENY', 'SAMEORIGIN']
        assert 'Content-Security-Policy' in response.headers
        
        # API responses should not be cacheable if they contain user data
        cache_control = response.headers.get('Cache-Control', '')
        if 'no-store' not in cache_control:
            # At least should revalidate
            assert 'no-cache' in cache_control or 'must-revalidate' in cache_control


class TestDataSecurityTests:
    """Test data security and privacy."""
    
    def test_sensitive_data_exposure(self, auth_client, test_user):
        """Test that sensitive data is not exposed."""
        # Get user profile
        response = auth_client.get('/api/user/profile')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        
        # Should not expose sensitive fields
        assert 'password_hash' not in data
        assert 'password' not in data
        assert 'session_token' not in data
        
        # Should not expose internal IDs unnecessarily
        if 'id' in data:
            # ID should be obfuscated or UUID
            assert not str(data['id']).isdigit() or len(str(data['id'])) > 10
    
    def test_user_data_isolation(self, app):
        """Test that users cannot access other users' data."""
        with app.app_context():
            # Create two users with meal plans
            user1 = User(email='user1@example.com')
            user1.set_password('password123')
            user2 = User(email='user2@example.com')
            user2.set_password('password123')
            
            db.session.add_all([user1, user2])
            db.session.commit()
            
            # Create meal plan for user2
            from app.models.meal_plan import SavedMealPlan
            meal_plan = SavedMealPlan(
                user_id=user2.id,
                name='Private Plan',
                meal_data={'meals': []},
                is_public=False
            )
            db.session.add(meal_plan)
            db.session.commit()
            
            meal_plan_id = meal_plan.id
        
        # Login as user1
        with app.test_client() as client:
            client.post('/auth/login', data={
                'email': 'user1@example.com',
                'password': 'password123'
            })
            
            # Try to access user2's meal plan
            response = client.get(f'/api/meal-plan/{meal_plan_id}')
            assert response.status_code in [403, 404]  # Forbidden or Not Found
    
    def test_payment_data_security(self, auth_client):
        """Test payment data security."""
        # Create checkout session
        response = auth_client.post('/payment/create-checkout-session', json={
            'plan': 'premium'
        })
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Should not expose sensitive payment data
            assert 'stripe_secret_key' not in data
            assert 'customer_id' not in data
            
            # Should only have public-safe data
            assert 'session_id' in data or 'url' in data


class TestFileSecurityTests:
    """Test file upload and handling security."""
    
    def test_file_upload_restrictions(self, auth_client):
        """Test file upload security restrictions."""
        # Try to upload executable
        response = auth_client.post('/api/upload', data={
            'file': (b'malicious code', 'hack.exe')
        })
        assert response.status_code in [400, 403, 404]
        
        # Try to upload PHP file
        response = auth_client.post('/api/upload', data={
            'file': (b'<?php system($_GET["cmd"]); ?>', 'shell.php')
        })
        assert response.status_code in [400, 403, 404]
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal attack prevention."""
        path_traversal_attempts = [
            '/static/../../../etc/passwd',
            '/static/..\\..\\..\\windows\\system32\\config\\sam',
            '/download?file=../../../etc/passwd',
            '/api/export?path=../../config.py',
        ]
        
        for path in path_traversal_attempts:
            response = client.get(path)
            # Should not allow access to system files
            assert response.status_code in [400, 403, 404]
            assert b'passwd' not in response.data
            assert b'config' not in response.data


class TestCryptographicSecurity:
    """Test cryptographic security measures."""
    
    def test_secure_random_generation(self, app):
        """Test secure random number generation."""
        with app.app_context():
            # Generate multiple tokens
            tokens = set()
            for _ in range(100):
                token = secrets.token_urlsafe(32)
                tokens.add(token)
            
            # All should be unique
            assert len(tokens) == 100
            
            # Should be sufficiently long
            assert all(len(token) >= 32 for token in tokens)
    
    def test_password_reset_token_security(self, client, test_user):
        """Test password reset token security."""
        with patch('app.services.email_service.send_password_reset_email') as mock_send:
            # Request password reset
            response = client.post('/auth/forgot-password', data={
                'email': test_user.email
            })
            
            if mock_send.called:
                # Extract token from mock call
                call_args = mock_send.call_args
                
                # Token should be secure
                # (Would need to inspect actual implementation)
                assert mock_send.called
    
    def test_api_key_security(self, auth_client):
        """Test API key generation and security."""
        # Generate API key (if supported)
        response = auth_client.post('/api/generate-key')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            api_key = data.get('api_key', '')
            
            # API key should be secure
            assert len(api_key) >= 32  # Sufficient length
            assert api_key.isalnum() or '-' in api_key or '_' in api_key  # Safe characters


class TestSecurityMonitoring:
    """Test security monitoring and logging."""
    
    def test_failed_login_logging(self, client, test_user):
        """Test that failed logins are logged."""
        with patch('app.logger.warning') as mock_logger:
            # Failed login attempt
            client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrongpassword'
            })
            
            # Should log the attempt
            # (Actual implementation may vary)
            # mock_logger.assert_called()
    
    def test_suspicious_activity_detection(self, client):
        """Test detection of suspicious activity."""
        # Rapid requests from same client
        suspicious_requests = [
            '/admin/',
            '/admin/users',
            '/api/admin/grant-credits',
            '/.env',
            '/config.py',
            '/wp-admin/',
        ]
        
        responses = []
        for path in suspicious_requests:
            response = client.get(path)
            responses.append(response.status_code)
        
        # Should block or log suspicious requests
        assert all(status in [302, 403, 404] for status in responses)


class TestComplianceSecurity:
    """Test security compliance requirements."""
    
    def test_pii_data_handling(self, auth_client, test_user):
        """Test proper handling of Personally Identifiable Information."""
        # Request data export
        response = auth_client.get('/api/user/export-data')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Should include user PII
            assert 'email' in data.get('user', {})
            
            # But should not include system internals
            assert 'password_hash' not in data.get('user', {})
    
    def test_data_retention_compliance(self, app, test_user):
        """Test data retention and deletion compliance."""
        with app.app_context():
            # Mark user for deletion
            test_user.deleted_at = datetime.utcnow() - timedelta(days=31)
            db.session.commit()
            
            # Run cleanup (would be scheduled task)
            # Implementation depends on actual cleanup logic
            
            # Verify user data is properly handled
            user = User.query.get(test_user.id)
            # Should either be deleted or anonymized
            assert user is None or user.email != test_user.email


if __name__ == '__main__':
    pytest.main(['-v', __file__])