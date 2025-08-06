"""Main application routes."""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import SavedMealPlan, UsageLog
from app.utils.database_timeout import db_ops, with_database_timeout
from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
from app.services.pdf_generator import PDFGenerator
from app.services.video_generator import VideoGenerator
from app.extensions import db, limiter
from app.utils.decorators import check_credits_or_premium
from datetime import datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/health')
def health_check():
    """Health check endpoint for Railway."""
    return jsonify({
        'status': 'healthy',
        'service': 'cibozer',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

def calculate_user_stats(user_id):
    """Calculate comprehensive user statistics for dashboard."""
    from app.models import SavedMealPlan, UsageLog
    
    # Get all user's meal plans - using ORM for security
    meal_plans = SavedMealPlan.query.filter_by(user_id=user_id).all()
    
    # Get usage logs for streak calculation - using ORM for security
    usage_logs = UsageLog.query.filter_by(
        user_id=user_id,
        action='meal_generation'
    ).order_by(UsageLog.created_at.desc()).all()
    
    # Basic stats
    total_plans = len(meal_plans)
    total_days = sum(plan.days or 1 for plan in meal_plans)
    total_calories = sum(plan.total_calories or 0 for plan in meal_plans)
    
    # Calculate weekly streak
    weekly_streak = calculate_weekly_streak(usage_logs)
    
    # Calculate progress percentage (based on milestones)
    progress_percentage = calculate_progress_percentage(total_plans, weekly_streak, current_user.is_premium())
    
    # Determine next milestone
    next_milestone = get_next_milestone(total_plans, weekly_streak, current_user.is_premium())
    
    # Premium-specific stats
    pdfs_generated = 0
    if current_user.is_premium():
        pdf_logs = UsageLog.query.filter_by(
            user_id=user_id,
            action='pdf_export'
        ).count()
        pdfs_generated = pdf_logs
    
    return {
        'total_plans': total_plans,
        'total_days': total_days,
        'calories_planned': f"{total_calories:,}" if total_calories > 0 else "0",
        'weekly_streak': weekly_streak,
        'progress_percentage': progress_percentage,
        'next_milestone': next_milestone,
        'pdfs_generated': pdfs_generated
    }

def calculate_weekly_streak(usage_logs):
    """Calculate user's weekly streak."""
    if not usage_logs:
        return 0
    
    # Group logs by week
    weekly_activity = {}
    for log in usage_logs:
        # Get Monday of the week for this log
        log_date = log.created_at.date()
        days_since_monday = log_date.weekday()
        monday = log_date - timedelta(days=days_since_monday)
        
        if monday not in weekly_activity:
            weekly_activity[monday] = True
    
    # Calculate consecutive weeks from most recent
    if not weekly_activity:
        return 0
    
    # Get current Monday
    today = datetime.now().date()
    current_monday = today - timedelta(days=today.weekday())
    
    streak = 0
    check_monday = current_monday
    
    # Check consecutive weeks backwards
    while check_monday in weekly_activity:
        streak += 1
        check_monday -= timedelta(days=7)
    
    return streak

def calculate_progress_percentage(total_plans, weekly_streak, is_premium):
    """Calculate overall progress percentage based on milestones."""
    progress = 0
    
    # Account creation (automatic)
    progress += 20
    
    # First meal plan
    if total_plans >= 1:
        progress += 25
    
    # Regular usage (5 plans)
    if total_plans >= 5:
        progress += 20
    
    # Weekly streak
    if weekly_streak >= 1:
        progress += 15
    
    # Premium upgrade
    if is_premium:
        progress += 20
    
    return min(progress, 100)

def get_next_milestone(total_plans, weekly_streak, is_premium):
    """Get the next milestone for the user."""
    if total_plans == 0:
        return "Create your first meal plan"
    elif total_plans < 5:
        return f"Create {5 - total_plans} more meal plans"
    elif weekly_streak == 0:
        return "Build a weekly streak"
    elif not is_premium:
        return "Upgrade to Premium"
    else:
        return "You're doing great! Keep it up!"

@main_bp.route('/setup-db-now')
def setup_db_now():
    """Emergency database setup"""
    try:
        from app.models import db, User
        
        # Create all tables
        db.create_all()
        
        # Create or update admin user
        admin = User.query.filter_by(email='admin@cibozer.com').first()
        if not admin:
            admin = User(
                email='admin@cibozer.com',
                full_name='Administrator',
                subscription_tier='premium',
                subscription_status='active',
                credits_balance=1000,
                is_active=True,
                email_verified=True
            )
            admin.set_password('Login123!')
            db.session.add(admin)
            result = 'Admin user created'
        else:
            admin.set_password('Login123!')
            result = 'Admin password updated to Login123!'
        
        db.session.commit()
        
        return f'<h1>SUCCESS!</h1><p>{result}</p><p>Email: admin@cibozer.com</p><p>Password: Login123!</p><a href="/auth/login">Login Now</a>'
        
    except Exception as e:
        import traceback
        return f'<pre>ERROR: {e}\n\n{traceback.format_exc()}</pre>'

@main_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@main_bp.route('/create')
@login_required
def create_meal_plan():
    """Create meal plan page."""
    return render_template('create_clean.html')

@main_bp.route('/create-new')
@login_required
def create_meal_plan_new():
    """New create meal plan page."""
    return render_template('create_new.html')

@main_bp.route('/generate', methods=['GET', 'POST'])
@login_required
def generate():
    """Generate meal plan page."""
    if request.method == 'GET':
        return render_template('generate.html')
    
    # This will be handled by generate_meal_plan
    return redirect(url_for('main.generate'))

@main_bp.route('/debug-415')
def debug_415():
    """Debug 415 error page."""
    return render_template('debug_415.html')

@main_bp.route('/onboarding')
@login_required
def onboarding():
    """Onboarding flow for new users."""
    return render_template('onboarding.html', user=current_user)

@main_bp.route('/offline')
def offline():
    """Offline page for PWA functionality."""
    return render_template('offline.html')

@main_bp.route('/api/generate-meal-plan', methods=['POST'])
@login_required
@check_credits_or_premium
@limiter.limit("60 per hour")
def generate_meal_plan():
    """Generate a meal plan based on user preferences."""
    try:
        data = request.get_json(force=True)
        
        # Validate input
        required_fields = ['calories', 'diet_type', 'meals_per_day']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Initialize enhanced meal optimizer
        print("DEBUG: About to import EnhancedMealOptimizer")
        try:
            from app.services.enhanced_meal_optimizer import EnhancedMealOptimizer
            print("DEBUG: Import successful")
            optimizer = EnhancedMealOptimizer()
            print(f"DEBUG: Optimizer initialized - class: {type(optimizer).__name__}")
        except Exception as e:
            print(f"DEBUG: Enhanced optimizer failed: {e}")
            print("DEBUG: Falling back to old optimizer")
            from app.services.meal_optimizer import MealOptimizer
            optimizer = MealOptimizer()
            print(f"DEBUG: Using fallback - class: {type(optimizer).__name__}")
        
        # Generate meal plan
        meal_plan = optimizer.generate_meal_plan(
            target_calories=int(data['calories']),
            diet_type=data['diet_type'],
            meals_per_day=int(data['meals_per_day']),
            days=int(data.get('days', 1)),
            restrictions=data.get('restrictions', []),
            cuisine_preference=data.get('cuisine_preference')
        )
        
        print(f"DEBUG: Generated meal plan with variety score: {meal_plan.get('variety_score', 'N/A')}")
        if meal_plan.get('days'):
            day1_meals = [meal['name'] for meal in meal_plan['days'][0]['meals']]
            print(f"DEBUG: Day 1 meals: {day1_meals}")
        
        # Deduct credits if not premium
        if not current_user.is_premium():
            current_user.use_credits(1)
            db.session.commit()
        
        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            action='meal_plan_generated',
            resource_type='meal_plan',
            credits_used=1 if not current_user.is_premium() else 0,
            credits_remaining=current_user.credits_balance,
            metadata={
                'calories': data['calories'],
                'diet_type': data['diet_type'],
                'days': data.get('days', 1)
            }
        )
        db.session.add(usage_log)
        db.session.commit()
        
        # Store in session for later use
        session['last_meal_plan'] = meal_plan
        
        return jsonify({
            'success': True,
            'meal_plan': meal_plan,
            'credits_remaining': current_user.credits_balance
        })
        
    except Exception as e:
        db.session.rollback()
        # Log detailed error for debugging but don't expose to user
        current_app.logger.error(f'Error occurred: {str(e)}', exc_info=True)
        return jsonify({'error': 'An error occurred. Please try again.'}), 500

@main_bp.route('/api/save-meal-plan', methods=['POST'])
@login_required
@with_database_timeout(30)
def save_meal_plan():
    """Save a meal plan to user's account."""
    try:
        data = request.get_json(force=True)
        
        # Use database operation wrapper for timeout protection
        saved_plan = SavedMealPlan(
            user_id=current_user.id,
            name=data.get('name', 'Untitled Meal Plan'),
            meal_plan_data=data['meal_plan'],
            total_calories=data.get('total_calories'),
            diet_type=data.get('diet_type'),
            days=data.get('days', 1)
        )
        
        # Use timeout-protected database operation
        created_plan = db_ops.create(saved_plan)
        
        return jsonify({
            'success': True,
            'meal_plan_id': created_plan.id,
            'message': 'Meal plan saved successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        # Log detailed error for debugging but don't expose to user
        current_app.logger.error(f'Error occurred: {str(e)}', exc_info=True)
        return jsonify({'error': 'An error occurred. Please try again.'}), 500

@main_bp.route('/api/export-pdf/<int:meal_plan_id>')
@login_required
def export_pdf(meal_plan_id):
    """Export meal plan as PDF."""
    try:
        # Get meal plan
        meal_plan = SavedMealPlan.query.get_or_404(meal_plan_id)
        
        # Check ownership
        if meal_plan.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if user can export PDF
        if not current_user.is_premium():
            return jsonify({'error': 'PDF export requires a premium subscription'}), 403
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        pdf_url = pdf_generator.generate_meal_plan_pdf(
            meal_plan.meal_plan_data,
            meal_plan.name
        )
        
        # Update meal plan with PDF URL
        meal_plan.pdf_url = pdf_url
        db.session.commit()
        
        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            action='pdf_exported',
            resource_type='pdf',
            resource_id=str(meal_plan_id)
        )
        db.session.add(usage_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'pdf_url': pdf_url
        })
        
    except Exception as e:
        db.session.rollback()
        # Log detailed error for debugging but don't expose to user
        current_app.logger.error(f'Error occurred: {str(e)}', exc_info=True)
        return jsonify({'error': 'An error occurred. Please try again.'}), 500

@main_bp.route('/api/generate-video/<int:meal_plan_id>')
@login_required
def generate_video(meal_plan_id):
    """Generate video for meal plan."""
    try:
        # Get meal plan
        meal_plan = SavedMealPlan.query.get_or_404(meal_plan_id)
        
        # Check ownership
        if meal_plan.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if user can generate video
        if not current_user.is_premium():
            return jsonify({'error': 'Video generation requires a premium subscription'}), 403
        
        # Generate video
        video_generator = VideoGenerator()
        video_url = video_generator.generate_meal_plan_video(
            meal_plan.meal_plan_data,
            meal_plan.name
        )
        
        # Update meal plan with video URL
        meal_plan.video_url = video_url
        db.session.commit()
        
        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            action='video_generated',
            resource_type='video',
            resource_id=str(meal_plan_id)
        )
        db.session.add(usage_log)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'video_url': video_url
        })
        
    except Exception as e:
        db.session.rollback()
        # Log detailed error for debugging but don't expose to user
        current_app.logger.error(f'Error occurred: {str(e)}', exc_info=True)
        return jsonify({'error': 'An error occurred. Please try again.'}), 500

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with progress tracking."""
    # Get recent meal plans - using ORM for security
    recent_plans = SavedMealPlan.query.filter_by(
        user_id=current_user.id
    ).order_by(SavedMealPlan.created_at.desc()).limit(6).all()
    
    # Calculate user statistics
    user_stats = calculate_user_stats(current_user.id)
    
    return render_template('dashboard.html', 
                         recent_plans=recent_plans,
                         user_stats=user_stats)

@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@main_bp.route('/pricing')
def pricing():
    """Pricing page."""
    return render_template('pricing.html')

@main_bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')