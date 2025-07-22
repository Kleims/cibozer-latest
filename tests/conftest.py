"""Pytest configuration and shared fixtures for Cibozer testing."""

import pytest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock

# Mock problematic video modules before any imports
# Also mock bcrypt to avoid PyO3 initialization issues in tests
mock_bcrypt = MagicMock()
# Return bytes that can be decoded to match User model expectations
mock_bcrypt.hashpw = MagicMock(return_value=b'$2b$12$fake.hash.for.testing')
mock_bcrypt.checkpw = MagicMock(return_value=True)
mock_bcrypt.gensalt = MagicMock(return_value=b'$2b$12$fake.salt')

with patch.dict('sys.modules', {
    'cv2': MagicMock(),
    'edge_tts': MagicMock(),
    'matplotlib.pyplot': MagicMock(),
    'simple_video_generator': MagicMock(),
    'video_service': MagicMock(),
    'bcrypt': mock_bcrypt,
}):
    from flask import Flask
    from models import db, User, Payment, UsageLog, SavedMealPlan
    
    # Mock app creation to avoid video service imports
    def create_test_app(config=None):
        """Create Flask app for testing without video dependencies."""
        app = Flask(__name__)
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key',
            'WTF_CSRF_ENABLED': False,
        })
        if config:
            app.config.update(config)
        
        # Import and register auth blueprint without video dependencies
        with app.app_context():
            db.init_app(app)
            # Register essential blueprints for testing
            try:
                from auth import auth_bp
                from payments import payments_bp
                app.register_blueprint(auth_bp)
                app.register_blueprint(payments_bp)
            except ImportError:
                pass  # Skip if blueprints can't be imported
            
        return app


@pytest.fixture(scope="session")
def app():
    """Create application for testing."""
    # Create a temporary directory for test database
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, 'test.db')
    
    # Override configuration for testing
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{test_db_path}',
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_fake',
        'STRIPE_SECRET_KEY': 'sk_test_fake',
    }
    
    app = create_test_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Cleanup
    try:
        os.unlink(test_db_path)
        os.rmdir(test_dir)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner.""" 
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email='test@example.com',
        password_hash='$2b$12$fake.hash.for.testing.purposes.only',
        is_active=True,
        email_verified=True,
        subscription_tier='free',
        subscription_status='active',
        credits_balance=5
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def premium_user(db_session):
    """Create a premium test user."""
    user = User(
        email='premium@example.com', 
        password_hash='$2b$12$fake.hash.for.testing.purposes.only',
        is_active=True,
        email_verified=True,
        subscription_tier='premium',
        subscription_status='active',
        credits_balance=999
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch('stripe.Customer') as mock_customer, \
         patch('stripe.Subscription') as mock_subscription, \
         patch('stripe.PaymentIntent') as mock_payment_intent:
        
        # Mock customer creation
        mock_customer.create.return_value = MagicMock(id='cus_fake123')
        
        # Mock subscription creation
        mock_subscription.create.return_value = MagicMock(
            id='sub_fake123',
            status='active',
            current_period_end=1234567890
        )
        
        # Mock payment intent
        mock_payment_intent.create.return_value = MagicMock(
            id='pi_fake123',
            status='succeeded',
            amount=999
        )
        
        yield {
            'customer': mock_customer,
            'subscription': mock_subscription, 
            'payment_intent': mock_payment_intent
        }


@pytest.fixture
def mock_video_service():
    """Mock video generation to avoid OpenCV issues."""
    with patch('video_service.VideoService') as mock:
        mock_instance = MagicMock()
        mock_instance.generate_video.return_value = True
        mock_instance.upload_video.return_value = {'success': True}
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_meal_optimizer():
    """Mock meal optimizer for consistent testing."""
    with patch('meal_optimizer.create_meal_plan') as mock:
        mock.return_value = {
            'success': True,
            'meals': [
                {
                    'name': 'Test Breakfast',
                    'ingredients': ['eggs', 'bread'],
                    'calories': 300,
                    'protein': 20,
                    'carbs': 30,
                    'fat': 15
                }
            ],
            'daily_totals': {
                'calories': 1500,
                'protein': 120,
                'carbs': 150,
                'fat': 50
            }
        }
        yield mock


@pytest.fixture(autouse=True)
def suppress_video_warnings():
    """Suppress OpenCV warnings during testing."""
    with patch('cv2.VideoWriter'), \
         patch('cv2.imread'), \
         patch('cv2.imwrite'):
        yield