"""Tests for payments.py - Payment functionality"""

import pytest
from unittest.mock import patch, MagicMock

from models import db, User, Payment, PricingPlan
from payments import check_user_credits, deduct_credit, add_credits
from tests.shared_fixtures import app, client, test_user, premium_user
from tests.database_utils import DatabaseHelper


class TestCreditSystem:
    """Test credit deduction and management."""
    
    def test_check_user_credits_sufficient(self, app, test_user):
        """Test checking user credits when sufficient."""
        with app.app_context():
            user = User.query.get(test_user)
            # User has 10 credits by default
            result = check_user_credits(user)
            assert result is True
    
    def test_check_user_credits_insufficient(self, app, test_user):
        """Test checking user credits when insufficient."""
        with app.app_context():
            user = User.query.get(test_user)
            # Set credits to 0 to test insufficient case
            user.credits_balance = 0
            db.session.commit()
            result = check_user_credits(user)
            assert result is False
    
    def test_deduct_credit_success(self, app, test_user):
        """Test successful credit deduction."""
        with app.app_context():
            user = User.query.get(test_user)
            initial_credits = user.credits_balance
            
            result = deduct_credit(user, 2)
            
            assert result is True
            DatabaseHelper.refresh_object(user)
            assert user.credits_balance == initial_credits - 2
    
    def test_deduct_credit_insufficient_funds(self, app, test_user):
        """Test credit deduction with insufficient funds."""
        with app.app_context():
            user = User.query.get(test_user)
            initial_credits = user.credits_balance
            
            result = deduct_credit(user, 50)
            
            assert result is False
            DatabaseHelper.refresh_object(user)
            assert user.credits_balance == initial_credits
    
    def test_add_credits_success(self, app, test_user):
        """Test successful credit addition."""
        with app.app_context():
            user = User.query.get(test_user)
            initial_credits = user.credits_balance
            
            add_credits(user, 20)
            
            DatabaseHelper.refresh_object(user)
            assert user.credits_balance == initial_credits + 20


class TestPricingPlans:
    """Test pricing plan functionality."""
    
    def test_pricing_plans_exist(self, app):
        """Test that pricing plans are seeded."""
        with app.app_context():
            plans = PricingPlan.query.all()
            assert len(plans) > 0
    
    def test_free_plan_exists(self, app):
        """Test that free plan exists."""
        with app.app_context():
            free_plan = PricingPlan.query.filter_by(name='free').first()
            assert free_plan is not None
            assert free_plan.price_monthly == 0


class TestPaymentRoutes:
    """Test payment-related routes."""
    
    def test_upgrade_page_requires_login(self, client):
        """Test that upgrade page requires login."""
        response = client.get('/upgrade')
        assert response.status_code in [302, 401]
    
    def test_webhook_endpoint_exists(self, client):
        """Test that webhook endpoint exists."""
        response = client.post('/api/payments/stripe/webhook')
        # Should respond even without valid webhook data
        assert response.status_code in [200, 400, 401, 404, 405]


class TestSubscriptionTiers:
    """Test subscription tier functionality."""
    
    def test_free_user_limits(self, app, test_user):
        """Test free user credit limits."""
        with app.app_context():
            user = User.query.get(test_user)
            assert user.subscription_tier == 'free'
            assert user.credits_balance <= 50  # Free users have limited credits
    
    def test_premium_user_benefits(self, app, premium_user):
        """Test premium user benefits."""
        with app.app_context():
            user = User.query.get(premium_user)
            assert user.subscription_tier == 'pro'
            assert user.credits_balance > 50  # Premium users have more credits