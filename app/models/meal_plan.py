"""Meal plan related models."""
from datetime import datetime, timezone
import secrets
from app.extensions import db


class SavedMealPlan(db.Model):
    """Saved meal plans for users."""
    __tablename__ = 'saved_meal_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Plan details
    name = db.Column(db.String(200), nullable=False)
    meal_plan_data = db.Column(db.JSON, nullable=False)  # Complete meal plan JSON
    
    # Metadata
    total_calories = db.Column(db.Integer)
    diet_type = db.Column(db.String(50))  # keto, paleo, vegan, etc.
    days = db.Column(db.Integer, default=1)
    
    # Files
    pdf_url = db.Column(db.String(500))
    video_url = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    # Sharing
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(32), unique=True)
    
    def generate_share_token(self):
        """Generate unique share token."""
        self.share_token = secrets.token_urlsafe(16)
        return self.share_token
    
    def __repr__(self):
        """String representation."""
        return f'<SavedMealPlan {self.id} - {self.name}>'


class SharedMealPlan(db.Model):
    """Publicly shared meal plans."""
    __tablename__ = 'shared_meal_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Share details
    share_token = db.Column(db.String(32), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Plan data
    meal_plan_data = db.Column(db.JSON, nullable=False)
    total_calories = db.Column(db.Integer)
    diet_type = db.Column(db.String(50))
    
    # Privacy
    requires_password = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(255))
    
    # Analytics
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    def increment_views(self):
        """Increment view counter."""
        self.view_count += 1
    
    def increment_downloads(self):
        """Increment download counter."""
        self.download_count += 1
    
    def __repr__(self):
        """String representation."""
        return f'<SharedMealPlan {self.share_token}>'


class MealPlanShare(db.Model):
    """Track individual shares of meal plans."""
    __tablename__ = 'meal_plan_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('saved_meal_plans.id'), nullable=False)
    shared_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Share details
    share_method = db.Column(db.String(50))  # email, link, social
    recipient_email = db.Column(db.String(120))
    
    # Tracking
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    accessed_at = db.Column(db.DateTime)
    access_count = db.Column(db.Integer, default=0)
    
    # Relationships
    meal_plan = db.relationship('SavedMealPlan', backref='shares')
    shared_by = db.relationship('User', backref='meal_plan_shares')
    
    def __repr__(self):
        """String representation."""
        return f'<MealPlanShare {self.id}>'