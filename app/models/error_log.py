"""Error logging model."""
from datetime import datetime, timezone
from app.extensions import db

class ErrorLog(db.Model):
    """Model for storing detailed error information."""
    
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    error_id = db.Column(db.String(36), unique=True, nullable=False, index=True)  # UUID
    error_type = db.Column(db.String(200), nullable=False, index=True)
    error_message = db.Column(db.Text, nullable=False)
    traceback = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False, index=True)  # info, warning, error, critical, fatal
    context = db.Column(db.Text, nullable=True)  # JSON string with additional context
    request_info = db.Column(db.Text, nullable=True)  # JSON string with request details
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    resolved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)  # Admin notes about the error
    counter = db.Column(db.Integer, default=1, nullable=False)  # How many times this error occurred
    first_occurrence = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_occurrence = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='error_logs')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def __init__(self, **kwargs):
        super(ErrorLog, self).__init__(**kwargs)
        if not self.first_occurrence:
            self.first_occurrence = datetime.now(timezone.utc)
        if not self.last_occurrence:
            self.last_occurrence = datetime.now(timezone.utc)
    
    def mark_resolved(self, resolved_by_user_id, notes=None):
        """Mark error as resolved."""
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by_user_id
        if notes:
            self.notes = notes
    
    def increment_counter(self):
        """Increment occurrence counter and update last occurrence."""
        self.counter += 1
        self.last_occurrence = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'error_id': self.error_id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'severity': self.severity,
            'user_id': self.user_id,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'counter': self.counter,
            'first_occurrence': self.first_occurrence.isoformat(),
            'last_occurrence': self.last_occurrence.isoformat(),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def get_error_summary(cls, hours=24):
        """Get error summary for the last N hours."""
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Get error counts by type
        error_types = db.session.query(
            cls.error_type,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= cutoff_time
        ).group_by(cls.error_type).all()
        
        # Get error counts by severity
        severities = db.session.query(
            cls.severity,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= cutoff_time
        ).group_by(cls.severity).all()
        
        # Get recent critical errors
        critical_errors = cls.query.filter(
            cls.severity.in_(['critical', 'fatal']),
            cls.created_at >= cutoff_time
        ).order_by(cls.created_at.desc()).limit(10).all()
        
        return {
            'period_hours': hours,
            'error_types': {et.error_type: et.count for et in error_types},
            'severities': {s.severity: s.count for s in severities},
            'critical_errors': [e.to_dict() for e in critical_errors],
            'total_errors': sum(et.count for et in error_types)
        }
    
    @classmethod
    def get_unresolved_errors(cls, limit=50):
        """Get unresolved errors sorted by severity and frequency."""
        return cls.query.filter_by(resolved=False).order_by(
            cls.severity.desc(),
            cls.counter.desc(),
            cls.created_at.desc()
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<ErrorLog {self.error_id}: {self.error_type} ({self.severity})>'