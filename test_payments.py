"""Comprehensive tests for payment processing functionality."""

import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from models import User, Payment, db
from payments import (
    charge_credits, create_stripe_customer, create_subscription, 
    process_payment, handle_webhook, cancel_subscription
)


class TestCreditSystem:
    """Test credit deduction and management."""
    
    def test_charge_credits_success(self, db_session, test_user):
        """Test successful credit deduction."""
        initial_credits = test_user.credits_balance
        
        result = charge_credits(test_user.id, 2)
        
        assert result is True
        db_session.refresh(test_user)
        assert test_user.credits_balance == initial_credits - 2
    
    def test_charge_credits_insufficient_balance(self, db_session, test_user):
        """Test credit deduction with insufficient balance."""
        test_user.credits_balance = 1
        db_session.commit()
        
        result = charge_credits(test_user.id, 5)
        
        assert result is False
        db_session.refresh(test_user)
        assert test_user.credits_balance == 1  # Unchanged
    
    def test_charge_credits_exact_balance(self, db_session, test_user):
        """Test credit deduction with exact balance."""
        test_user.credits_balance = 3
        db_session.commit()
        
        result = charge_credits(test_user.id, 3)
        
        assert result is True
        db_session.refresh(test_user)
        assert test_user.credits_balance == 0
    
    def test_charge_credits_nonexistent_user(self, db_session):
        """Test credit deduction for non-existent user."""
        result = charge_credits(99999, 1)
        assert result is False


class TestStripeIntegration:
    """Test Stripe payment integration."""
    
    @pytest.mark.payment
    def test_create_stripe_customer_success(self, mock_stripe, test_user):
        """Test successful Stripe customer creation."""
        mock_stripe['customer'].create.return_value = MagicMock(id='cus_test123')
        
        customer_id = create_stripe_customer(test_user.email)
        
        assert customer_id == 'cus_test123'
        mock_stripe['customer'].create.assert_called_once_with(email=test_user.email)
    
    @pytest.mark.payment
    def test_create_stripe_customer_failure(self, mock_stripe, test_user):
        """Test Stripe customer creation failure."""
        mock_stripe['customer'].create.side_effect = Exception("Stripe error")
        
        customer_id = create_stripe_customer(test_user.email)
        
        assert customer_id is None
    
    @pytest.mark.payment
    def test_create_subscription_success(self, mock_stripe, test_user):
        """Test successful subscription creation."""
        mock_stripe['subscription'].create.return_value = MagicMock(
            id='sub_test123',
            status='active',
            current_period_end=1234567890
        )
        
        subscription = create_subscription('cus_test123', 'price_premium')
        
        assert subscription['id'] == 'sub_test123'
        assert subscription['status'] == 'active'
    
    @pytest.mark.payment
    def test_process_payment_success(self, mock_stripe, db_session, test_user):
        """Test successful payment processing."""
        mock_stripe['payment_intent'].create.return_value = MagicMock(
            id='pi_test123',
            status='succeeded',
            amount=999
        )
        
        result = process_payment(test_user.id, 999, 'pm_test123')
        
        assert result['success'] is True
        assert result['payment_intent_id'] == 'pi_test123'
        
        # Check payment record created
        payment = Payment.query.filter_by(user_id=test_user.id).first()
        assert payment is not None
        assert payment.amount == 9.99  # Amount in dollars
        assert payment.status == 'succeeded'
    
    @pytest.mark.payment
    def test_process_payment_failure(self, mock_stripe, test_user):
        """Test payment processing failure."""
        mock_stripe['payment_intent'].create.side_effect = Exception("Card declined")
        
        result = process_payment(test_user.id, 999, 'pm_test123')
        
        assert result['success'] is False
        assert 'error' in result


class TestSubscriptionManagement:
    """Test subscription lifecycle management."""
    
    def test_subscription_upgrade(self, db_session, test_user, mock_stripe):
        """Test upgrading user subscription."""
        # Setup subscription mock
        mock_stripe['subscription'].create.return_value = MagicMock(
            id='sub_premium123',
            status='active'
        )
        
        # Simulate subscription upgrade
        test_user.subscription_tier = 'premium'
        test_user.subscription_status = 'active'
        test_user.stripe_subscription_id = 'sub_premium123'
        db_session.commit()
        
        assert test_user.subscription_tier == 'premium'
        assert test_user.subscription_status == 'active'
    
    def test_subscription_cancellation(self, db_session, premium_user, mock_stripe):
        """Test subscription cancellation."""
        premium_user.stripe_subscription_id = 'sub_test123'
        db_session.commit()
        
        # Mock Stripe cancellation
        with patch('stripe.Subscription.delete') as mock_cancel:
            mock_cancel.return_value = MagicMock(status='canceled')
            
            result = cancel_subscription(premium_user.id)
            
            assert result is True
            db_session.refresh(premium_user)
            assert premium_user.subscription_status == 'canceled'


