#!/usr/bin/env python3
"""
JavaScript Loader Configuration System
Automatically switches between development and production JavaScript loading
"""

import os
from pathlib import Path

class JSLoaderConfig:
    def __init__(self, app_config=None):
        self.is_production = self._detect_production_environment(app_config)
        self.base_template = 'base_production.html' if self.is_production else 'base.html'
        
    def _detect_production_environment(self, app_config):
        """Detect if we're in production environment"""
        # Check environment variables
        if os.environ.get('FLASK_ENV') == 'production':
            return True
        if os.environ.get('ENVIRONMENT') == 'production':
            return True
        if os.environ.get('NODE_ENV') == 'production':
            return True
            
        # Check app config if provided
        if app_config and hasattr(app_config, 'DEBUG') and not app_config.DEBUG:
            return True
            
        # Check for production indicators
        if os.environ.get('PORT'):  # Common in production deployments
            return True
            
        return False
    
    def get_js_files(self):
        """Get the appropriate JavaScript files for current environment"""
        if self.is_production:
            return {
                'bundle': 'js/dist/cibozer.min.js',
                'additional': []  # Add any additional production files here
            }
        else:
            return {
                'bundle': None,  # No bundle in development
                'individual': [
                    'js/error-handling.js',
                    'js/touch-gestures.js', 
                    'js/keyboard-navigation.js',
                    'js/cibozer-clean.js'
                ]
            }
    
    def get_base_template(self):
        """Get the appropriate base template"""
        return self.base_template
    
    def render_js_includes(self, url_for_func):
        """Render the appropriate JavaScript includes"""
        js_config = self.get_js_files()
        
        if self.is_production:
            # Production: Use minified bundle
            return f'<script src="{url_for_func("static", filename=js_config["bundle"])}"></script>'
        else:
            # Development: Use individual files with cache busting
            includes = []
            for js_file in js_config['individual']:
                cache_bust = f'?v={{{{ range(1000, 9999) | random }}}}'
                includes.append(f'<script src="{url_for_func("static", filename=js_file)}{cache_bust}"></script>')
            return '\n    '.join(includes)

def configure_js_loading(app):
    """Configure JavaScript loading for Flask app"""
    js_config = JSLoaderConfig(app.config)
    
    # Add template global for JavaScript loading
    @app.template_global()
    def get_js_config():
        return js_config
    
    # Add context processor for JavaScript files
    @app.context_processor
    def inject_js_config():
        return {
            'js_config': js_config,
            'is_production': js_config.is_production
        }
    
    return js_config

# Usage example for templates:
TEMPLATE_USAGE = """
<!-- In your template, use this instead of hardcoded script tags: -->
{% if is_production %}
    <!-- Production: Single minified bundle -->
    <script src="{{ url_for('static', filename='js/dist/cibozer.min.js') }}"></script>
{% else %}
    <!-- Development: Individual files with cache busting -->
    <script src="{{ url_for('static', filename='js/error-handling.js') }}?v={{ range(1000, 9999) | random }}"></script>
    <script src="{{ url_for('static', filename='js/touch-gestures.js') }}?v={{ range(1000, 9999) | random }}"></script>
    <script src="{{ url_for('static', filename='js/keyboard-navigation.js') }}?v={{ range(1000, 9999) | random }}"></script>
    <script src="{{ url_for('static', filename='js/cibozer-clean.js') }}"></script>
{% endif %}
"""

if __name__ == '__main__':
    # Test the configuration
    config = JSLoaderConfig()
    print(f"Environment: {'Production' if config.is_production else 'Development'}")
    print(f"Base template: {config.get_base_template()}")
    print(f"JS files: {config.get_js_files()}")