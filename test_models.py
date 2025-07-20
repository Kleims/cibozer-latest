"""
Test cases for database models
Tests User model functionality and relationships
"""

import pytest
from datetime import datetime, timedelta, timezone
from models import db, User, UsageLog, Payment, SavedMealPlan
from flask import Flask
from app_config import get_app_config


@pytest.fixture
def app():
    """Create test Flask app"""
    app = Flask(__name__)
    config = get_app_config()
    app.config.update(config.to_flask_config())
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            full_name='Test User'
        )
        user.set_password('TestPassword123!')
        db.session.add(user)
        db.session.commit()
        return user


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, app):
        """Test creating a new user"""
        with app.app_context():
            user = User(
                email='newuser@example.com',
                full_name='New User'
            )
            user.set_password('SecurePassword123!')
            
            assert user.email == 'newuser@example.com'
            assert user.full_name == 'New User'
            assert user.subscription_tier == 'free'
            assert user.credits_balance == 3
            assert user.is_active is True
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was saved
            saved_user = User.query.filter_by(email='newuser@example.com').first()
            assert saved_user is not None
            assert saved_user.check_password('SecurePassword123!')
    
    def test_password_hashing(self, app, test_user):
        """Test password hashing and verification"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Check correct password
            assert user.check_password('TestPassword123!') is True
            
            # Check incorrect password
            assert user.check_password('WrongPassword') is False
            
            # Verify password hash is not stored as plain text
            assert user.password_hash != 'TestPassword123!'
            assert len(user.password_hash) > 20
    
    def test_premium_subscription(self, app, test_user):
        """Test premium subscription checks"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Default user is not premium
            assert user.is_premium() is False
            
            # Set as pro user with valid subscription
            user.subscription_tier = 'pro'
            user.subscription_end_date = datetime.now(timezone.utc) + timedelta(days=30)
            db.session.commit()
            
            assert user.is_premium() is True
            
            # Expired subscription
            user.subscription_end_date = datetime.now(timezone.utc) - timedelta(days=1)
            db.session.commit()
            
            assert user.is_premium() is False
    
    def test_credits_system(self, app, test_user):
        """Test credits usage and balance"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Check initial credits
            assert user.credits_balance == 3
            assert user.has_credits() is True
            
            # Use 1 credit
            assert user.use_credits(1) is True
            assert user.credits_balance == 2
            
            # Use multiple credits
            assert user.use_credits(2) is True
            assert user.credits_balance == 0
            assert user.has_credits() is False
            
            # Try to use more credits than available
            assert user.use_credits(1) is False
            assert user.credits_balance == 0
    
    def test_can_generate_plan(self, app, test_user):
        """Test meal plan generation permissions"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Free user with credits
            assert user.can_generate_plan() is True
            
            # Free user without credits
            user.credits_balance = 0
            db.session.commit()
            assert user.can_generate_plan() is False
            
            # Premium user without credits
            user.subscription_tier = 'premium'
            user.subscription_end_date = datetime.now(timezone.utc) + timedelta(days=30)
            db.session.commit()
            assert user.can_generate_plan() is True
    
    def test_reset_token(self, app, test_user):
        """Test password reset token functionality"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # Generate token
            token = user.generate_reset_token()
            assert token is not None
            assert len(token) > 20
            assert user.reset_token == token
            assert user.reset_token_expires is not None
            
            # Verify valid token
            assert user.verify_reset_token(token) is True
            
            # Verify invalid token
            assert user.verify_reset_token('invalid-token') is False
            
            # Clear token
            user.clear_reset_token()
            assert user.reset_token is None
            assert user.reset_token_expires is None
    
    def test_monthly_usage(self, app, test_user):
        """Test monthly usage tracking"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            # No usage initially
            assert user.get_monthly_usage() == 0
            
            # Add usage logs
            log1 = UsageLog(
                user_id=user.id,
                action_type='generate_plan',
                credits_used=1
            )
            log2 = UsageLog(
                user_id=user.id,
                action_type='generate_plan',
                credits_used=1
            )
            log3 = UsageLog(
                user_id=user.id,
                action_type='export_pdf',  # Different action type
                credits_used=0
            )
            
            db.session.add_all([log1, log2, log3])
            db.session.commit()
            
            # Should count only generate_plan actions
            assert user.get_monthly_usage() == 2


class TestUsageLog:
    """Test UsageLog model"""
    
    def test_usage_log_creation(self, app, test_user):
        """Test creating usage logs"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            log = UsageLog(
                user_id=user.id,
                action_type='generate_plan',
                credits_used=1,
                extra_data={'diet_type': 'balanced', 'calories': 2000}
            )
            
            db.session.add(log)
            db.session.commit()
            
            # Verify log was saved
            saved_log = UsageLog.query.filter_by(user_id=user.id).first()
            assert saved_log is not None
            assert saved_log.action_type == 'generate_plan'
            assert saved_log.credits_used == 1
            assert saved_log.extra_data['diet_type'] == 'balanced'
            assert saved_log.timestamp is not None


class TestPayment:
    """Test Payment model"""
    
    def test_payment_creation(self, app, test_user):
        """Test creating payment records"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            payment = Payment(
                user_id=user.id,
                stripe_payment_intent_id='pi_test_123',
                amount=999,  # $9.99 in cents
                currency='usd',
                status='succeeded',
                payment_type='subscription'
            )
            
            db.session.add(payment)
            db.session.commit()
            
            # Verify payment was saved
            saved_payment = Payment.query.filter_by(user_id=user.id).first()
            assert saved_payment is not None
            assert saved_payment.amount == 999
            assert saved_payment.status == 'succeeded'


class TestSavedMealPlan:
    """Test SavedMealPlan model"""
    
    def test_meal_plan_creation(self, app, test_user):
        """Test creating saved meal plans"""
        with app.app_context():
            user = User.query.filter_by(email='test@example.com').first()
            
            meal_plan = SavedMealPlan(
                user_id=user.id,
                name='Weekly Meal Plan',
                diet_type='balanced',
                target_calories=2000,
                meals_data={'monday': {'breakfast': 'Oatmeal'}}
            )
            
            db.session.add(meal_plan)
            db.session.commit()
            
            # Verify meal plan was saved
            saved_plan = SavedMealPlan.query.filter_by(user_id=user.id).first()
            assert saved_plan is not None
            assert saved_plan.name == 'Weekly Meal Plan'
            assert saved_plan.diet_type == 'balanced'
            assert saved_plan.meals_data['monday']['breakfast'] == 'Oatmeal'