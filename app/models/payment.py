"""Payment and pricing models."""
from datetime import datetime, timezone
from app.extensions import db


class Payment(db.Model):
    """Payment transaction model."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Payment details
    amount = db.Column(db.Float, nullable=False)  # Amount in dollars
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), nullable=False)  # pending, completed, failed, refunded
    payment_method = db.Column(db.String(50))  # stripe, paypal, etc.
    
    # Stripe specific
    stripe_payment_intent_id = db.Column(db.String(100), unique=True)
    stripe_charge_id = db.Column(db.String(100))
    stripe_invoice_id = db.Column(db.String(100))
    
    # What was purchased
    product_type = db.Column(db.String(50))  # subscription, credits, one-time
    product_id = db.Column(db.String(50))
    description = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    
    # Metadata
    payment_metadata = db.Column(db.JSON)
    
    def __repr__(self):
        """String representation."""
        return f'<Payment {self.id} - ${self.amount} - {self.status}>'


class PricingPlan(db.Model):
    """Pricing plan configuration."""
    __tablename__ = 'pricing_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # free, pro, premium
    display_name = db.Column(db.String(100), nullable=False)
    
    # Pricing
    price_monthly = db.Column(db.Float, default=0.0)  # Monthly price in dollars
    price_yearly = db.Column(db.Float, default=0.0)   # Yearly price in dollars
    
    # Features
    features = db.Column(db.JSON)  # List of feature strings
    credits_per_month = db.Column(db.Integer, default=0)  # 0 for unlimited
    max_meal_plans = db.Column(db.Integer, default=0)  # 0 for unlimited
    video_generation = db.Column(db.Boolean, default=False)
    pdf_export = db.Column(db.Boolean, default=False)
    api_access = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    
    # Stripe
    stripe_price_id_monthly = db.Column(db.String(100))
    stripe_price_id_yearly = db.Column(db.String(100))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        """String representation."""
        return f'<PricingPlan {self.name} - ${self.price_monthly}/mo>'