class TestWebhookHandling:
    """Test Stripe webhook processing."""
    
    @pytest.mark.payment
    def test_webhook_subscription_created(self, client, db_session, test_user):
        """Test handling subscription created webhook."""
        webhook_data = {
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_webhook123',
                    'customer': test_user.stripe_customer_id or 'cus_test123',
                    'status': 'active'
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_data
            
            response = client.post('/webhook/stripe', 
                                 json=webhook_data,
                                 headers={'stripe-signature': 'test_sig'})
            
            assert response.status_code == 200
    
    @pytest.mark.payment 
    def test_webhook_payment_succeeded(self, client, db_session, test_user):
        """Test handling successful payment webhook."""
        webhook_data = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_webhook123',
                    'amount': 999,
                    'customer': test_user.stripe_customer_id or 'cus_test123'
                }
            }
        }
        
        with patch('stripe.Webhook.construct_event') as mock_construct:
            mock_construct.return_value = webhook_data
            
            response = client.post('/webhook/stripe',
                                 json=webhook_data, 
                                 headers={'stripe-signature': 'test_sig'})
            
            assert response.status_code == 200


class TestPaymentValidation:
    """Test payment validation and security."""
    
    def test_payment_amount_validation(self, test_user):
        """Test payment amount validation."""
        # Test negative amount
        result = process_payment(test_user.id, -100, 'pm_test123')
        assert result['success'] is False
        
        # Test zero amount
        result = process_payment(test_user.id, 0, 'pm_test123')
        assert result['success'] is False
        
        # Test excessively large amount
        result = process_payment(test_user.id, 1000000, 'pm_test123')
        assert result['success'] is False
    
    def test_payment_user_validation(self):
        """Test payment validation for invalid users."""
        result = process_payment(99999, 999, 'pm_test123')
        assert result['success'] is False
        assert 'User not found' in result.get('error', '')


class TestCreditRefillSystem:
    """Test monthly credit refill functionality."""
    
    def test_monthly_credit_refill(self, db_session):
        """Test monthly credit refill for free users."""
        # Create multiple free users with different credit levels
        users = []
        for i in range(3):
            user = User(
                email=f'free{i}@example.com',
                password_hash='test_hash',
                subscription_tier='free',
                subscription_status='active',
                credits_balance=i  # 0, 1, 2 credits
            )
            users.append(user)
            db_session.add(user)
        db_session.commit()
        
        # Import and test refill function
        from payments import refill_monthly_credits
        
        with patch('payments.db.session.commit') as mock_commit:
            refill_monthly_credits()
            
            # Verify all free users have 5 credits
            for user in users:
                db_session.refresh(user)
                assert user.credits_balance == 5
            
            mock_commit.assert_called()
    
    def test_premium_users_not_affected_by_refill(self, db_session, premium_user):
        """Test that premium users are not affected by credit refill."""
        initial_credits = premium_user.credits_balance
        
        from payments import refill_monthly_credits
        refill_monthly_credits()
        
        db_session.refresh(premium_user)
        assert premium_user.credits_balance == initial_credits


@pytest.mark.integration
class TestPaymentFlowIntegration:
    """Integration tests for complete payment flows."""
    
    def test_upgrade_to_premium_flow(self, client, db_session, test_user, mock_stripe):
        """Test complete upgrade to premium flow."""
        # Mock successful payment and subscription
        mock_stripe['payment_intent'].create.return_value = MagicMock(
            id='pi_upgrade123',
            status='succeeded',
            amount=1999
        )
        mock_stripe['subscription'].create.return_value = MagicMock(
            id='sub_premium123', 
            status='active'
        )
        
        # Simulate upgrade request
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
        
        response = client.post('/upgrade', data={
            'tier': 'premium',
            'payment_method': 'pm_test123'
        })
        
        # Should redirect to success page
        assert response.status_code in [200, 302]
    
    def test_credit_usage_in_meal_generation(self, client, db_session, test_user):
        """Test credit deduction during meal plan generation."""
        initial_credits = test_user.credits_balance
        
        with client.session_transaction() as sess:
            sess['user_id'] = test_user.id
        
        # Mock meal optimizer to avoid actual generation
        with patch('meal_optimizer.create_meal_plan') as mock_optimizer:
            mock_optimizer.return_value = {'success': True, 'meals': []}
            
            response = client.post('/api/generate', json={
                'target_calories': 2000,
                'diet_type': 'standard',
                'days': 1
            })
            
            if response.status_code == 200:
                # Credits should be deducted
                db_session.refresh(test_user)
                assert test_user.credits_balance < initial_credits