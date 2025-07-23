"""Application factory for Cibozer."""
import os
import logging
from flask import Flask, render_template
from flask_migrate import Migrate

from config import get_config
from app.extensions import init_extensions, db


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Load configuration
    config_class = get_config() if config_name is None else config_name
    app.config.from_object(config_class)
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # Configure logging
    configure_logging(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register security headers
    register_security_headers(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Create necessary directories
    create_directories(app)
    
    return app


def register_blueprints(app):
    """Register application blueprints."""
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payments_bp as payment_bp
    from app.routes.share import share_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(share_bp, url_prefix='/share')
    app.register_blueprint(api_bp)
    
    app.logger.info('Blueprints registered successfully')


def register_error_handlers(app):
    """Register error handlers."""
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403


def register_security_headers(app):
    """Register security headers."""
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net"
        return response


def configure_logging(app):
    """Configure application logging."""
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/cibozer.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Cibozer startup')


def create_directories(app):
    """Create necessary directories."""
    directories = [
        'logs',
        'static/uploads',
        'static/videos',
        'static/pdfs',
        'static/temp'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            app.logger.info(f'Created directory: {directory}')


def register_commands(app):
    """Register CLI commands."""
    @app.cli.command()
    def init_db():
        """Initialize the database."""
        db.create_all()
        print('Database initialized!')
    
    @app.cli.command()
    def seed_db():
        """Seed the database with initial data."""
        from app.utils.seed import seed_database
        seed_database()
        print('Database seeded!')
    
    @app.cli.command()
    def create_admin():
        """Create an admin user."""
        from app.models import User
        email = input('Enter admin email: ')
        password = input('Enter admin password: ')
        
        admin = User(
            email=email,
            subscription_tier='premium',
            subscription_status='active',
            email_verified=True,
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f'Admin user {email} created successfully!')