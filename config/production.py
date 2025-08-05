"""Production configuration."""
import os
from .default import Config

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production database (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Enhanced Security Settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'true').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'true').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Strict')
    
    # Server configuration
    SERVER_NAME = os.environ.get('SERVER_NAME')
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'https')
    
    # CSRF Protection
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_SSL_STRICT = os.environ.get('WTF_CSRF_SSL_STRICT', 'true').lower() == 'true'
    
    # Production cache (Redis if available)
    CACHE_TYPE = 'redis' if os.environ.get('REDIS_URL') else 'simple'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    
    # Enhanced Stripe Configuration
    STRIPE_PRICE_ID_PRO = os.environ.get('STRIPE_PRICE_ID_PRO')
    STRIPE_PRICE_ID_PREMIUM = os.environ.get('STRIPE_PRICE_ID_PREMIUM')
    
    # Error Tracking
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    
    # Rate limiting (Redis preferred for production)
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    
    # JavaScript minification in production
    MINIFY_JS = True
    ENV = 'production'
    
    # Ensure critical settings are set
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to syslog on production
        import logging
        from logging.handlers import SysLogHandler
        
        if not app.debug and not app.testing:
            if app.config.get('LOG_TO_STDOUT'):
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = logging.FileHandler('logs/cibozer.log')
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Cibozer startup')