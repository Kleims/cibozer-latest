"""
Monitoring and observability routes for Cibozer
Provides endpoints for health checks, metrics, and dashboard
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required, current_user
from app.services.monitoring_service import get_monitoring_service
from app.models import User
from functools import wraps

# Create monitoring blueprint
monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@monitoring_bp.route('/health')
def health_check():
    """Public health check endpoint"""
    monitoring = get_monitoring_service()
    health_status = monitoring.health.run_checks()
    
    status_code = 200 if health_status['healthy'] else 503
    return jsonify(health_status), status_code


@monitoring_bp.route('/health/ready')
def readiness_check():
    """Kubernetes readiness probe"""
    monitoring = get_monitoring_service()
    
    # Check critical components
    db_check = monitoring.health.checks.get('database', {}).get('last_result', {})
    
    ready = db_check.get('healthy', False)
    
    return jsonify({
        'ready': ready,
        'timestamp': datetime.utcnow().isoformat()
    }), 200 if ready else 503


@monitoring_bp.route('/health/live')
def liveness_check():
    """Kubernetes liveness probe"""
    # Simple check that the application is running
    return jsonify({
        'alive': True,
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@monitoring_bp.route('/metrics')
@login_required
@admin_required
def metrics():
    """Prometheus-style metrics endpoint"""
    monitoring = get_monitoring_service()
    
    # Collect current system metrics
    monitoring.collect_system_metrics()
    
    # Get all metrics
    all_metrics = monitoring.metrics.get_metrics()
    
    # Format metrics in Prometheus format
    metrics_text = []
    
    # Add counters
    for name, value in monitoring.metrics.counters.items():
        metrics_text.append(f'# TYPE {name} counter')
        metrics_text.append(f'{name} {value}')
    
    # Add gauges  
    for name, value in monitoring.metrics.gauges.items():
        metrics_text.append(f'# TYPE {name} gauge')
        metrics_text.append(f'{name} {value}')
    
    # Add histogram summaries
    for name, values in monitoring.metrics.histograms.items():
        if values:
            stats = monitoring.metrics.get_histogram_stats(name)
            metrics_text.append(f'# TYPE {name} histogram')
            metrics_text.append(f'{name}_count {stats["count"]}')
            metrics_text.append(f'{name}_sum {sum(values)}')
            metrics_text.append(f'{name}_bucket{{le="50"}} {stats["p50"]}')
            metrics_text.append(f'{name}_bucket{{le="95"}} {stats["p95"]}')
            metrics_text.append(f'{name}_bucket{{le="99"}} {stats["p99"]}')
    
    return '\n'.join(metrics_text), 200, {'Content-Type': 'text/plain'}


@monitoring_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Monitoring dashboard"""
    monitoring = get_monitoring_service()
    dashboard_data = monitoring.get_dashboard_data()
    
    return render_template('monitoring/dashboard.html', data=dashboard_data)


@monitoring_bp.route('/api/dashboard')
@login_required
@admin_required
def dashboard_api():
    """API endpoint for dashboard data"""
    monitoring = get_monitoring_service()
    return jsonify(monitoring.get_dashboard_data())


