"""
Shared pytest configuration and fixtures for all tests.
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.payment import PricingPlan
from app.models.meal_plan import SavedMealPlan


@pytest.fixture(scope='function')
def app():
    """Create and configure test Flask application."""
    # Use testing configuration
    app = create_app('testing')
    
    # Override specific settings for tests
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key-only-for-testing',
        'STRIPE_SECRET_KEY': 'sk_test_mock_key',
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_mock_key',
        'OPENAI_API_KEY': 'test-api-key',
        'RATELIMIT_ENABLED': False,  # Disable rate limiting for tests
    })
    
    # Create application context
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default pricing plans
        plans = [
            PricingPlan(
                name='free',
                display_name='Free Plan',
                price_monthly=0,
                credits_included=5
            ),
            PricingPlan(
                name='premium',
                display_name='Premium Plan',
                price_monthly=9.99,
                credits_included=100
            )
        ]
        
        for plan in plans:
            existing = PricingPlan.query.filter_by(name=plan.name).first()
            if not existing:
                db.session.add(plan)
        
        db.session.commit()
        
        yield app
        
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def auth_client(client, test_user):
    """Create authenticated test client."""
    # Login the test user
    client.post('/auth/login', data={
        'email': test_user.email,
        'password': 'testpassword123'
    })
    return client


@pytest.fixture(scope='function')
def test_user(app):
    """Create a test user."""
    user = User(
        email='test@example.com',
        full_name='Test User',
        credits_balance=10
    )
    user.set_password('testpassword123')
    
    db.session.add(user)
    db.session.commit()
    
    return user


@pytest.fixture(scope='function')
def admin_user(app):
    """Create an admin test user."""
    user = User(
        email='admin@example.com',
        full_name='Admin User',
        is_admin=True,
        credits_balance=100
    )
    user.set_password('adminpassword123')
    
    db.session.add(user)
    db.session.commit()
    
    return user


@pytest.fixture(scope='function')
def sample_meal_plan():
    """Create a sample meal plan data structure."""
    return {
        'diet_type': 'standard',
        'calories': 2000,
        'meals': [
            {
                'name': 'Breakfast',
                'items': [
                    {
                        'food': 'Oatmeal',
                        'quantity': '1 cup',
                        'calories': 300,
                        'protein': 10,
                        'carbs': 50,
                        'fat': 5
                    }
                ],
                'total_calories': 300
            },
            {
                'name': 'Lunch',
                'items': [
                    {
                        'food': 'Grilled Chicken Salad',
                        'quantity': '1 serving',
                        'calories': 450,
                        'protein': 40,
                        'carbs': 20,
                        'fat': 15
                    }
                ],
                'total_calories': 450
            },
            {
                'name': 'Dinner',
                'items': [
                    {
                        'food': 'Salmon with Rice',
                        'quantity': '1 serving',
                        'calories': 600,
                        'protein': 35,
                        'carbs': 45,
                        'fat': 25
                    }
                ],
                'total_calories': 600
            }
        ],
        'totals': {
            'calories': 1350,
            'protein': 85,
            'carbs': 115,
            'fat': 45
        }
    }


@pytest.fixture(scope='function')
def saved_meal_plan(app, test_user, sample_meal_plan):
    """Create a saved meal plan in database."""
    meal_plan = SavedMealPlan(
        user_id=test_user.id,
        name='Test Meal Plan',
        diet_type='standard',
        total_calories=2000,
        meal_data=sample_meal_plan,
        is_public=False
    )
    
    db.session.add(meal_plan)
    db.session.commit()
    
    return meal_plan


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    def mock_create(*args, **kwargs):
        class MockChoice:
            def __init__(self):
                self.message = type('obj', (object,), {
                    'content': '''
                    {
                        "meals": [
                            {
                                "name": "Breakfast",
                                "items": [
                                    {
                                        "food": "Oatmeal",
                                        "quantity": "1 cup",
                                        "calories": 300
                                    }
                                ]
                            }
                        ]
                    }
                    '''
                })
        
        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]
        
        return MockResponse()
    
    monkeypatch.setattr('openai.ChatCompletion.create', mock_create)


@pytest.fixture
def mock_stripe(monkeypatch):
    """Mock Stripe API calls."""
    class MockStripeCustomer:
        def __init__(self, **kwargs):
            self.id = 'cus_test123'
            self.email = kwargs.get('email')
    
    class MockStripeSubscription:
        def __init__(self, **kwargs):
            self.id = 'sub_test123'
            self.status = 'active'
            self.current_period_end = 1234567890
    
    monkeypatch.setattr('stripe.Customer.create', lambda **kwargs: MockStripeCustomer(**kwargs))
    monkeypatch.setattr('stripe.Subscription.create', lambda **kwargs: MockStripeSubscription(**kwargs))


# Test environment setup
def pytest_configure(config):
    """Configure pytest environment."""
    # Set testing environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['TESTING'] = '1'


def pytest_unconfigure(config):
    """Clean up after tests."""
    # Remove testing environment variables
    if 'FLASK_ENV' in os.environ:
        del os.environ['FLASK_ENV']
    if 'TESTING' in os.environ:
        del os.environ['TESTING']