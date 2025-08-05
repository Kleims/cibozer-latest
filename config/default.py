"""Default configuration settings."""
import os
from datetime import timedelta

class Config:
    """Base configuration."""
    
    # Basic Flask config - SECURITY: Must set SECRET_KEY environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        import secrets
        SECRET_KEY = secrets.token_urlsafe(32)
        print("WARNING: SECRET_KEY not set! Using randomly generated key. Set SECRET_KEY environment variable for production.")
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///cibozer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,  # Allow up to 30 total connections (10 + 20 overflow)
        'pool_recycle': 3600,  # Recycle connections every hour
        'pool_pre_ping': True,  # Verify connections before use
        'pool_timeout': 30,  # Connection timeout in seconds
        'pool_reset_on_return': 'commit',  # Reset connections on return
        'connect_args': {
            'timeout': 30,  # Query timeout in seconds (SQLite)
            'check_same_thread': False,  # Allow SQLite to be used across threads
            'isolation_level': None  # Use autocommit mode for better performance
        } if 'sqlite' in (os.environ.get('DATABASE_URL') or 'sqlite:///cibozer.db') else {
            'connect_timeout': 30,  # Connection timeout for PostgreSQL/MySQL
            'server_side_cursors': False,  # Disable server-side cursors for better timeout handling
            'pool_reset_on_return': 'commit',  # Reset connection state
            'application_name': 'Cibozer',  # For connection identification
        }
    }
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@cibozer.com')
    
    # Stripe configuration
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # OpenAI configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', 'on', '1']
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Application specific
    MEALS_PER_PAGE = 10
    FREE_CREDITS = 3
    PRO_PRICE = 999  # $9.99 in cents
    PREMIUM_PRICE = 1999  # $19.99 in cents
    
    # Video generation
    VIDEO_OUTPUT_DIR = 'static/videos'
    VIDEO_CLEANUP_DAYS = 7
    
    # PDF generation
    PDF_OUTPUT_DIR = 'static/pdfs'
    PDF_CLEANUP_DAYS = 30