"""Main application routes."""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import SavedMealPlan, UsageLog
from app.services.meal_optimizer import MealOptimizer
from app.services.pdf_generator import PDFGenerator
from app.services.video_generator import VideoGenerator
from app.extensions import db, limiter
from app.utils.decorators import check_credits_or_premium

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@main_bp.route('/create')
@login_required
def create_meal_plan():
    """Create meal plan page."""
    return render_template('create.html')

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

@main_bp.route('/api/generate-meal-plan', methods=['POST'])
@login_required
@check_credits_or_premium
@limiter.limit("10 per hour")
def generate_meal_plan():
    """Generate a meal plan based on user preferences."""
    try:
        data = request.get_json()
        
        # Validate input
        required_fields = ['calories', 'diet_type', 'meals_per_day']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Initialize meal optimizer
        optimizer = MealOptimizer()
        
        # Generate meal plan
        meal_plan = optimizer.generate_meal_plan(
            target_calories=int(data['calories']),
            diet_type=data['diet_type'],
            meals_per_day=int(data['meals_per_day']),
            days=int(data.get('days', 1)),
            restrictions=data.get('restrictions', []),
            cuisine_preference=data.get('cuisine_preference')
        )
        
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
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/save-meal-plan', methods=['POST'])
@login_required
def save_meal_plan():
    """Save a meal plan to user's account."""
    try:
        data = request.get_json()
        
        saved_plan = SavedMealPlan(
            user_id=current_user.id,
            name=data.get('name', 'Untitled Meal Plan'),
            meal_plan_data=data['meal_plan'],
            total_calories=data.get('total_calories'),
            diet_type=data.get('diet_type'),
            days=data.get('days', 1)
        )
        
        db.session.add(saved_plan)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'meal_plan_id': saved_plan.id,
            'message': 'Meal plan saved successfully!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard."""
    meal_plans = db.session.query(SavedMealPlan).filter_by(
        user_id=current_user.id
    ).order_by(SavedMealPlan.created_at.desc()).limit(10).all()
    
    return render_template('index.html', meal_plans=meal_plans)

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