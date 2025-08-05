"""
Log Management and Analysis Routes for Cibozer
Provides endpoints for viewing, searching, and analyzing logs
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, current_app, send_file
from flask_login import login_required, current_user
from app.services.logging_service import get_logging_service
from functools import wraps
import tempfile
import os

# Create logs blueprint
logs_bp = Blueprint('logs', __name__, url_prefix='/logs')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@logs_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Logs dashboard"""
    logging_service = get_logging_service()
    
    # Get recent log summary
    error_summary = logging_service.aggregator.get_error_summary(hours=24)
    logger_stats = logging_service.aggregator.get_logger_stats()
    patterns = logging_service.aggregator.analyze_patterns(hours=24)
    
    dashboard_data = {
        'error_summary': error_summary,
        'logger_stats': logger_stats,
        'patterns': patterns,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return render_template('logs/dashboard.html', data=dashboard_data)


@logs_bp.route('/api/recent')
@login_required
@admin_required
def get_recent_logs():
    """Get recent log entries"""
    logging_service = get_logging_service()
    
    # Parse query parameters
    limit = request.args.get('limit', 100, type=int)
    level = request.args.get('level')
    logger_name = request.args.get('logger')
    hours = request.args.get('hours', 1, type=int)
    
    since = datetime.utcnow() - timedelta(hours=hours) if hours else None
    
    logs = logging_service.aggregator.get_recent_logs(
        limit=limit,
        level=level,
        logger_name=logger_name,
        since=since
    )
    
    return jsonify({
        'logs': [
            {
                'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                'level': log.level,
                'logger': log.logger_name,
                'message': log.message,
                'module': log.module,
                'function': log.function,
                'line': log.line_number,
                'user_id': log.user_id,
                'session_id': log.session_id,
                'trace_id': log.trace_id,
                'span_id': log.span_id,
                'extra_fields': log.extra_fields
            }
            for log in logs
        ],
        'total_count': len(logs),
        'filters': {
            'limit': limit,
            'level': level,
            'logger': logger_name,
            'hours': hours
        }
    })


@logs_bp.route('/api/search')
@login_required
@admin_required
def search_logs():
    """Search logs by message content"""
    logging_service = get_logging_service()
    
    query = request.args.get('q', '')
    limit = request.args.get('limit', 100, type=int)
    
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    logs = logging_service.aggregator.search_logs(query, limit)
    
    return jsonify({
        'logs': [
            {
                'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                'level': log.level,
                'logger': log.logger_name,
                'message': log.message,
                'module': log.module,
                'function': log.function,
                'user_id': log.user_id,
                'trace_id': log.trace_id
            }
            for log in logs
        ],
        'total_found': len(logs),
        'query': query,
        'limit': limit
    })


@logs_bp.route('/api/errors')
@login_required
@admin_required
def get_error_summary():
    """Get error summary and analysis"""
    logging_service = get_logging_service()
    
    hours = request.args.get('hours', 24, type=int)
    error_summary = logging_service.aggregator.get_error_summary(hours)
    
    return jsonify({
        'summary': error_summary,
        'period_hours': hours
    })


@logs_bp.route('/api/patterns')
@login_required
@admin_required
def get_log_patterns():
    """Get log pattern analysis"""
    logging_service = get_logging_service()
    
    hours = request.args.get('hours', 24, type=int)
    patterns = logging_service.aggregator.analyze_patterns(hours)
    
    return jsonify({
        'patterns': patterns,
        'period_hours': hours
    })


@logs_bp.route('/api/loggers')
@login_required
@admin_required
def get_logger_stats():
    """Get statistics for all loggers"""
    logging_service = get_logging_service()
    stats = logging_service.aggregator.get_logger_stats()
    
    return jsonify({
        'loggers': stats,
        'total_loggers': len(stats)
    })


@logs_bp.route('/api/export')
@login_required
@admin_required
def export_logs():
    """Export logs in various formats"""
    logging_service = get_logging_service()
    
    # Parse parameters
    format_type = request.args.get('format', 'json')
    limit = request.args.get('limit', 1000, type=int)
    level = request.args.get('level')
    logger_name = request.args.get('logger')
    hours = request.args.get('hours', 24, type=int)
    
    # Prepare filters
    since = datetime.utcnow() - timedelta(hours=hours)
    filters = {
        'limit': limit,
        'level': level,
        'logger_name': logger_name,
        'since': since
    }
    
    try:
        # Export logs
        exported_data = logging_service.export_logs(format_type, filters)
        
        # Create temporary file
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"cibozer_logs_{timestamp}.{format_type}"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False) as temp_file:
            temp_file.write(exported_data)
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting logs: {e}")
        return jsonify({'error': 'Export failed'}), 500
    finally:
        # Clean up temp file
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass


@logs_bp.route('/api/live')
@login_required
@admin_required
def get_live_logs():
    """Get live log stream (last 50 entries)"""
    logging_service = get_logging_service()
    
    # Get very recent logs
    logs = logging_service.aggregator.get_recent_logs(limit=50)
    
    return jsonify({
        'logs': [
            {
                'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                'level': log.level,
                'logger': log.logger_name,
                'message': log.message[:200],  # Truncate for live view
                'module': log.module,
                'function': log.function,
                'user_id': log.user_id,
                'trace_id': log.trace_id
            }
            for log in logs
        ],
        'timestamp': datetime.utcnow().isoformat()
    })