@monitoring_bp.route('/api/metrics/<metric_name>')
@login_required
@admin_required
def get_metric(metric_name):
    """Get specific metric data"""
    monitoring = get_monitoring_service()
    
    # Get time range from query parameters
    hours = request.args.get('hours', 1, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    metrics = monitoring.metrics.get_metrics(metric_name, since)
    
    return jsonify({
        'metric': metric_name,
        'period_hours': hours,
        'data_points': len(metrics),
        'data': [
            {
                'timestamp': m.timestamp.isoformat(),
                'value': m.value,
                'tags': m.tags
            }
            for m in metrics
        ]
    })


@monitoring_bp.route('/api/errors')
@login_required
@admin_required
def get_errors():
    """Get error summary"""
    monitoring = get_monitoring_service()
    hours = request.args.get('hours', 24, type=int)
    
    error_summary = monitoring.error_tracker.get_error_summary(hours)
    
    return jsonify(error_summary)


@monitoring_bp.route('/api/performance')
@login_required
@admin_required
def get_performance():
    """Get performance metrics"""
    monitoring = get_monitoring_service()
    
    # Get request duration statistics
    duration_stats = monitoring.metrics.get_histogram_stats('http.request.duration')
    
    # Get recent request times
    recent_times = list(monitoring.performance.request_times)
    
    return jsonify({
        'response_time_stats': duration_stats,
        'recent_request_times': recent_times[-100:],  # Last 100 requests
        'slow_requests_count': monitoring.metrics.counters.get('http.requests.slow', 0)
    })


@monitoring_bp.route('/api/alerts')
@login_required
@admin_required
def get_alerts():
    """Get alert history"""
    monitoring = get_monitoring_service()
    
    limit = request.args.get('limit', 50, type=int)
    alerts = list(monitoring.alerts.alert_history)[-limit:]
    
    return jsonify({
        'alerts': alerts,
        'total_count': len(monitoring.alerts.alert_history)
    })


@monitoring_bp.route('/api/alerts/check')
@login_required
@admin_required
def check_alerts():
    """Manually trigger alert checking"""
    monitoring = get_monitoring_service()
    monitoring.alerts.check_alerts()
    
    return jsonify({'message': 'Alert check completed'})


@monitoring_bp.route('/api/system')
@login_required
@admin_required
def get_system_metrics():
    """Get current system metrics"""
    monitoring = get_monitoring_service()
    
    # Force collection of current metrics
    monitoring.collect_system_metrics()
    
    # Get latest values
    system_metrics = {
        'cpu_percent': monitoring.metrics.gauges.get('system.cpu.percent', 0),
        'memory_percent': monitoring.metrics.gauges.get('system.memory.percent', 0),
        'disk_percent': monitoring.metrics.gauges.get('system.disk.percent', 0),
        'process_memory_rss': monitoring.metrics.gauges.get('process.memory.rss', 0),
        'process_cpu_percent': monitoring.metrics.gauges.get('process.cpu.percent', 0),
        'process_threads': monitoring.metrics.gauges.get('process.threads', 0)
    }
    
    return jsonify(system_metrics)


@monitoring_bp.route('/status')
def status_page():
    """Public status page"""
    monitoring = get_monitoring_service()
    
    # Get basic health information (no sensitive data)
    health_status = monitoring.health.run_checks()
    
    # Calculate uptime (simplified)
    app_start_time = getattr(current_app, 'start_time', datetime.utcnow())
    uptime = datetime.utcnow() - app_start_time
    
    # Get basic metrics
    total_requests = monitoring.metrics.counters.get('http.requests.total', 0)
    total_errors = monitoring.metrics.counters.get('errors.total', 0)
    
    status_data = {
        'service': 'Cibozer',
        'status': 'operational' if health_status['healthy'] else 'degraded',
        'uptime_seconds': int(uptime.total_seconds()),
        'uptime_human': str(uptime).split('.')[0],  # Remove microseconds
        'total_requests': total_requests,
        'total_errors': total_errors,
        'components': {
            'database': health_status['checks'].get('database', {}).get('healthy', False),
            'disk_space': health_status['checks'].get('disk_space', {}).get('healthy', False),
            'memory': health_status['checks'].get('memory', {}).get('healthy', False)
        },
        'last_updated': datetime.utcnow().isoformat()
    }
    
    return render_template('monitoring/status.html', status=status_data)


@monitoring_bp.route('/api/status')
def status_api():
    """API endpoint for status data"""
    monitoring = get_monitoring_service()
    
    health_status = monitoring.health.run_checks()
    
    return jsonify({
        'healthy': health_status['healthy'],
        'status': 'operational' if health_status['healthy'] else 'degraded',
        'components': {
            name: check.get('healthy', False)
            for name, check in health_status['checks'].items()
        },
        'timestamp': datetime.utcnow().isoformat()
    })


# Error handlers for monitoring blueprint
@monitoring_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Monitoring endpoint not found'}), 404


@monitoring_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal monitoring error'}), 500