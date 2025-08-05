"""
SLA Monitoring Routes for Cibozer
Provides endpoints for SLA monitoring, reporting, and management
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, render_template, request, current_app, send_file
from flask_login import login_required, current_user
from app.services.sla_service import get_sla_service, SLATarget, MetricType
from functools import wraps
import tempfile
import os

# Create SLA blueprint
sla_bp = Blueprint('sla', __name__, url_prefix='/sla')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


@sla_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """SLA monitoring dashboard"""
    sla_service = get_sla_service()
    dashboard_data = sla_service.get_sla_dashboard_data()
    
    return render_template('sla/dashboard.html', data=dashboard_data)


@sla_bp.route('/api/dashboard')
@login_required
@admin_required
def dashboard_api():
    """API endpoint for SLA dashboard data"""
    sla_service = get_sla_service()
    return jsonify(sla_service.get_sla_dashboard_data())


@sla_bp.route('/api/targets')
@login_required
@admin_required
def get_targets():
    """Get all SLA targets"""
    sla_service = get_sla_service()
    
    targets_data = []
    for target_name, target in sla_service.targets.items():
        targets_data.append({
            'name': target.name,
            'description': target.description,
            'metric_type': target.metric_type.value,
            'target_value': target.target_value,
            'comparison': target.comparison,
            'time_window_minutes': target.time_window_minutes,
            'alert_threshold': target.alert_threshold,
            'critical_threshold': target.critical_threshold,
            'tags': target.tags
        })
    
    return jsonify({
        'targets': targets_data,
        'total_count': len(targets_data)
    })


@sla_bp.route('/api/targets', methods=['POST'])
@login_required
@admin_required
def create_target():
    """Create a new SLA target"""
    sla_service = get_sla_service()
    data = request.get_json()
    
    try:
        # Validate required fields
        required_fields = ['name', 'description', 'metric_type', 'target_value', 'comparison']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create SLA target
        target = SLATarget(
            name=data['name'],
            description=data['description'],
            metric_type=MetricType(data['metric_type']),
            target_value=float(data['target_value']),
            comparison=data['comparison'],
            time_window_minutes=data.get('time_window_minutes', 60),
            alert_threshold=float(data.get('alert_threshold', data['target_value'])),
            critical_threshold=float(data.get('critical_threshold', data['target_value'])),
            tags=data.get('tags', {})
        )
        
        # Validate comparison operator
        if target.comparison not in ['>=', '<=', '==', '>', '<']:
            return jsonify({'error': 'Invalid comparison operator'}), 400
        
        sla_service.add_target(target)
        
        return jsonify({
            'message': 'SLA target created successfully',
            'target_name': target.name
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        current_app.logger.error(f"Error creating SLA target: {e}")
        return jsonify({'error': 'Failed to create SLA target'}), 500


@sla_bp.route('/api/targets/<target_name>', methods=['DELETE'])
@login_required
@admin_required
def delete_target(target_name):
    """Delete an SLA target"""
    sla_service = get_sla_service()
    
    if target_name not in sla_service.targets:
        return jsonify({'error': 'SLA target not found'}), 404
    
    sla_service.remove_target(target_name)
    
    return jsonify({
        'message': f'SLA target {target_name} deleted successfully'
    })


@sla_bp.route('/api/targets/<target_name>/report')
@login_required
@admin_required
def get_target_report(target_name):
    """Get compliance report for a specific target"""
    sla_service = get_sla_service()
    
    hours = request.args.get('hours', 24, type=int)
    
    if target_name not in sla_service.targets:
        return jsonify({'error': 'SLA target not found'}), 404
    
    report = sla_service.get_compliance_report(target_name, hours)
    
    if not report:
        return jsonify({'error': 'No data available for the specified time period'}), 404
    
    return jsonify({
        'report': {
            'target_name': report.target_name,
            'time_period': report.time_period,
            'total_measurements': report.total_measurements,
            'compliant_measurements': report.compliant_measurements,
            'compliance_percentage': report.compliance_percentage,
            'status': report.status.value,
            'average_value': report.average_value,
            'min_value': report.min_value,
            'max_value': report.max_value,
            'uptime_percentage': report.uptime_percentage,
            'downtime_minutes': report.downtime_minutes,
            'breaches': report.breaches
        }
    })


@sla_bp.route('/api/measurements/<target_name>', methods=['POST'])
@login_required
@admin_required
def record_measurement(target_name):
    """Record a measurement for an SLA target"""
    sla_service = get_sla_service()
    data = request.get_json()
    
    if 'value' not in data:
        return jsonify({'error': 'Missing value field'}), 400
    
    try:
        value = float(data['value'])
        metadata = data.get('metadata', {})
        
        success = sla_service.record_measurement(target_name, value, metadata)
        
        if not success:
            return jsonify({'error': 'SLA target not found'}), 404
        
        return jsonify({
            'message': 'Measurement recorded successfully',
            'target_name': target_name,
            'value': value
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid value format'}), 400
    except Exception as e:
        current_app.logger.error(f"Error recording SLA measurement: {e}")
        return jsonify({'error': 'Failed to record measurement'}), 500


@sla_bp.route('/api/alerts')
@login_required
@admin_required
def get_sla_alerts():
    """Get recent SLA alerts"""
    sla_service = get_sla_service()
    
    limit = request.args.get('limit', 50, type=int)
    severity = request.args.get('severity')  # Filter by severity
    
    alerts = list(sla_service.alerts)
    
    # Filter by severity if specified
    if severity:
        alerts = [alert for alert in alerts if alert['severity'] == severity]
    
    # Sort by timestamp (newest first) and limit
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    alerts = alerts[:limit]
    
    # Format timestamps
    for alert in alerts:
        alert['timestamp_iso'] = datetime.fromtimestamp(alert['timestamp']).isoformat()
    
    return jsonify({
        'alerts': alerts,
        'total_count': len(alerts),
        'filters': {
            'limit': limit,
            'severity': severity
        }
    })


@sla_bp.route('/api/compliance/summary')
@login_required
@admin_required
def compliance_summary():
    """Get overall compliance summary"""
    sla_service = get_sla_service()
    
    hours = request.args.get('hours', 24, type=int)
    reports = sla_service.get_all_compliance_reports(hours)
    
    # Calculate overall statistics
    if reports:
        total_targets = len(reports)
        overall_compliance = sum(r.compliance_percentage for r in reports.values()) / total_targets
        
        status_counts = {
            'healthy': len([r for r in reports.values() if r.status.value == 'healthy']),
            'warning': len([r for r in reports.values() if r.status.value == 'warning']),
            'critical': len([r for r in reports.values() if r.status.value == 'critical']),
            'breached': len([r for r in reports.values() if r.status.value == 'breached'])
        }
        
        total_breaches = sum(len(r.breaches) for r in reports.values())
        total_measurements = sum(r.total_measurements for r in reports.values())
    else:
        total_targets = 0
        overall_compliance = 100.0
        status_counts = {'healthy': 0, 'warning': 0, 'critical': 0, 'breached': 0}
        total_breaches = 0
        total_measurements = 0
    
    return jsonify({
        'summary': {
            'total_targets': total_targets,
            'overall_compliance': overall_compliance,
            'status_counts': status_counts,
            'total_breaches': total_breaches,
            'total_measurements': total_measurements,
            'time_period_hours': hours
        },
        'reports': {name: {
            'target_name': report.target_name,
            'compliance_percentage': report.compliance_percentage,
            'status': report.status.value,
            'total_measurements': report.total_measurements,
            'breaches_count': len(report.breaches)
        } for name, report in reports.items()}
    })


@sla_bp.route('/api/trends/<target_name>')
@login_required
@admin_required
def get_compliance_trends(target_name):
    """Get compliance trends for a target over time"""
    sla_service = get_sla_service()
    
    if target_name not in sla_service.targets:
        return jsonify({'error': 'SLA target not found'}), 404
    
    hours = request.args.get('hours', 24, type=int)
    
    # Get measurements for the time period
    since_timestamp = datetime.utcnow().timestamp() - (hours * 3600)
    measurements = [
        m for m in sla_service.measurements[target_name]
        if m.timestamp >= since_timestamp
    ]
    
    if not measurements:
        return jsonify({'error': 'No data available'}), 404
    
    # Group measurements by hour
    hourly_data = {}
    for measurement in measurements:
        hour_key = datetime.fromtimestamp(measurement.timestamp).strftime('%Y-%m-%d %H:00')
        if hour_key not in hourly_data:
            hourly_data[hour_key] = []
        hourly_data[hour_key].append(measurement)
    
    # Calculate hourly compliance
    trends = []
    for hour, hour_measurements in sorted(hourly_data.items()):
        compliant = [m for m in hour_measurements if m.status.value == 'healthy']
        compliance_rate = (len(compliant) / len(hour_measurements)) * 100
        
        avg_value = sum(m.value for m in hour_measurements) / len(hour_measurements)
        
        trends.append({
            'hour': hour,
            'compliance_percentage': compliance_rate,
            'average_value': avg_value,
            'total_measurements': len(hour_measurements),
            'compliant_measurements': len(compliant)
        })
    
    return jsonify({
        'target_name': target_name,
        'trends': trends,
        'period_hours': hours
    })


@sla_bp.route('/api/export')
@login_required
@admin_required
def export_sla_data():
    """Export SLA data"""
    sla_service = get_sla_service()
    
    target_name = request.args.get('target')
    hours = request.args.get('hours', 24, type=int)
    format_type = request.args.get('format', 'json')
    
    try:
        # Export data
        export_data = sla_service.export_sla_data(target_name, hours)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        if format_type == 'json':
            filename = f"sla_data_{timestamp}.json"
            content = json.dumps(export_data, indent=2, default=str)
            mimetype = 'application/json'
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_type}', delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        return send_file(
            temp_file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting SLA data: {e}")
        return jsonify({'error': 'Export failed'}), 500
    finally:
        # Clean up temp file
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass


@sla_bp.route('/api/cleanup', methods=['POST'])
@login_required
@admin_required
def cleanup_old_data():
    """Manually trigger SLA data cleanup"""
    sla_service = get_sla_service()
    
    days = request.json.get('days', 7) if request.is_json else 7
    
    try:
        sla_service.cleanup_old_data(days)
        
        return jsonify({
            'message': 'SLA data cleanup completed',
            'retention_days': days
        })
        
    except Exception as e:
        current_app.logger.error(f"SLA cleanup failed: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500


@sla_bp.route('/reports')
@login_required
@admin_required
def reports_page():
    """SLA reports page"""
    return render_template('sla/reports.html')


@sla_bp.route('/targets')
@login_required
@admin_required
def targets_page():
    """SLA targets management page"""
    return render_template('sla/targets.html')


# Health check endpoint (public)
@sla_bp.route('/health')
def sla_health():
    """Public SLA health check"""
    sla_service = get_sla_service()
    dashboard_data = sla_service.get_sla_dashboard_data()
    
    # Return simplified health status
    return jsonify({
        'overall_status': dashboard_data['overall_status'],
        'overall_compliance': dashboard_data['overall_compliance'],
        'healthy_targets': dashboard_data['healthy_targets'],
        'total_targets': dashboard_data['total_targets'],
        'timestamp': dashboard_data['timestamp']
    })


# Error handlers
@sla_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'SLA endpoint not found'}), 404


@sla_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal SLA error'}), 500