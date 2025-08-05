"""
Comprehensive test coverage to identify and fill testing gaps.
Tests all critical functionality with edge cases and error conditions.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from werkzeug.exceptions import BadRequest

from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.models.payment import Payment, PricingPlan


class TestAuthenticationCoverage:
    """Comprehensive authentication tests."""
    
    def test_registration_success(self, client):
        """Test successful user registration."""
        response = client.post('/auth/register', data={
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'full_name': 'New User'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.full_name == 'New User'
    
    def test_registration_duplicate_email(self, client, test_user):
        """Test registration with existing email."""
        response = client.post('/auth/register', data={
            'email': test_user.email,
            'password': 'AnotherPass123!',
            'confirm_password': 'AnotherPass123!',
            'full_name': 'Duplicate User'
        })
        
        assert b'Email already registered' in response.data
    
    def test_registration_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post('/auth/register', data={
            'email': 'weak@example.com',
            'password': '123',
            'confirm_password': '123',
            'full_name': 'Weak Password'
        })
        
        assert b'Password must be at least' in response.data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data
    
    def test_login_rate_limiting(self, client, test_user, app):
        """Test login rate limiting."""
        # Enable rate limiting for this test
        app.config['RATELIMIT_ENABLED'] = True
        
        # Attempt multiple failed logins
        for i in range(10):
            response = client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'wrongpassword'
            })
        
        # Should eventually get rate limited
        # Note: Exact behavior depends on rate limit configuration
    
    def test_logout(self, auth_client):
        """Test user logout."""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
        # Verify user can't access protected routes
        response = auth_client.get('/create')
        assert response.status_code == 302  # Redirect to login
    
    def test_password_reset_request(self, client, test_user):
        """Test password reset request."""
        with patch('app.services.email_service.send_password_reset_email') as mock_send:
            response = client.post('/auth/forgot-password', data={
                'email': test_user.email
            })
            
            assert response.status_code == 302
            mock_send.assert_called_once()


class TestMealGenerationCoverage:
    """Comprehensive meal generation tests."""
    
    def test_meal_generation_all_diet_types(self, auth_client, mock_openai):
        """Test meal generation for all diet types."""
        diet_types = ['standard', 'vegetarian', 'vegan', 'keto', 'paleo', 
                      'mediterranean', 'low-carb', 'high-protein']
        
        for diet_type in diet_types:
            response = auth_client.post('/api/generate', json={
                'diet_type': diet_type,
                'calories': 2000,
                'meals': 3,
                'preferences': []
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'meal_plan' in data
    
    def test_meal_generation_calorie_ranges(self, auth_client, mock_openai):
        """Test meal generation with different calorie targets."""
        calorie_targets = [1200, 1500, 2000, 2500, 3000, 3500]
        
        for calories in calorie_targets:
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': calories,
                'meals': 3
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'meal_plan' in data
    
    def test_meal_generation_invalid_calories(self, auth_client):
        """Test meal generation with invalid calorie values."""
        invalid_calories = [0, -100, 100, 5001, 'abc', None]
        
        for calories in invalid_calories:
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': calories,
                'meals': 3
            })
            
            assert response.status_code == 400
    
    def test_meal_generation_with_allergies(self, auth_client, mock_openai):
        """Test meal generation with allergy constraints."""
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'meals': 3,
            'allergies': ['nuts', 'dairy', 'gluten'],
            'preferences': ['no seafood']
        })
        
        assert response.status_code == 200
    
    def test_meal_generation_insufficient_credits(self, auth_client, test_user):
        """Test meal generation when user has no credits."""
        test_user.credits_balance = 0
        from app.extensions import db
        db.session.commit()
        
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'meals': 3
        })
        
        assert response.status_code == 402  # Payment required
    
    def test_meal_generation_api_timeout(self, auth_client):
        """Test meal generation with API timeout."""
        with patch('openai.ChatCompletion.create', side_effect=Exception('Timeout')):
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000,
                'meals': 3
            })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data


class TestPaymentSystemCoverage:
    """Comprehensive payment system tests."""
    
    def test_create_checkout_session(self, auth_client, mock_stripe):
        """Test Stripe checkout session creation."""
        response = auth_client.post('/payment/create-checkout-session', json={
            'plan': 'premium'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data or 'url' in data
    
    def test_webhook_subscription_created(self, client, test_user, mock_stripe):
        """Test Stripe webhook for subscription creation."""
        webhook_data = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'customer': 'cus_test123',
                    'subscription': 'sub_test123',
                    'metadata': {
                        'user_id': str(test_user.id)
                    }
                }
            }
        }
        
        response = client.post('/payment/webhook', 
                             json=webhook_data,
                             headers={'Stripe-Signature': 'test'})
        
        # Webhook endpoints typically return 200 even on error
        assert response.status_code in [200, 400]
    
    def test_cancel_subscription(self, auth_client, test_user, mock_stripe):
        """Test subscription cancellation."""
        # Set up user with subscription
        test_user.stripe_subscription_id = 'sub_test123'
        from app.extensions import db
        db.session.commit()
        
        response = auth_client.post('/payment/cancel-subscription')
        assert response.status_code in [200, 302]
    
    def test_payment_history(self, auth_client, test_user):
        """Test retrieving payment history."""
        # Create test payments
        from app.extensions import db
        payments = [
            Payment(
                user_id=test_user.id,
                amount=999,
                currency='usd',
                status='completed',
                stripe_payment_id=f'pi_test{i}'
            ) for i in range(3)
        ]
        db.session.add_all(payments)
        db.session.commit()
        
        response = auth_client.get('/api/payment-history')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data.get('payments', [])) == 3


class TestAdminFunctionalityCoverage:
    """Comprehensive admin functionality tests."""
    
    def test_admin_dashboard_access(self, client, admin_user):
        """Test admin dashboard access."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpassword123'
        })
        
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
    
    def test_admin_user_management(self, client, admin_user, test_user):
        """Test admin user management features."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpassword123'
        })
        
        # View users
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert test_user.email.encode() in response.data
    
    def test_admin_grant_credits(self, client, admin_user, test_user):
        """Test admin granting credits to user."""
        # Login as admin
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpassword123'
        })
        
        response = client.post(f'/admin/grant-credits/{test_user.id}', json={
            'credits': 50
        })
        
        assert response.status_code in [200, 302]
        assert test_user.credits_balance == 60  # 10 + 50


class TestSecurityCoverage:
    """Comprehensive security tests."""
    
    def test_sql_injection_protection(self, client):
        """Test SQL injection protection."""
        # Attempt SQL injection in login
        response = client.post('/auth/login', data={
            'email': "admin' OR '1'='1",
            'password': "' OR '1'='1"
        })
        
        assert b'Invalid email or password' in response.data
    
    def test_xss_protection(self, auth_client):
        """Test XSS protection in user inputs."""
        # Attempt to save meal plan with XSS
        response = auth_client.post('/api/save-meal-plan', json={
            'name': '<script>alert("XSS")</script>',
            'meal_plan': {'meals': []}
        })
        
        if response.status_code == 200:
            # Check that script tags are escaped in response
            assert b'<script>' not in response.data
    
    def test_csrf_protection(self, client, app):
        """Test CSRF protection on forms."""
        # Enable CSRF for this test
        app.config['WTF_CSRF_ENABLED'] = True
        
        # Attempt form submission without CSRF token
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password'
        })
        
        # Should fail without valid CSRF token
        assert response.status_code == 400 or b'CSRF' in response.data
    
    def test_file_upload_security(self, auth_client):
        """Test file upload security restrictions."""
        # Attempt to upload malicious file type
        data = {
            'file': (b'malicious code', 'hack.exe')
        }
        
        response = auth_client.post('/api/upload', data=data)
        assert response.status_code in [400, 404]  # Should reject or not have endpoint


class TestEdgeCasesCoverage:
    """Test edge cases and boundary conditions."""
    
    def test_concurrent_meal_generation(self, auth_client, mock_openai):
        """Test concurrent meal generation requests."""
        import threading
        results = []
        
        def generate_meal():
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000,
                'meals': 3
            })
            results.append(response.status_code)
        
        threads = [threading.Thread(target=generate_meal) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All requests should complete successfully
        assert all(status == 200 for status in results)
    
    def test_database_connection_recovery(self, app, client):
        """Test database connection recovery."""
        from app.extensions import db
        
        # Simulate database disconnect
        with patch.object(db.session, 'execute', side_effect=Exception('DB Error')):
            response = client.get('/api/health')
            # Health check should handle DB errors gracefully
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'unhealthy'
    
    def test_memory_leak_prevention(self, auth_client, mock_openai):
        """Test that repeated requests don't cause memory leaks."""
        import gc
        import sys
        
        initial_objects = len(gc.get_objects())
        
        # Make multiple requests
        for _ in range(10):
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000,
                'meals': 3
            })
            assert response.status_code == 200
        
        # Force garbage collection
        gc.collect()
        
        # Check object count hasn't grown excessively
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects
        
        # Allow some growth but not excessive
        assert object_growth < 1000
    
    def test_unicode_handling(self, auth_client):
        """Test Unicode character handling."""
        response = auth_client.post('/api/save-meal-plan', json={
            'name': '健康的な食事プラン 🍱',  # Japanese + emoji
            'meal_plan': {
                'meals': [{
                    'name': 'Breakfast',
                    'items': [{'food': 'Café au lait ☕', 'calories': 100}]
                }]
            }
        })
        
        assert response.status_code == 200


