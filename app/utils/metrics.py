"""Application metrics collection and monitoring"""
import time
import psutil
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Info
from flask import request, g
from functools import wraps
import json
from datetime import datetime

# Prometheus metrics
request_count = Counter(
    'cibozer_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'cibozer_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'cibozer_active_users',
    'Number of active users'
)

meal_plans_generated = Counter(
    'cibozer_meal_plans_generated_total',
    'Total meal plans generated',
    ['diet_type', 'days']
)

credits_used = Counter(
    'cibozer_credits_used_total',
    'Total credits consumed'
)

payment_transactions = Counter(
    'cibozer_payment_transactions_total',
    'Total payment transactions',
    ['status', 'plan']
)

error_count = Counter(
    'cibozer_errors_total',
    'Total application errors',
    ['error_type', 'severity']
)

db_query_duration = Histogram(
    'cibozer_db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

cache_hits = Counter(
    'cibozer_cache_hits_total',
    'Cache hit count',
    ['cache_type']
)

cache_misses = Counter(
    'cibozer_cache_misses_total',
    'Cache miss count',
    ['cache_type']
)

# System metrics
cpu_usage = Gauge('cibozer_cpu_usage_percent', 'CPU usage percentage')
memory_usage = Gauge('cibozer_memory_usage_bytes', 'Memory usage in bytes')
disk_usage = Gauge('cibozer_disk_usage_percent', 'Disk usage percentage')

# Application info
app_info = Info('cibozer_app', 'Application information')
app_info.info({
    'version': '1.0.0',
    'environment': 'production'
})

class MetricsCollector:
    """Collect and expose application metrics"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize metrics collection"""
        self.app = app
        
        # Add before/after request handlers
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Add metrics endpoint
        @app.route('/metrics')
        def metrics():
            # Update system metrics
            self.collect_system_metrics()
            
            # Return Prometheus metrics
            return prometheus_client.generate_latest()
    
    def before_request(self):
        """Track request start time"""
        g.start_time = time.time()
    
    def after_request(self, response):
        """Track request metrics"""
        if hasattr(g, 'start_time'):
            # Calculate request duration
            duration = time.time() - g.start_time
            
            # Record metrics
            request_duration.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
            
            request_count.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=response.status_code
            ).inc()
        
        return response
    
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_usage.set(psutil.cpu_percent(interval=1))
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage.set(memory.used)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage.set(disk.percent)
            
        except Exception as e:
            print(f"Failed to collect system metrics: {e}")
    
    @staticmethod
    def track_meal_plan_generated(diet_type, days):
        """Track meal plan generation"""
        meal_plans_generated.labels(
            diet_type=diet_type,
            days=str(days)
        ).inc()
    
    @staticmethod
    def track_credits_used(amount=1):
        """Track credit usage"""
        credits_used.inc(amount)
    
    @staticmethod
    def track_payment(status, plan):
        """Track payment transaction"""
        payment_transactions.labels(
            status=status,
            plan=plan
        ).inc()
    
    @staticmethod
    def track_error(error_type, severity='error'):
        """Track application errors"""
        error_count.labels(
            error_type=error_type,
            severity=severity
        ).inc()
    
    @staticmethod
    def track_db_query(query_type, duration):
        """Track database query performance"""
        db_query_duration.labels(
            query_type=query_type
        ).observe(duration)
    
    @staticmethod
    def track_cache_hit(cache_type='default'):
        """Track cache hit"""
        cache_hits.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def track_cache_miss(cache_type='default'):
        """Track cache miss"""
        cache_misses.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def update_active_users(count):
        """Update active users gauge"""
        active_users.set(count)

# Decorators for metric tracking
def track_performance(metric_name=None):
    """Decorator to track function performance"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Track in custom metrics if needed
                if metric_name:
                    custom_histogram = Histogram(
                        f'cibozer_{metric_name}_duration_seconds',
                        f'Duration of {metric_name}'
                    )
                    custom_histogram.observe(duration)
                
                return result
                
            except Exception as e:
                # Track error
                MetricsCollector.track_error(
                    error_type=type(e).__name__,
                    severity='error'
                )
                raise
        
        return decorated_function
    return decorator

def track_db_operation(operation_type):
    """Decorator to track database operations"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                MetricsCollector.track_db_query(operation_type, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                MetricsCollector.track_db_query(f"{operation_type}_error", duration)
                raise
        
        return decorated_function
    return decorator

