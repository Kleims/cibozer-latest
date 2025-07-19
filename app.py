"""
Cibozer Web Application
Flask-based web interface for AI meal planning and video generation
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
import os
import json
import time
import asyncio
from datetime import datetime
import traceback
import logging
from logging.handlers import RotatingFileHandler
import meal_optimizer as mo
import tempfile
import shutil
from pathlib import Path
from video_service import VideoService
from pdf_generator import PDFGenerator
from admin import admin_bp
from auth import auth_bp
from models import db, User, UsageLog, SavedMealPlan, PricingPlan
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    raise ValueError("SECRET_KEY environment variable must be set")
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///cibozer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.debug = os.environ.get('DEBUG', 'False').lower() == 'true'  # Only enable in development

# Setup comprehensive logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/cibozer.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Cibozer startup')

# Console logging for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.DEBUG)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please sign in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Global request logging
@app.before_request
def log_request_info():
    app.logger.info(f"🌐 REQUEST: {request.method} {request.url}")
    app.logger.info(f"   Remote: {request.remote_addr}")
    app.logger.info(f"   Agent: {request.headers.get('User-Agent', 'N/A')[:100]}")
    if request.method in ['POST', 'PUT', 'PATCH']:
        try:
            if request.is_json:
                app.logger.info(f"   JSON Body: {request.get_json()}")
            elif request.form:
                app.logger.info(f"   Form Data: {dict(request.form)}")
        except Exception as e:
            app.logger.warning(f"   Could not log request body: {e}")

@app.after_request
def log_response_info(response):
    app.logger.info(f"📤 RESPONSE: {response.status_code} for {request.method} {request.path}")
    if response.status_code >= 400:
        app.logger.error(f"   Error Response: {response.get_data(as_text=True)[:500]}")
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "font-src 'self' cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response

# Global error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"🚫 404 ERROR: {request.method} {request.path} not found")
    return jsonify({
        "error": "Route not found",
        "path": request.path,
        "method": request.method,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"💥 500 ERROR: {str(error)}")
    db.session.rollback()
    return jsonify({
        "error": "Internal server error",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 500

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

# Create database tables
with app.app_context():
    db.create_all()
    # Seed default pricing plans
    PricingPlan.seed_default_plans()
    
    # Create admin user if doesn't exist
    admin_user = User.query.filter_by(email='admin').first()
    if not admin_user:
        admin_user = User(
            email='admin',
            full_name='Administrator',
            subscription_tier='premium',
            credits_balance=999999,  # Unlimited credits
            is_active=True
        )
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("✅ Admin user created: admin/admin")

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# SECURITY: Simple rate limiting
request_counts = {}

def rate_limit_check():
    """Simple rate limiting - 3 requests per minute per IP"""
    ip = request.remote_addr
    now = time.time()
    
    if ip in request_counts:
        # Clean old entries
        request_counts[ip] = [req_time for req_time in request_counts[ip] if now - req_time < 60]
        
        # Check limit
        if len(request_counts[ip]) >= 3:
            return False
        
        request_counts[ip].append(now)
    else:
        request_counts[ip] = [now]
    
    return True

# Initialize meal optimizer
optimizer = mo.MealPlanOptimizer()

# Initialize video service
video_service = VideoService(upload_enabled=False)  # Enable uploads when credentials are set

# Initialize PDF generator
pdf_generator = PDFGenerator()

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/generated', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('videos', exist_ok=True)
os.makedirs('logs', exist_ok=True)
os.makedirs('pdfs', exist_ok=True)

# Store section categories
STORE_SECTIONS = {
    'produce': ['apple', 'banana', 'orange', 'lemon', 'lime', 'grape', 'strawberry', 'blueberry', 
                'raspberry', 'blackberry', 'mango', 'pineapple', 'watermelon', 'cantaloupe',
                'carrot', 'celery', 'onion', 'garlic', 'ginger', 'potato', 'sweet_potato',
                'tomato', 'cucumber', 'lettuce', 'spinach', 'kale', 'broccoli', 'cauliflower',
                'bell_pepper', 'mushroom', 'zucchini', 'asparagus', 'green_bean', 'corn',
                'avocado', 'herbs', 'cilantro', 'parsley', 'basil', 'mint'],
    
    'dairy': ['milk', 'cheese', 'yogurt', 'butter', 'cream', 'sour_cream', 'cottage_cheese',
              'cream_cheese', 'mozzarella', 'cheddar', 'parmesan', 'feta', 'egg'],
    
    'meat_seafood': ['chicken', 'beef', 'pork', 'turkey', 'lamb', 'fish', 'salmon', 'tuna',
                     'shrimp', 'crab', 'lobster', 'bacon', 'sausage', 'ham', 'ground_beef',
                     'ground_turkey', 'steak', 'chicken_breast', 'chicken_thigh'],
    
    'bakery': ['bread', 'tortilla', 'pita', 'bagel', 'croissant', 'muffin', 'roll', 'bun'],
    
    'pantry': ['rice', 'pasta', 'noodle', 'quinoa', 'oat', 'flour', 'sugar', 'salt', 'pepper',
               'oil', 'olive_oil', 'vinegar', 'sauce', 'ketchup', 'mustard', 'mayonnaise',
               'honey', 'maple_syrup', 'peanut_butter', 'jam', 'jelly', 'cereal', 'granola',
               'beans', 'lentil', 'chickpea', 'black_bean', 'kidney_bean', 'canned_tomato',
               'tomato_sauce', 'broth', 'stock', 'spices', 'seasoning'],
    
    'frozen': ['frozen_vegetable', 'frozen_fruit', 'ice_cream', 'frozen_meal', 'frozen_pizza'],
    
    'beverages': ['water', 'juice', 'soda', 'coffee', 'tea', 'wine', 'beer', 'milk_alternative'],
    
    'snacks': ['chips', 'crackers', 'popcorn', 'nuts', 'almonds', 'cashews', 'peanuts',
               'chocolate', 'candy', 'cookies', 'protein_bar']
}

def categorize_grocery_items(grocery_dict):
    """Categorize grocery items by store section"""
    categorized = {
        'produce': [],
        'dairy': [],
        'meat_seafood': [],
        'bakery': [],
        'pantry': [],
        'frozen': [],
        'beverages': [],
        'snacks': [],
        'other': []
    }
    
    for item, data in grocery_dict.items():
        item_lower = item.lower()
        categorized_flag = False
        
        # Check each category
        for section, keywords in STORE_SECTIONS.items():
            for keyword in keywords:
                if keyword in item_lower:
                    categorized[section].append({
                        'item': item.replace('_', ' ').title(),
                        'amount': round(data['amount'], 2),
                        'unit': data['unit']
                    })
                    categorized_flag = True
                    break
            if categorized_flag:
                break
        
        # If not categorized, add to 'other'
        if not categorized_flag:
            categorized['other'].append({
                'item': item.replace('_', ' ').title(),
                'amount': round(data['amount'], 2),
                'unit': data['unit']
            })
    
    # Remove empty categories and sort items within each category
    result = {}
    for section, items in categorized.items():
        if items:
            items.sort(key=lambda x: x['item'])
            result[section] = items
    
    return result

@app.route('/')
def index():
    """Main landing page"""
    app.logger.info(f"INDEX route accessed from {request.remote_addr}")
    app.logger.debug(f"Request headers: {dict(request.headers)}")
    
    try:
        app.logger.info("Attempting to render index.html template")
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index.html: {str(e)}")
        app.logger.error(f"Template folder: {app.template_folder}")
        app.logger.error(f"Static folder: {app.static_folder}")
        return jsonify({
            "error": "Template rendering failed",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 500

@app.route('/create')
@login_required
def create_meal_plan():
    """Meal plan creation page"""
    # Get available options from the optimizer
    diet_types = list(optimizer.diet_profiles.keys())
    meal_patterns = list(optimizer.meal_patterns.keys())
    
    return render_template('create.html', 
                         diet_types=diet_types,
                         meal_patterns=meal_patterns,
                         diet_profiles=optimizer.diet_profiles,
                         meal_patterns_data=optimizer.meal_patterns)

@app.route('/api/generate', methods=['POST'])
@login_required
def generate_meal_plan():
    """API endpoint to generate meal plan"""
    
    app.logger.info("🍽️ MEAL PLAN GENERATION STARTED")
    app.logger.info(f"   User: {current_user.email if current_user else 'Unknown'}")
    
    # Check if user can generate plan
    if not current_user.can_generate_plan():
        app.logger.warning(f"   User {current_user.email} has no credits available (balance: {current_user.credits_balance})")
        
        # PRODUCTION: Enforce credit limits properly
        return jsonify({
            'error': 'No credits available',
            'message': 'You have used all your free credits. Upgrade to Pro for unlimited meal plans!',
            'credits_remaining': current_user.credits_balance,
            'upgrade_url': url_for('auth.upgrade') if hasattr(url_for, '__call__') else '/auth/upgrade'
        }), 403
    
    # SECURITY: Check rate limit first
    if not rate_limit_check():
        app.logger.warning(f"   Rate limit exceeded for user {current_user.email}")
        return jsonify({'error': 'Rate limit exceeded. Please wait a minute.'}), 429
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        app.logger.info(f"   Request data: {dict(data) if data else 'None'}")
        
        # Extract parameters
        diet_type = data.get('diet_type', 'standard')
        calories = int(data.get('calories', 2000))
        pattern = data.get('pattern', 'standard')
        restrictions = data.get('restrictions', [])
        days = int(data.get('days', 1))  # New: number of days
        
        app.logger.info(f"   Parameters: diet={diet_type}, calories={calories}, pattern={pattern}, days={days}")
        app.logger.info(f"   Restrictions: {restrictions}")
        
        # Validate inputs
        if diet_type not in optimizer.diet_profiles:
            app.logger.error(f"   Invalid diet type: {diet_type}")
            app.logger.error(f"   Available diet types: {list(optimizer.diet_profiles.keys())}")
            return jsonify({'error': 'Invalid diet type'}), 400
        
        if not (800 <= calories <= 5000):
            app.logger.error(f"   Invalid calories: {calories}")
            return jsonify({'error': 'Calories must be between 800 and 5000'}), 400
        
        if pattern not in optimizer.meal_patterns:
            app.logger.error(f"   Invalid pattern: {pattern}")
            app.logger.error(f"   Available patterns: {list(optimizer.meal_patterns.keys())}")
            return jsonify({'error': 'Invalid meal pattern'}), 400
            
        if not (1 <= days <= 7):
            app.logger.error(f"   Invalid days: {days}")
            return jsonify({'error': 'Days must be between 1 and 7'}), 400
        
        # Create preferences
        preferences = {
            'diet': diet_type,
            'calories': calories,
            'pattern': pattern,
            'restrictions': restrictions if isinstance(restrictions, list) else [],
            'cuisines': ['all'],
            'cooking_methods': ['all'],
            'measurement_system': 'US',
            'allow_substitutions': True,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate meal plans for requested days
        app.logger.info("   Starting meal plan generation...")
        start_time = time.time()
        
        if days == 1:
            # Single day plan
            app.logger.info("   Generating single day plan...")
            try:
                day_meals, metrics = optimizer.generate_single_day_plan(preferences)
                app.logger.info(f"   Generated {len(day_meals)} meals")
                app.logger.info(f"   Meals: {list(day_meals.keys())}")
                
                totals = optimizer.calculate_day_totals(day_meals)
                app.logger.info(f"   Totals calculated: {totals}")
            except Exception as e:
                app.logger.error(f"   Error generating single day plan: {str(e)}")
                app.logger.error(f"   Exception type: {type(e).__name__}")
                import traceback
                app.logger.error(f"   Traceback: {traceback.format_exc()}")
                raise
            
            response = {
                'success': True,
                'meal_plan': {
                    'meals': day_meals,
                    'totals': totals,
                    'preferences': preferences,
                    'metrics': {
                        'generation_time': round(time.time() - start_time, 2),
                        'accuracy': metrics.get('final_accuracy', 0),
                        'iterations': metrics.get('iterations', 0),
                        'convergence_achieved': metrics.get('convergence_achieved', False)
                    }
                }
            }
            
            # Log usage for single day
            if not current_user.is_premium():
                current_user.use_credits(1)
            
            app.logger.info(f"   Response prepared successfully")
            app.logger.info(f"   Generation time: {round(time.time() - start_time, 2)}s")
            
            usage_log = UsageLog(
                user_id=current_user.id,
                action_type='generate_plan',
                credits_used=1 if not current_user.is_premium() else 0,
                extra_data={
                    'diet_type': diet_type,
                    'calories': calories,
                    'days': 1,
                    'pattern': pattern
                }
            )
            db.session.add(usage_log)
            db.session.commit()
            app.logger.info(f"   Usage logged successfully")
        else:
            # Multiple day plan
            week_plan = {}
            week_totals = {}
            total_metrics = {
                'iterations': 0,
                'accuracy': 0,
                'convergence_achieved': True
            }
            
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for i in range(days):
                day_name = day_names[i]
                day_meals, metrics = optimizer.generate_single_day_plan(preferences)
                week_plan[day_name] = day_meals
                week_totals[day_name] = optimizer.calculate_day_totals(day_meals)
                
                # Aggregate metrics
                total_metrics['iterations'] += metrics.get('iterations', 0)
                total_metrics['accuracy'] += metrics.get('final_accuracy', 0)
                total_metrics['convergence_achieved'] &= metrics.get('convergence_achieved', False)
            
            # Calculate average metrics
            total_metrics['accuracy'] = round(total_metrics['accuracy'] / days, 1)
            
            # Calculate week summary
            week_summary = {
                'avg_calories': round(sum(t['calories'] for t in week_totals.values()) / days),
                'avg_protein': round(sum(t['protein'] for t in week_totals.values()) / days),
                'avg_carbs': round(sum(t['carbs'] for t in week_totals.values()) / days),
                'avg_fat': round(sum(t['fat'] for t in week_totals.values()) / days),
                'total_days': days
            }
            
            response = {
                'success': True,
                'meal_plan': {
                    'is_weekly': True,
                    'days': week_plan,
                    'daily_totals': week_totals,
                    'week_summary': week_summary,
                    'preferences': preferences,
                    'metrics': {
                        'generation_time': round(time.time() - start_time, 2),
                        'accuracy': total_metrics['accuracy'],
                        'iterations': total_metrics['iterations'],
                        'convergence_achieved': total_metrics['convergence_achieved']
                    }
                }
            }
        
        # Log usage and deduct credits if not premium
        if not current_user.is_premium():
            credits_used = min(days, 3)  # Cap at 3 credits for weekly plans
            current_user.use_credits(credits_used)
        
        usage_log = UsageLog(
            user_id=current_user.id,
            action_type='generate_plan',
            credits_used=credits_used if not current_user.is_premium() else 0,
            metadata={
                'diet_type': diet_type,
                'calories': calories,
                'days': days,
                'pattern': pattern
            }
        )
        db.session.add(usage_log)
        db.session.commit()
        
        app.logger.info("🎉 MEAL PLAN GENERATION COMPLETED SUCCESSFULLY")
        return jsonify(response)
        
    except Exception as e:
        app.logger.error("💥 MEAL PLAN GENERATION FAILED")
        app.logger.error(f"   Error: {str(e)}")
        app.logger.error(f"   Exception type: {type(e).__name__}")
        import traceback
        app.logger.error(f"   Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Failed to generate meal plan',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }), 500

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """API endpoint to generate video from meal plan"""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        platforms = data.get('platforms', ['youtube_shorts'])
        voice = data.get('voice', 'christopher')
        auto_upload = data.get('auto_upload', False)
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Run async video generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(
                video_service.generate_and_upload_videos(
                    meal_plan, platforms, voice, auto_upload
                )
            )
            
            # Extract video paths for response
            video_urls = {}
            for platform, result in results['generation'].items():
                if result['status'] == 'success' and result['video_path']:
                    # Convert to relative URL
                    video_urls[platform] = result['video_path'].replace('\\', '/')
            
            return jsonify({
                'success': True,
                'video_urls': video_urls,
                'upload_results': results['upload'],
                'summary': results['summary'],
                'message': f"Generated {results['summary']['successful_generations']} videos"
            })
            
        finally:
            loop.close()
        
    except Exception as e:
        print(f"Error generating video: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to generate video',
            'details': str(e)
        }), 500

@app.route('/api/export-grocery-list', methods=['POST'])
def export_grocery_list():
    """API endpoint to export grocery list"""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate grocery list
        grocery_list = {}
        
        # Check if it's a weekly plan
        if meal_plan.get('is_weekly'):
            # Process weekly plan
            for day_name, day_meals in meal_plan.get('days', {}).items():
                for meal_name, meal_data in day_meals.items():
                    for ingredient in meal_data.get('ingredients', []):
                        item = ingredient.get('item', '')
                        amount = ingredient.get('amount', 0)
                        unit = ingredient.get('unit', 'g')
                        
                        if item not in grocery_list:
                            grocery_list[item] = {'amount': 0, 'unit': unit}
                        grocery_list[item]['amount'] += amount
        else:
            # Process single day plan
            meals = meal_plan.get('meals', {})
            for meal_name, meal_data in meals.items():
                for ingredient in meal_data.get('ingredients', []):
                    item = ingredient.get('item', '')
                    amount = ingredient.get('amount', 0)
                    unit = ingredient.get('unit', 'g')
                    
                    if item not in grocery_list:
                        grocery_list[item] = {'amount': 0, 'unit': unit}
                    grocery_list[item]['amount'] += amount
        
        # Categorize items by store section
        store_sections = categorize_grocery_items(grocery_list)
        
        # Format for display
        formatted_list = []
        for item, data in grocery_list.items():
            formatted_list.append({
                'item': item.replace('_', ' ').title(),
                'amount': round(data['amount'], 2),
                'unit': data['unit']
            })
        
        formatted_list.sort(key=lambda x: x['item'])
        
        return jsonify({
            'success': True,
            'grocery_list': formatted_list,
            'categorized_list': store_sections
        })
        
    except Exception as e:
        print(f"Error exporting grocery list: {e}")
        return jsonify({
            'error': 'Failed to export grocery list',
            'details': str(e)
        }), 500

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/api/video/platforms')
def get_video_platforms():
    """Get available video platforms"""
    return jsonify(video_service.get_platform_info())

@app.route('/api/video/stats')
def get_video_stats():
    """Get video generation statistics"""
    return jsonify(video_service.get_video_stats())

@app.route('/api/video/test-voice', methods=['POST'])
def test_voice():
    """Test voice generation"""
    try:
        data = request.get_json()
        text = data.get('text', 'Hello! This is a test of Edge TTS Christopher voice.')
        
        # Run async voice test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            audio_path = loop.run_until_complete(
                video_service.test_voice_generation(text)
            )
            
            return jsonify({
                'success': True,
                'audio_path': audio_path.replace('\\', '/'),
                'message': 'Voice test successful'
            })
            
        finally:
            loop.close()
            
    except Exception as e:
        print(f"Error testing voice: {e}")
        return jsonify({
            'error': 'Failed to test voice',
            'details': str(e)
        }), 500

@app.route('/videos/<path:filename>')
def serve_video(filename):
    """Serve generated video files"""
    try:
        video_path = os.path.join('videos', filename)
        if os.path.exists(video_path):
            return send_file(video_path, mimetype='video/mp4')
        else:
            return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to serve video', 'details': str(e)}), 500

@app.route('/api/save-meal-plan', methods=['POST'])
def save_meal_plan():
    """Save meal plan to storage"""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        name = data.get('name', f'meal_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_name = safe_name[:50]  # Limit length
        
        # Create saved_plans directory if it doesn't exist
        os.makedirs('saved_plans', exist_ok=True)
        
        # Save to JSON file
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join('saved_plans', filename)
        
        save_data = {
            'name': name,
            'created_at': datetime.now().isoformat(),
            'meal_plan': meal_plan
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Meal plan saved as "{name}"'
        })
        
    except Exception as e:
        print(f"Error saving meal plan: {e}")
        return jsonify({
            'error': 'Failed to save meal plan',
            'details': str(e)
        }), 500

@app.route('/api/load-meal-plans')
def load_meal_plans():
    """Load list of saved meal plans"""
    try:
        saved_plans_dir = 'saved_plans'
        if not os.path.exists(saved_plans_dir):
            return jsonify({'plans': []})
        
        plans = []
        for filename in os.listdir(saved_plans_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(saved_plans_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        plans.append({
                            'filename': filename,
                            'name': data.get('name', 'Unnamed'),
                            'created_at': data.get('created_at', ''),
                            'calories': data.get('meal_plan', {}).get('totals', {}).get('calories', 0),
                            'diet_type': data.get('meal_plan', {}).get('preferences', {}).get('diet', 'Unknown')
                        })
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        # Sort by creation date (newest first)
        plans.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'plans': plans})
        
    except Exception as e:
        print(f"Error loading meal plans: {e}")
        return jsonify({
            'error': 'Failed to load meal plans',
            'details': str(e)
        }), 500

@app.route('/api/load-meal-plan/<filename>')
def load_meal_plan(filename):
    """Load a specific meal plan"""
    try:
        # Sanitize filename
        if not filename.endswith('.json') or '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join('saved_plans', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Meal plan not found'}), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
        
    except Exception as e:
        print(f"Error loading meal plan: {e}")
        return jsonify({
            'error': 'Failed to load meal plan',
            'details': str(e)
        }), 500

@app.route('/api/delete-meal-plan/<filename>', methods=['DELETE'])
def delete_meal_plan(filename):
    """Delete a saved meal plan"""
    try:
        # Sanitize filename
        if not filename.endswith('.json') or '..' in filename or '/' in filename:
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join('saved_plans', filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Meal plan not found'}), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Meal plan deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting meal plan: {e}")
        return jsonify({
            'error': 'Failed to delete meal plan',
            'details': str(e)
        }), 500

@app.route('/api/export-pdf', methods=['POST'])
def export_pdf():
    """Export meal plan as PDF"""
    try:
        data = request.get_json()
        meal_plan = data.get('meal_plan')
        export_type = data.get('type', 'meal_plan')  # 'meal_plan' or 'grocery_list'
        
        if not meal_plan:
            return jsonify({'error': 'No meal plan provided'}), 400
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_type == 'grocery_list':
            # Export grocery list
            grocery_list = []
            days = 1
            
            if meal_plan.get('is_weekly'):
                days = len(meal_plan.get('days', {}))
                for day_meals in meal_plan.get('days', {}).values():
                    for meal_data in day_meals.values():
                        for ingredient in meal_data.get('ingredients', []):
                            grocery_list.append(ingredient)
            else:
                for meal_data in meal_plan.get('meals', {}).values():
                    for ingredient in meal_data.get('ingredients', []):
                        grocery_list.append(ingredient)
            
            # Aggregate ingredients
            aggregated = {}
            for item in grocery_list:
                key = item.get('item', '')
                if key not in aggregated:
                    aggregated[key] = {'amount': 0, 'unit': item.get('unit', '')}
                aggregated[key]['amount'] += item.get('amount', 0)
            
            # Format for PDF
            formatted_list = []
            for item_name, data in aggregated.items():
                formatted_list.append({
                    'item': item_name.replace('_', ' ').title(),
                    'amount': round(data['amount'], 2),
                    'unit': data['unit']
                })
            formatted_list.sort(key=lambda x: x['item'])
            
            filename = f'grocery_list_{timestamp}.pdf'
            filepath = os.path.join('pdfs', filename)
            pdf_generator.generate_grocery_list_pdf(formatted_list, filepath, days)
            
        else:
            # Export full meal plan
            filename = f'meal_plan_{timestamp}.pdf'
            filepath = os.path.join('pdfs', filename)
            pdf_generator.generate_meal_plan_pdf(meal_plan, filepath)
        
        # Return file for download
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Error exporting PDF: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to export PDF',
            'details': str(e)
        }), 500

# DEBUG ENDPOINT REMOVED FOR SECURITY
# Use /api/generate with proper authentication instead

@app.route('/api/user-status')
@login_required
def user_status():
    """Get current user status and credits"""
    return jsonify({
        'user': {
            'email': current_user.email,
            'credits_balance': current_user.credits_balance,
            'is_premium': current_user.is_premium(),
            'can_generate_plan': current_user.can_generate_plan(),
            'subscription_tier': current_user.subscription_tier
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        app.logger.error(f"Database health check failed: {str(e)}")
        db_status = 'unhealthy'
    
    # Test meal optimizer
    try:
        optimizer_test = len(optimizer.diet_profiles) > 0
        optimizer_status = 'healthy' if optimizer_test else 'unhealthy'
    except Exception as e:
        app.logger.error(f"Optimizer health check failed: {str(e)}")
        optimizer_status = 'unhealthy'
    
    overall_status = 'healthy' if all([
        db_status == 'healthy',
        optimizer_status == 'healthy'
    ]) else 'unhealthy'
    
    response = {
        'status': overall_status,
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'checks': {
            'database': db_status,
            'meal_optimizer': optimizer_status
        },
        'uptime': 'active'
    }
    
    status_code = 200 if overall_status == 'healthy' else 503
    return jsonify(response), status_code

@app.route('/api/metrics')
def metrics():
    """Basic metrics endpoint for monitoring"""
    try:
        # Get user counts
        total_users = User.query.count()
        active_users = User.query.filter(User.is_active == True).count()
        premium_users = User.query.filter(User.subscription_tier.in_(['pro', 'premium'])).count()
        
        # Get usage stats from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_plans = UsageLog.query.filter(
            UsageLog.timestamp >= yesterday,
            UsageLog.action_type == 'generate_plan'
        ).count()
        
        return jsonify({
            'users': {
                'total': total_users,
                'active': active_users,
                'premium': premium_users
            },
            'usage': {
                'meal_plans_24h': recent_plans
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Metrics endpoint failed: {str(e)}")
        return jsonify({'error': 'Metrics unavailable'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting Cibozer Web Application...")
    print("Visit: http://localhost:5001")
    print("TROUBLESHOOT: Running on port 5001 to avoid conflicts")
    app.run(debug=os.environ.get('DEBUG', 'False').lower() == 'true', host='127.0.0.1', port=5001)