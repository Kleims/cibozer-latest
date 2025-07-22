"""Shared test fixtures to reduce code duplication across test modules"""

import pytest
from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from models import db, User, PricingPlan
import auth


def create_test_app():
    """Create a Flask test app with common configuration"""
    import os
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth.auth_bp)
    
    return app


@pytest.fixture
def app():
    """Create and configure test app"""
    app = create_test_app()
    
    with app.app_context():
        db.create_all()
        # Seed pricing plans if needed
        if PricingPlan.query.count() == 0:
            PricingPlan.seed_default_plans()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a standard test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            password_hash=generate_password_hash('testpass123'),
            credits_balance=10,
            subscription_tier='free'
        )
        db.session.add(user)
        db.session.commit()
        # Return just the ID to avoid detached instance issues
        return user.id


@pytest.fixture
def premium_user(app):
    """Create a premium test user"""
    with app.app_context():
        user = User(
            email='premium@example.com',
            password_hash=generate_password_hash('testpass123'),
            credits_balance=100,
            subscription_tier='pro'
        )
        db.session.add(user)
        db.session.commit()
        # Return just the ID to avoid detached instance issues
        return user.id


@pytest.fixture
def admin_user(app):
    """Create an admin test user"""
    with app.app_context():
        user = User(
            email='admin@example.com',
            password_hash=generate_password_hash('adminpass123'),
            credits_balance=1000,
            subscription_tier='pro',
            is_admin=True
        )
        db.session.add(user)
        db.session.commit()
        # Return just the ID to avoid detached instance issues
        return user.id