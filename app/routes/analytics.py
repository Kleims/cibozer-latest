"""
Analytics endpoints for tracking user behavior and application metrics
"""

import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from flask_login import current_user
from app.extensions import db
from app.models import UsageLog
from app.services.monitoring_service import get_monitoring_service
from sqlalchemy import func, desc
from collections import defaultdict

# Create analytics blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/track', methods=['POST'])
def track_events():
    """Endpoint to receive analytics events from frontend"""
    try:
        data = request.get_json()
        if not data or 'events' not in data:
            return jsonify({'error': 'Invalid data format'}), 400
        
        events = data.get('events', [])
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        
        # Get monitoring service
        monitoring = get_monitoring_service()
        
        # Process each event
        for event in events:
            try:
                # Store event in database
                usage_log = UsageLog(
                    user_id=user_id if not user_id.startswith('anon_') else None,
                    session_id=session_id,
                    action=event.get('event'),
                    resource_type='analytics',
                    metadata=event.get('properties', {}),
                    endpoint=request.endpoint,
                    method='POST',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                db.session.add(usage_log)
                
                # Track event in monitoring system
                monitoring.metrics.increment(f'analytics.event.{event.get("event")}')
                
                # Track specific events
                event_name = event.get('event')
                if event_name == 'meal_plan_generate':
                    monitoring.metrics.increment('business.meal_plans.generated')
                elif event_name == 'meal_plan_save':
                    monitoring.metrics.increment('business.meal_plans.saved')
                elif event_name == 'user_identify':
                    monitoring.metrics.increment('business.users.identified')
                elif event_name == 'form_submit':
                    monitoring.metrics.increment('business.forms.submitted')
                elif event_name == 'javascript_error':
                    monitoring.metrics.increment('frontend.javascript.errors')
                
            except Exception as e:
                current_app.logger.error(f"Error processing analytics event: {e}")
                continue
        
        # Commit all events
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'events_processed': len(events)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Analytics tracking error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/dashboard')
def analytics_dashboard():
    """Get analytics dashboard data"""
    try:
        # Time ranges
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Get event counts by type (last 24h)
        event_counts = db.session.query(
            UsageLog.action,
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.created_at >= last_24h,
            UsageLog.resource_type == 'analytics'
        ).group_by(UsageLog.action).all()
        
        # Get user activity (last 7 days)
        user_activity = db.session.query(
            func.date(UsageLog.created_at).label('date'),
            func.count(func.distinct(UsageLog.user_id)).label('active_users'),
            func.count(func.distinct(UsageLog.session_id)).label('sessions')
        ).filter(
            UsageLog.created_at >= last_7d,
            UsageLog.resource_type == 'analytics'
        ).group_by(func.date(UsageLog.created_at)).all()
        
        # Get popular pages (last 7 days)
        popular_pages = db.session.query(
            UsageLog.metadata['page_url'].astext.label('page_url'),
            func.count(UsageLog.id).label('views')
        ).filter(
            UsageLog.created_at >= last_7d,
            UsageLog.action == 'page_view',
            UsageLog.resource_type == 'analytics'
        ).group_by(
            UsageLog.metadata['page_url'].astext
        ).order_by(desc('views')).limit(10).all()
        
        # Get conversion funnel data
        funnel_data = get_conversion_funnel(last_7d)
        
        # Get performance metrics
        performance_data = get_performance_metrics(last_24h)
        
        # Get error analytics
        error_data = get_error_analytics(last_24h)
        
        return jsonify({
            'overview': {
                'total_events_24h': sum(count for _, count in event_counts),
                'unique_users_7d': len(set(activity.active_users for activity in user_activity)),
                'total_sessions_7d': sum(activity.sessions for activity in user_activity),
                'bounce_rate': calculate_bounce_rate(last_7d)
            },
            'events': {
                'by_type': [{'event': event, 'count': count} for event, count in event_counts],
                'timeline': format_user_activity(user_activity)
            },
            'pages': {
                'popular': [{'url': url, 'views': views} for url, views in popular_pages]
            },
            'funnel': funnel_data,
            'performance': performance_data,
            'errors': error_data,
            'timestamp': now.isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Analytics dashboard error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


def get_conversion_funnel(since):
    """Calculate conversion funnel metrics"""
    try:
        # Define funnel steps
        steps = [
            ('page_view', 'Page Views'),
            ('form_field_focus', 'Form Interactions'),
            ('meal_plan_generate', 'Meal Plans Generated'),
            ('meal_plan_save', 'Meal Plans Saved')
        ]
        
        funnel_data = []
        
        for step_event, step_name in steps:
            count = db.session.query(func.count(func.distinct(UsageLog.session_id))).filter(
                UsageLog.created_at >= since,
                UsageLog.action == step_event,
                UsageLog.resource_type == 'analytics'
            ).scalar() or 0
            
            funnel_data.append({
                'step': step_name,
                'count': count,
                'event': step_event
            })
        
        # Calculate conversion rates
        for i, step in enumerate(funnel_data):
            if i == 0:
                step['conversion_rate'] = 100.0
            else:
                previous_count = funnel_data[i-1]['count']
                step['conversion_rate'] = (step['count'] / max(previous_count, 1)) * 100
        
        return funnel_data
        
    except Exception as e:
        current_app.logger.error(f"Error calculating conversion funnel: {e}")
        return []


def get_performance_metrics(since):
    """Get performance-related analytics"""
    try:
        # Get page load times
        load_times = db.session.query(
            UsageLog.metadata['load_time'].astext.cast(db.Integer).label('load_time')
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.action == 'page_performance',
            UsageLog.resource_type == 'analytics',
            UsageLog.metadata['load_time'].astext.cast(db.Integer) < 30000  # Filter outliers
        ).all()
        
        load_time_values = [lt.load_time for lt in load_times if lt.load_time]
        
        # Get scroll depths
        scroll_depths = db.session.query(
            UsageLog.metadata['max_scroll_depth'].astext.cast(db.Integer).label('scroll_depth')
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.action == 'page_scroll_complete',
            UsageLog.resource_type == 'analytics'
        ).all()
        
        scroll_values = [sd.scroll_depth for sd in scroll_depths if sd.scroll_depth]
        
        return {
            'page_load': {
                'count': len(load_time_values),
                'average': sum(load_time_values) / len(load_time_values) if load_time_values else 0,
                'median': sorted(load_time_values)[len(load_time_values)//2] if load_time_values else 0
            },
            'engagement': {
                'average_scroll_depth': sum(scroll_values) / len(scroll_values) if scroll_values else 0,
                'sessions_with_deep_scroll': len([s for s in scroll_values if s > 75])
            }
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance metrics: {e}")
        return {}


def get_error_analytics(since):
    """Get error-related analytics"""
    try:
        # JavaScript errors
        js_errors = db.session.query(
            UsageLog.metadata['error_message'].astext.label('error_message'),
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.action == 'javascript_error',
            UsageLog.resource_type == 'analytics'
        ).group_by(
            UsageLog.metadata['error_message'].astext
        ).order_by(desc('count')).limit(10).all()
        
        # Form abandonment
        form_abandons = db.session.query(
            UsageLog.metadata['form_id'].astext.label('form_id'),
            func.count(UsageLog.id).label('count')
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.action == 'form_abandon',
            UsageLog.resource_type == 'analytics'
        ).group_by(
            UsageLog.metadata['form_id'].astext
        ).order_by(desc('count')).all()
        
        return {
            'javascript_errors': [
                {'message': error.error_message[:100], 'count': error.count}
                for error in js_errors
            ],
            'form_abandonment': [
                {'form_id': abandon.form_id, 'count': abandon.count}
                for abandon in form_abandons
            ],
            'total_js_errors': sum(error.count for error in js_errors),
            'total_form_abandons': sum(abandon.count for abandon in form_abandons)
        }
        
    except Exception as e:
        current_app.logger.error(f"Error getting error analytics: {e}")
        return {}


def calculate_bounce_rate(since):
    """Calculate bounce rate (single page sessions)"""
    try:
        # Get sessions with only one page view
        single_page_sessions = db.session.query(
            UsageLog.session_id
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.action == 'page_view',
            UsageLog.resource_type == 'analytics'
        ).group_by(
            UsageLog.session_id
        ).having(func.count(UsageLog.id) == 1).all()
        
        # Get total sessions
        total_sessions = db.session.query(
            func.count(func.distinct(UsageLog.session_id))
        ).filter(
            UsageLog.created_at >= since,
            UsageLog.resource_type == 'analytics'
        ).scalar() or 0
        
        if total_sessions == 0:
            return 0
        
        bounce_rate = (len(single_page_sessions) / total_sessions) * 100
        return round(bounce_rate, 2)
        
    except Exception as e:
        current_app.logger.error(f"Error calculating bounce rate: {e}")
        return 0


def format_user_activity(activity_data):
    """Format user activity data for charts"""
    return [
        {
            'date': activity.date.isoformat() if activity.date else '',
            'active_users': activity.active_users or 0,
            'sessions': activity.sessions or 0
        }
        for activity in activity_data
    ]


@analytics_bp.route('/events/<event_name>')
def get_event_details(event_name):
    """Get detailed analytics for a specific event"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Get event occurrences
        events = db.session.query(UsageLog).filter(
            UsageLog.created_at >= since,
            UsageLog.action == event_name,
            UsageLog.resource_type == 'analytics'
        ).order_by(desc(UsageLog.created_at)).limit(100).all()
        
        # Aggregate by hour
        hourly_counts = defaultdict(int)
        for event in events:
            hour_key = event.created_at.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1
        
        return jsonify({
            'event_name': event_name,
            'total_count': len(events),
            'period_hours': hours,
            'hourly_breakdown': [
                {'hour': hour, 'count': count}
                for hour, count in sorted(hourly_counts.items())
            ],
            'recent_events': [
                {
                    'timestamp': event.created_at.isoformat(),
                    'user_id': event.user_id,
                    'session_id': event.session_id,
                    'properties': event.metadata
                }
                for event in events[:20]  # Last 20 events
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting event details: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@analytics_bp.route('/users/<user_id>/journey')
def get_user_journey(user_id):
    """Get user journey analytics"""
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get user events
        events = db.session.query(UsageLog).filter(
            UsageLog.user_id == user_id,
            UsageLog.created_at >= since,
            UsageLog.resource_type == 'analytics'
        ).order_by(UsageLog.created_at).all()
        
        # Group by session
        sessions = defaultdict(list)
        for event in events:
            sessions[event.session_id].append({
                'event': event.action,
                'timestamp': event.created_at.isoformat(),
                'properties': event.metadata
            })
        
        return jsonify({
            'user_id': user_id,
            'period_days': days,
            'total_sessions': len(sessions),
            'total_events': len(events),
            'sessions': dict(sessions)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting user journey: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Error handlers
@analytics_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Analytics endpoint not found'}), 404


@analytics_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal analytics error'}), 500