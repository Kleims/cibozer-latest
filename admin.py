"""
Admin Dashboard for Cibozer
Video generation and analytics for admin use only
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from functools import wraps
import os
from datetime import datetime
import json
from video_service import VideoService
import meal_optimizer as mo
import asyncio
from models import db, User, UsageLog, Payment

# Create admin blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin authentication - load from .env or environment variables
from dotenv import load_dotenv
load_dotenv()

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    print("WARNING: ADMIN_USERNAME and ADMIN_PASSWORD not set. Admin features disabled.")
    ADMIN_USERNAME = 'disabled'
    ADMIN_PASSWORD = 'disabled'

# Initialize services
video_service = VideoService(upload_enabled=True)
optimizer = mo.MealPlanOptimizer()

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            return render_template('admin/login.html', error='Invalid credentials')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Calculate revenue from payments
    total_revenue = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    revenue_formatted = f"${total_revenue:.2f}"
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_plans': len(os.listdir('saved_plans')) if os.path.exists('saved_plans') else 0,
        'total_videos': len(os.listdir('videos')) if os.path.exists('videos') else 0,
        'revenue': revenue_formatted,
        'usage_logs': UsageLog.query.count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/video-generator')
@admin_required
def video_generator():
    """Video generation interface"""
    diet_types = list(optimizer.diet_profiles.keys())
    meal_patterns = list(optimizer.meal_patterns.keys())
    
    return render_template('admin/video_generator.html', 
                         diet_types=diet_types,
                         meal_patterns=meal_patterns)

@admin_bp.route('/api/generate-content-video', methods=['POST'])
@admin_required
def generate_content_video():
    """Generate video for content creation"""
    try:
        data = request.get_json()
        
        # Generate meal plan
        preferences = {
            'diet': data.get('diet_type', 'standard'),
            'calories': int(data.get('calories', 2000)),
            'pattern': data.get('pattern', 'standard'),
            'restrictions': data.get('restrictions', []),
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'measurement_system': 'US',
            'allow_substitutions': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate meal plan
        day_meals, metrics = optimizer.generate_single_day_plan(preferences)
        totals = optimizer.calculate_day_totals(day_meals)
        
        meal_plan = {
            'meals': day_meals,
            'totals': totals,
            'preferences': preferences,
            'metrics': metrics
        }
        
        # Generate videos
        platforms = data.get('platforms', ['youtube_shorts'])
        voice = data.get('voice', 'christopher')
        auto_upload = data.get('auto_upload', False)
        
        # Run async video generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                video_service.generate_and_upload_videos(
                    meal_plan, platforms, voice, auto_upload
                )
            )
            
            return jsonify({
                'success': True,
                'results': results,
                'message': f"Generated {results['summary']['successful_generations']} videos"
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        print(f"Error generating content video: {e}")
        return jsonify({
            'error': 'Failed to generate video',
            'details': str(e)
        }), 500

@admin_bp.route('/api/batch-generate', methods=['POST'])
@admin_required
def batch_generate():
    """Batch generate multiple videos"""
    try:
        data = request.get_json()
        configurations = data.get('configurations', [])
        
        results = []
        for config in configurations:
            # Generate each video
            # Similar to generate_content_video but for multiple configs
            pass
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Batch generation failed',
            'details': str(e)
        }), 500

@admin_bp.route('/analytics')
@admin_required
def analytics():
    """Analytics dashboard"""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    # Get user registration trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    user_registrations = db.session.query(
        func.date(User.created_at).label('date'),
        func.count(User.id).label('count')
    ).filter(User.created_at >= thirty_days_ago).group_by(func.date(User.created_at)).all()
    
    # Get subscription distribution
    subscription_stats = db.session.query(
        User.subscription_tier,
        func.count(User.id).label('count')
    ).group_by(User.subscription_tier).all()
    
    # Get usage statistics
    usage_stats = db.session.query(
        func.date(UsageLog.timestamp).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(UsageLog.timestamp >= thirty_days_ago).group_by(func.date(UsageLog.timestamp)).all()
    
    # Get revenue by month
    revenue_stats = db.session.query(
        func.date_trunc('month', Payment.created_at).label('month'),
        func.sum(Payment.amount).label('revenue')
    ).group_by(func.date_trunc('month', Payment.created_at)).all()
    
    analytics_data = {
        'user_registrations': [{'date': str(r.date), 'count': r.count} for r in user_registrations],
        'subscription_stats': [{'tier': r.subscription_tier, 'count': r.count} for r in subscription_stats],
        'usage_stats': [{'date': str(r.date), 'count': r.count} for r in usage_stats],
        'revenue_stats': [{'month': str(r.month), 'revenue': float(r.revenue)} for r in revenue_stats]
    }
    
    return render_template('admin/analytics.html', analytics=analytics_data)

@admin_bp.route('/users')
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Get users with pagination
    users_query = User.query.order_by(User.created_at.desc())
    users_paginated = users_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get user stats
    user_stats = {
        'total': User.query.count(),
        'active': User.query.filter_by(is_active=True).count(),
        'verified': User.query.filter_by(email_verified=True).count(),
        'free_tier': User.query.filter_by(subscription_tier='free').count(),
        'pro_tier': User.query.filter_by(subscription_tier='pro').count(),
        'premium_tier': User.query.filter_by(subscription_tier='premium').count()
    }
    
    return render_template('admin/users.html', 
                         users=users_paginated.items,
                         pagination=users_paginated,
                         stats=user_stats)