class BusinessMetrics:
    """Track business-specific metrics"""
    
    @staticmethod
    def track_user_signup(user_type='free'):
        """Track new user signups"""
        counter = Counter(
            'cibozer_user_signups_total',
            'Total user signups',
            ['user_type']
        )
        counter.labels(user_type=user_type).inc()
    
    @staticmethod
    def track_subscription_change(from_tier, to_tier):
        """Track subscription changes"""
        counter = Counter(
            'cibozer_subscription_changes_total',
            'Subscription tier changes',
            ['from_tier', 'to_tier']
        )
        counter.labels(from_tier=from_tier, to_tier=to_tier).inc()
    
    @staticmethod
    def track_feature_usage(feature_name):
        """Track feature usage"""
        counter = Counter(
            'cibozer_feature_usage_total',
            'Feature usage count',
            ['feature']
        )
        counter.labels(feature=feature_name).inc()
    
    @staticmethod
    def update_revenue_metrics(mrr, arr, paying_users):
        """Update revenue metrics"""
        mrr_gauge = Gauge('cibozer_mrr_dollars', 'Monthly recurring revenue')
        arr_gauge = Gauge('cibozer_arr_dollars', 'Annual recurring revenue')
        paying_users_gauge = Gauge('cibozer_paying_users', 'Number of paying users')
        
        mrr_gauge.set(mrr)
        arr_gauge.set(arr)
        paying_users_gauge.set(paying_users)

# Health check metrics
class HealthMetrics:
    """Application health metrics"""
    
    @staticmethod
    def check_database_health():
        """Check database connectivity"""
        health_gauge = Gauge(
            'cibozer_database_health',
            'Database health status (1=healthy, 0=unhealthy)'
        )
        
        try:
            from app.extensions import db
            db.session.execute('SELECT 1')
            health_gauge.set(1)
            return True
        except:
            health_gauge.set(0)
            return False
    
    @staticmethod
    def check_redis_health():
        """Check Redis connectivity"""
        health_gauge = Gauge(
            'cibozer_redis_health',
            'Redis health status (1=healthy, 0=unhealthy)'
        )
        
        try:
            from app.extensions import cache
            cache.set('health_check', 'ok', timeout=1)
            result = cache.get('health_check')
            if result == 'ok':
                health_gauge.set(1)
                return True
        except:
            pass
        
        health_gauge.set(0)
        return False
    
    @staticmethod
    def check_external_services():
        """Check external service health"""
        services = {
            'stripe': check_stripe_health,
            'email': check_email_health,
            'cdn': check_cdn_health
        }
        
        for service, check_func in services.items():
            gauge = Gauge(
                f'cibozer_{service}_health',
                f'{service.title()} health status'
            )
            
            try:
                if check_func():
                    gauge.set(1)
                else:
                    gauge.set(0)
            except:
                gauge.set(0)

def check_stripe_health():
    """Check Stripe API health"""
    # Implementation would check Stripe API
    return True

def check_email_health():
    """Check email service health"""
    # Implementation would check email service
    return True

def check_cdn_health():
    """Check CDN health"""
    # Implementation would check CDN
    return True

# Custom metric aggregations
class MetricAggregator:
    """Aggregate metrics for dashboards"""
    
    @staticmethod
    def get_dashboard_metrics():
        """Get metrics for monitoring dashboard"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'requests': {
                'total': get_metric_value('cibozer_requests_total'),
                'rate': calculate_rate('cibozer_requests_total', 60),  # per minute
                'errors': get_metric_value('cibozer_errors_total')
            },
            'performance': {
                'p50_latency': get_histogram_percentile('cibozer_request_duration_seconds', 0.5),
                'p95_latency': get_histogram_percentile('cibozer_request_duration_seconds', 0.95),
                'p99_latency': get_histogram_percentile('cibozer_request_duration_seconds', 0.99)
            },
            'business': {
                'meal_plans_today': get_metric_value('cibozer_meal_plans_generated_total', window='24h'),
                'active_users': get_metric_value('cibozer_active_users'),
                'revenue': {
                    'mrr': get_metric_value('cibozer_mrr_dollars'),
                    'paying_users': get_metric_value('cibozer_paying_users')
                }
            },
            'system': {
                'cpu_usage': get_metric_value('cibozer_cpu_usage_percent'),
                'memory_usage': get_metric_value('cibozer_memory_usage_bytes'),
                'disk_usage': get_metric_value('cibozer_disk_usage_percent')
            },
            'health': {
                'database': get_metric_value('cibozer_database_health'),
                'redis': get_metric_value('cibozer_redis_health'),
                'stripe': get_metric_value('cibozer_stripe_health')
            }
        }

def get_metric_value(metric_name, window=None):
    """Get current value of a metric"""
    # Implementation would query Prometheus
    return 0

def calculate_rate(metric_name, seconds):
    """Calculate rate of change"""
    # Implementation would calculate rate
    return 0

def get_histogram_percentile(metric_name, percentile):
    """Get histogram percentile"""
    # Implementation would calculate percentile
    return 0