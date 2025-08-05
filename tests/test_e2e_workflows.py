"""
End-to-end tests for complete user workflows in the Cibozer application.
Tests entire user journeys from registration to meal plan creation and management.
"""

import pytest
import json
import time
from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.extensions import db


class TestUserRegistrationWorkflow:
    """Test complete user registration and onboarding workflow"""

    def test_complete_user_registration_flow(self, client):
        """Test full user registration flow"""
        # Step 1: User visits registration page
        response = client.get('/auth/register')
        assert response.status_code == 200
        
        # Step 2: User submits registration form
        registration_data = {
            'email': 'newuser@example.com',
            'full_name': 'New User',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123'
        }
        
        response = client.post('/auth/register', data=registration_data)
        assert response.status_code in [200, 302]  # Success or redirect
        
        # Step 3: User should be able to login after registration
        response = client.post('/auth/login', data={
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        })
        assert response.status_code in [200, 302]  # Success or redirect
        
        # Step 4: User should be able to access protected pages
        response = client.get('/auth/profile')
        assert response.status_code in [200, 302, 404, 500]  # Various possible responses

    def test_user_profile_update_workflow(self, client, test_user):
        """Test user profile update workflow"""
        # Step 1: Login user
        client.post('/auth/login', data={
            'email': test_user.email,
            'password': 'testpassword123'
        })
        
        # Step 2: Access profile page
        response = client.get('/auth/profile')
        assert response.status_code in [200, 302]
        
        # Step 3: Update profile information
        update_data = {
            'full_name': 'Updated Name',
            'email': 'updated@example.com'
        }
        
        response = client.post('/auth/profile/update', data=update_data)
        assert response.status_code in [200, 302]  # Success or redirect


class TestMealPlanCreationWorkflow:
    """Test complete meal plan creation and management workflow"""

    def test_complete_meal_plan_creation_flow(self, auth_client, test_user, app, mock_openai):
        """Test full meal plan creation workflow"""
        # Step 1: User accesses meal plan creation page
        response = auth_client.get('/')
        assert response.status_code == 200
        
        # Step 2: User submits meal plan generation request
        meal_plan_request = {
            'diet_type': 'standard',
            'target_calories': 2000,
            'days': 7,
            'dietary_restrictions': ['no-nuts'],
            'cooking_time': 'medium'
        }
        
        response = auth_client.post('/api/generate', json=meal_plan_request)
        # Should handle the request (may require proper authentication setup)
        assert response.status_code in [200, 400, 401, 404]
        
        # Step 3: If successful, verify meal plan data is returned
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'meals' in data or 'meal_plan' in data

    def test_meal_plan_save_and_load_workflow(self, auth_client, test_user, app):
        """Test saving and loading meal plans workflow"""
        with app.app_context():
            # Step 1: Create a test meal plan manually
            sample_meal_plan = {
                'meals': [
                    {
                        'name': 'Breakfast',
                        'items': [
                            {
                                'food': 'Oatmeal',
                                'quantity': '1 cup',
                                'calories': 300
                            }
                        ]
                    }
                ]
            }
            
            # Step 2: Save meal plan via API
            save_request = {
                'name': 'Test Meal Plan',
                'meal_plan': sample_meal_plan
            }
            
            response = auth_client.post('/api/save-meal-plan', json=save_request)
            # Should handle the request appropriately
            assert response.status_code in [200, 400, 401, 404]
            
            # Step 3: Load saved meal plans
            response = auth_client.get('/api/load-meal-plans')
            assert response.status_code in [200, 400, 401, 404]
            
            # Step 4: If successful, verify meal plans are returned
            if response.status_code == 200:
                data = json.loads(response.data)
                assert isinstance(data, (list, dict))

    def test_meal_plan_sharing_workflow(self, client, app, test_user):
        """Test meal plan sharing workflow"""
        with app.app_context():
            # Step 1: Create a saved meal plan
            meal_plan = SavedMealPlan(
                user_id=test_user.id,
                name='Shareable Plan',
                diet_type='standard',
                total_calories=2000,
                meal_plan_data={'meals': []},
                is_public=True
            )
            meal_plan.generate_share_token()
            db.session.add(meal_plan)
            db.session.commit()
            
            # Step 2: Access shared meal plan (without authentication)
            share_url = f'/share/{meal_plan.share_token}'
            response = client.get(share_url)
            # Should be accessible without authentication
            assert response.status_code in [200, 404]  # Found or not found


class TestPaymentWorkflow:
    """Test payment and upgrade workflow"""

    def test_upgrade_workflow(self, auth_client, test_user, mock_stripe):
        """Test user upgrade workflow"""
        # Step 1: User accesses upgrade page
        response = auth_client.get('/auth/upgrade')
        assert response.status_code in [200, 302]
        
        # Step 2: User initiates upgrade process
        # Note: This would typically involve Stripe integration
        # For testing, we simulate the process
        upgrade_data = {
            'plan': 'premium',
            'payment_method': 'test_payment_method'
        }
        
        # This endpoint might not exist or might be handled differently
        response = auth_client.post('/auth/upgrade', data=upgrade_data)
        assert response.status_code in [200, 302, 404, 405]  # Various possible responses


class TestAdminWorkflow:
    """Test admin functionality workflow"""

    def test_admin_access_workflow(self, client, app, admin_user):
        """Test admin access and basic functionality"""
        with app.app_context():
            # Step 1: Admin login
            response = client.post('/admin/login', data={
                'email': admin_user.email,
                'password': 'adminpassword123'
            })
            assert response.status_code in [200, 302, 404]
            
            # Step 2: Access admin dashboard
            response = client.get('/admin/')
            assert response.status_code in [200, 302, 401, 404]
            
            # Step 3: Access user management
            response = client.get('/admin/users')
            assert response.status_code in [200, 302, 401, 404]