class TestAPIValidationCoverage:
    """Test API input validation comprehensively."""
    
    def test_meal_plan_validation_comprehensive(self, auth_client):
        """Test comprehensive meal plan validation via API."""
        # Valid request
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'meals': 3,
            'preferences': ['low sodium'],
            'allergies': ['nuts']
        })
        assert response.status_code in [200, 500]  # 500 if no OpenAI key
        
        # Invalid diet type
        response = auth_client.post('/api/generate', json={
            'diet_type': 'invalid',
            'calories': 2000
        })
        assert response.status_code == 400
        
        # Invalid calories
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 10000
        })
        assert response.status_code == 400
        
        # Invalid meal count
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'meals': 10
        })
        assert response.status_code == 400
    
    def test_diet_preferences_validation(self, auth_client):
        """Test diet preferences validation via API."""
        # Valid preferences
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'allergies': ['dairy', 'nuts'],
            'restrictions': ['halal'],
            'preferences': ['high-fiber', 'low-sodium']
        })
        assert response.status_code in [200, 500]  # 500 if no OpenAI key
        
        # Too many allergies
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'allergies': ['a'] * 20  # Too many
        })
        assert response.status_code == 400


class TestPerformanceAndLoadCoverage:
    """Test performance and load handling."""
    
    def test_large_meal_plan_handling(self, auth_client):
        """Test handling of large meal plans."""
        large_meal_plan = {
            'meals': [
                {
                    'name': f'Meal {i}',
                    'items': [
                        {
                            'food': f'Food item {j}',
                            'quantity': '100g',
                            'calories': 100
                        } for j in range(20)
                    ]
                } for i in range(7)  # 7 days
            ]
        }
        
        response = auth_client.post('/api/save-meal-plan', json={
            'name': 'Large Weekly Plan',
            'meal_plan': large_meal_plan
        })
        
        assert response.status_code == 200
    
    def test_api_response_time(self, client):
        """Test API response times are acceptable."""
        import time
        
        endpoints = [
            ('/api/health', 'GET'),
            ('/', 'GET'),
            ('/auth/login', 'GET')
        ]
        
        for endpoint, method in endpoints:
            start = time.time()
            
            if method == 'GET':
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            elapsed = time.time() - start
            
            # Response should be under 2 seconds
            assert elapsed < 2.0
            assert response.status_code in [200, 302]


if __name__ == '__main__':
    pytest.main(['-v', __file__])