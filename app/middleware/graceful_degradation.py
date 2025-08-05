"""
Graceful degradation middleware for Cibozer
Handles service failures and enables fallback modes
"""

import os
import time
import json
import redis
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import g, jsonify, current_app, request
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise ServiceUnavailableError("Service is currently unavailable")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        self.failure_count = 0
        self.state = 'closed'
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


class ServiceUnavailableError(Exception):
    """Raised when a service is unavailable"""
    pass


class GracefulDegradationMiddleware:
    """Middleware for handling graceful degradation"""
    
    def __init__(self, app=None):
        self.app = app
        self.circuit_breakers = {}
        self.feature_flags = {}
        self.cache_client = None
        self.degraded_mode = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app"""
        self.app = app
        
        # Initialize Redis for feature flags
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Register before_request handler
        app.before_request(self.check_system_health)
        
        # Initialize circuit breakers for services
        self._init_circuit_breakers()
        
        # Load feature flags
        self._load_feature_flags()
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers for external services"""
        services = ['database', 'redis', 'stripe', 'email', 'openai']
        
        for service in services:
            threshold = self.app.config.get(f'{service.upper()}_CIRCUIT_BREAKER_THRESHOLD', 5)
            timeout = self.app.config.get(f'{service.upper()}_CIRCUIT_BREAKER_TIMEOUT', 60)
            self.circuit_breakers[service] = CircuitBreaker(threshold, timeout)
    
    def _load_feature_flags(self):
        """Load feature flags from Redis"""
        try:
            flags = self.redis_client.hgetall('feature_flags')
            self.feature_flags = {k: v == 'true' for k, v in flags.items()}
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
            self.feature_flags = self._default_feature_flags()
    
    def _default_feature_flags(self) -> Dict[str, bool]:
        """Default feature flags for degraded mode"""
        return {
            'meal_generation': True,
            'pdf_export': True,
            'video_generation': False,
            'email_notifications': True,
            'payment_processing': True,
            'social_sharing': False,
            'ai_recommendations': False,
            'analytics': False,
            'read_only_mode': False,
            'cache_only_mode': False
        }
    
    def check_system_health(self):
        """Check system health before each request"""
        g.degraded_features = []
        g.system_health = self._get_system_health()
        
        # Enable degraded mode if needed
        if g.system_health['overall_status'] != 'healthy':
            self._enable_degraded_mode()
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        health = {
            'overall_status': 'healthy',
            'services': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Check each service
        for service, breaker in self.circuit_breakers.items():
            health['services'][service] = {
                'status': 'healthy' if breaker.state == 'closed' else 'unhealthy',
                'circuit_state': breaker.state,
                'failure_count': breaker.failure_count
            }
        
        # Determine overall status
        unhealthy_services = [
            s for s, info in health['services'].items()
            if info['status'] == 'unhealthy'
        ]
        
        if unhealthy_services:
            health['overall_status'] = 'degraded'
            if 'database' in unhealthy_services:
                health['overall_status'] = 'critical'
        
        return health
    
    def _enable_degraded_mode(self):
        """Enable appropriate degraded mode based on failures"""
        health = g.system_health
        
        # Critical: Database failure
        if health['services'].get('database', {}).get('status') == 'unhealthy':
            self._enable_read_only_mode()
            g.degraded_features.extend(['meal_generation', 'user_registration', 'payments'])
        
        # High: Redis failure
        if health['services'].get('redis', {}).get('status') == 'unhealthy':
            self._enable_cache_bypass_mode()
            g.degraded_features.append('rate_limiting')
        
        # Medium: Email service failure
        if health['services'].get('email', {}).get('status') == 'unhealthy':
            self._enable_email_queue_mode()
            g.degraded_features.append('instant_emails')
        
        # Low: AI service failure
        if health['services'].get('openai', {}).get('status') == 'unhealthy':
            self._enable_fallback_meal_generation()
            g.degraded_features.append('ai_meal_generation')
    
    def _enable_read_only_mode(self):
        """Enable read-only mode for database failures"""
        self.feature_flags['read_only_mode'] = True
        logger.warning("Enabled read-only mode due to database issues")
    
    def _enable_cache_bypass_mode(self):
        """Bypass cache for Redis failures"""
        self.feature_flags['cache_only_mode'] = False
        logger.warning("Disabled caching due to Redis issues")
    
    def _enable_email_queue_mode(self):
        """Queue emails for later delivery"""
        self.feature_flags['email_queue_mode'] = True
        logger.warning("Enabled email queue mode due to email service issues")
    
    def _enable_fallback_meal_generation(self):
        """Use fallback meal generation without AI"""
        self.feature_flags['fallback_meal_generation'] = True
        logger.warning("Enabled fallback meal generation due to AI service issues")
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.feature_flags.get(feature, True)
    
    def with_circuit_breaker(self, service: str):
        """Decorator to wrap functions with circuit breaker"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                breaker = self.circuit_breakers.get(service)
                if not breaker:
                    return func(*args, **kwargs)
                
                try:
                    return breaker.call(func, *args, **kwargs)
                except ServiceUnavailableError:
                    logger.error(f"{service} is unavailable")
                    return self._get_fallback_response(service)
            
            return wrapper
        return decorator
    
    def _get_fallback_response(self, service: str) -> Any:
        """Get fallback response for failed service"""
        fallbacks = {
            'stripe': {'error': 'Payment processing temporarily unavailable'},
            'email': {'message': 'Email will be sent when service is restored'},
            'openai': {'message': 'Using standard meal recommendations'},
        }
        
        return jsonify(fallbacks.get(service, {'error': f'{service} temporarily unavailable'})), 503
    
    def degrade_gracefully(self, primary_func: Callable, fallback_func: Callable):
        """Execute primary function with fallback on failure"""
        @wraps(primary_func)
        def wrapper(*args, **kwargs):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Primary function failed: {e}, using fallback")
                return fallback_func(*args, **kwargs)
        
        return wrapper


# Initialize middleware
graceful_degradation = GracefulDegradationMiddleware()


# Decorators for common patterns
def requires_feature(feature: str):
    """Decorator to check if feature is enabled"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not graceful_degradation.is_feature_enabled(feature):
                return jsonify({
                    'error': f'{feature} is temporarily disabled',
                    'degraded': True
                }), 503
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """Decorator to provide fallback functionality"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Function {func.__name__} failed: {e}")
                return fallback_func(*args, **kwargs)
        return wrapper
    return decorator


def cache_on_failure(timeout: int = 3600):
    """Cache successful responses to use during failures"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"fallback:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            try:
                result = func(*args, **kwargs)
                # Cache successful result
                if graceful_degradation.redis_client:
                    graceful_degradation.redis_client.setex(
                        cache_key, 
                        timeout, 
                        json.dumps(result)
                    )
                return result
            except Exception as e:
                logger.error(f"Function failed, checking cache: {e}")
                # Try to get cached result
                if graceful_degradation.redis_client:
                    cached = graceful_degradation.redis_client.get(cache_key)
                    if cached:
                        logger.info("Returning cached result")
                        return json.loads(cached)
                raise
        
        return wrapper
    return decorator


# Health check endpoint
def get_degradation_status():
    """Get current degradation status"""
    return {
        'degraded_mode': graceful_degradation.degraded_mode,
        'degraded_features': getattr(g, 'degraded_features', []),
        'feature_flags': graceful_degradation.feature_flags,
        'circuit_breakers': {
            service: {
                'state': breaker.state,
                'failure_count': breaker.failure_count
            }
            for service, breaker in graceful_degradation.circuit_breakers.items()
        },
        'system_health': getattr(g, 'system_health', {})
    }