"""Tests for payments.py - Payment functionality"""

import pytest
from unittest.mock import patch, MagicMock
from app import app, db
from models import User, Payment, PricingPlan
from payments import check_user_credits, deduct_credit, add_credits


@pytest.fixture
def client():
    """Create test client with temporary database"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed pricing plans if needed
            if PricingPlan.query.count() == 0:
                PricingPlan.seed_default_plans()
            yield client


@pytest.fixture
def test_user(client):
    """Create a test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            credits_balance=10,
            subscription_tier='free'
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture  
def premium_user(client):
    """Create a premium test user"""
    with app.app_context():
        user = User(
            email='premium@example.com', 
            credits_balance=0,
            subscription_tier='premium'
        )
        db.session.add(user)
        db.session.commit()
        return user


class TestCreditSystem:
    """Test credit deduction and management."""
    
    def test_deduct_credit_success(self, test_user):
        """Test successful credit deduction."""
        with app.app_context():
            initial_credits = test_user.credits_balance
            
            result = deduct_credit(test_user, 2)
            
            assert result is True
            db.session.refresh(test_user)
            assert test_user.credits_balance == initial_credits - 2
    
    def test_add_credits_success(self, test_user):
        """Test successful credit addition."""
        with app.app_context():
            initial_credits = test_user.credits_balance
            
            result = add_credits(test_user, 10)
            
            assert result is True
            db.session.refresh(test_user)
            assert test_user.credits_balance == initial_credits + 10

    def test_check_user_credits_free_user(self, test_user):
        """Test credit checking for free user."""
        with app.app_context():
            test_user.credits_balance = 5
            test_user.subscription_tier = 'free'
            db.session.commit()
            
            result = check_user_credits(test_user)
            
            assert result is True  # Has credits available

    def test_check_user_credits_premium_user(self, premium_user):
        """Test credit checking for premium user."""
        with app.app_context():
            result = check_user_credits(premium_user)
            
            assert result is True  # Premium users have unlimited credits
    
    def test_deduct_credit_insufficient_funds(self, test_user):
        """Test credit deduction with insufficient funds."""
        with app.app_context():
            test_user.credits_balance = 1
            db.session.commit()
            
            result = deduct_credit(test_user, 5)
            
            assert result is False
            # Balance should remain unchanged
            assert test_user.credits_balance == 1

    def test_get_pricing_plans(self, client):
        """Test getting pricing plans via API endpoint."""
        response = client.get('/api/pricing-plans')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'plans' in data
        assert isinstance(data['plans'], list)


class TestWebhooks:
    """Test webhook functionality."""
    
    def test_stripe_webhook_exists(self, client):
        """Test that Stripe webhook endpoint exists."""
        # Test that the endpoint exists (will likely fail auth but that's OK)
        response = client.post('/stripe-webhook')
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

        
class TestSubscriptionManagement:
    """Test subscription management."""
    
    def test_cancel_subscription_exists(self, client):
        """Test that cancel subscription endpoint exists."""
        response = client.post('/cancel-subscription')
        # Should redirect or return error, but not 404
        assert response.status_code != 404
        
    def test_create_checkout_session_exists(self, client):
        """Test that create checkout session endpoint exists."""
        response = client.post('/create-checkout-session')
        # Should redirect or return error, but not 404
        assert response.status_code != 404


class TestPaymentRoutes:
    """Test payment-related routes."""
    
    def test_upgrade_page(self, client):
        """Test upgrade page loads."""
        response = client.get('/upgrade')
        # Might redirect to login, but should not 404
        assert response.status_code in [200, 302, 401]
        
    def test_payment_success_page(self, client):
        """Test payment success page."""
        response = client.get('/payment-success')
        assert response.status_code in [200, 302]
        
    def test_payment_cancel_page(self, client):
        """Test payment cancel page."""  
        response = client.get('/payment-cancel')
        assert response.status_code in [200, 302]


class TestPricingPlans:
    """Test pricing plan functionality."""
    
    def test_pricing_plans_seeded(self, client):
        """Test that pricing plans are properly seeded."""
        with app.app_context():
            plans = PricingPlan.query.all()
            assert len(plans) > 0
            
            # Check for expected plan types
            plan_names = [p.name for p in plans]
            assert 'Free' in plan_names or 'free' in plan_names
            
    def test_pricing_plan_model(self, client):
        """Test PricingPlan model functionality."""
        with app.app_context():
            plan = PricingPlan.query.first()
            assert plan is not None
            assert hasattr(plan, 'name')
            assert hasattr(plan, 'price')
            assert hasattr(plan, 'credits_per_month')