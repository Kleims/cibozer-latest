"""API routes for Cibozer."""
import os
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app.models import User, UsageLog, SavedMealPlan
from app.services.meal_optimizer import MealOptimizer
from app.services.pdf_generator import PDFGenerator
from app.services.video_generator import VideoGenerator
from app.extensions import db, csrf
from app.utils.decorators import check_credits_or_premium
from app.utils.validators import sanitize_input

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Rate limiting helper
def rate_limit_check(user_id, action='api_call', limit=10, window=3600):
    """Check if user has exceeded rate limit."""
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=window)
    recent_count = UsageLog.query.filter(
        UsageLog.user_id == user_id,
        UsageLog.action == action,
        UsageLog.created_at > cutoff
    ).count()
    return recent_count < limit

@api_bp.route('/generate', methods=['POST'])
@login_required
@check_credits_or_premium
def generate_meal_plan():
    """Generate a meal plan based on user preferences."""
    try:
        # Rate limiting
        if not current_user.is_premium() and not rate_limit_check(current_user.id, 'meal_generation'):
            return jsonify({
                'error': 'Rate limit exceeded. Please try again later.',
                'rate_limit': True
            }), 429
        
        data = request.get_json()
        
        # Validate and sanitize input
        calories = int(data.get('calories', 2000))
        diet_type = sanitize_input(data.get('diet_type', 'standard'))
        meals_per_day = int(data.get('meals_per_day', 3))
        days = int(data.get('days', 1))
        restrictions = data.get('restrictions', [])
        cuisine = sanitize_input(data.get('cuisine_preference'))
        
        # Initialize optimizer
        optimizer = MealOptimizer()
        
        # Generate meal plan
        meal_plan = optimizer.generate_meal_plan(
            target_calories=calories,
            diet_type=diet_type,
            meals_per_day=meals_per_day,
            days=days,
            restrictions=restrictions,
            cuisine_preference=cuisine
        )
        
        # Format for frontend
        formatted_plan = format_meal_plan_for_frontend(meal_plan)
        
        # Deduct credits if not premium
        if not current_user.is_premium():
            current_user.use_credits(1)
            db.session.commit()
        
        # Log usage
        log_usage('meal_generation', {
            'calories': calories,
            'diet_type': diet_type,
            'days': days
        })
        
        return jsonify({
            'success': True,
            'meal_plan': formatted_plan,
            'credits_remaining': current_user.credits_balance
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating meal plan: {str(e)}")
        return jsonify({'error': 'Failed to generate meal plan'}), 500

@api_bp.route('/export-grocery-list', methods=['POST'])
@login_required
def export_grocery_list():
    """Export grocery list from meal plan."""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Extract and categorize ingredients
        grocery_list = categorize_grocery_items(meal_plan)
        
        # Create text file
        grocery_text = generate_grocery_list_text(grocery_list)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
        temp_file.write(grocery_text)
        temp_file.close()
        
        # Log usage
        log_usage('grocery_export')
        
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'grocery_list_{datetime.now().strftime("%Y%m%d")}.txt',
            mimetype='text/plain'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting grocery list: {str(e)}")
        return jsonify({'error': 'Failed to export grocery list'}), 500

@api_bp.route('/save-meal-plan', methods=['POST'])
@login_required
def save_meal_plan():
    """Save meal plan to database."""
    try:
        data = request.get_json()
        
        name = sanitize_input(data.get('name', 'Untitled Meal Plan'))
        meal_plan_data = data.get('meal_plan')
        
        if not meal_plan_data:
            return jsonify({'error': 'No meal plan data provided'}), 400
        
        # Create saved meal plan
        saved_plan = SavedMealPlan(
            user_id=current_user.id,
            name=name,
            meal_plan_data=meal_plan_data,
            total_calories=meal_plan_data.get('total_calories'),
            diet_type=meal_plan_data.get('diet_type'),
            days=len(meal_plan_data.get('days', []))
        )
        
        db.session.add(saved_plan)
        db.session.commit()
        
        # Log usage
        log_usage('meal_plan_saved', {'plan_id': saved_plan.id})
        
        return jsonify({
            'success': True,
            'id': saved_plan.id,
            'message': 'Meal plan saved successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving meal plan: {str(e)}")
        return jsonify({'error': 'Failed to save meal plan'}), 500

@api_bp.route('/load-meal-plans', methods=['GET'])
@login_required
def load_meal_plans():
    """Load user's saved meal plans."""
    try:
        plans = SavedMealPlan.query.filter_by(
            user_id=current_user.id
        ).order_by(SavedMealPlan.created_at.desc()).all()
        
        plans_data = [{
            'id': plan.id,
            'name': plan.name,
            'created_at': plan.created_at.isoformat(),
            'total_calories': plan.total_calories,
            'diet_type': plan.diet_type,
            'days': plan.days
        } for plan in plans]
        
        return jsonify({
            'success': True,
            'meal_plans': plans_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading meal plans: {str(e)}")
        return jsonify({'error': 'Failed to load meal plans'}), 500

@api_bp.route('/load-meal-plan/<int:plan_id>', methods=['GET'])
@login_required
def load_meal_plan(plan_id):
    """Load specific meal plan."""
    try:
        plan = SavedMealPlan.query.filter_by(
            id=plan_id,
            user_id=current_user.id
        ).first()
        
        if not plan:
            return jsonify({'error': 'Meal plan not found'}), 404
        
        return jsonify({
            'success': True,
            'meal_plan': plan.meal_plan_data,
            'name': plan.name
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading meal plan: {str(e)}")
        return jsonify({'error': 'Failed to load meal plan'}), 500

@api_bp.route('/delete-meal-plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_meal_plan(plan_id):
    """Delete saved meal plan."""
    try:
        plan = SavedMealPlan.query.filter_by(
            id=plan_id,
            user_id=current_user.id
        ).first()
        
        if not plan:
            return jsonify({'error': 'Meal plan not found'}), 404
        
        # Delete associated files if they exist
        if plan.pdf_url:
            try:
                os.remove(plan.pdf_url)
            except:
                pass
        
        if plan.video_url:
            try:
                os.remove(plan.video_url)
            except:
                pass
        
        db.session.delete(plan)
        db.session.commit()
        
        # Log usage
        log_usage('meal_plan_deleted', {'plan_id': plan_id})
        
        return jsonify({
            'success': True,
            'message': 'Meal plan deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting meal plan: {str(e)}")
        return jsonify({'error': 'Failed to delete meal plan'}), 500

@api_bp.route('/export-pdf', methods=['POST'])
@login_required
def export_pdf():
    """Export meal plan as PDF."""
    try:
        if not current_user.is_premium():
            return jsonify({'error': 'PDF export requires a premium subscription'}), 403
        
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        title = sanitize_input(data.get('title', 'My Meal Plan'))
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate PDF
        pdf_generator = PDFGenerator()
        pdf_path = pdf_generator.generate_meal_plan_pdf(meal_plan, title)
        
        # Log usage
        log_usage('pdf_export')
        
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f'meal_plan_{datetime.now().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error exporting PDF: {str(e)}")
        return jsonify({'error': 'Failed to export PDF'}), 500

@api_bp.route('/generate-video', methods=['POST'])
@login_required
def generate_video():
    """Generate video from meal plan."""
    try:
        if not current_user.is_premium():
            return jsonify({'error': 'Video generation requires a premium subscription'}), 403
        
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        platform = data.get('platform', 'youtube')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate video
        video_generator = VideoGenerator()
        video_url = video_generator.generate_meal_plan_video(
            meal_plan,
            platform=platform
        )
        
        # Log usage
        log_usage('video_generation', {'platform': platform})
        
        return jsonify({
            'success': True,
            'video_url': video_url
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating video: {str(e)}")
        return jsonify({'error': 'Failed to generate video'}), 500

@api_bp.route('/user-status', methods=['GET'])
@login_required
def user_status():
    """Get current user status."""
    return jsonify({
        'email': current_user.email,
        'subscription_tier': current_user.subscription_tier,
        'is_premium': current_user.is_premium(),
        'credits_balance': current_user.credits_balance,
        'subscription_status': current_user.subscription_status
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint."""
    try:
        # Get basic metrics
        user_count = User.query.count()
        meal_plan_count = SavedMealPlan.query.count()
        
        return jsonify({
            'users': user_count,
            'meal_plans': meal_plan_count,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except:
        return jsonify({'error': 'Failed to get metrics'}), 500

# Helper functions
def format_meal_plan_for_frontend(meal_plan):
    """Format meal plan for frontend consumption."""
    # Implementation would go here
    return meal_plan

def categorize_grocery_items(meal_plan):
    """Categorize grocery items by store section."""
    categories = {
        'produce': [],
        'meat': [],
        'dairy': [],
        'pantry': [],
        'frozen': [],
        'other': []
    }
    
    # Extract ingredients from meal plan
    for day in meal_plan.get('days', []):
        for meal in day.get('meals', []):
            for ingredient in meal.get('ingredients', []):
                # Simple categorization logic
                # In production, this would be more sophisticated
                categories['other'].append(ingredient)
    
    return categories

def generate_grocery_list_text(grocery_list):
    """Generate formatted grocery list text."""
    text = "GROCERY LIST\n"
    text += "=" * 40 + "\n\n"
    
    for category, items in grocery_list.items():
        if items:
            text += f"{category.upper()}\n"
            text += "-" * 20 + "\n"
            for item in items:
                text += f"• {item}\n"
            text += "\n"
    
    return text

def log_usage(action, metadata=None):
    """Log user action."""
    try:
        usage_log = UsageLog(
            user_id=current_user.id,
            action=action,
            metadata=metadata or {},
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            endpoint=request.endpoint,
            method=request.method
        )
        db.session.add(usage_log)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(f"Failed to log usage: {str(e)}")