@logs_bp.route('/api/trace/<trace_id>')
@login_required
@admin_required
def get_logs_by_trace(trace_id):
    """Get all logs for a specific trace ID"""
    logging_service = get_logging_service()
    
    # Search for logs with this trace ID
    all_logs = logging_service.aggregator.get_recent_logs(limit=10000)
    trace_logs = [log for log in all_logs if log.trace_id == trace_id]
    
    # Sort by timestamp
    trace_logs.sort(key=lambda x: x.timestamp)
    
    return jsonify({
        'logs': [
            {
                'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                'level': log.level,
                'logger': log.logger_name,
                'message': log.message,
                'module': log.module,
                'function': log.function,
                'span_id': log.span_id,
                'extra_fields': log.extra_fields
            }
            for log in trace_logs
        ],
        'trace_id': trace_id,
        'total_logs': len(trace_logs)
    })


@logs_bp.route('/api/user/<user_id>')
@login_required
@admin_required
def get_logs_by_user(user_id):
    """Get logs for a specific user"""
    logging_service = get_logging_service()
    
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get all recent logs and filter by user
    all_logs = logging_service.aggregator.get_recent_logs(limit=10000, since=since)
    user_logs = [log for log in all_logs if log.user_id == user_id]
    
    # Sort by timestamp
    user_logs.sort(key=lambda x: x.timestamp, reverse=True)
    
    return jsonify({
        'logs': [
            {
                'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                'level': log.level,
                'logger': log.logger_name,
                'message': log.message,
                'module': log.module,
                'function': log.function,
                'session_id': log.session_id,
                'trace_id': log.trace_id
            }
            for log in user_logs[:100]  # Limit to 100 most recent
        ],
        'user_id': user_id,
        'total_logs': len(user_logs),
        'period_hours': hours
    })


@logs_bp.route('/api/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_logs():
    """Manually trigger log cleanup"""
    logging_service = get_logging_service()
    
    days = request.json.get('days', 30) if request.is_json else 30
    
    try:
        logging_service.cleanup_old_logs(days)
        
        return jsonify({
            'message': 'Log cleanup completed',
            'days_retention': days
        })
        
    except Exception as e:
        current_app.logger.error(f"Log cleanup failed: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500


@logs_bp.route('/viewer')
@login_required
@admin_required
def log_viewer():
    """Interactive log viewer page"""
    return render_template('logs/viewer.html')


# Log analysis endpoints
@logs_bp.route('/api/analysis/security')
@login_required
@admin_required
def security_analysis():
    """Analyze security-related logs"""
    logging_service = get_logging_service()
    
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get security logs
    security_logs = logging_service.aggregator.get_recent_logs(
        logger_name='cibozer.security',
        since=since,
        limit=1000
    )
    
    # Analyze security events
    event_types = {}
    failed_logins = 0
    suspicious_activities = []
    
    for log in security_logs:
        if 'event_type' in log.extra_fields:
            event_type = log.extra_fields['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            if event_type == 'failed_login':
                failed_logins += 1
            elif event_type in ['multiple_failed_logins', 'suspicious_access']:
                suspicious_activities.append({
                    'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                    'event_type': event_type,
                    'user_id': log.user_id,
                    'details': log.extra_fields.get('details', {})
                })
    
    return jsonify({
        'security_events': event_types,
        'failed_logins': failed_logins,
        'suspicious_activities': suspicious_activities,
        'total_security_logs': len(security_logs),
        'period_hours': hours
    })


@logs_bp.route('/api/analysis/performance')
@login_required
@admin_required
def performance_analysis():
    """Analyze performance-related logs"""
    logging_service = get_logging_service()
    
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get performance logs
    perf_logs = logging_service.aggregator.get_recent_logs(
        logger_name='cibozer.performance',
        since=since,
        limit=1000
    )
    
    # Analyze performance metrics
    metrics = {}
    slow_operations = []
    
    for log in perf_logs:
        if 'metric_name' in log.extra_fields:
            metric_name = log.extra_fields['metric_name']
            value = log.extra_fields.get('value', 0)
            
            if metric_name not in metrics:
                metrics[metric_name] = {'count': 0, 'total': 0, 'max': 0, 'values': []}
            
            metrics[metric_name]['count'] += 1
            metrics[metric_name]['total'] += value
            metrics[metric_name]['max'] = max(metrics[metric_name]['max'], value)
            metrics[metric_name]['values'].append(value)
            
            # Flag slow operations
            if value > 5000:  # More than 5 seconds
                slow_operations.append({
                    'timestamp': datetime.fromtimestamp(log.timestamp).isoformat(),
                    'metric': metric_name,
                    'value': value,
                    'details': log.extra_fields.get('details', {})
                })
    
    # Calculate averages
    for metric_data in metrics.values():
        metric_data['average'] = metric_data['total'] / metric_data['count']
        
        # Calculate percentiles
        values = sorted(metric_data['values'])
        if values:
            metric_data['p95'] = values[int(len(values) * 0.95)]
            metric_data['p99'] = values[int(len(values) * 0.99)]
    
    return jsonify({
        'performance_metrics': metrics,
        'slow_operations': slow_operations,
        'total_performance_logs': len(perf_logs),
        'period_hours': hours
    })


# Error handlers
@logs_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Logs endpoint not found'}), 404


@logs_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal logs error'}), 500