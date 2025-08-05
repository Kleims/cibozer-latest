"""Enhanced rate limiting configuration"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def get_user_id():
    """Get user ID for authenticated rate limiting"""
    from flask_login import current_user
    if current_user.is_authenticated:
        return f"user:{current_user.id}"
    return get_remote_address()

def configure_rate_limiting(app):
    """Configure rate limiting with different tiers"""
    
    limiter = Limiter(
        app,
        key_func=get_user_id,
        default_limits=["1000 per day", "100 per hour"],
        storage_uri="redis://localhost:6379" if app.config.get('ENV') == 'production' else "memory://"
    )
    
    # Define rate limit decorators for different endpoints
    rate_limits = {
        'api_strict': limiter.limit("5 per minute"),
        'api_normal': limiter.limit("30 per minute"),
        'api_generous': limiter.limit("100 per minute"),
        'auth_strict': limiter.limit("5 per minute"),
        'auth_normal': limiter.limit("10 per minute"),
    }
    
    return limiter, rate_limits

def check_rate_limit_headers(response):
    """Add rate limit headers to responses"""
    # This would be added as an after_request handler
    # X-RateLimit-Limit: the rate limit ceiling for that request
    # X-RateLimit-Remaining: the number of requests left for the time window
    # X-RateLimit-Reset: the remaining window before the rate limit resets in UTC epoch seconds
    return response
