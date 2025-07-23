"""Payment processing service for Stripe integration."""
import stripe
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import current_app
from app.models import User, Payment, PricingPlan
from app.extensions import db


class PaymentProcessor:
    """Service for processing payments via Stripe."""
    
    def __init__(self):
        self.stripe = stripe
        self.stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
    
    def create_checkout_session(
        self,
        user: User,
        price_id: str,
        success_url: str,
        cancel_url: str,
        mode: str = 'subscription'
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session.
        
        Args:
            user: User model instance
            price_id: Stripe price ID
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            mode: 'subscription' or 'payment'
            
        Returns:
            Stripe session object
        """
        try:
            # Create or get Stripe customer
            customer_id = self._get_or_create_customer(user)
            
            # Create checkout session
            session = self.stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=str(user.id),
                metadata={
                    'user_id': user.id,
                    'user_email': user.email
                }
            )
            
            current_app.logger.info(f"Checkout session created for user {user.id}: {session.id}")
            return session
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Stripe error creating checkout: {str(e)}")
            raise
    
    def _get_or_create_customer(self, user: User) -> str:
        """Get existing Stripe customer or create new one."""
        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        # Create new customer
        customer = self.stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={
                'user_id': user.id
            }
        )
        
        # Save customer ID
        user.stripe_customer_id = customer.id
        db.session.commit()
        
        return customer.id
    
    def handle_successful_payment(self, session: Dict[str, Any]):
        """Handle successful payment from Stripe webhook."""
        try:
            user_id = int(session['client_reference_id'])
            user = User.query.get(user_id)
            
            if not user:
                current_app.logger.error(f"User not found for payment session: {session['id']}")
                return
            
            # Update user based on payment mode
            if session['mode'] == 'subscription':
                self._handle_subscription_payment(user, session)
            else:
                self._handle_one_time_payment(user, session)
            
            # Record payment
            self._record_payment(user, session)
            
            current_app.logger.info(f"Payment processed successfully for user {user_id}")
            
        except Exception as e:
            current_app.logger.error(f"Error handling successful payment: {str(e)}")
            raise
    
    def _handle_subscription_payment(self, user: User, session: Dict[str, Any]):
        """Handle subscription payment."""
        subscription_id = session['subscription']
        subscription = self.stripe.Subscription.retrieve(subscription_id)
        
        # Get price details
        price_id = subscription['items']['data'][0]['price']['id']
        pricing_plan = PricingPlan.query.filter_by(stripe_price_id_monthly=price_id).first()
        
        if not pricing_plan:
            pricing_plan = PricingPlan.query.filter_by(stripe_price_id_yearly=price_id).first()
        
        if pricing_plan:
            user.subscription_tier = pricing_plan.name
            user.subscription_status = 'active'
            user.stripe_subscription_id = subscription_id
            user.subscription_end_date = datetime.fromtimestamp(
                subscription['current_period_end'],
                tz=timezone.utc
            )
            
            # Give unlimited credits for premium users
            if pricing_plan.credits_per_month == 0:
                user.credits_balance = 999999  # Effectively unlimited
        
        db.session.commit()
    
    def _handle_one_time_payment(self, user: User, session: Dict[str, Any]):
        """Handle one-time payment (e.g., credit purchase)."""
        # Implementation for credit purchases
        payment_intent = self.stripe.PaymentIntent.retrieve(session['payment_intent'])
        amount = payment_intent['amount'] / 100  # Convert from cents
        
        # Add credits based on amount
        # Example: $10 = 10 credits
        credits_to_add = int(amount)
        user.credits_balance += credits_to_add
        
        db.session.commit()
    
    def _record_payment(self, user: User, session: Dict[str, Any]):
        """Record payment in database."""
        payment = Payment(
            user_id=user.id,
            amount=session['amount_total'] / 100,  # Convert from cents
            currency=session['currency'].upper(),
            status='completed',
            payment_method='stripe',
            stripe_payment_intent_id=session.get('payment_intent'),
            stripe_invoice_id=session.get('invoice'),
            product_type='subscription' if session['mode'] == 'subscription' else 'credits',
            description=f"{session['mode'].title()} payment",
            completed_at=datetime.now(timezone.utc),
            metadata={
                'session_id': session['id'],
                'mode': session['mode']
            }
        )
        
        db.session.add(payment)
        db.session.commit()
    
    def cancel_subscription(self, user: User) -> bool:
        """Cancel user's subscription."""
        try:
            if not user.stripe_subscription_id:
                return False
            
            # Cancel at period end
            subscription = self.stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            user.subscription_status = 'cancelled'
            db.session.commit()
            
            current_app.logger.info(f"Subscription cancelled for user {user.id}")
            return True
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Error cancelling subscription: {str(e)}")
            return False
    
    def reactivate_subscription(self, user: User) -> bool:
        """Reactivate cancelled subscription."""
        try:
            if not user.stripe_subscription_id:
                return False
            
            subscription = self.stripe.Subscription.modify(
                user.stripe_subscription_id,
                cancel_at_period_end=False
            )
            
            user.subscription_status = 'active'
            db.session.commit()
            
            current_app.logger.info(f"Subscription reactivated for user {user.id}")
            return True
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Error reactivating subscription: {str(e)}")
            return False
    
    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        try:
            event = self.stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            current_app.logger.info(f"Stripe webhook received: {event['type']}")
            
            # Handle different event types
            if event['type'] == 'checkout.session.completed':
                self.handle_successful_payment(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.updated':
                self._handle_subscription_updated(event['data']['object'])
            
            elif event['type'] == 'customer.subscription.deleted':
                self._handle_subscription_deleted(event['data']['object'])
            
            elif event['type'] == 'invoice.payment_failed':
                self._handle_payment_failed(event['data']['object'])
            
            return {'status': 'success'}
            
        except ValueError:
            current_app.logger.error("Invalid webhook payload")
            raise
        except stripe.error.SignatureVerificationError:
            current_app.logger.error("Invalid webhook signature")
            raise
    
    def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription update event."""
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if user:
            user.subscription_end_date = datetime.fromtimestamp(
                subscription['current_period_end'],
                tz=timezone.utc
            )
            db.session.commit()
    
    def _handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription deletion event."""
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if user:
            user.subscription_status = 'expired'
            user.subscription_tier = 'free'
            user.credits_balance = 3  # Reset to free tier credits
            db.session.commit()
    
    def _handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment event."""
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            # Log the failed payment
            current_app.logger.warning(f"Payment failed for user {user.id}")
            # Could send email notification here
    
    def get_customer_portal_url(self, user: User, return_url: str) -> Optional[str]:
        """Get Stripe customer portal URL for subscription management."""
        try:
            if not user.stripe_customer_id:
                return None
            
            session = self.stripe.billing_portal.Session.create(
                customer=user.stripe_customer_id,
                return_url=return_url
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Error creating portal session: {str(e)}")
            return None