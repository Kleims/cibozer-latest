"""
Stripe Payment Integration for Cibozer
Handles subscriptions, payments, and credit purchases
"""

import os
from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta, timezone
from models import db, User, Payment, PricingPlan
import logging
from app_config import get_app_config

# Configure logging
logger = logging.getLogger(__name__)

# Load centralized configuration
config = get_app_config()

# Try to import Stripe, but handle if not installed
try:
    import stripe
    if config.payment.STRIPE_ENABLED and config.payment.STRIPE_SECRET_KEY:
        stripe.api_key = config.payment.STRIPE_SECRET_KEY
        STRIPE_AVAILABLE = True
        logger.info("[OK] Stripe configured successfully")
    else:
        STRIPE_AVAILABLE = False
        logger.warning("[WARN] Stripe not enabled or secret key not configured - payments disabled")
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False
    logger.warning("[WARN] Stripe module not installed - payments disabled")

STRIPE_PUBLISHABLE_KEY = config.payment.STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET = config.payment.STRIPE_WEBHOOK_SECRET

# Validate Stripe configuration
if STRIPE_AVAILABLE and not STRIPE_PUBLISHABLE_KEY:
    logger.warning("[WARN] Stripe publishable key not configured - checkout may fail")

# Create payments blueprint
payments_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Pricing configuration from centralized config
PRICING_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'credits': 3,
        'features': ['3 meal plans per month', 'Basic meal suggestions', 'PDF export']
    },
    'pro': {
        'name': 'Pro',
        'price': int(config.payment.PRO_PRICE * 100),  # Convert to cents
        'credits': config.payment.PRO_CREDITS,
        'stripe_price_id': config.payment.STRIPE_PRICE_ID_PRO,
        'features': ['Unlimited meal plans', 'Video generation', 'Advanced nutrition tracking', 'Priority support']
    },
    'premium': {
        'name': 'Premium',
        'price': int(config.payment.PREMIUM_PRICE * 100),  # Convert to cents
        'credits': config.payment.PREMIUM_CREDITS,
        'stripe_price_id': config.payment.STRIPE_PRICE_ID_PREMIUM,
        'features': ['Everything in Pro', 'Custom diet profiles', 'Grocery list automation', 'Recipe scaling', 'API access']
    }
}

@payments_bp.route('/plans')
def get_pricing_plans():
    """Get available pricing plans"""
    return jsonify({
        'plans': PRICING_PLANS,
        'publishable_key': STRIPE_PUBLISHABLE_KEY
    })

@payments_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        plan = data.get('plan', 'pro')
        
        if plan not in ['pro', 'premium']:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Check if Stripe is configured
        if not STRIPE_AVAILABLE or not stripe.api_key or stripe.api_key.startswith('sk_your_'):
            logger.warning("Stripe not configured - using test mode")
            # Simulate successful upgrade for testing
            current_user.subscription_tier = plan
            current_user.subscription_status = 'active'
            current_user.credits_balance = -1  # Unlimited
            current_user.subscription_end_date = datetime.now(timezone.utc) + timedelta(days=30)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'test_mode': True,
                'message': f'Test mode: Upgraded to {plan.title()} plan'
            })
        
        # Get or create Stripe customer
        if not current_user.stripe_customer_id:
            if not STRIPE_AVAILABLE:
                return jsonify({'error': 'Stripe not available'}), 500
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={'user_id': current_user.id}
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        price_id = PRICING_PLANS[plan]['stripe_price_id']
        if not price_id:
            return jsonify({'error': 'Stripe price ID not configured'}), 500
        
        checkout_session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'auth/account?upgraded=true',
            cancel_url=request.host_url + 'auth/upgrade',
            metadata={
                'user_id': current_user.id,
                'plan': plan
            }
        )
        
        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        return jsonify({'error': 'Payment processing error'}), 500
    except Exception as e:
        logger.error(f"Checkout error: {str(e)}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@payments_bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        if not current_user.stripe_subscription_id:
            return jsonify({'error': 'No active subscription found'}), 404
        
        # Check if Stripe is configured
        if not STRIPE_AVAILABLE or not stripe.api_key or stripe.api_key.startswith('sk_your_'):
            # Test mode cancellation
            current_user.subscription_status = 'cancelled'
            current_user.subscription_tier = 'free'
            current_user.credits_balance = 3
            db.session.commit()
            
            return jsonify({
                'success': True,
                'test_mode': True,
                'message': 'Test mode: Subscription cancelled'
            })
        
        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            current_user.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        current_user.subscription_status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Subscription will be cancelled at the end of the billing period',
            'end_date': datetime.fromtimestamp(subscription.current_period_end).isoformat()
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe cancellation error: {str(e)}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500
    except Exception as e:
        logger.error(f"Cancellation error: {str(e)}")
        return jsonify({'error': 'Failed to process cancellation'}), 500

@payments_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    if not STRIPE_WEBHOOK_SECRET:
        logger.warning("Webhook secret not configured")
        return jsonify({'received': True}), 200
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid webhook payload")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid webhook signature")
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle different event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)
    
    return jsonify({'received': True}), 200

