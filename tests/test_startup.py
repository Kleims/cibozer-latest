"""
Tests for application startup and imports
"""

import pytest
import sys
import os
from unittest.mock import patch


class TestStartup:
    """Test application startup components"""
    
    def test_flask_import(self):
        """Test that Flask can be imported"""
        import flask
        assert flask is not None
        assert hasattr(flask, 'Flask')
    
    def test_create_app_import(self):
        """Test that create_app can be imported"""
        from app import create_app
        assert create_app is not None
        assert callable(create_app)
    
    def test_app_creation(self):
        """Test that app can be created"""
        from app import create_app
        app = create_app()
        assert app is not None
        assert app.name == 'app'
    
    def test_database_import(self):
        """Test that database models can be imported"""
        from models import db, User
        assert db is not None
        assert User is not None
    
    def test_blueprint_imports(self):
        """Test that blueprints can be imported"""
        try:
            from app.routes.admin import admin_bp
            assert admin_bp is not None
        except ImportError:
            # Try alternative import path
            import admin
            assert hasattr(admin, 'admin_bp')
        
        try:
            from app.routes.auth import auth_bp
            assert auth_bp is not None
        except ImportError:
            # Try alternative import path  
            import auth
            assert hasattr(auth, 'auth_bp')
    
    def test_app_configuration(self):
        """Test app configuration"""
        from app import create_app
        app = create_app()
        
        # Check essential config values exist
        assert 'SECRET_KEY' in app.config
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
    
    def test_environment_setup(self):
        """Test environment variable loading"""
        with patch.dict(os.environ, {'FLASK_ENV': 'testing'}):
            from app import create_app
            app = create_app()
            assert app.config.get('TESTING') is True