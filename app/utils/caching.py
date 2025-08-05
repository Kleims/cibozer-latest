"""Caching configuration and utilities"""
from functools import wraps
from flask import request, current_app
from app.extensions import cache
import hashlib
import json

def make_cache_key(*args, **kwargs):
    """Generate cache key from function arguments"""
    # Get function name from the wrapped function
    func_name = request.endpoint if hasattr(request, 'endpoint') else 'unknown'
    
    # Create a unique key based on function name and arguments
    key_parts = [func_name]
    
    # Add args
    for arg in args:
        if isinstance(arg, (dict, list)):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(arg))
    
    # Add kwargs
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (dict, list)):
            key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
        else:
            key_parts.append(f"{k}:{v}")
    
    # Add user context if authenticated
    from flask_login import current_user
    if current_user.is_authenticated:
        key_parts.append(f"user:{current_user.id}")
    
    # Create hash of the key
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached_route(timeout=300):
    """Cache route responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Don't cache POST requests
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Generate cache key
            cache_key = make_cache_key(*args, **kwargs)
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Generate response
            response = f(*args, **kwargs)
            
            # Cache successful responses only
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout=timeout)
            
            return response
        
        return decorated_function
    return decorator

def cache_user_data(timeout=600):
    """Cache user-specific data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            
            if not current_user.is_authenticated:
                return f(*args, **kwargs)
            
            # Create user-specific cache key
            cache_key = f"user_data:{current_user.id}:{f.__name__}"
            
            # Try cache first
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Generate data
            result = f(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator

def invalidate_user_cache(user_id):
    """Invalidate all cache entries for a user"""
    # This is a simple implementation - in production, use cache tags
    cache_keys = [
        f"user_data:{user_id}:*",
        f"meal_plans:{user_id}:*",
        f"user_status:{user_id}"
    ]
    
    for pattern in cache_keys:
        # Note: This requires cache backend that supports pattern deletion
        try:
            cache.delete_many(pattern)
        except:
            pass

def warm_cache():
    """Pre-warm cache with common data"""
    from app.models import User, SavedMealPlan
    from flask import current_app
    
    current_app.logger.info("Starting cache warming...")
    
    # Cache commonly accessed data
    try:
        # Cache user count
        user_count = User.query.count()
        cache.set('stats:user_count', user_count, timeout=3600)
        
        # Cache recent public meal plans
        public_plans = SavedMealPlan.query.filter_by(is_public=True)\
            .order_by(SavedMealPlan.created_at.desc()).limit(10).all()
        
        public_plan_data = [{
            'id': plan.id,
            'name': plan.name,
            'diet_type': plan.diet_type,
            'total_calories': plan.total_calories
        } for plan in public_plans]
        
        cache.set('public:recent_plans', public_plan_data, timeout=1800)
        
        current_app.logger.info(f"Cache warmed: {user_count} users, {len(public_plans)} public plans")
        
    except Exception as e:
        current_app.logger.error(f"Cache warming failed: {e}")


def get_cache_stats():
    """Get cache performance statistics"""
    try:
        # This would need to be implemented based on the cache backend
        return {
            'cache_type': cache.cache._cache.__class__.__name__,
            'status': 'active'
        }
    except:
        return {'status': 'unknown'}

# Cache configuration for different environments
def configure_caching(app):
    """Configure caching based on environment"""
    if app.config.get('ENV') == 'production':
        # Use Redis in production
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CACHE_REDIS_URL'] = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
        app.config['CACHE_KEY_PREFIX'] = 'cibozer:'
    else:
        # Use simple cache in development
        app.config['CACHE_TYPE'] = 'SimpleCache'
        app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    
    # Configure cache key generation
    app.config['CACHE_KEY_PREFIX'] = 'cibozer:'