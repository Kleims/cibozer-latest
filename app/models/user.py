"""User model for authentication and subscription tracking."""
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User model for authentication and subscription tracking."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    
    # Subscription info
    subscription_tier = db.Column(db.String(20), default='free')  # free, pro, premium
    subscription_status = db.Column(db.String(20), default='active')  # active, cancelled, expired
    subscription_end_date = db.Column(db.DateTime)
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    
    # Credits system
    credits_balance = db.Column(db.Integer, default=3)  # Free users start with 3 credits
    
    # Tracking
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime)
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Trial
    trial_ends_at = db.Column(db.DateTime)
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    shared_meal_plans = db.relationship('SharedMealPlan', backref='creator', lazy='dynamic')
    meal_plans = db.relationship('SavedMealPlan', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches."""
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.password_hash.encode('utf-8')
        )
    
    def is_premium(self):
        """Check if user has active premium subscription."""
        if self.subscription_tier in ['pro', 'premium']:
            # If no end date, subscription is unlimited (e.g., admin users)
            if self.subscription_end_date is None:
                return True
            # If there is an end date, check if it's still valid
            if self.subscription_end_date:
                # Handle both naive and aware datetimes for SQLite compatibility
                end_date = self.subscription_end_date
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                if end_date > datetime.now(timezone.utc):
                    return True
        return False
    
    def has_credits(self):
        """Check if user has credits available."""
        return self.credits_balance > 0
    
    def use_credits(self, amount=1):
        """Deduct credits from balance."""
        if self.credits_balance >= amount:
            self.credits_balance -= amount
            return True
        return False
    
    def generate_reset_token(self):
        """Generate password reset token."""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token."""
        if not self.reset_token or self.reset_token != token:
            return False
        
        # Handle timezone comparison for SQLite compatibility
        expires = self.reset_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        
        if expires < datetime.now(timezone.utc):
            return False
        return True
    
    def clear_reset_token(self):
        """Clear password reset token."""
        self.reset_token = None
        self.reset_token_expires = None
    
    def can_generate_plan(self):
        """Check if user can generate a meal plan."""
        if self.is_premium():
            return True
        return self.has_credits()
    
    def get_monthly_usage(self):
        """Get usage count for current month."""
        from datetime import datetime, timezone
        from app.models.usage import UsageLog
        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return db.session.query(UsageLog).filter(
            UsageLog.user_id == self.id,
            UsageLog.created_at >= start_of_month,
            UsageLog.action == 'meal_plan_generated'
        ).count()
    
    def __repr__(self):
        """String representation."""
        return f'<User {self.email}>'