"""Configuration module."""
import os
from .default import Config
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])