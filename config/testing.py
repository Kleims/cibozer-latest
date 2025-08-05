"""Testing configuration."""
from .default import Config

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}  # Override to remove pool options for SQLite
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-for-unit-tests'
    MAIL_SUPPRESS_SEND = True
    RATELIMIT_ENABLED = False