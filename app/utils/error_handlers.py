"""Comprehensive error handling"""
import traceback
from flask import jsonify, render_template, request
from app.extensions import db
from app.services.monitoring_service import monitoring_service

def register_error_handlers(app):
    """Register all error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request'}), 400
        return render_template('errors/400.html'), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized'}), 401
        return render_template('errors/401.html'), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(429)
    def too_many_requests(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Too many requests. Please try again later.'}), 429
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        
        # Log the actual error internally
        app.logger.error(f'Internal error: {str(error)}')
        tb = traceback.format_exc()
        if app.debug:
            app.logger.error(f'Traceback: {tb}')
            # In debug mode, show the actual error
            return f'<pre>ERROR: {str(error)}\n\n{tb}</pre>', 500
        
        # Log to monitoring service
        monitoring_service.log_error('internal_server_error', {
            'error': str(error),
            'path': request.path,
            'method': request.method
        })
        
        # Don't expose internal details to users
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        
        # Log unexpected errors
        app.logger.error(f'Unexpected error: {type(error).__name__}: {str(error)}')
        if app.debug:
            tb = traceback.format_exc()
            app.logger.error(f'Traceback: {tb}')
        
        # Log to monitoring service
        monitoring_service.log_error('unexpected_error', {
            'error_type': type(error).__name__,
            'error': str(error),
            'path': request.path
        })
        
        # Generic error response
        if request.path.startswith('/api/'):
            return jsonify({'error': 'An error occurred'}), 500
        return render_template('errors/500.html'), 500
