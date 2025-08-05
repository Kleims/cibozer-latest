"""
Distributed Tracing Routes for Cibozer
Provides endpoints to view and analyze traces
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import login_required, current_user
from app.services.tracing_service import get_tracing_service
from functools import wraps

# Create tracing blueprint
tracing_bp = Blueprint('tracing', __name__, url_prefix='/tracing')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@tracing_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Tracing dashboard"""
    tracing = get_tracing_service()
    
    # Get dashboard data
    summary = tracing.get_trace_summary()
    operation_stats = tracing.get_operation_stats()
    recent_traces = tracing.get_traces(limit=20)
    
    dashboard_data = {
        'summary': summary,
        'operation_stats': operation_stats,
        'recent_traces': [
            {
                'trace_id': trace.trace_id,
                'operation_name': trace.operation_name,
                'service_name': trace.service_name,
                'duration_ms': trace.duration_ms,
                'span_count': trace.span_count,
                'status': trace.status,
                'error_count': trace.error_count,
                'start_time': datetime.fromtimestamp(trace.start_time).isoformat()
            }
            for trace in recent_traces
        ],
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return render_template('tracing/dashboard.html', data=dashboard_data)


@tracing_bp.route('/api/traces')
@login_required
@admin_required
def get_traces():
    """Get traces with filtering"""
    tracing = get_tracing_service()
    
    # Parse query parameters
    limit = request.args.get('limit', 100, type=int)
    service = request.args.get('service')
    operation = request.args.get('operation')
    status = request.args.get('status')
    min_duration_ms = request.args.get('min_duration', type=float)
    
    traces = tracing.get_traces(
        limit=limit,
        service=service,
        operation=operation,
        status=status,
        min_duration_ms=min_duration_ms
    )
    
    return jsonify({
        'traces': [
            {
                'trace_id': trace.trace_id,
                'operation_name': trace.operation_name,
                'service_name': trace.service_name,
                'duration_ms': trace.duration_ms,
                'span_count': trace.span_count,
                'status': trace.status,
                'error_count': trace.error_count,
                'start_time': datetime.fromtimestamp(trace.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(trace.end_time).isoformat() if trace.end_time else None
            }
            for trace in traces
        ],
        'total_count': len(traces),
        'filters': {
            'service': service,
            'operation': operation,
            'status': status,
            'min_duration_ms': min_duration_ms
        }
    })


@tracing_bp.route('/api/trace/<trace_id>')
@login_required
@admin_required
def get_trace_detail(trace_id):
    """Get detailed trace information"""
    tracing = get_tracing_service()
    trace = tracing.get_trace(trace_id)
    
    if not trace:
        return jsonify({'error': 'Trace not found'}), 404
    
    # Convert spans to JSON-serializable format
    spans_data = []
    for span in trace.spans:
        span_data = {
            'span_id': span.span_id,
            'trace_id': span.trace_id,
            'parent_span_id': span.parent_span_id,
            'operation_name': span.operation_name,
            'start_time': datetime.fromtimestamp(span.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(span.end_time).isoformat() if span.end_time else None,
            'duration_ms': span.duration_ms,
            'status': span.status,
            'error_message': span.error_message,
            'tags': span.tags,
            'logs': [
                {
                    'timestamp': datetime.fromtimestamp(log['timestamp']).isoformat(),
                    'message': log['message'],
                    'level': log['level'],
                    'fields': log['fields']
                }
                for log in span.logs
            ]
        }
        spans_data.append(span_data)
    
    return jsonify({
        'trace': {
            'trace_id': trace.trace_id,
            'root_span_id': trace.root_span_id,
            'operation_name': trace.operation_name,
            'service_name': trace.service_name,
            'start_time': datetime.fromtimestamp(trace.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(trace.end_time).isoformat() if trace.end_time else None,
            'duration_ms': trace.duration_ms,
            'status': trace.status,
            'error_count': trace.error_count,
            'span_count': trace.span_count
        },
        'spans': spans_data
    })


@tracing_bp.route('/api/operations')
@login_required
@admin_required
def get_operation_stats():
    """Get operation performance statistics"""
    tracing = get_tracing_service()
    stats = tracing.get_operation_stats()
    
    # Sort by average duration (slowest first)
    sorted_stats = sorted(
        stats.items(),
        key=lambda x: x[1]['avg_duration_ms'],
        reverse=True
    )
    
    return jsonify({
        'operations': [
            {
                'operation_name': op_name,
                'stats': op_stats
            }
            for op_name, op_stats in sorted_stats
        ],
        'total_operations': len(stats)
    })


@tracing_bp.route('/api/services')
@login_required
@admin_required
def get_service_map():
    """Get service dependency map"""
    tracing = get_tracing_service()
    dependencies = tracing.get_service_dependencies()
    
    # Create nodes and edges for service map visualization
    nodes = set()
    edges = []
    
    for service, deps in dependencies.items():
        nodes.add(service)
        for dep in deps:
            nodes.add(dep)
            edges.append({'from': service, 'to': dep})
    
    return jsonify({
        'nodes': [{'id': node, 'label': node} for node in nodes],
        'edges': edges,
        'dependencies': dependencies
    })


@tracing_bp.route('/api/summary')
@login_required
@admin_required
def get_trace_summary():
    """Get tracing system summary"""
    tracing = get_tracing_service()
    return jsonify(tracing.get_trace_summary())


@tracing_bp.route('/api/search')
@login_required
@admin_required
def search_traces():
    """Search traces by various criteria"""
    tracing = get_tracing_service()
    
    # Parse search parameters
    query = request.args.get('q', '')
    tag_key = request.args.get('tag_key')
    tag_value = request.args.get('tag_value')
    error_only = request.args.get('error_only', type=bool)
    slow_only = request.args.get('slow_only', type=bool)
    min_duration = request.args.get('min_duration', type=float)
    max_duration = request.args.get('max_duration', type=float)
    
    traces = list(tracing.trace_history)
    
    # Apply filters
    if query:
        traces = [
            t for t in traces 
            if query.lower() in t.operation_name.lower() or 
               query.lower() in t.service_name.lower()
        ]
    
    if error_only:
        traces = [t for t in traces if t.status == 'error']
    
    if slow_only or min_duration:
        threshold = min_duration or 1000  # Default 1 second
        traces = [t for t in traces if t.duration_ms and t.duration_ms >= threshold]
    
    if max_duration:
        traces = [t for t in traces if t.duration_ms and t.duration_ms <= max_duration]
    
    if tag_key and tag_value:
        traces = [
            t for t in traces 
            if any(
                span.tags.get(tag_key) == tag_value
                for span in t.spans
            )
        ]
    
    # Sort by start time (newest first)
    traces.sort(key=lambda t: t.start_time, reverse=True)
    
    # Limit results
    limit = request.args.get('limit', 50, type=int)
    traces = traces[:limit]
    
    return jsonify({
        'traces': [
            {
                'trace_id': trace.trace_id,
                'operation_name': trace.operation_name,
                'service_name': trace.service_name,
                'duration_ms': trace.duration_ms,
                'span_count': trace.span_count,
                'status': trace.status,
                'error_count': trace.error_count,
                'start_time': datetime.fromtimestamp(trace.start_time).isoformat()
            }
            for trace in traces
        ],
        'total_found': len(traces),
        'search_params': {
            'query': query,
            'tag_key': tag_key,
            'tag_value': tag_value,
            'error_only': error_only,
            'slow_only': slow_only,
            'min_duration': min_duration,
            'max_duration': max_duration
        }
    })


@tracing_bp.route('/api/config', methods=['GET', 'POST'])
@login_required
@admin_required
def tracing_config():
    """Get or update tracing configuration"""
    tracing = get_tracing_service()
    
    if request.method == 'POST':
        data = request.get_json()
        
        if 'enabled' in data:
            tracing.enabled = bool(data['enabled'])
        
        if 'sample_rate' in data:
            rate = float(data['sample_rate'])
            if 0 <= rate <= 1:
                tracing.sample_rate = rate
        
        if 'max_trace_duration' in data:
            duration = int(data['max_trace_duration'])
            if duration > 0:
                tracing.max_trace_duration = duration
        
        return jsonify({'message': 'Configuration updated'})
    
    return jsonify({
        'enabled': tracing.enabled,
        'sample_rate': tracing.sample_rate,
        'max_trace_duration_ms': tracing.max_trace_duration,
        'active_traces': len(tracing.traces),
        'active_spans': len(tracing.active_spans),
        'trace_history_size': len(tracing.trace_history),
        'span_history_size': len(tracing.span_history)
    })


@tracing_bp.route('/api/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_traces():
    """Manually trigger trace cleanup"""
    tracing = get_tracing_service()
    
    max_age_hours = request.json.get('max_age_hours', 24) if request.is_json else 24
    
    old_trace_count = len(tracing.trace_history)
    old_span_count = len(tracing.span_history)
    
    tracing.cleanup_old_data(max_age_hours)
    
    return jsonify({
        'message': 'Cleanup completed',
        'traces_before': old_trace_count,
        'traces_after': len(tracing.trace_history),
        'spans_before': old_span_count,
        'spans_after': len(tracing.span_history),
        'max_age_hours': max_age_hours
    })


# Trace visualization page
@tracing_bp.route('/trace/<trace_id>')
@login_required
@admin_required
def trace_detail_page(trace_id):
    """Display detailed trace visualization"""
    tracing = get_tracing_service()
    trace = tracing.get_trace(trace_id)
    
    if not trace:
        return render_template('errors/404.html'), 404
    
    return render_template('tracing/trace_detail.html', trace_id=trace_id)


# Error handlers
@tracing_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Tracing endpoint not found'}), 404


@tracing_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal tracing error'}), 500