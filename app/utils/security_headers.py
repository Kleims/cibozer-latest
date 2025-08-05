"""Comprehensive security headers"""

def add_security_headers(response):
    """Add security headers to all responses"""
    
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Content Security Policy
    csp = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://js.stripe.com",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
        "font-src": "'self' https://fonts.gstatic.com",
        "img-src": "'self' data: https: blob:",
        "connect-src": "'self' https://api.stripe.com",
        "frame-src": "https://js.stripe.com https://hooks.stripe.com",
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
        "frame-ancestors": "'none'",
        "upgrade-insecure-requests": ""
    }
    
    csp_string = "; ".join(f"{key} {value}" for key, value in csp.items())
    response.headers['Content-Security-Policy'] = csp_string
    
    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Permissions Policy (replaces Feature Policy)
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Additional headers
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['Expect-CT'] = 'max-age=86400, enforce'
    
    # Cross-Origin policies (configured to not break functionality)
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    response.headers['Cross-Origin-Resource-Policy'] = 'cross-origin'
    
    # Remove server header for security
    response.headers.pop('Server', None)
    
    # Cache control for sensitive pages (admin, auth, etc.)
    from flask import request
    sensitive_paths = ['/admin', '/auth', '/api', '/payment']
    if (response.headers.get('Content-Type', '').startswith('text/html') and 
        any(request.path.startswith(path) for path in sensitive_paths)):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    return response

def configure_security_headers(app):
    """Configure security headers for the application"""
    
    @app.after_request
    def set_security_headers(response):
        return add_security_headers(response)
    
    return app