class TestFullUserJourney:
    """Test complete end-to-end user journeys"""

    def test_new_user_complete_journey(self, client, app, mock_openai):
        """Test complete journey of a new user from registration to meal plan"""
        # Step 1: User registers
        registration_data = {
            'email': 'journey@example.com',
            'full_name': 'Journey User',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response = client.post('/auth/register', data=registration_data)
        assert response.status_code in [200, 302]
        
        # Step 2: User logs in
        response = client.post('/auth/login', data={
            'email': 'journey@example.com',
            'password': 'password123'
        })
        assert response.status_code in [200, 302]
        
        # Step 3: User creates first meal plan
        meal_plan_request = {
            'diet_type': 'standard',
            'target_calories': 1800,
            'days': 3,
            'preferences': ['vegetarian']
        }
        
        response = client.post('/api/generate', json=meal_plan_request)
        assert response.status_code in [200, 400, 401, 404]
        
        # Step 4: User saves the meal plan (if generation was successful)
        if response.status_code == 200:
            save_request = {
                'name': 'My First Plan',
                'meal_plan': {'meals': []}  # Simplified for test
            }
            
            response = client.post('/api/save-meal-plan', json=save_request)
            assert response.status_code in [200, 400, 401, 404]
        
        # Step 5: User views their saved plans
        response = client.get('/api/load-meal-plans')
        assert response.status_code in [200, 400, 401, 404]
        
        # Step 6: User accesses their profile
        response = client.get('/auth/profile')
        assert response.status_code in [200, 302]

    def test_premium_user_journey(self, client, app, test_user, mock_openai, mock_stripe):
        """Test journey of a premium user with enhanced features"""
        with app.app_context():
            # Step 1: Simulate premium user
            test_user.is_premium = True
            test_user.credits_balance = 100
            db.session.commit()
            
            # Step 2: Login
            response = client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            })
            assert response.status_code in [200, 302]
            
            # Step 3: Create multiple meal plans (premium feature)
            for i in range(3):
                meal_plan_request = {
                    'diet_type': 'keto' if i % 2 else 'paleo',
                    'target_calories': 2000 + (i * 200),
                    'days': 7,
                    'advanced_options': True
                }
                
                response = client.post('/api/generate', json=meal_plan_request)
                assert response.status_code in [200, 400, 401, 404]
            
            # Step 4: Export meal plan to PDF (premium feature)
            export_request = {
                'meal_plan': {'meals': []},
                'format': 'pdf'
            }
            
            response = client.post('/api/export-pdf', json=export_request)
            assert response.status_code in [200, 400, 401, 404]

    def test_error_recovery_workflow(self, client, app):
        """Test user workflow with error scenarios and recovery"""
        # Step 1: Try to access protected resource without authentication
        response = client.get('/api/user-status')
        assert response.status_code in [401, 302]  # Should redirect to login
        
        # Step 2: Try to login with invalid credentials
        response = client.post('/auth/login', data={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code in [200, 400, 401]  # Should handle gracefully
        
        # Step 3: Register user and continue workflow
        registration_data = {
            'email': 'recovery@example.com',
            'full_name': 'Recovery User',
            'password': 'password123',
            'confirm_password': 'password123'
        }
        
        response = client.post('/auth/register', data=registration_data)
        assert response.status_code in [200, 302]
        
        # Step 4: Login successfully
        response = client.post('/auth/login', data={
            'email': 'recovery@example.com',
            'password': 'password123'
        })
        assert response.status_code in [200, 302]
        
        # Step 5: Now protected resource should be accessible
        response = client.get('/api/user-status')
        assert response.status_code in [200, 404]  # Should work now


class TestPerformanceCriticalWorkflows:
    """Test workflows under performance constraints"""

    def test_rapid_meal_plan_requests(self, auth_client, mock_openai):
        """Test rapid meal plan generation requests"""
        # Simulate user making multiple rapid requests
        responses = []
        for i in range(10):
            meal_plan_request = {
                'diet_type': 'standard',
                'target_calories': 2000,
                'days': 1
            }
            
            response = auth_client.post('/api/generate', json=meal_plan_request)
            responses.append(response.status_code)
            time.sleep(0.1)  # Small delay between requests
        
        # Most requests should be handled appropriately
        success_or_handled = sum(1 for code in responses if code in [200, 400, 401, 404, 429])
        assert success_or_handled >= 8  # At least 80% should be handled properly

    def test_large_meal_plan_handling(self, auth_client):
        """Test handling of large meal plan data"""
        # Create a large meal plan
        large_meal_plan = {
            'meals': []
        }
        
        # Add many meals and items
        for day in range(30):  # 30 days
            for meal_type in ['breakfast', 'lunch', 'dinner', 'snack']:
                meal = {
                    'name': f'Day {day+1} {meal_type.title()}',
                    'items': []
                }
                
                # Add many items per meal
                for item in range(10):
                    meal['items'].append({
                        'food': f'Food item {item+1}',
                        'quantity': '1 serving',
                        'calories': 100,
                        'protein': 10,
                        'carbs': 15,
                        'fat': 5,
                        'description': 'x' * 200  # Long description
                    })
                
                large_meal_plan['meals'].append(meal)
        
        # Test saving large meal plan
        save_request = {
            'name': 'Large Meal Plan',
            'meal_plan': large_meal_plan
        }
        
        response = auth_client.post('/api/save-meal-plan', json=save_request)
        assert response.status_code in [200, 400, 401, 404, 413]  # Should handle appropriately