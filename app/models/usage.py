"""Usage tracking and API key models."""
from datetime import datetime, timezone
import secrets
from app.extensions import db


class UsageLog(db.Model):
    """Log user actions and API usage."""
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Action details
    action = db.Column(db.String(100), nullable=False)  # meal_plan_generated, pdf_exported, etc.
    resource_type = db.Column(db.String(50))  # meal_plan, video, pdf
    resource_id = db.Column(db.String(100))
    
    # Request details
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    endpoint = db.Column(db.String(200))
    method = db.Column(db.String(10))
    
    # Response
    status_code = db.Column(db.Integer)
    response_time_ms = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    # Credits
    credits_used = db.Column(db.Integer, default=0)
    credits_remaining = db.Column(db.Integer)
    
    # Metadata
    usage_metadata = db.Column(db.JSON)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        """String representation."""
        return f'<UsageLog {self.id} - {self.action}>'


class APIKey(db.Model):
    """API keys for premium users."""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Key details
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Permissions
    scopes = db.Column(db.JSON)  # List of allowed scopes
    rate_limit = db.Column(db.Integer, default=1000)  # Requests per hour
    
    # Usage tracking
    last_used_at = db.Column(db.DateTime)
    total_requests = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref='api_keys')
    
    @classmethod
    def generate_key(cls):
        """Generate a secure API key."""
        return 'ck_' + secrets.token_urlsafe(48)
    
    def increment_usage(self):
        """Increment usage counter."""
        self.total_requests += 1
        self.last_used_at = datetime.now(timezone.utc)
    
    def is_valid(self):
        """Check if API key is valid."""
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True
    
    def __repr__(self):
        """String representation."""
        return f'<APIKey {self.name} - {self.key[:8]}...>'