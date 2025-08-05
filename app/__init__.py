"""Application factory for Cibozer."""
import os
import logging
import logging.handlers
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
    
    # Register security headers and middleware
    register_security_headers(app)
    register_security_middleware(app)
    
    # Register CLI commands
    register_commands(app)
    
    # Create necessary directories
    create_directories(app)
    
    # Initialize monitoring and tracing
    initialize_monitoring_tracing(app)
    
    # Register shutdown handlers
    register_shutdown_handlers(app)
    
    return app


def register_blueprints(app):
    """Register application blueprints."""
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.payment import payments_bp as payment_bp
    from app.routes.share import share_bp
    from app.routes.api import api_bp
    from app.routes.monitoring import monitoring_bp
    from app.routes.analytics import analytics_bp
    from app.routes.tracing import tracing_bp
    from app.routes.logs import logs_bp
    from app.routes.sla import sla_bp
    from app.routes.debug_setup import debug_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(share_bp, url_prefix='/share')
    app.register_blueprint(api_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(tracing_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(sla_bp)
    app.register_blueprint(debug_bp)
    
    app.logger.info('Blueprints registered successfully')


def register_error_handlers(app):
    """Register error handlers."""
    from app.utils.error_handlers import register_error_handlers as register_all_handlers
    register_all_handlers(app)


def register_security_headers(app):
    """Register security headers."""
    from app.utils.security_headers import configure_security_headers
    configure_security_headers(app)


def register_security_middleware(app):
    """Register security middleware."""
    from app.middleware.security import SecurityMiddleware
    security_middleware = SecurityMiddleware(app)


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


def initialize_monitoring_tracing(app):
    """Initialize monitoring, tracing, logging and SLA services."""
    from datetime import datetime
    from app.services.monitoring_service import get_monitoring_service
    from app.services.tracing_service import init_tracing
    from app.services.logging_service import init_logging_service
    from app.services.sla_service import get_sla_service
    
    # Set app start time for uptime calculation
    app.start_time = datetime.utcnow()
    
    # Initialize logging service first (since other services may use it)
    init_logging_service(app)
    app.logger.info('Logging service initialized')
    
    # Initialize monitoring service
    monitoring = get_monitoring_service()
    app.logger.info('Monitoring service initialized')
    
    # Initialize SLA service
    sla_service = get_sla_service()
    app.logger.info('SLA service initialized')
    
    # Initialize distributed tracing
    init_tracing(app)
    app.logger.info('Distributed tracing initialized')
    
    # Background monitoring tasks will be started automatically
    app.logger.info('Monitoring services initialized and ready')


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


def register_shutdown_handlers(app):
    """Register proper shutdown handlers for graceful termination."""
    import signal
    import atexit
    
    def cleanup_handler():
        """Cleanup resources on shutdown."""
        try:
            # Close database connections
            if hasattr(db, 'session'):
                db.session.close()
                app.logger.info('Database connections closed')
            
            # Close file handlers
            for handler in app.logger.handlers:
                if hasattr(handler, 'close'):
                    handler.close()
            
            app.logger.info('Application shutdown complete')
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def signal_handler(signum, frame):
        """Handle termination signals."""
        app.logger.info(f'Received signal {signum}, shutting down gracefully...')
        cleanup_handler()
        exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Register exit handler
    atexit.register(cleanup_handler)