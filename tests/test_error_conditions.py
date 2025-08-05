"""
Test error conditions and edge cases for robustness.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import time
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.extensions import db


class TestDatabaseErrorHandling:
    """Test database error scenarios."""
    
    def test_database_connection_failure(self, app, client):
        """Test handling of database connection failures."""
        with patch('app.extensions.db.session.execute') as mock_execute:
            mock_execute.side_effect = OperationalError('connection failed', None, None)
            
            response = client.get('/api/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'unhealthy'
    
    def test_database_integrity_error(self, auth_client, test_user):
        """Test handling of database integrity violations."""
        # Try to create duplicate email
        with patch('app.extensions.db.session.commit') as mock_commit:
            mock_commit.side_effect = IntegrityError('duplicate key', None, None)
            
            response = auth_client.post('/auth/register', data={
                'email': test_user.email,  # Duplicate
                'password': 'password123',
                'confirm_password': 'password123'
            })
            
            assert response.status_code in [200, 400]
            assert b'already registered' in response.data or b'error' in response.data
    
    def test_database_transaction_rollback(self, auth_client):
        """Test proper transaction rollback on errors."""
        initial_count = SavedMealPlan.query.count()
        
        with patch('app.models.meal_plan.SavedMealPlan.save') as mock_save:
            mock_save.side_effect = Exception('Save failed')
            
            response = auth_client.post('/api/save-meal-plan', json={
                'name': 'Test Plan',
                'meal_plan': {'meals': []}
            })
            
            assert response.status_code == 500
            # Verify rollback occurred
            assert SavedMealPlan.query.count() == initial_count


class TestAPIErrorScenarios:
    """Test API error handling."""
    
    def test_malformed_json_request(self, auth_client):
        """Test handling of malformed JSON."""
        response = auth_client.post(
            '/api/generate',
            data='{"invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_missing_required_fields(self, auth_client):
        """Test API with missing required fields."""
        # Missing diet_type
        response = auth_client.post('/api/generate', json={
            'calories': 2000
        })
        assert response.status_code == 400
        
        # Missing calories
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard'
        })
        assert response.status_code == 400
    
    def test_invalid_content_type(self, auth_client):
        """Test API with invalid content type."""
        response = auth_client.post(
            '/api/generate',
            data='diet_type=standard&calories=2000',
            content_type='application/x-www-form-urlencoded'
        )
        assert response.status_code in [400, 415]
    
    def test_api_timeout_handling(self, auth_client):
        """Test API timeout scenarios."""
        with patch('openai.ChatCompletion.create') as mock_create:
            # Simulate timeout
            mock_create.side_effect = TimeoutError('Request timed out')
            
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000
            })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_api_rate_limit_exceeded(self, auth_client):
        """Test OpenAI rate limit handling."""
        with patch('openai.ChatCompletion.create') as mock_create:
            mock_create.side_effect = Exception('Rate limit exceeded')
            
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000
            })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data


class TestAuthenticationErrors:
    """Test authentication error scenarios."""
    
    def test_expired_session(self, client, test_user):
        """Test handling of expired sessions."""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user.id)
            sess['_fresh'] = False
            sess['_permanent'] = False
        
        # Mock session expiry
        with patch('flask_login.utils._get_user') as mock_get_user:
            mock_get_user.return_value = None
            
            response = client.get('/create')
            assert response.status_code == 302  # Redirect to login
    
    def test_invalid_session_data(self, client):
        """Test handling of corrupted session data."""
        with client.session_transaction() as sess:
            sess['_user_id'] = 'invalid-user-id'
        
        response = client.get('/create')
        assert response.status_code == 302  # Redirect to login
    
    def test_concurrent_login_attempts(self, client, test_user):
        """Test concurrent login handling."""
        import threading
        results = []
        
        def attempt_login():
            response = client.post('/auth/login', data={
                'email': test_user.email,
                'password': 'testpassword123'
            })
            results.append(response.status_code)
        
        threads = [threading.Thread(target=attempt_login) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All attempts should be handled gracefully
        assert all(status in [200, 302] for status in results)


class TestFileHandlingErrors:
    """Test file handling error scenarios."""
    
    def test_pdf_generation_failure(self, auth_client):
        """Test PDF generation error handling."""
        with patch('app.services.pdf_generator.generate_meal_plan_pdf') as mock_pdf:
            mock_pdf.side_effect = Exception('PDF generation failed')
            
            response = auth_client.post('/api/export-pdf', json={
                'meal_plan': {'meals': []}
            })
            
            assert response.status_code == 500
    
    def test_large_file_handling(self, auth_client):
        """Test handling of large file requests."""
        # Create a very large meal plan
        large_meal_plan = {
            'meals': [
                {
                    'name': f'Meal {i}',
                    'items': [{'food': f'Item {j}', 'calories': 100} for j in range(100)]
                } for i in range(100)
            ]
        }
        
        response = auth_client.post('/api/save-meal-plan', json={
            'name': 'Huge Plan',
            'meal_plan': large_meal_plan
        })
        
        # Should handle gracefully (either save or reject)
        assert response.status_code in [200, 400, 413]


class TestPaymentErrorScenarios:
    """Test payment processing error scenarios."""
    
    def test_stripe_api_failure(self, auth_client):
        """Test Stripe API failure handling."""
        with patch('stripe.checkout.Session.create') as mock_create:
            mock_create.side_effect = Exception('Stripe API error')
            
            response = auth_client.post('/payment/create-checkout-session', json={
                'plan': 'premium'
            })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_invalid_webhook_signature(self, client):
        """Test invalid webhook signature handling."""
        response = client.post('/payment/webhook', 
                             json={'type': 'payment_intent.succeeded'},
                             headers={'Stripe-Signature': 'invalid'})
        
        assert response.status_code in [400, 401]
    
    def test_duplicate_payment_processing(self, auth_client, test_user):
        """Test duplicate payment prevention."""
        from app.models.payment import Payment
        
        # Create existing payment
        payment = Payment(
            user_id=test_user.id,
            stripe_payment_id='pi_test123',
            amount=999,
            status='completed'
        )
        db.session.add(payment)
        db.session.commit()
        
        # Try to process same payment again
        with patch('stripe.PaymentIntent.retrieve') as mock_retrieve:
            mock_retrieve.return_value = MagicMock(
                id='pi_test123',
                amount=999,
                status='succeeded'
            )
            
            response = client.post('/payment/webhook', json={
                'type': 'payment_intent.succeeded',
                'data': {'object': {'id': 'pi_test123'}}
            })
            
            # Should handle gracefully without creating duplicate
            payments = Payment.query.filter_by(stripe_payment_id='pi_test123').all()
            assert len(payments) == 1


class TestResourceExhaustionScenarios:
    """Test resource exhaustion scenarios."""
    
    def test_memory_exhaustion_protection(self, auth_client):
        """Test protection against memory exhaustion."""
        # Try to allocate excessive memory
        response = auth_client.post('/api/generate', json={
            'diet_type': 'standard',
            'calories': 2000,
            'preferences': ['a' * 1000000] * 100  # Very large request
        })
        
        assert response.status_code in [400, 413]  # Bad request or too large
    
    def test_cpu_intensive_request_timeout(self, auth_client):
        """Test timeout on CPU-intensive requests."""
        with patch('app.services.meal_optimizer.MealOptimizer.generate_meal_plan') as mock_generate:
            # Simulate long-running operation
            def slow_operation(*args, **kwargs):
                time.sleep(35)  # Exceed typical timeout
                return {'meals': []}
            
            mock_generate.side_effect = slow_operation
            
            start = time.time()
            response = auth_client.post('/api/generate', json={
                'diet_type': 'standard',
                'calories': 2000
            })
            elapsed = time.time() - start
            
            # Should timeout before 35 seconds
            assert elapsed < 35
            assert response.status_code in [500, 504]


class TestConcurrencyAndRaceConditions:
    """Test concurrency and race condition scenarios."""
    
    def test_concurrent_credit_deduction(self, app, test_user):
        """Test concurrent credit deduction handling."""
        import threading
        from app.extensions import db
        
        test_user.credits_balance = 5
        db.session.commit()
        
        results = []
        
        def use_credit():
            with app.app_context():
                user = User.query.get(test_user.id)
                if user.credits_balance > 0:
                    user.credits_balance -= 1
                    try:
                        db.session.commit()
                        results.append('success')
                    except:
                        db.session.rollback()
                        results.append('failed')
        
        # Simulate 10 concurrent requests for 5 credits
        threads = [threading.Thread(target=use_credit) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Check final state
        with app.app_context():
            user = User.query.get(test_user.id)
            # Credits should not go negative
            assert user.credits_balance >= 0
            # Successful deductions should match final balance
            assert results.count('success') == 5 - user.credits_balance


if __name__ == '__main__':
    pytest.main(['-v', __file__])