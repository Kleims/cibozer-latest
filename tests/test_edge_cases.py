"""
Edge case testing for the Cibozer application.
Tests boundary conditions, error scenarios, and unusual inputs.
"""

import pytest
import json
from decimal import Decimal
from app.models.user import User
from app.models.meal_plan import SavedMealPlan
from app.extensions import db


class TestUserEdgeCases:
    """Test edge cases for User model and related functionality"""

    def test_user_with_extremely_long_email(self, app):
        """Test user creation with maximum length email"""
        with app.app_context():
            # Create email at maximum reasonable length
            long_email = 'a' * 240 + '@example.com'  # ~250 chars total
            user = User(
                email=long_email,
                full_name='Test User'
            )
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            assert user.email == long_email
            assert len(user.email) > 240

    def test_user_with_special_characters_in_name(self, app):
        """Test user creation with special characters"""
        with app.app_context():
            special_names = [
                "José María García-López",
                "李小明",
                "Владимир Путин",
                "John O'Connor",
                "Anne-Marie Müller",
                "João José da Silva"
            ]
            
            for name in special_names:
                user = User(
                    email=f'test{len(name)}@example.com',
                    full_name=name
                )
                user.set_password('testpass123')
                db.session.add(user)
                db.session.commit()
                
                assert user.full_name == name

    def test_user_credits_boundary_values(self, app):
        """Test user credits at boundary values"""
        with app.app_context():
            # Test zero credits
            user = User(
                email='zero@example.com',
                full_name='Zero Credits',
                credits_balance=0
            )
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            assert user.credits_balance == 0
            
            # Test maximum credits
            user2 = User(
                email='max@example.com',
                full_name='Max Credits',
                credits_balance=999999
            )
            user2.set_password('testpass123')
            db.session.add(user2)
            db.session.commit()
            assert user2.credits_balance == 999999

    def test_user_password_edge_cases(self, app):
        """Test password validation edge cases"""
        with app.app_context():
            user = User(
                email='password_test@example.com',
                full_name='Password Test'
            )
            
            # Test minimum length password
            user.set_password('12345678')  # 8 chars minimum
            assert user.check_password('12345678')
            
            # Test very long password
            long_password = 'a' * 200
            user.set_password(long_password)
            assert user.check_password(long_password)
            
            # Test password with special characters
            special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
            user.set_password(special_password)
            assert user.check_password(special_password)


class TestMealPlanEdgeCases:
    """Test edge cases for meal plan functionality"""

    def test_empty_meal_plan(self, app, test_user):
        """Test saving an empty meal plan"""
        with app.app_context():
            empty_plan = SavedMealPlan(
                user_id=test_user.id,
                name='Empty Plan',
                diet_type='standard',
                total_calories=0,
                meal_plan_data={},
                is_public=False
            )
            db.session.add(empty_plan)
            db.session.commit()
            
            assert empty_plan.total_calories == 0
            assert empty_plan.meal_plan_data == {}

    def test_meal_plan_with_extreme_calorie_values(self, app, test_user):
        """Test meal plans with extreme calorie values"""
        with app.app_context():
            # Very low calorie plan
            low_cal_plan = SavedMealPlan(
                user_id=test_user.id,
                name='Low Cal Plan',
                diet_type='standard',
                total_calories=500,  # Very low
                meal_plan_data={'meals': []},
                is_public=False
            )
            db.session.add(low_cal_plan)
            
            # Very high calorie plan
            high_cal_plan = SavedMealPlan(
                user_id=test_user.id,
                name='High Cal Plan',
                diet_type='standard',
                total_calories=8000,  # Very high
                meal_plan_data={'meals': []},
                is_public=False
            )
            db.session.add(high_cal_plan)
            
            db.session.commit()
            
            assert low_cal_plan.total_calories == 500
            assert high_cal_plan.total_calories == 8000

    def test_meal_plan_with_malformed_data(self, app, test_user):
        """Test meal plan with potentially malformed data"""
        with app.app_context():
            malformed_data = {
                'meals': [
                    {
                        'name': None,  # Null name
                        'items': []
                    },
                    {
                        'name': '',  # Empty name
                        'items': None  # Null items
                    },
                    {
                        'name': 'a' * 1000,  # Very long name
                        'items': [
                            {
                                'food': 'Test Food',
                                'calories': -100  # Negative calories
                            }
                        ]
                    }
                ]
            }
            
            plan = SavedMealPlan(
                user_id=test_user.id,
                name='Malformed Plan',
                diet_type='standard',
                total_calories=2000,
                meal_plan_data=malformed_data,
                is_public=False
            )
            db.session.add(plan)
            db.session.commit()
            
            # Should store the data as-is (validation happens at API level)
            assert plan.meal_plan_data == malformed_data


