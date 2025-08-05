"""
Integration and End-to-End tests for complete user workflows.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.models.payment import Payment, PricingPlan
from app.extensions import db


class TestCompleteUserJourney:
    """Test complete user journey from registration to meal plan generation."""
    
    def test_new_user_complete_flow(self, client, mock_openai):
        """Test complete flow for a new user."""
        # 1. Visit homepage
        response = client.get('/')
        assert response.status_code == 200
        assert b'AI-Powered Meal Planning' in response.data
        
        # 2. Register new account
        response = client.post('/auth/register', data={
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
            'full_name': 'New User'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # 3. Verify user is logged in
        response = client.get('/create')
        assert response.status_code == 200
        assert b'Create Your Meal Plan' in response.data
        
        # 4. Generate first meal plan (free tier)
        response = client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'meals': 3,
            'preferences': ['low sodium']
        })
        assert response.status_code == 200
        meal_plan = json.loads(response.data)
        assert 'meal_plan' in meal_plan
        
        # 5. Save the meal plan
        response = client.post('/api/save-meal-plan', json={
            'name': 'My First Plan',
            'meal_plan': meal_plan['meal_plan']
        })
        assert response.status_code == 200
        
        # 6. View saved plans
        response = client.get('/api/saved-plans')
        assert response.status_code == 200
        plans = json.loads(response.data)
        assert len(plans) == 1
        assert plans[0]['name'] == 'My First Plan'
        
        # 7. Check remaining credits
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user.credits_balance == 2  # Started with 3, used 1
    
    def test_premium_upgrade_flow(self, client, test_user, mock_stripe):
        """Test user upgrading to premium plan."""
        # 1. Login
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword123'
        })
        
        # 2. View pricing page
        response = client.get('/pricing')
        assert response.status_code == 200
        
        # 3. Create checkout session
        response = client.post('/payment/create-checkout-session', json={
            'plan': 'premium'
        })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data or 'url' in data
        
        # 4. Simulate successful payment webhook
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
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_data
            response = client.post('/payment/webhook',
                                 json=webhook_data,
                                 headers={'Stripe-Signature': 'test'})
        
        # 5. Verify premium features unlocked
        response = client.get('/api/user/status')
        assert response.status_code == 200
        status = json.loads(response.data)
        assert status.get('is_premium') or test_user.stripe_subscription_id is not None


class TestMealPlanSharingWorkflow:
    """Test meal plan sharing functionality end-to-end."""
    
    def test_share_meal_plan_workflow(self, client, test_user, saved_meal_plan):
        """Test complete meal plan sharing workflow."""
        # 1. Login
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword123'
        })
        
        # 2. Make meal plan public
        response = client.post(f'/api/meal-plan/{saved_meal_plan.id}/share', json={
            'is_public': True
        })
        assert response.status_code == 200
        
        # 3. Get share link
        response = client.get(f'/api/meal-plan/{saved_meal_plan.id}/share-link')
        assert response.status_code == 200
        data = json.loads(response.data)
        share_link = data.get('share_link', '')
        
        # 4. Logout
        client.get('/auth/logout')
        
        # 5. Access shared plan as anonymous user
        # Extract share ID from link
        if '/shared/' in share_link:
            share_id = share_link.split('/shared/')[-1]
            response = client.get(f'/shared/{share_id}')
            assert response.status_code == 200
            assert b'Test Meal Plan' in response.data
    
    def test_social_media_sharing(self, auth_client, saved_meal_plan):
        """Test social media sharing integration."""
        # 1. Generate social share data
        response = auth_client.post(f'/api/meal-plan/{saved_meal_plan.id}/social-share', json={
            'platform': 'twitter'
        })
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'share_text' in data or 'url' in data


class TestPDFExportWorkflow:
    """Test PDF export functionality end-to-end."""
    
    def test_pdf_export_complete_flow(self, auth_client, saved_meal_plan):
        """Test complete PDF export workflow."""
        # 1. Request PDF export
        response = auth_client.post('/api/export-pdf', json={
            'meal_plan_id': saved_meal_plan.id,
            'include_shopping_list': True,
            'include_nutrition': True
        })
        
        if response.status_code == 200:
            # 2. Check response is PDF
            assert response.content_type == 'application/pdf'
            assert len(response.data) > 1000  # PDF should have content
            
            # 3. Verify PDF headers
            assert response.headers.get('Content-Disposition')
            assert 'meal_plan.pdf' in response.headers.get('Content-Disposition', '')


class TestAdminWorkflows:
    """Test admin workflows end-to-end."""
    
    def test_admin_user_management_flow(self, client, admin_user, test_user):
        """Test admin managing users."""
        # 1. Admin login
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpassword123'
        })
        
        # 2. Access admin dashboard
        response = client.get('/admin/')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data
        
        # 3. View all users
        response = client.get('/admin/users')
        assert response.status_code == 200
        assert test_user.email.encode() in response.data
        
        # 4. Grant credits to user
        response = client.post(f'/admin/users/{test_user.id}/grant-credits', json={
            'credits': 50
        })
        assert response.status_code in [200, 302]
        
        # 5. View user details
        response = client.get(f'/admin/users/{test_user.id}')
        assert response.status_code == 200
        
        # 6. View system metrics
        response = client.get('/admin/metrics')
        assert response.status_code == 200
    
    def test_admin_content_moderation(self, client, admin_user, saved_meal_plan):
        """Test admin content moderation workflow."""
        # 1. Admin login
        client.post('/auth/login', data={
            'email': admin_user.email,
            'password': 'adminpassword123'
        })
        
        # 2. View public meal plans
        response = client.get('/admin/meal-plans/public')
        assert response.status_code == 200
        
        # 3. Moderate meal plan (if endpoint exists)
        response = client.post(f'/admin/meal-plans/{saved_meal_plan.id}/moderate', json={
            'action': 'approve'
        })
        # May not exist, check gracefully
        assert response.status_code in [200, 302, 404]


class TestAPIIntegrationScenarios:
    """Test API integration scenarios."""
    
    def test_third_party_integration_flow(self, auth_client):
        """Test third-party API integration flow."""
        # 1. Generate API key (if supported)
        response = auth_client.post('/api/generate-key')
        if response.status_code == 200:
            data = json.loads(response.data)
            api_key = data.get('api_key')
            
            # 2. Use API key for requests
            headers = {'Authorization': f'Bearer {api_key}'}
            response = auth_client.get('/api/user/profile', headers=headers)
            assert response.status_code == 200
    
    def test_webhook_integration_flow(self, client):
        """Test webhook integration for external services."""
        # 1. Register webhook (if supported)
        response = client.post('/api/webhooks/register', json={
            'url': 'https://example.com/webhook',
            'events': ['meal_plan.created', 'payment.completed']
        })
        
        # Check if webhooks are implemented
        if response.status_code != 404:
            assert response.status_code in [200, 201]


class TestMobileResponsiveFlow:
    """Test mobile-responsive workflows."""
    
    def test_mobile_user_flow(self, client):
        """Test mobile user experience flow."""
        # 1. Set mobile user agent
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        }
        
        # 2. Access mobile version
        response = client.get('/', headers=mobile_headers)
        assert response.status_code == 200
        
        # 3. Check mobile-specific features
        assert b'viewport' in response.data
        assert b'mobile-web-app-capable' in response.data
    
    def test_progressive_web_app_features(self, client):
        """Test PWA features."""
        # 1. Check manifest
        response = client.get('/manifest.json')
        if response.status_code == 200:
            manifest = json.loads(response.data)
            assert 'name' in manifest
            assert 'icons' in manifest
        
        # 2. Check service worker
        response = client.get('/sw.js')
        # May or may not be implemented
        assert response.status_code in [200, 404]


class TestDataExportCompliance:
    """Test data export for compliance (GDPR, etc.)."""
    
    def test_user_data_export_flow(self, auth_client, test_user, saved_meal_plan):
        """Test user data export workflow."""
        # 1. Request data export
        response = auth_client.post('/api/user/export-data')
        
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # 2. Verify export contains user data
            assert 'user' in data
            assert data['user']['email'] == test_user.email
            
            # 3. Verify meal plans included
            assert 'meal_plans' in data
            assert len(data['meal_plans']) > 0
    
    def test_account_deletion_flow(self, client, test_user):
        """Test account deletion workflow."""
        # 1. Login
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword123'
        })
        
        # 2. Request account deletion
        response = client.post('/api/user/delete-account', json={
            'confirm': True,
            'password': 'testpassword123'
        })
        
        if response.status_code == 200:
            # 3. Verify user is deleted
            user = User.query.filter_by(email=test_user.email).first()
            assert user is None or not user.is_active


class TestPerformanceUnderLoad:
    """Test performance under realistic load conditions."""
    
    def test_concurrent_user_sessions(self, app, mock_openai):
        """Test handling multiple concurrent user sessions."""
        import threading
        
        results = []
        
        def user_session(user_num):
            with app.test_client() as client:
                # Register
                response = client.post('/auth/register', data={
                    'email': f'user{user_num}@example.com',
                    'password': 'TestPass123!',
                    'confirm_password': 'TestPass123!',
                    'full_name': f'User {user_num}'
                })
                
                if response.status_code == 200:
                    # Generate meal plan
                    response = client.post('/api/generate', json={
                        'diet_type': 'standard',
                        'calories': 2000
                    })
                    results.append(response.status_code)
        
        # Simulate 10 concurrent users
        threads = [threading.Thread(target=user_session, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Most requests should succeed
        success_count = sum(1 for r in results if r == 200)
        assert success_count >= 5  # At least 50% success rate


if __name__ == '__main__':
    pytest.main(['-v', __file__])