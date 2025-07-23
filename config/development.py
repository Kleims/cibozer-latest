"""Development configuration."""
from .default import Config

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Less secure settings for development
    SESSION_COOKIE_SECURE = False
    
    # Development database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dev_cibozer.db'
    
    # Disable rate limiting in development
    RATELIMIT_ENABLED = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'
    
    # Cache settings
    CACHE_TYPE = 'simple'
    
    # Email backend for development
    MAIL_DEBUG = True
    MAIL_SUPPRESS_SEND = True  # Don't actually send emails in dev