def handle_checkout_completed(session):
    """Handle successful checkout"""
    try:
        user_id = session['metadata']['user_id']
        plan = session['metadata']['plan']
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found for checkout session")
            return
        
        # Update user subscription
        user.subscription_tier = plan
        user.subscription_status = 'active'
        user.stripe_subscription_id = session['subscription']
        user.credits_balance = -1  # Unlimited
        
        # Set subscription end date (will be updated by subscription webhook)
        user.subscription_end_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        db.session.commit()
        logger.info(f"User {user.email} upgraded to {plan}")
        
    except Exception as e:
        logger.error(f"Error handling checkout: {str(e)}")

def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    try:
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if not user:
            return
        
        # Update subscription status
        user.subscription_status = subscription['status']
        
        if subscription['status'] == 'active':
            user.subscription_end_date = datetime.fromtimestamp(subscription['current_period_end'])
        
        db.session.commit()
        logger.info(f"Updated subscription for {user.email}: {subscription['status']}")
        
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")

def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    try:
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if not user:
            return
        
        # Downgrade to free tier
        user.subscription_tier = 'free'
        user.subscription_status = 'cancelled'
        user.stripe_subscription_id = None
        user.credits_balance = 3
        
        db.session.commit()
        logger.info(f"Cancelled subscription for {user.email}")
        
    except Exception as e:
        logger.error(f"Error handling subscription deletion: {str(e)}")

def handle_payment_succeeded(invoice):
    """Record successful payment"""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if not user:
            return
        
        # Record payment
        payment = Payment(
            user_id=user.id,
            amount=invoice['amount_paid'] / 100,  # Convert from cents
            currency=invoice['currency'],
            stripe_payment_id=invoice['payment_intent'],
            status='completed',
            description=f"Subscription payment for {user.subscription_tier}"
        )
        db.session.add(payment)
        db.session.commit()
        
        logger.info(f"Recorded payment of ${payment.amount} for {user.email}")
        
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")

@payments_bp.route('/usage')
@login_required
def get_usage():
    """Get user's credit usage and limits"""
    return jsonify({
        'subscription_tier': current_user.subscription_tier,
        'subscription_status': current_user.subscription_status,
        'credits_balance': current_user.credits_balance,
        'unlimited': current_user.credits_balance == -1,
        'subscription_end_date': current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None
    })

# Utility functions
def check_user_credits(user):
    """Check if user has available credits"""
    # Check if user has active premium subscription (unlimited credits)
    if user.subscription_tier in ['pro', 'premium'] and user.subscription_status == 'active':
        # Verify subscription hasn't expired
        if user.subscription_end_date and user.subscription_end_date > datetime.now(timezone.utc):
            return True  # Unlimited credits for active subscribers
        else:
            # Subscription expired, downgrade user
            user.subscription_tier = 'free'
            user.subscription_status = 'expired' 
            user.credits_balance = 0  # Reset to free tier
            db.session.commit()
    
    # Check free tier credits
    return user.credits_balance > 0

def deduct_credit(user, amount=1):
    """Deduct credits from user's balance"""
    # Check if user has active premium subscription (unlimited credits)
    if user.subscription_tier in ['pro', 'premium'] and user.subscription_status == 'active':
        # Verify subscription hasn't expired
        if user.subscription_end_date and user.subscription_end_date > datetime.now(timezone.utc):
            return True  # Unlimited credits for active subscribers
        else:
            # Subscription expired, downgrade user
            user.subscription_tier = 'free'
            user.subscription_status = 'expired'
            user.credits_balance = 0  # Reset to free tier
            db.session.commit()
    
    # Check free tier credits
    if user.credits_balance >= amount:
        user.credits_balance -= amount
        db.session.commit()
        return True
    return False

def refill_monthly_credits():
    """Refill credits for free tier users at the start of each month"""
    from datetime import datetime, timezone
    from models import User, db
    
    # Get all free tier users
    free_users = User.query.filter_by(subscription_tier='free').all()
    
    refilled_count = 0
    for user in free_users:
        # Give free users 3 credits per month
        if user.credits_balance < 3:
            user.credits_balance = 3
            refilled_count += 1
    
    if refilled_count > 0:
        db.session.commit()
        logger.info(f"Refilled credits for {refilled_count} free tier users")
    
    return refilled_count

def add_credits(user, amount):
    """Add credits to user's balance (for credit purchases)"""
    user.credits_balance += amount
    db.session.commit()
    logger.info(f"Added {amount} credits to user {user.email}")
    return True