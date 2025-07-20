"""
Admin Dashboard for Cibozer
Video generation and analytics for admin use only
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, current_app
from functools import wraps
import os
from datetime import datetime, timezone, timedelta
import json
from video_service import VideoService
import meal_optimizer as mo
import asyncio
from models import db, User, UsageLog, Payment
from sqlalchemy import func, case

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
    # Get statistics with optimized queries
    user_stats = db.session.query(
        func.count(User.id).label('total'),
        func.sum(case((User.is_active == True, 1), else_=0)).label('active')
    ).first()
    
    # Calculate revenue from payments
    total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
    revenue_formatted = f"${total_revenue:.2f}"
    
    # Get usage log count
    usage_count = db.session.query(func.count(UsageLog.id)).scalar() or 0
    
    stats = {
        'total_users': user_stats.total or 0,
        'active_users': user_stats.active or 0,
        'total_plans': len(os.listdir('saved_plans')) if os.path.exists('saved_plans') else 0,
        'total_videos': len(os.listdir('videos')) if os.path.exists('videos') else 0,
        'revenue': revenue_formatted,
        'usage_logs': usage_count
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
        total_generated = 0
        total_failed = 0
        
        for i, config in enumerate(configurations):
            try:
                # Generate meal plan for each configuration
                preferences = {
                    'diet': config.get('diet_type', 'standard'),
                    'calories': int(config.get('calories', 2000)),
                    'pattern': config.get('pattern', 'standard'),
                    'restrictions': config.get('restrictions', []),
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
                platforms = config.get('platforms', ['youtube_shorts'])
                voice = config.get('voice', 'christopher')
                auto_upload = config.get('auto_upload', False)
                
                # Run async video generation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    video_results = loop.run_until_complete(
                        video_service.generate_and_upload_videos(
                            meal_plan, platforms, voice, auto_upload
                        )
                    )
                    
                    results.append({
                        'index': i,
                        'config': config,
                        'status': 'success',
                        'videos_generated': video_results['summary']['successful_generations'],
                        'videos_uploaded': video_results['summary']['successful_uploads']
                    })
                    
                    total_generated += video_results['summary']['successful_generations']
                    
                finally:
                    loop.close()
                    
            except Exception as e:
                results.append({
                    'index': i,
                    'config': config,
                    'status': 'failed',
                    'error': str(e)
                })
                total_failed += 1
                current_app.logger.error(f"Batch generation failed for config {i}: {e}")
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_configurations': len(configurations),
                'total_generated': total_generated,
                'total_failed': total_failed,
                'success_rate': (len(configurations) - total_failed) / len(configurations) * 100 if configurations else 0
            }
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
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
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
    
    # Get revenue statistics (compatible with SQLite and PostgreSQL)
    try:
        # Try PostgreSQL date_trunc function first
        revenue_stats = db.session.query(
            func.date_trunc('month', Payment.created_at).label('month'),
            func.sum(Payment.amount).label('revenue')
        ).group_by(func.date_trunc('month', Payment.created_at)).all()
    except Exception as e:
        # Fallback to SQLite strftime function
        app.logger.warning(f"PostgreSQL date_trunc failed, using SQLite fallback: {str(e)}")
        revenue_stats = db.session.query(
            func.strftime('%Y-%m', Payment.created_at).label('month'),
            func.sum(Payment.amount).label('revenue')
        ).group_by(func.strftime('%Y-%m', Payment.created_at)).all()
    
    # Calculate total revenue and MRR
    total_revenue = db.session.query(func.sum(Payment.amount)).scalar() or 0
    total_revenue = total_revenue / 100  # Convert from cents
    
    # Calculate MRR (Monthly Recurring Revenue) with single query
    mrr_stats = db.session.query(
        func.sum(case((User.subscription_tier == 'pro', 1), else_=0)).label('pro_count'),
        func.sum(case((User.subscription_tier == 'premium', 1), else_=0)).label('premium_count')
    ).filter(User.subscription_status == 'active').first()
    
    active_pro = mrr_stats.pro_count or 0
    active_premium = mrr_stats.premium_count or 0
    current_mrr = (active_pro * 9.99) + (active_premium * 19.99)
    
    # Calculate totals
    total_users = User.query.count()
    paying_users = User.query.filter(User.subscription_tier.in_(['pro', 'premium'])).count()
    conversion_rate = (paying_users / total_users * 100) if total_users > 0 else 0
    
    analytics_data = {
        'user_registrations': [{'date': str(r.date), 'count': r.count} for r in user_registrations],
        'subscription_stats': [{'tier': r.subscription_tier, 'count': r.count} for r in subscription_stats],
        'usage_stats': [{'date': str(r.date), 'count': r.count} for r in usage_stats],
        'revenue_stats': [{'month': str(r.month), 'revenue': float(r.revenue) / 100} for r in revenue_stats],
        'summary': {
            'total_users': total_users,
            'paying_users': paying_users,
            'conversion_rate': round(conversion_rate, 1),
            'total_revenue': total_revenue,
            'current_mrr': round(current_mrr, 2),
            'active_pro': active_pro,
            'active_premium': active_premium
        }
    }
    
    return render_template('admin/analytics.html', analytics=analytics_data)

@admin_bp.route('/refill-credits', methods=['POST'])
@admin_required
def refill_credits():
    """Manually trigger monthly credit refill for free users"""
    from payments import refill_monthly_credits
    
    try:
        refilled_count = refill_monthly_credits()
        return jsonify({
            'success': True, 
            'message': f'Refilled credits for {refilled_count} free tier users',
            'count': refilled_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
    
    # Get user stats with a single optimized query
    stats_query = db.session.query(
        func.count(User.id).label('total'),
        func.sum(case((User.is_active == True, 1), else_=0)).label('active'),
        func.sum(case((User.email_verified == True, 1), else_=0)).label('verified'),
        func.sum(case((User.subscription_tier == 'free', 1), else_=0)).label('free_tier'),
        func.sum(case((User.subscription_tier == 'pro', 1), else_=0)).label('pro_tier'),
        func.sum(case((User.subscription_tier == 'premium', 1), else_=0)).label('premium_tier')
    ).first()
    
    user_stats = {
        'total': stats_query.total or 0,
        'active': stats_query.active or 0,
        'verified': stats_query.verified or 0,
        'free_tier': stats_query.free_tier or 0,
        'pro_tier': stats_query.pro_tier or 0,
        'premium_tier': stats_query.premium_tier or 0
    }
    
    return render_template('admin/users.html', 
                         users=users_paginated.items,
                         pagination=users_paginated,
                         stats=user_stats)