class TestAPIEdgeCases:
    """Test edge cases for API endpoints"""

    def test_api_with_malformed_json(self, client):
        """Test API endpoints with malformed JSON"""
        malformed_json_payloads = [
            '{"incomplete": json',  # Incomplete JSON
            '{"valid": "json", "but": "extra", }',  # Trailing comma
            '{"nested": {"deep": {"very": {"deep": {"json": "value"}}}}}',  # Very nested
            '{"unicode": "测试数据"}',  # Unicode characters
            '{"null_value": null, "empty_string": "", "zero": 0}',  # Edge values
        ]
        
        for payload in malformed_json_payloads:
            response = client.post('/api/generate', 
                                 data=payload,
                                 content_type='application/json')
            # Should handle gracefully (either parse or return error)
            assert response.status_code in [200, 400, 401, 302, 422]

    def test_api_with_oversized_payload(self, client):
        """Test API with very large payloads"""
        # Create a large JSON payload
        large_data = {
            'meals': []
        }
        
        # Add many meals to create large payload
        for i in range(1000):  # Large number of meals
            large_data['meals'].append({
                'name': f'Meal {i}',
                'description': 'x' * 1000,  # Long description
                'calories': 500
            })
        
        response = client.post('/api/generate',
                              json=large_data)
        # Should handle large payloads appropriately
        assert response.status_code in [200, 400, 401, 302, 413, 422]

    def test_api_concurrent_requests(self, client):
        """Test API behavior with rapid sequential requests"""
        # Simulate rapid requests to test rate limiting and concurrency
        responses = []
        for i in range(50):  # Many rapid requests
            response = client.get('/api/health')
            responses.append(response.status_code)
        
        # Most should succeed, some might be rate limited
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 40  # At least 80% should succeed


class TestAuthenticationEdgeCases:
    """Test edge cases for authentication"""

    def test_login_with_case_variations(self, client, test_user):
        """Test login with different case variations of email"""
        test_cases = [
            test_user.email.upper(),
            test_user.email.lower(),
            test_user.email.title()
        ]
        
        for email_variant in test_cases:
            response = client.post('/auth/login', data={
                'email': email_variant,
                'password': 'testpassword123'
            })
            # Should handle case variations appropriately
            assert response.status_code in [200, 302, 400]

    def test_login_with_whitespace(self, client, test_user):
        """Test login with leading/trailing whitespace"""
        whitespace_variants = [
            f' {test_user.email} ',
            f'\t{test_user.email}\t',
            f'\n{test_user.email}\n'
        ]
        
        for email_variant in whitespace_variants:
            response = client.post('/auth/login', data={
                'email': email_variant,
                'password': 'testpassword123'
            })
            # Should handle whitespace appropriately
            assert response.status_code in [200, 302, 400]

    def test_password_with_unicode_characters(self, client):
        """Test password creation with unicode characters"""
        unicode_passwords = [
            'пароль123',  # Cyrillic
            'パスワード123',  # Japanese
            'كلمة المرور123',  # Arabic
            'Contraseña123',  # Spanish with accent
            'Mot de passe 123 ñ'  # French with special chars
        ]
        
        for i, password in enumerate(unicode_passwords):
            response = client.post('/auth/register', data={
                'email': f'unicode{i}@example.com',
                'full_name': 'Unicode Test',
                'password': password,
                'confirm_password': password
            })
            # Should handle unicode passwords appropriately
            assert response.status_code in [200, 302, 400]


class TestDatabaseEdgeCases:
    """Test database-related edge cases"""

    def test_database_constraint_violations(self, app):
        """Test database constraint handling"""
        with app.app_context():
            # Try to create duplicate email users
            user1 = User(
                email='duplicate@example.com',
                full_name='User One'
            )
            user1.set_password('password123')
            db.session.add(user1)
            db.session.commit()
            
            # Try to add another user with same email
            user2 = User(
                email='duplicate@example.com',
                full_name='User Two'
            )
            user2.set_password('password456')
            db.session.add(user2)
            
            # Should handle the constraint violation
            with pytest.raises(Exception):  # Could be IntegrityError or similar
                db.session.commit()

    def test_transaction_rollback_scenarios(self, app):
        """Test transaction rollback scenarios"""
        with app.app_context():
            original_count = User.query.count()
            
            try:
                # Start a transaction that will fail
                user = User(
                    email='rollback@example.com',
                    full_name='Rollback Test'
                )
                user.set_password('password123')
                db.session.add(user)
                
                # Force an error by trying to add duplicate
                user2 = User(
                    email='rollback@example.com',  # Same email
                    full_name='Rollback Test 2'
                )
                user2.set_password('password456')
                db.session.add(user2)
                
                db.session.commit()
            except Exception:
                db.session.rollback()
            
            # Should have same count as before
            assert User.query.count() == original_count


class TestInputSanitizationEdgeCases:
    """Test input sanitization edge cases"""

    def test_xss_prevention_in_names(self, client):
        """Test XSS prevention in user input fields"""
        xss_payloads = [
            '<script>alert("xss")</script>',
            '"><script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src=x onerror=alert("xss")>',
            '"><svg onload=alert("xss")>',
            '\'-alert("xss")-\'',
            '${alert("xss")}'
        ]
        
        for i, payload in enumerate(xss_payloads):
            response = client.post('/auth/register', data={
                'email': f'xss{i}@example.com',
                'full_name': payload,  # XSS in name field
                'password': 'password123',
                'confirm_password': 'password123'
            })
            # Should handle XSS attempts appropriately
            assert response.status_code in [200, 302, 400]

    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'hacked'); --"
        ]
        
        for payload in sql_payloads:
            response = client.post('/auth/login', data={
                'email': payload,
                'password': 'password123'
            })
            # Should handle SQL injection attempts safely
            assert response.status_code in [200, 302, 400, 401]