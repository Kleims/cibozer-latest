"""
Centralized configuration management for Cibozer Flask application
Handles all app settings, security, database, and service configurations
"""

# Standard library imports
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

# Third-party imports
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def _get_required_secret_key():
    """Get SECRET_KEY or raise error in production"""
    # First try to get from environment variable
    env_key = os.getenv('SECRET_KEY')
    if env_key:
        return env_key
    
    # Check if we're in production
    is_production = (os.getenv('FLASK_ENV') == 'production' or 
                    not os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
    
    if is_production:
        raise ValueError(
            "CRITICAL: SECRET_KEY environment variable is required in production!\n"
            "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
            "Then set it in your environment: export SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')"
        )
    
    # Only generate a key for development
    generated_key = secrets.token_urlsafe(32)
    print("[WARNING] Using generated SECRET_KEY for development only - NOT for production!")
    return generated_key

@dataclass
class FlaskConfig:
    """Flask-specific configuration"""
    SECRET_KEY: str = field(default_factory=lambda: os.getenv('SECRET_KEY') or _get_required_secret_key())
    DEBUG: bool = field(default_factory=lambda: os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
    TESTING: bool = False
    
    # Session
    SESSION_COOKIE_SECURE: bool = field(default_factory=lambda: os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true')
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=7)
    
    # CSRF
    WTF_CSRF_ENABLED: bool = True
    WTF_CSRF_TIME_LIMIT: Optional[int] = None

@dataclass
class DatabaseConfig:
    """Database configuration"""
    DATABASE_URL: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///instance/cibozer.db'))
    SQLALCHEMY_DATABASE_URI: str = field(init=False)
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: Dict[str, Any] = field(default_factory=lambda: {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    })
    
    def __post_init__(self):
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL

@dataclass
class SecurityConfig:
    """Security-related configuration"""
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = field(default_factory=lambda: os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true')
    RATE_LIMIT_DEFAULT: str = "100 per minute"
    RATE_LIMIT_STORAGE_URL: str = field(default_factory=lambda: os.getenv('RATE_LIMIT_STORAGE_URL', 'memory://'))
    
    # Password requirements
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPER: bool = True
    PASSWORD_REQUIRE_LOWER: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Security headers
    SECURITY_HEADERS_ENABLED: bool = True
    ALLOWED_HOSTS: List[str] = field(default_factory=lambda: os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,cibozer.com').split(','))
    
    # File upload
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: List[str] = field(default_factory=lambda: ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'pdf', 'json'])

@dataclass
class PaymentConfig:
    """Payment processing configuration"""
    STRIPE_ENABLED: bool = field(default_factory=lambda: bool(os.getenv('STRIPE_SECRET_KEY')))
    STRIPE_SECRET_KEY: Optional[str] = field(default_factory=lambda: os.getenv('STRIPE_SECRET_KEY'))
    STRIPE_PUBLISHABLE_KEY: Optional[str] = field(default_factory=lambda: os.getenv('STRIPE_PUBLISHABLE_KEY'))
    STRIPE_WEBHOOK_SECRET: Optional[str] = field(default_factory=lambda: os.getenv('STRIPE_WEBHOOK_SECRET'))
    STRIPE_PRICE_ID_PRO: Optional[str] = field(default_factory=lambda: os.getenv('STRIPE_PRICE_ID_PRO'))
    STRIPE_PRICE_ID_PREMIUM: Optional[str] = field(default_factory=lambda: os.getenv('STRIPE_PRICE_ID_PREMIUM'))
    
    # Pricing
    PRO_PRICE: float = 9.99
    PREMIUM_PRICE: float = 19.99
    PRO_CREDITS: int = 100
    PREMIUM_CREDITS: int = 500

@dataclass
class AdminConfig:
    """Admin panel configuration"""
    ADMIN_ENABLED: bool = field(default_factory=lambda: bool(os.getenv('ADMIN_PASSWORD')))
    ADMIN_EMAIL: Optional[str] = field(default_factory=lambda: os.getenv('ADMIN_EMAIL', 'admin@cibozer.com'))
    ADMIN_PASSWORD: Optional[str] = field(default_factory=lambda: os.getenv('ADMIN_PASSWORD'))
    ADMIN_SESSION_LIFETIME: timedelta = timedelta(hours=2)

@dataclass
class EmailConfig:
    """Email configuration"""
    MAIL_ENABLED: bool = field(default_factory=lambda: bool(os.getenv('MAIL_SERVER')))
    MAIL_SERVER: Optional[str] = field(default_factory=lambda: os.getenv('MAIL_SERVER'))
    MAIL_PORT: int = field(default_factory=lambda: int(os.getenv('MAIL_PORT', '587')))
    MAIL_USE_TLS: bool = field(default_factory=lambda: os.getenv('MAIL_USE_TLS', 'True').lower() == 'true')
    MAIL_USERNAME: Optional[str] = field(default_factory=lambda: os.getenv('MAIL_USERNAME'))
    MAIL_PASSWORD: Optional[str] = field(default_factory=lambda: os.getenv('MAIL_PASSWORD'))
    MAIL_DEFAULT_SENDER: Optional[str] = field(default_factory=lambda: os.getenv('MAIL_DEFAULT_SENDER', 'noreply@cibozer.com'))

@dataclass
class LoggingConfig:
    """Logging configuration"""
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_TO_FILE: bool = field(default_factory=lambda: os.getenv('LOG_TO_FILE', 'True').lower() == 'true')
    LOG_FILE_PATH: str = 'logs/app.log'
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT: int = 5

@dataclass
class VideoConfig:
    """Video generation configuration"""
    # Video Settings
    WIDTH: int = field(default_factory=lambda: int(os.getenv('CIBOZER_VIDEO_WIDTH', '1920')))
    HEIGHT: int = field(default_factory=lambda: int(os.getenv('CIBOZER_VIDEO_HEIGHT', '1080')))
    FPS: int = field(default_factory=lambda: int(os.getenv('CIBOZER_VIDEO_FPS', '30')))
    QUALITY: str = field(default_factory=lambda: os.getenv('CIBOZER_VIDEO_QUALITY', '1080p'))
    
    # Output Settings
    OUTPUT_PATH: str = field(default_factory=lambda: os.getenv('CIBOZER_OUTPUT_PATH', './cibozer_output'))
    GENERATE_SHORTS: bool = field(default_factory=lambda: os.getenv('CIBOZER_GENERATE_SHORTS', 'true').lower() == 'true')
    GENERATE_METADATA: bool = field(default_factory=lambda: os.getenv('CIBOZER_GENERATE_METADATA', 'true').lower() == 'true')
    SAVE_MEAL_PLANS: bool = field(default_factory=lambda: os.getenv('CIBOZER_SAVE_MEAL_PLANS', 'true').lower() == 'true')
    
    # Font Settings
    FONT_SIZE_SCALE: float = 1.0
    FONT_FAMILY_PREFERENCE: str = "arial"
    
    # Performance Settings
    MAX_BATCH_SIZE: int = 50
    ENABLE_CACHING: bool = True
    PARALLEL_PROCESSING: bool = True

@dataclass
class AppConfig:
    """Main application configuration combining all sections"""
    # Sub-configurations
    flask: FlaskConfig = field(default_factory=FlaskConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    payment: PaymentConfig = field(default_factory=PaymentConfig)
    admin: AdminConfig = field(default_factory=AdminConfig)
    email: EmailConfig = field(default_factory=EmailConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    
    # App-specific settings
    APP_NAME: str = "Cibozer"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "AI-Powered Meal Planning Platform"
    
    # Paths
    UPLOAD_FOLDER: str = field(default_factory=lambda: os.getenv('UPLOAD_FOLDER', 'uploads'))
    VIDEO_FOLDER: str = field(default_factory=lambda: os.getenv('VIDEO_FOLDER', 'videos'))
    PDF_FOLDER: str = field(default_factory=lambda: os.getenv('PDF_FOLDER', 'pdfs'))
    SAVED_PLANS_FOLDER: str = field(default_factory=lambda: os.getenv('SAVED_PLANS_FOLDER', 'saved_plans'))
    
    # Features
    ENABLE_SOCIAL_UPLOAD: bool = field(default_factory=lambda: os.path.exists('social_credentials.json'))
    ENABLE_VIDEO_GENERATION: bool = True
    ENABLE_PDF_EXPORT: bool = True
    
    # Performance
    REQUEST_TIMEOUT: int = 300  # 5 minutes
    VIDEO_GENERATION_TIMEOUT: int = 600  # 10 minutes
    
    # Meal Optimizer Settings
    MIN_CALORIES: int = 800
    MAX_CALORIES: int = 5000
    WARN_CALORIES_LOW: int = 1200
    WARN_CALORIES_HIGH: int = 3500
    MAX_ITERATIONS: int = 25
    ACCURACY_TARGET: float = 0.95
    CALORIE_TOLERANCE: int = 50
    
    def __post_init__(self):
        """Validate configuration and create necessary directories"""
        self._validate_config()
        self._create_directories()
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate secret key
        if len(self.flask.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        # Validate database URL
        if not self.database.DATABASE_URL:
            raise ValueError("DATABASE_URL is required")
        
        # Validate payment config if enabled
        if self.payment.STRIPE_ENABLED:
            if not all([self.payment.STRIPE_SECRET_KEY, self.payment.STRIPE_PUBLISHABLE_KEY]):
                raise ValueError("Stripe keys are required when payments are enabled")
        
        # Validate admin config if enabled
        if self.admin.ADMIN_ENABLED:
            if not self.admin.ADMIN_PASSWORD:
                raise ValueError("ADMIN_PASSWORD is required when admin is enabled")
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.UPLOAD_FOLDER,
            self.VIDEO_FOLDER,
            self.PDF_FOLDER,
            self.SAVED_PLANS_FOLDER,
            'logs',
            'instance'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def to_flask_config(self) -> Dict[str, Any]:
        """Convert to Flask configuration dictionary"""
        config = {}
        
        # Flask config
        for key, value in self.flask.__dict__.items():
            config[key] = value
        
        # Database config
        for key, value in self.database.__dict__.items():
            config[key] = value
        
        # Other configs as needed
        config['MAX_CONTENT_LENGTH'] = self.security.MAX_CONTENT_LENGTH
        
        return config
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for Python logging module"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': self.logging.LOG_FORMAT
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.logging.LOG_LEVEL,
                    'formatter': 'default'
                }
            },
            'root': {
                'level': self.logging.LOG_LEVEL,
                'handlers': ['console']
            }
        }


# Global configuration instance
_app_config: Optional[AppConfig] = None

def get_app_config() -> AppConfig:
    """Get global application configuration instance (singleton pattern)"""
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config

def reload_app_config() -> AppConfig:
    """Reload application configuration"""
    global _app_config
    _app_config = AppConfig()
    return _app_config

def validate_config() -> bool:
    """Validate the current configuration"""
    try:
        config = get_app_config()
        logging.info(f"Configuration validated successfully for {config.APP_NAME} v{config.APP_VERSION}")
        return True
    except Exception as e:
        logging.error(f"Configuration validation failed: {str(e)}")
        return False

def save_env_template(filename: str = ".env.example") -> None:
    """Save a complete environment template file"""
    template = """# Cibozer Environment Configuration Template
# Copy this file to .env and modify as needed

# Flask Settings
SECRET_KEY=your-secret-key-at-least-32-chars-long
FLASK_DEBUG=False

# Database
DATABASE_URL=sqlite:///instance/cibozer.db
# For PostgreSQL: postgresql://user:password@localhost/cibozer

# Security
RATE_LIMIT_ENABLED=True
RATE_LIMIT_STORAGE_URL=memory://
SESSION_COOKIE_SECURE=True
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Stripe Payment Processing (Optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_PREMIUM=price_...

# Admin Panel (Optional)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-admin-password

# Email Configuration (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=True

# Paths
UPLOAD_FOLDER=uploads
VIDEO_FOLDER=videos
PDF_FOLDER=pdfs
SAVED_PLANS_FOLDER=saved_plans

# Video Configuration (from config.py)
CIBOZER_VIDEO_WIDTH=1920
CIBOZER_VIDEO_HEIGHT=1080
CIBOZER_VIDEO_FPS=30
CIBOZER_VIDEO_QUALITY=1080p
CIBOZER_OUTPUT_PATH=./cibozer_output
CIBOZER_GENERATE_SHORTS=true
CIBOZER_GENERATE_METADATA=true
CIBOZER_SAVE_MEAL_PLANS=true
"""
    
    with open(filename, 'w') as f:
        f.write(template)
    
    print(f"Environment template saved to: {filename}")

if __name__ == "__main__":
    # Generate env template when run directly
    save_env_template()
    
    # Validate and show config
    if validate_config():
        config = get_app_config()
        print(f"\n{config.APP_NAME} Configuration Loaded Successfully")
        print(f"Version: {config.APP_VERSION}")
        print(f"Debug Mode: {config.flask.DEBUG}")
        print(f"Database: {config.database.DATABASE_URL}")
        print(f"Payments: {'Enabled' if config.payment.STRIPE_ENABLED else 'Disabled'}")
        print(f"Admin Panel: {'Enabled' if config.admin.ADMIN_ENABLED else 'Disabled'}")
        print(f"Email: {'Enabled' if config.email.MAIL_ENABLED else 'Disabled'}")