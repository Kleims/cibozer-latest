"""User model for authentication and subscription tracking."""
from datetime import datetime, timezone, timedelta
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
    # Email verification
    email_verification_token = db.Column(db.String(100), unique=True, nullable=True)
    email_verification_expires = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Trial
    trial_ends_at = db.Column(db.DateTime)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    password_changed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    shared_meal_plans = db.relationship('SharedMealPlan', backref='creator', lazy='dynamic')
    meal_plans = db.relationship('SavedMealPlan', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password with secure bcrypt rounds."""
        # Use 12 rounds for security (default is 12, but being explicit)
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
        self.password_changed_at = datetime.now(timezone.utc)
    
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
        """Get usage count for current month - optimized query."""
        from datetime import datetime, timezone
        from app.models.usage import UsageLog
        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Use optimized query with indexed fields
        return UsageLog.query.filter(
            UsageLog.user_id == self.id,
            UsageLog.action == 'meal_plan_generated',
            UsageLog.created_at >= start_of_month
        ).with_entities(UsageLog.id).count()
    

    def generate_verification_token(self):
        """Generate email verification token"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
        return self.email_verification_token
    
    def verify_email(self, token):
        """Verify email with token"""
        if (self.email_verification_token == token and 
            self.email_verification_expires and 
            self.email_verification_expires > datetime.now(timezone.utc)):
            self.email_verified = True
            self.email_verification_token = None
            self.email_verification_expires = None
            return True
        return False


    def is_locked(self):
        """Check if account is locked due to failed attempts"""
        if self.locked_until:
            if self.locked_until.tzinfo is None:
                self.locked_until = self.locked_until.replace(tzinfo=timezone.utc)
            return self.locked_until > datetime.now(timezone.utc)
        return False
    
    def increment_failed_login(self):
        """Increment failed login counter and lock if necessary"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.now(timezone.utc)
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    def reset_failed_login(self):
        """Reset failed login counter on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_failed_login = None
    def __repr__(self):
        """String representation."""
        return f'<User {self.email}>'