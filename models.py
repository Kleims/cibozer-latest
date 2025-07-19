"""
Database models for Cibozer
User authentication and subscription management
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and subscription tracking"""
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    email_verified = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Trial
    trial_ends_at = db.Column(db.DateTime)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='user', lazy='dynamic')
    payments = db.relationship('Payment', backref='user', lazy='dynamic')
    meal_plans = db.relationship('SavedMealPlan', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Check if password matches"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_premium(self):
        """Check if user has active premium subscription"""
        if self.subscription_tier in ['pro', 'premium']:
            if self.subscription_end_date and self.subscription_end_date > datetime.utcnow():
                return True
        return False
    
    def has_credits(self):
        """Check if user has credits available"""
        return self.credits_balance > 0
    
    def use_credits(self, amount=1):
        """Deduct credits from balance"""
        if self.credits_balance >= amount:
            self.credits_balance -= amount
            db.session.commit()
            return True
        return False
    
    def can_generate_plan(self):
        """Check if user can generate a meal plan"""
        if self.is_premium():
            return True
        return self.has_credits()
    
    def get_monthly_usage(self):
        """Get usage count for current month"""
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.usage_logs.filter(
            UsageLog.timestamp >= start_of_month,
            UsageLog.action_type == 'generate_plan'
        ).count()


class UsageLog(db.Model):
    """Track user actions and credit usage"""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # generate_plan, export_pdf, etc
    credits_used = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    extra_data = db.Column(db.JSON)  # Store additional info like diet_type, calories, etc


class Payment(db.Model):
    """Track payments and transactions"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_payment_intent_id = db.Column(db.String(100))
    amount = db.Column(db.Integer)  # Amount in cents
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(20))  # succeeded, pending, failed
    payment_type = db.Column(db.String(20))  # subscription, credits
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payment_data = db.Column(db.JSON)


class SavedMealPlan(db.Model):
    """Store user's saved meal plans"""
    __tablename__ = 'saved_meal_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    meal_plan_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'meal_plan': self.meal_plan_data
        }


class PricingPlan(db.Model):
    """Define subscription tiers and pricing"""
    __tablename__ = 'pricing_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # free, pro, premium
    display_name = db.Column(db.String(50))
    price_monthly = db.Column(db.Integer)  # Price in cents
    price_yearly = db.Column(db.Integer)   # Price in cents
    stripe_price_id_monthly = db.Column(db.String(100))
    stripe_price_id_yearly = db.Column(db.String(100))
    
    # Features
    meal_plans_limit = db.Column(db.Integer)  # -1 for unlimited
    max_days_planning = db.Column(db.Integer, default=1)
    pdf_export = db.Column(db.Boolean, default=False)
    advanced_features = db.Column(db.Boolean, default=False)
    priority_support = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def seed_default_plans():
        """Create default pricing plans"""
        plans = [
            {
                'name': 'free',
                'display_name': 'Free',
                'price_monthly': 0,
                'price_yearly': 0,
                'meal_plans_limit': 3,
                'max_days_planning': 1,
                'pdf_export': False,
                'advanced_features': False,
                'priority_support': False
            },
            {
                'name': 'pro',
                'display_name': 'Pro',
                'price_monthly': 999,  # $9.99
                'price_yearly': 7900,  # $79/year
                'meal_plans_limit': -1,  # Unlimited
                'max_days_planning': 7,
                'pdf_export': True,
                'advanced_features': True,
                'priority_support': True
            },
            {
                'name': 'premium',
                'display_name': 'Premium',
                'price_monthly': 1999,  # $19.99
                'price_yearly': 17900,  # $179/year
                'meal_plans_limit': -1,
                'max_days_planning': 7,
                'pdf_export': True,
                'advanced_features': True,
                'priority_support': True
            }
        ]
        
        for plan_data in plans:
            plan = PricingPlan.query.filter_by(name=plan_data['name']).first()
            if not plan:
                plan = PricingPlan(**plan_data)
                db.session.add(plan)
        
        db.session.commit()