"""Tests for app_config.py"""

import pytest
import os
from unittest.mock import patch

from app_config import (
    get_app_config, reload_app_config, validate_config,
    FlaskConfig, DatabaseConfig, SecurityConfig, 
    PaymentConfig, AdminConfig, EmailConfig, LoggingConfig,
    VideoConfig, AppConfig
)


class TestAppConfig:
    """Test application configuration"""
    
    def test_get_app_config(self):
        """Test getting app configuration"""
        config = get_app_config()
        assert config is not None
        assert isinstance(config, AppConfig)
        assert config.APP_NAME == "Cibozer"
        assert config.APP_VERSION == "1.0.0"
    
    def test_reload_app_config(self):
        """Test reloading configuration"""
        config1 = get_app_config()
        config2 = reload_app_config()
        # Should get new instance
        assert config2 is not config1
        assert isinstance(config2, AppConfig)
    
    def test_validate_config(self):
        """Test configuration validation"""
        result = validate_config()
        assert isinstance(result, bool)
    
    def test_flask_config(self):
        """Test Flask configuration"""
        config = get_app_config()
        assert hasattr(config.flask, 'SECRET_KEY')
        assert hasattr(config.flask, 'DEBUG')
        assert hasattr(config.flask, 'SESSION_COOKIE_SECURE')
    
    def test_database_config(self):
        """Test database configuration"""
        config = get_app_config()
        assert hasattr(config.database, 'DATABASE_URL')
        assert hasattr(config.database, 'SQLALCHEMY_DATABASE_URI')
        assert config.database.SQLALCHEMY_TRACK_MODIFICATIONS == False
    
    def test_security_config(self):
        """Test security configuration"""
        config = get_app_config()
        assert config.security.PASSWORD_MIN_LENGTH == 8
        assert config.security.PASSWORD_REQUIRE_UPPER == True
        assert config.security.MAX_CONTENT_LENGTH == 16 * 1024 * 1024
    
    def test_payment_config(self):
        """Test payment configuration"""
        config = get_app_config()
        assert config.payment.PRO_PRICE == 9.99
        assert config.payment.PREMIUM_PRICE == 19.99
        assert config.payment.PRO_CREDITS == 100
        assert config.payment.PREMIUM_CREDITS == 500
    
    def test_video_config(self):
        """Test video configuration"""
        config = get_app_config()
        assert config.video.WIDTH == 1920
        assert config.video.HEIGHT == 1080
        assert config.video.FPS == 30
        assert config.video.QUALITY == "1080p"
    
    def test_to_flask_config(self):
        """Test conversion to Flask configuration dictionary"""
        config = get_app_config()
        flask_config = config.to_flask_config()
        
        assert isinstance(flask_config, dict)
        assert 'SECRET_KEY' in flask_config
        assert 'DEBUG' in flask_config
        assert 'SQLALCHEMY_DATABASE_URI' in flask_config
        assert 'MAX_CONTENT_LENGTH' in flask_config
    
    @patch.dict(os.environ, {'FLASK_DEBUG': 'True'})
    def test_environment_override(self):
        """Test that environment variables override defaults"""
        config = reload_app_config()
        assert config.flask.DEBUG == True
    
    def test_path_creation(self):
        """Test that required directories are created"""
        config = reload_app_config()
        # Check that upload folders are set
        assert config.UPLOAD_FOLDER is not None
        assert config.VIDEO_FOLDER is not None
        assert config.PDF_FOLDER is not None
        assert config.SAVED_PLANS_FOLDER is not None