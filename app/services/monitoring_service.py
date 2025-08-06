"""
Comprehensive Monitoring Service for Cibozer
Implements application monitoring, metrics collection, and observability
"""

import os
import time
# import psutil  # Disabled for production deployment
import json
import traceback
import logging
import uuid
import requests
from datetime import datetime, timezone, timedelta
from functools import wraps
from collections import defaultdict, deque
from threading import Lock
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from flask import request, current_app, g
from app.models import ErrorLog, UsageLog
from app.extensions import db
from sqlalchemy import text


@dataclass
class Metric:
    """Represents a metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}


@dataclass
class Alert:
    """Represents an alert condition"""
    id: str
    name: str
    condition: str
    threshold: float
    severity: str  # critical, warning, info
    channels: List[str]  # email, slack, webhook
    enabled: bool = True
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None


class MetricsCollector:
    """Collects and stores application metrics"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.lock = Lock()
        
    def increment(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        with self.lock:
            self.counters[name] += value
            self._record_metric(name, self.counters[name], tags)
    
    def gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        with self.lock:
            self.gauges[name] = value
            self._record_metric(name, value, tags)
    
    def histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a histogram value"""
        with self.lock:
            self.histograms[name].append(value)
            # Keep only last 1000 values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            self._record_metric(name, value, tags)
    
    def _record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Internal method to record metric"""
        metric = Metric(name, value, datetime.utcnow(), tags or {})
        self.metrics[name].append(metric)
    
    def get_metrics(self, name: str = None, since: datetime = None) -> List[Metric]:
        """Get metrics, optionally filtered by name and time"""
        with self.lock:
            if name:
                metrics = list(self.metrics.get(name, []))
            else:
                metrics = []
                for metric_list in self.metrics.values():
                    metrics.extend(metric_list)
            
            if since:
                metrics = [m for m in metrics if m.timestamp >= since]
            
            return sorted(metrics, key=lambda m: m.timestamp)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get histogram statistics"""
        values = self.histograms.get(name, [])
        if not values:
            return {}
        
        values_sorted = sorted(values)
        length = len(values_sorted)
        
        return {
            'count': length,
            'min': min(values_sorted),
            'max': max(values_sorted),
            'mean': sum(values_sorted) / length,
            'p50': values_sorted[int(length * 0.5)],
            'p95': values_sorted[int(length * 0.95)],
            'p99': values_sorted[int(length * 0.99)]
        }


class PerformanceMonitor:
    """Monitors application performance"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        
    def timing(self, name: str):
        """Decorator to time function execution"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self.metrics.histogram(f'{name}.duration', 
                                         (time.time() - start_time) * 1000)
                    self.metrics.increment(f'{name}.success')
                    return result
                except Exception as e:
                    self.metrics.increment(f'{name}.error')
                    self.metrics.increment(f'{name}.error.{type(e).__name__}')
                    raise
            return wrapper
        return decorator
    
    def track_request(self):
        """Track HTTP request performance"""
        start_time = time.time()
        
        def finalize():
            duration = (time.time() - start_time) * 1000
            self.request_times.append(duration)
            
            tags = {
                'method': request.method,
                'endpoint': request.endpoint or 'unknown',
                'status_code': str(getattr(g, 'status_code', 'unknown'))
            }
            
            self.metrics.histogram('http.request.duration', duration, tags)
            self.metrics.increment('http.requests.total', tags=tags)
            
            # Track slow requests
            if duration > 5000:  # 5 seconds
                self.metrics.increment('http.requests.slow', tags=tags)
                current_app.logger.warning(f"Slow request: {request.method} {request.path} took {duration:.2f}ms")
        
        return finalize


class HealthChecker:
    """Performs health checks on application components"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.checks = {}
        
    def register_check(self, name: str, check_func, timeout: int = 30):
        """Register a health check"""
        self.checks[name] = {
            'func': check_func,
            'timeout': timeout,
            'last_result': None,
            'last_check': None
        }
    
    def run_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_healthy = True
        
        for name, check_config in self.checks.items():
            try:
                start_time = time.time()
                result = check_config['func']()
                duration = (time.time() - start_time) * 1000
                
                check_result = {
                    'healthy': result.get('healthy', True),
                    'message': result.get('message', 'OK'),
                    'details': result.get('details', {}),
                    'duration_ms': duration,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                results[name] = check_result
                check_config['last_result'] = check_result
                check_config['last_check'] = datetime.utcnow()
                
                # Record metrics
                self.metrics.histogram(f'health.{name}.duration', duration)
                self.metrics.gauge(f'health.{name}.status', 1 if check_result['healthy'] else 0)
                
                if not check_result['healthy']:
                    overall_healthy = False
                    
            except Exception as e:
                check_result = {
                    'healthy': False,
                    'message': f'Health check failed: {str(e)}',
                    'details': {'error': type(e).__name__},
                    'duration_ms': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
                results[name] = check_result
                overall_healthy = False
                
                self.metrics.increment(f'health.{name}.errors')
        
        return {
            'healthy': overall_healthy,
            'checks': results,
            'timestamp': datetime.utcnow().isoformat()
        }


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        
    def register_alert(self, alert: Alert):
        """Register an alert rule"""
        self.alerts[alert.id] = alert
        
    def check_alerts(self):
        """Check all alert conditions"""
        current_time = datetime.utcnow()
        
        for alert_id, alert in self.alerts.items():
            if not alert.enabled:
                continue
                
            # Check cooldown
            if (alert.last_triggered and 
                current_time - alert.last_triggered < timedelta(minutes=alert.cooldown_minutes)):
                continue
            
            try:
                if self._evaluate_condition(alert):
                    self._trigger_alert(alert)
                    alert.last_triggered = current_time
                    
            except Exception as e:
                current_app.logger.error(f"Error evaluating alert {alert_id}: {e}")
    
    def _evaluate_condition(self, alert: Alert) -> bool:
        """Evaluate alert condition"""
        # Simple condition evaluation - can be extended
        if alert.condition.startswith('metric:'):
            metric_name = alert.condition.split(':', 1)[1]
            recent_metrics = self.metrics.get_metrics(metric_name, 
                                                    datetime.utcnow() - timedelta(minutes=5))
            if recent_metrics:
                latest_value = recent_metrics[-1].value
                return latest_value > alert.threshold
        
        return False
    
    def _trigger_alert(self, alert: Alert):
        """Trigger an alert"""
        alert_data = {
            'id': alert.id,
            'name': alert.name,
            'severity': alert.severity,
            'condition': alert.condition,
            'threshold': alert.threshold,
            'timestamp': datetime.utcnow().isoformat(),
            'channels': alert.channels
        }
        
        self.alert_history.append(alert_data)
        self.metrics.increment(f'alerts.triggered.{alert.severity}')
        
        # Send notifications
        for channel in alert.channels:
            try:
                self._send_notification(channel, alert_data)
            except Exception as e:
                current_app.logger.error(f"Failed to send alert to {channel}: {e}")
        
        current_app.logger.warning(f"Alert triggered: {alert.name}")
    
    def _send_notification(self, channel: str, alert_data: Dict[str, Any]):
        """Send notification to specified channel"""
        if channel == 'email':
            self._send_email_alert(alert_data)
        elif channel == 'slack':
            self._send_slack_alert(alert_data)
        elif channel.startswith('webhook:'):
            webhook_url = channel.split(':', 1)[1]
            self._send_webhook_alert(webhook_url, alert_data)
    
    def _send_email_alert(self, alert_data: Dict[str, Any]):
        """Send email alert (placeholder)"""
        # Implement email sending logic
        pass
    
    def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """Send Slack alert (placeholder)"""
        # Implement Slack webhook logic
        pass
    
    def _send_webhook_alert(self, url: str, alert_data: Dict[str, Any]):
        """Send webhook alert"""
        try:
            response = requests.post(url, json=alert_data, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            current_app.logger.error(f"Webhook alert failed: {e}")


class ErrorTracker:
    """Tracks and analyzes application errors"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.errors = deque(maxlen=500)
        self.error_counts = defaultdict(int)
        
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an error occurrence"""
        error_data = {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'timestamp': datetime.utcnow().isoformat(),
            'context': context or {}
        }
        
        # Add request context if available
        if request:
            error_data['request'] = {
                'method': request.method,
                'path': request.path,
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr,
                'user_id': getattr(g, 'user_id', None)
            }
        
        self.errors.append(error_data)
        self.error_counts[type(error).__name__] += 1
        
        # Record metrics
        self.metrics.increment('errors.total')
        self.metrics.increment(f'errors.{type(error).__name__}')
        
        # Log error
        current_app.logger.error(f"Error tracked: {type(error).__name__}: {str(error)}")
        
        return error_data
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.errors 
            if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) >= since
        ]
        
        error_types = defaultdict(int)
        for error in recent_errors:
            error_types[error['type']] += 1
        
        return {
            'total_errors': len(recent_errors),
            'error_types': dict(error_types),
            'error_rate': len(recent_errors) / hours if hours > 0 else 0,
            'recent_errors': recent_errors[-10:]  # Last 10 errors
        }


class MonitoringService:
    """Main monitoring service that coordinates all monitoring components"""
    
    def __init__(self, app=None):
        self.app = app
        self.metrics = MetricsCollector()
        self.performance = PerformanceMonitor(self.metrics)
        self.health = HealthChecker(self.metrics)
        self.alerts = AlertManager(self.metrics)
        self.error_tracker = ErrorTracker(self.metrics)  # Enhanced error tracking
        
        self.setup_logging()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring with Flask app"""
        self.app = app
        
        # Register default health checks
        self._register_default_health_checks()
        
        # Register default alerts
        self._register_default_alerts()
        
        # Setup request monitoring
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        
        # Setup error tracking
        app.errorhandler(Exception)(self._handle_error)
        
        # Store service in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['monitoring'] = self
    
    def _before_request(self):
        """Before request handler"""
        g.request_start_time = time.time()
        g.monitoring_finalize = self.performance.track_request()
    
    def _after_request(self, response):
        """After request handler"""
        g.status_code = response.status_code
        
        # Record response metrics
        self.metrics.increment('http.responses.total', 
                             tags={'status_code': str(response.status_code)})
        
        if hasattr(g, 'monitoring_finalize'):
            g.monitoring_finalize()
        
        return response
    
    def _handle_error(self, error):
        """Global error handler"""
        self.error_tracker.track_error(error)
        self.log_error(error)  # Keep existing error logging
        # Re-raise the error to let Flask handle it normally
        raise error
    
    def _register_default_health_checks(self):
        """Register default health checks"""
        
        def database_check():
            """Check database connectivity"""
            try:
                db.session.execute(text('SELECT 1'))
                return {'healthy': True, 'message': 'Database connection OK'}
            except Exception as e:
                return {'healthy': False, 'message': f'Database error: {str(e)}'}
        
        def disk_space_check():
            """Check disk space"""
            try:
                disk_usage = psutil.disk_usage('/')
                free_percent = (disk_usage.free / disk_usage.total) * 100
                
                if free_percent < 10:
                    return {'healthy': False, 'message': f'Low disk space: {free_percent:.1f}% free'}
                elif free_percent < 20:
                    return {'healthy': True, 'message': f'Disk space warning: {free_percent:.1f}% free'}
                else:
                    return {'healthy': True, 'message': f'Disk space OK: {free_percent:.1f}% free'}
            except Exception as e:
                return {'healthy': False, 'message': f'Disk check error: {str(e)}'}
        
        def memory_check():
            """Check memory usage"""
            try:
                memory = psutil.virtual_memory()
                if memory.percent > 90:
                    return {'healthy': False, 'message': f'High memory usage: {memory.percent}%'}
                elif memory.percent > 80:
                    return {'healthy': True, 'message': f'Memory usage warning: {memory.percent}%'}
                else:
                    return {'healthy': True, 'message': f'Memory usage OK: {memory.percent}%'}
            except Exception as e:
                return {'healthy': False, 'message': f'Memory check error: {str(e)}'}
        
        self.health.register_check('database', database_check)
        self.health.register_check('disk_space', disk_space_check)
        self.health.register_check('memory', memory_check)
    
    def _register_default_alerts(self):
        """Register default alert rules"""
        
        # High error rate alert
        error_rate_alert = Alert(
            id='high_error_rate',
            name='High Error Rate',
            condition='metric:errors.total',
            threshold=10,  # More than 10 errors in 5 minutes
            severity='warning',
            channels=['email']
        )
        
        # Slow response time alert
        slow_response_alert = Alert(
            id='slow_response',
            name='Slow Response Time',
            condition='metric:http.requests.slow',
            threshold=5,  # More than 5 slow requests in 5 minutes
            severity='warning',
            channels=['email']
        )
        
        self.alerts.register_alert(error_rate_alert)
        self.alerts.register_alert(slow_response_alert)
    
    def collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.gauge('system.cpu.percent', cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.metrics.gauge('system.memory.percent', memory.percent)
            self.metrics.gauge('system.memory.available', memory.available)
            self.metrics.gauge('system.memory.used', memory.used)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.metrics.gauge('system.disk.percent', (disk.used / disk.total) * 100)
            self.metrics.gauge('system.disk.free', disk.free)
            self.metrics.gauge('system.disk.used', disk.used)
            
            # Process metrics
            process = psutil.Process()
            self.metrics.gauge('process.memory.rss', process.memory_info().rss)
            self.metrics.gauge('process.memory.vms', process.memory_info().vms)
            self.metrics.gauge('process.cpu.percent', process.cpu_percent())
            self.metrics.gauge('process.threads', process.num_threads())
            
        except Exception as e:
            current_app.logger.error(f"Error collecting system metrics: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        
        # Get recent metrics
        request_metrics = self.metrics.get_metrics('http.requests.total', last_hour)
        error_metrics = self.metrics.get_metrics('errors.total', last_hour)
        
        # Calculate rates
        request_count = len(request_metrics)
        error_count = len(error_metrics)
        error_rate = (error_count / max(request_count, 1)) * 100
        
        # Get performance stats
        response_time_stats = self.metrics.get_histogram_stats('http.request.duration')
        
        # Get health status
        health_status = self.health.run_checks()
        
        # Get error summary
        error_summary = self.error_tracker.get_error_summary(24)
        
        return {
            'overview': {
                'requests_last_hour': request_count,
                'errors_last_hour': error_count,
                'error_rate_percent': error_rate,
                'avg_response_time_ms': response_time_stats.get('mean', 0),
                'healthy': health_status['healthy']
            },
            'performance': response_time_stats,
            'health': health_status,
            'errors': error_summary,
            'alerts': list(self.alerts.alert_history)[-10:],  # Last 10 alerts
            'timestamp': now.isoformat()
        }
    
    def setup_logging(self):
        """Configure structured logging."""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure main application logger
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/app.log'),
                logging.StreamHandler()
            ]
        )
        
        # Create specialized loggers
        self.error_logger = logging.getLogger('cibozer.errors')
        self.performance_logger = logging.getLogger('cibozer.performance')
        self.security_logger = logging.getLogger('cibozer.security')
        
        # Add file handlers for each logger
        error_handler = logging.FileHandler('logs/errors.log')
        performance_handler = logging.FileHandler('logs/performance.log')
        security_handler = logging.FileHandler('logs/security.log')
        
        # Set formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        error_handler.setFormatter(detailed_formatter)
        performance_handler.setFormatter(detailed_formatter)
        security_handler.setFormatter(detailed_formatter)
        
        self.error_logger.addHandler(error_handler)
        self.performance_logger.addHandler(performance_handler)
        self.security_logger.addHandler(security_handler)
    
    def log_error(self, error, context=None, user_id=None, severity='error'):
        """Log detailed error information."""
        try:
            error_id = str(uuid.uuid4())
            
            # Prepare error details
            error_details = {
                'error_id': error_id,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'severity': severity,
                'context': context or {},
                'request_info': self._get_request_info(),
                'user_id': user_id,
                'stack_trace': traceback.format_stack()
            }
            
            # Log to file
            self.error_logger.error(json.dumps(error_details, indent=2))
            
            # Store in database
            self._store_error_in_db(error_details)
            
            # Send alert for critical errors
            if severity in ['critical', 'fatal']:
                self._send_error_alert(error_details)
            
            return error_id
            
        except Exception as e:
            # Fallback logging if our error logging fails
            logging.critical(f"Failed to log error: {str(e)}")
    
    def log_performance(self, operation, duration, metadata=None):
        """Log performance metrics."""
        try:
            perf_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'operation': operation,
                'duration_ms': duration * 1000,  # Convert to milliseconds
                'metadata': metadata or {},
                'request_info': self._get_request_info()
            }
            
            self.performance_logger.info(json.dumps(perf_data))
            
            # Store slow operations in database
            if duration > 2.0:  # Slower than 2 seconds
                self._store_slow_operation(perf_data)
                
        except Exception as e:
            logging.error(f"Failed to log performance data: {str(e)}")
    
    def log_security_event(self, event_type, details, user_id=None, severity='warning'):
        """Log security-related events."""
        try:
            security_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': event_type,
                'severity': severity,
                'details': details,
                'user_id': user_id,
                'request_info': self._get_request_info(),
                'session_id': getattr(g, 'session_id', None)
            }
            
            self.security_logger.warning(json.dumps(security_data))
            
            # Store in database for analysis
            self._store_security_event(security_data)
            
        except Exception as e:
            logging.error(f"Failed to log security event: {str(e)}")
    
    def _get_request_info(self):
        """Extract relevant request information."""
        if not request:
            return {}
        
        return {
            'method': request.method,
            'url': request.url,
            'endpoint': request.endpoint,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'referrer': request.headers.get('Referer', ''),
            'content_type': request.content_type,
            'content_length': request.content_length
        }
    
    def _store_error_in_db(self, error_details):
        """Store error in database for analysis."""
        try:
            error_log = ErrorLog(
                error_id=error_details['error_id'],
                error_type=error_details['error_type'],
                error_message=error_details['error_message'][:1000],  # Limit message length
                traceback=error_details['traceback'],
                severity=error_details['severity'],
                context=json.dumps(error_details['context']),
                request_info=json.dumps(error_details['request_info']),
                user_id=error_details.get('user_id'),
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(error_log)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logging.critical(f"Failed to store error in database: {str(e)}")
    
    def _store_slow_operation(self, perf_data):
        """Store slow operation for analysis."""
        try:
            # Create a performance log entry
            usage_log = UsageLog(
                user_id=perf_data.get('user_id'),
                action='slow_operation',
                resource_type='performance',
                metadata={
                    'operation': perf_data['operation'],
                    'duration_ms': perf_data['duration_ms'],
                    'metadata': perf_data['metadata']
                },
                endpoint=perf_data.get('request_info', {}).get('endpoint'),
                method=perf_data.get('request_info', {}).get('method'),
                ip_address=perf_data.get('request_info', {}).get('remote_addr'),
                user_agent=perf_data.get('request_info', {}).get('user_agent')
            )
            
            db.session.add(usage_log)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to store slow operation: {str(e)}")
    
    def _store_security_event(self, security_data):
        """Store security event for analysis."""
        try:
            usage_log = UsageLog(
                user_id=security_data.get('user_id'),
                action='security_event',
                resource_type='security',
                metadata={
                    'event_type': security_data['event_type'],
                    'severity': security_data['severity'],
                    'details': security_data['details']
                },
                endpoint=security_data.get('request_info', {}).get('endpoint'),
                method=security_data.get('request_info', {}).get('method'),
                ip_address=security_data.get('request_info', {}).get('remote_addr'),
                user_agent=security_data.get('request_info', {}).get('user_agent')
            )
            
            db.session.add(usage_log)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to store security event: {str(e)}")
    
    def _send_error_alert(self, error_details):
        """Send alert for critical errors (email, Slack, etc.)."""
        try:
            # In production, you would integrate with services like:
            # - Email alerts
            # - Slack notifications
            # - PagerDuty
            # - Sentry
            
            alert_message = f"""
            CRITICAL ERROR ALERT - Cibozer
            
            Error ID: {error_details['error_id']}
            Type: {error_details['error_type']}
            Message: {error_details['error_message']}
            Time: {error_details['timestamp']}
            User: {error_details.get('user_id', 'Anonymous')}
            URL: {error_details.get('request_info', {}).get('url', 'Unknown')}
            """
            
            # For now, just log the alert
            logging.critical(f"CRITICAL ERROR ALERT: {alert_message}")
            
        except Exception as e:
            logging.error(f"Failed to send error alert: {str(e)}")
    
    def get_error_statistics(self, hours=24):
        """Get error statistics for monitoring dashboard."""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Get error counts by type
            error_stats = db.session.query(
                ErrorLog.error_type,
                db.func.count(ErrorLog.id).label('count')
            ).filter(
                ErrorLog.created_at >= cutoff_time
            ).group_by(ErrorLog.error_type).all()
            
            # Get error counts by severity
            severity_stats = db.session.query(
                ErrorLog.severity,
                db.func.count(ErrorLog.id).label('count')
            ).filter(
                ErrorLog.created_at >= cutoff_time
            ).group_by(ErrorLog.severity).all()
            
            return {
                'period_hours': hours,
                'error_types': {stat.error_type: stat.count for stat in error_stats},
                'severity_levels': {stat.severity: stat.count for stat in severity_stats},
                'total_errors': sum(stat.count for stat in error_stats)
            }
            
        except Exception as e:
            logging.error(f"Failed to get error statistics: {str(e)}")
            return {}

# Global monitoring service instance
monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance"""
    return monitoring_service


# Convenience decorators
def monitor_performance(name: str):
    """Decorator to monitor function performance"""
    return monitoring_service.performance.timing(name)


def track_error(error: Exception, context: Dict[str, Any] = None):
    """Track an error"""
    return monitoring_service.error_tracker.track_error(error, context)


# Legacy decorators for automatic monitoring
def monitor_errors(severity='error'):
    """Decorator to automatically monitor errors in functions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                from flask_login import current_user
                user_id = current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None
                
                error_id = monitoring_service.log_error(
                    error=e,
                    context={
                        'function': f.__name__,
                        'args': str(args)[:500],  # Limit args length
                        'kwargs': str(kwargs)[:500]
                    },
                    user_id=user_id,
                    severity=severity
                )
                
                # Re-raise the exception
                raise e
        return decorated_function
    return decorator

def monitor_performance(operation_name=None):
    """Decorator to automatically monitor function performance."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = datetime.now()
            op_name = operation_name or f.__name__
            
            try:
                result = f(*args, **kwargs)
                
                # Calculate duration
                duration = (datetime.now() - start_time).total_seconds()
                
                # Log performance
                monitoring_service.log_performance(
                    operation=op_name,
                    duration=duration,
                    metadata={
                        'function': f.__name__,
                        'success': True
                    }
                )
                
                return result
                
            except Exception as e:
                # Calculate duration even for failed operations
                duration = (datetime.now() - start_time).total_seconds()
                
                monitoring_service.log_performance(
                    operation=op_name,
                    duration=duration,
                    metadata={
                        'function': f.__name__,
                        'success': False,
                        'error': str(e)
                    }
                )
                
                raise e
        return decorated_function
    return decorator

def monitor_security(event_type, severity='warning'):
    """Decorator to monitor security-related events."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            user_id = current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None
            
            try:
                result = f(*args, **kwargs)
                
                # Log successful security event
                monitoring_service.log_security_event(
                    event_type=event_type,
                    details={
                        'function': f.__name__,
                        'success': True,
                        'user_id': user_id
                    },
                    user_id=user_id,
                    severity='info'
                )
                
                return result
                
            except Exception as e:
                # Log failed security event
                monitoring_service.log_security_event(
                    event_type=f"{event_type}_failed",
                    details={
                        'function': f.__name__,
                        'success': False,
                        'error': str(e),
                        'user_id': user_id
                    },
                    user_id=user_id,
                    severity=severity
                )
                
                raise e
        return decorated_function
    return decorator