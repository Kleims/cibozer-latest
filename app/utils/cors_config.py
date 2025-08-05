"""CORS configuration for API security"""
from flask_cors import CORS

def configure_cors(app):
    """Configure CORS with security in mind"""
    
    # Define allowed origins based on environment
    if app.config.get('ENV') == 'production':
        origins = [
            'https://cibozer.com',
            'https://www.cibozer.com',
            'https://app.cibozer.com'
        ]
    else:
        # Development - be more permissive but still secure
        origins = [
            'http://localhost:3000',
            'http://localhost:5000',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5000'
        ]
    
    CORS(app, 
         origins=origins,
         allow_headers=['Content-Type', 'Authorization', 'X-API-Key'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         supports_credentials=True,
         max_age=3600)
    
    return app
