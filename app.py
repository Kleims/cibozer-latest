"""
Cibozer Web Application
Flask-based web interface for AI meal planning and video generation
"""

# Standard library imports
import asyncio
import json
import logging
import logging.config
import os
import shutil
import tempfile
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Third-party imports
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Local application imports
import meal_optimizer as mo
from admin import admin_bp
from app_config import get_app_config, validate_config
from auth import auth_bp
from logging_setup import setup_app_logging, get_logger, log_execution_time, audit_logger
from meal_optimizer_web import get_web_optimizer
from middleware import (
    validate_request, MealPlanRequestSchema, VideoGenerationRequestSchema,
    ExportGroceryListSchema, SaveMealPlanSchema, ExportPDFSchema, 
    TestVoiceSchema, FrontendLogsSchema, sanitize_input, validate_json_request
)
from models import db, User, UsageLog, SavedMealPlan, PricingPlan
from payments import payments_bp, check_user_credits, deduct_credit
from pdf_generator import PDFGenerator
from share_routes import share_bp
# Removed redundant simple_logger import - using logging_setup instead
from utils.security import (
    secure_path_join, validate_json_filename, validate_video_filename, 
    validate_pdf_filename, validate_secret_key, SecurityError
)
from video_service import VideoService

# Load environment variables
load_dotenv()

# Load and validate centralized configuration
if not validate_config():
    raise ValueError("Configuration validation failed. Check your environment variables.")

config = get_app_config()

# Initialize Flask app with centralized config
app = Flask(__name__)

# Add request logging using the centralized logger
logger = get_logger(__name__)

# Removed duplicate logging decorators - consolidated below
app.config.update(config.to_flask_config())

# Set up centralized logging
setup_app_logging(app)

# Validate SECRET_KEY strength
if not config.flask.DEBUG and not validate_secret_key(config.flask.SECRET_KEY):
    app.logger.warning("[SECURITY] Weak SECRET_KEY detected. Please use a stronger key.")
    app.logger.info("[SECURITY] Generate a secure key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'")

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
CORS(app)
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access with detailed logging"""
    app.logger.error(f"[UNAUTHORIZED] Attempted to access: {request.endpoint}")
    app.logger.error(f"[UNAUTHORIZED] Request URL: {request.url}")
    app.logger.error(f"[UNAUTHORIZED] Request path: {request.path}")
    app.logger.error(f"[UNAUTHORIZED] Request method: {request.method}")
    
    # Store the target URL
    next_url = request.url
    app.logger.error(f"[UNAUTHORIZED] Setting next URL to: {next_url}")
    
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('auth.login', next=next_url))
login_manager.login_message = 'Please sign in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Optimized request logging - single instance
@app.before_request
def log_request_info():
    try:
        user = current_user.email if current_user.is_authenticated else "anonymous"
    except Exception:
        user = "anonymous"
    
    # Only log essential info to reduce performance impact
    app.logger.info(f"[REQ] {request.method} {request.path} | User: {user}")

@app.after_request
def log_response_info(response):
    try:
        user = current_user.email if current_user.is_authenticated else "anonymous"
    except Exception:
        user = "anonymous"
    
    # Only log errors and essential info
    if response.status_code >= 400:
        app.logger.error(f"[RESP] {response.status_code} for {request.method} {request.path} | User: {user}")
    
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
    app.logger.warning(f"[404] {request.method} {request.path} not found")
    return jsonify({
        "error": "Route not found",
        "path": request.path,
        "method": request.method,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"[500] Internal server error: {str(error)}")
    log_error(f"[500] Internal server error: {str(error)}")
    log_error(f"[500] Request path: {request.path}")
    log_error(f"[500] Request method: {request.method}")
    
    # Check if it's a template error
    if "Could not build url" in str(error) or "url_for" in str(error):
        log_error(f"[500] Template/URL error detected: {str(error)}")
        import traceback
        log_error(f"[500] Traceback: {traceback.format_exc()}")
    
    db.session.rollback()
    return render_template('error.html', error=str(error)), 500

# Register blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(payments_bp)
app.register_blueprint(share_bp)

# Create database tables
with app.app_context():
    db.create_all()
    # Seed default pricing plans
    PricingPlan.seed_default_plans()
    
    # Create admin user if doesn't exist
    # Only create admin user if credentials are provided in environment
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@cibozer.com')
    admin_password = os.environ.get('ADMIN_PASSWORD')
    
    if admin_password:
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                full_name='Administrator',
                subscription_tier='premium',
                credits_balance=999999,  # Unlimited credits
                is_active=True
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info(f"Admin user created: {admin_email}")
    else:
        app.logger.warning("ADMIN_PASSWORD not set - admin user creation skipped. Run create_admin.py to create admin.")

# Configuration
# Additional Flask config from centralized configuration
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.security.MAX_CONTENT_LENGTH

# Clear template cache to ensure we get fresh templates
app.jinja_env.cache = {}
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

# SECURITY: Configurable rate limiting
request_counts = {}
RATE_LIMIT_REQUESTS = int(config.security.RATE_LIMIT_DEFAULT.split()[0])  # Extract number from "10 per minute"
RATE_LIMIT_WINDOW = 60  # seconds

def rate_limit_check():
    """Configurable rate limiting based on centralized config"""
    if not config.security.RATE_LIMIT_ENABLED:
        return True
        
    ip = request.remote_addr
    now = time.time()
    
    if ip in request_counts:
        # Clean old entries based on configured window
        request_counts[ip] = [req_time for req_time in request_counts[ip] if now - req_time < RATE_LIMIT_WINDOW]
        
        # Check limit based on configuration
        if len(request_counts[ip]) >= RATE_LIMIT_REQUESTS:
            app.logger.warning(f"Rate limit exceeded for IP {ip}: {len(request_counts[ip])} requests in last {RATE_LIMIT_WINDOW}s")
            return False
        
        request_counts[ip].append(now)
    else:
        request_counts[ip] = [now]
    
    return True

# Initialize meal optimizer
try:
    # Use web-safe optimizer to prevent input() crashes
    optimizer = get_web_optimizer()
    app.logger.info("[OK] Meal optimizer initialized successfully")
except Exception as e:
    app.logger.error(f"[ERROR] Failed to initialize meal optimizer: {str(e)}")
    raise RuntimeError(f"Critical: Meal optimizer initialization failed: {str(e)}")

# Initialize video service (optional - don't crash if fails)
try:
    # Check if social media credentials exist
    import os
    credentials_exist = os.path.exists('social_credentials.json')
    from video_service import VideoService
    video_service = VideoService(upload_enabled=credentials_exist)
    
    if credentials_exist:
        app.logger.info("[OK] Video service initialized with upload capabilities")
    else:
        app.logger.info("[OK] Video service initialized (uploads disabled - no credentials)")
        app.logger.info("[INFO] To enable uploads: copy social_credentials_template.json to social_credentials.json and configure")
except ImportError as e:
    app.logger.warning(f"[WARN] Video service module not found: {str(e)}")
    video_service = None
except Exception as e:
    app.logger.warning(f"[WARN] Video service initialization failed: {str(e)}")
    video_service = None

# Initialize PDF generator
try:
    pdf_generator = PDFGenerator()
    app.logger.info("[OK] PDF generator initialized successfully")
except Exception as e:
    app.logger.warning(f"[WARN] PDF generator initialization failed: {str(e)}")
    pdf_generator = None

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

def format_ingredients_for_frontend(ingredients):
    """Convert ingredient format from optimizer to frontend expected format"""
    if isinstance(ingredients, list) and len(ingredients) > 0:
        # Check if already in correct format (list of dicts)
        if isinstance(ingredients[0], dict) and 'item' in ingredients[0]:
            # Convert to simple string format expected by frontend
            return [f"{ing['item'].replace('_', ' ')}: {ing['amount']}{ing.get('unit', 'g')}" for ing in ingredients]
        # If already in string format, return as is
        elif isinstance(ingredients[0], str):
            return ingredients
    return ingredients

@app.route('/')
def index():
    """Main landing page"""
    app.logger.info("INDEX route accessed")
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/create-new')
@login_required
def create_meal_plan_new():
    """New meal plan creation page to bypass cache"""
    return render_template('create_new.html')

@app.route('/create')
@login_required
def create_meal_plan():
    """Meal plan creation page"""
    try:
        app.logger.info(f"[CREATE] Page accessed by user: {current_user.email if current_user.is_authenticated else 'Unknown'}")
        app.logger.info(f"[CREATE] User credits: {current_user.credits_balance if current_user.is_authenticated else 'N/A'}")
        app.logger.info("CREATE MEAL PLAN page accessed")
        
        # Check if optimizer exists
        if not hasattr(app, 'optimizer') and 'optimizer' not in globals():
            log_error("Optimizer not found - reinitializing")
            global optimizer
            # Use web-safe optimizer to prevent input() crashes
            optimizer = get_web_optimizer()
        
        # Get available options from the optimizer
        app.logger.info("Getting diet types from optimizer")
        diet_types = list(optimizer.diet_profiles.keys())
        app.logger.info(f"Diet types: {diet_types}")
        
        app.logger.info("Getting meal patterns from optimizer")
        meal_patterns = list(optimizer.meal_patterns.keys())
        app.logger.info(f"Meal patterns: {meal_patterns}")
        
        app.logger.info("Rendering create.html template")
        app.logger.info(f"Template variables: diet_types={len(diet_types)}, meal_patterns={len(meal_patterns)}")
        
        # Log the exact template being rendered
        template_name = 'create.html'
        app.logger.info(f"About to render template: {template_name}")
        
        try:
            # Check if template exists
            import os
            template_path = os.path.join(app.template_folder, template_name)
            app.logger.info(f"[CREATE] Template folder: {app.template_folder}")
            app.logger.info(f"[CREATE] Template path: {template_path}")
            app.logger.info(f"[CREATE] Template exists: {os.path.exists(template_path)}")
            
            result = render_template(template_name, 
                                   diet_types=diet_types,
                                   meal_patterns=meal_patterns,
                                   diet_profiles=optimizer.diet_profiles,
                                   meal_patterns_data=optimizer.meal_patterns)
            app.logger.info("Template rendered successfully")
            return result
        except Exception as template_error:
            app.logger.error(f"[CREATE] Template rendering failed: {str(template_error)}")
            app.logger.error(f"[CREATE] Error type: {type(template_error).__name__}")
            import traceback
            app.logger.error(f"[CREATE] Full traceback:\n{traceback.format_exc()}")
            
            # Return error page with more details
            return render_template('error.html', error=f"{type(template_error).__name__}: {str(template_error)}"), 500
        
    except Exception as e:
        log_error(f"Error in create_meal_plan: {str(e)}")
        log_error(f"Exception type: {type(e)}")
        import traceback
        log_error(f"Traceback: {traceback.format_exc()}")
        
        # Return a simple error page instead of crashing
        return render_template('error.html', error=str(e)), 500

@app.route('/api/debug-logs', methods=['POST'])
def receive_debug_logs():
    """Receive debug logs from browser"""
    try:
        data = request.get_json()
        logs = data.get('logs', [])
        
        # Save to file in logs directory
        import json
        from datetime import datetime
        
        # Ensure logs directory exists
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Use secure path join for file creation
        log_filename = f'debug_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        log_file = secure_path_join(logs_dir, log_filename)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2)
        
        # Also save to text file for easy reading
        latest_log = secure_path_join(logs_dir, 'latest_debug.log')
        with open(latest_log, 'w', encoding='utf-8') as f:
            for log in logs:
                # Sanitize log messages to prevent injection
                timestamp = str(log.get('timestamp', 'unknown'))[:50]
                log_type = str(log.get('type', 'unknown'))[:20]
                message = str(log.get('message', ''))[:1000]
                f.write(f"[{timestamp}] {log_type.upper()}: {message}\n")
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        app.logger.error(f"Failed to save debug logs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/debug/template')
def debug_template():
    """Debug what template is actually being served"""
    # Use secure path for template access
    template_path = secure_path_join('templates', 'create.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Find the API call lines
    lines = template_content.split('\n')
    api_lines = []
    for i, line in enumerate(lines):
        if '/api/generate' in line:
            api_lines.append(f"Line {i+1}: {line.strip()}")
    
    return f"<pre>Template API calls found:\n" + "\n".join(api_lines) + "</pre>"

@app.route('/api/generate-debug', methods=['POST'])
@login_required  
def debug_generate():
    """Debug endpoint - REDIRECT to correct endpoint"""
    app.logger.info("=== 🚨 GENERATE-DEBUG ENDPOINT CALLED ===")
    app.logger.info("🚨 REDIRECTING to correct endpoint!")
    
    # Get the request data and validate it
    if request.is_json:
        data = request.get_json()
        
        # Transform to expected format
        validated_data = {
            'calories': int(data.get('calories', 2000)),
            'diet': data.get('diet', 'standard'),
            'days': int(data.get('days', 1)),
            'meal_structure': data.get('meal_structure', 'standard'),
            'restrictions': data.get('restrictions', []),
            'cuisines': data.get('cuisines', ['all']),
            'cooking_methods': data.get('cooking_methods', ['all']),
            'measurement_system': data.get('measurement_system', 'metric'),
            'allow_substitutions': data.get('allow_substitutions', True)
        }
        
        app.logger.info(f"Transformed data: {validated_data}")
        
        # Call the correct endpoint function directly
        return generate_meal_plan(validated_data=validated_data)
    else:
        return jsonify({'error': 'Invalid request format'}), 400

@app.route('/api/generate', methods=['POST'], endpoint='generate_meal_plan')
@login_required
@validate_request(MealPlanRequestSchema)
def generate_meal_plan(validated_data=None):
    """API endpoint to generate meal plan"""
    
    app.logger.info("=== ✅ CORRECT GENERATE ENDPOINT CALLED ===")
    app.logger.info("✅ SUCCESS: Frontend is calling the correct /api/generate endpoint!")
    app.logger.info(f"GENERATE_MEAL_PLAN_REQUEST - Data: {validated_data}")
    app.logger.info("[START] Meal plan generation")
    app.logger.info(f"   User: {current_user.email if current_user else 'Unknown'}")
    
    # Check if user has credits
    if not check_user_credits(current_user):
        app.logger.warning(f"   User {current_user.email} has no credits available (balance: {current_user.credits_balance})")
        
        # PRODUCTION: Enforce credit limits properly
        return jsonify({
            'error': 'No credits available',
            'message': 'You have used all your free credits. Upgrade to Pro for unlimited meal plans!',
            'credits_remaining': current_user.credits_balance,
            'upgrade_url': url_for('auth.upgrade')
        }), 403
    
    # SECURITY: Check rate limit first
    if not rate_limit_check():
        app.logger.warning(f"   Rate limit exceeded for user {current_user.email}")
        return jsonify({'error': 'Rate limit exceeded. Please wait a minute.'}), 429
    
    try:
        # Use validated data from middleware
        diet_type = validated_data.get('diet', 'standard')
        calories = validated_data.get('calories', 2000)
        pattern = validated_data.get('meal_structure', 'standard')
        restrictions = validated_data.get('restrictions', [])
        days = validated_data.get('days', 7)
        cuisines = validated_data.get('cuisines', ['all'])
        cooking_methods = validated_data.get('cooking_methods', ['all'])
        measurement_system = validated_data.get('measurement_system', 'metric')
        allow_substitutions = validated_data.get('allow_substitutions', True)
        
        app.logger.info(f"   Validated parameters: diet={diet_type}, calories={calories}, pattern={pattern}, days={days}")
        app.logger.info(f"   Restrictions: {restrictions}, Cuisines: {cuisines}")
        
        # Create preferences - respect user inputs
        preferences = {
            'diet': diet_type,
            'calories': calories,
            'pattern': pattern,
            'restrictions': restrictions if isinstance(restrictions, list) else [],
            'cuisines': cuisines if isinstance(cuisines, list) and cuisines else ['all'],
            'cooking_methods': cooking_methods if isinstance(cooking_methods, list) and cooking_methods else ['all'],
            'measurement_system': measurement_system if measurement_system in ['US', 'metric'] else 'US',
            'allow_substitutions': allow_substitutions,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate meal plans for requested days
        app.logger.info("   Starting meal plan generation...")
        start_time = time.time()
        
        if days == 1:
            # Single day plan
            app.logger.info("   Generating single day plan...")
            try:
                app.logger.info(f"   === CALLING OPTIMIZER ===")
                app.logger.info(f"   Preferences passed: {preferences}")
                result = optimizer.generate_single_day_plan(preferences)
                app.logger.info(f"   Optimizer returned type: {type(result)}")
                app.logger.info(f"   Optimizer result: {result}")
                
                if isinstance(result, tuple) and len(result) == 2:
                    day_meals, metrics = result
                    app.logger.info(f"   Unpacked tuple: day_meals type={type(day_meals)}, metrics type={type(metrics)}")
                else:
                    app.logger.error(f"   Unexpected result format from optimizer: {result}")
                    raise Exception("Optimizer returned unexpected format")
                
                app.logger.info(f"   Generated {len(day_meals) if day_meals else 0} meals")
                app.logger.info(f"   Day meals type: {type(day_meals)}")
                if day_meals:
                    app.logger.info(f"   Meals: {list(day_meals.keys())}")
                    for meal_name, meal_data in day_meals.items():
                        app.logger.info(f"     {meal_name}: {type(meal_data)} with keys {list(meal_data.keys()) if isinstance(meal_data, dict) else 'NOT_DICT'}")
                else:
                    app.logger.warning(f"   day_meals is empty or None")
                
                totals = optimizer.calculate_day_totals(day_meals)
                app.logger.info(f"   Totals calculated: {totals}")
            except Exception as e:
                app.logger.error(f"   Error generating single day plan: {str(e)}")
                app.logger.error(f"   Exception type: {type(e).__name__}")
                import traceback
                app.logger.error(f"   Traceback: {traceback.format_exc()}")
                raise
            
            # Format meals for frontend
            formatted_meals = {}
            for meal_name, meal_data in day_meals.items():
                formatted_meal = meal_data.copy()
                if 'ingredients' in formatted_meal:
                    formatted_meal['ingredients'] = format_ingredients_for_frontend(meal_data['ingredients'])
                formatted_meals[meal_name] = formatted_meal
            
            response = {
                'success': True,
                'meal_plan': {
                    'meals': formatted_meals,
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
            
            # Deduct credit for single day
            if not current_user.is_premium():
                success = deduct_credit(current_user, 1)
                if not success:
                    return jsonify({
                        'error': 'Insufficient credits',
                        'message': 'You need 1 credit for a meal plan',
                        'credits_remaining': current_user.credits_balance
                    }), 403
            
            app.logger.info(f"   Response prepared successfully")
            app.logger.info(f"   Generation time: {round(time.time() - start_time, 2)}s")
            app.logger.info(f"   === DETAILED RESPONSE DEBUG ===")
            app.logger.info(f"   response['success']: {response.get('success')}")
            app.logger.info(f"   response['meal_plan'] exists: {'meal_plan' in response}")
            if 'meal_plan' in response:
                mp = response['meal_plan']
                app.logger.info(f"   meal_plan keys: {list(mp.keys()) if isinstance(mp, dict) else 'NOT_DICT'}")
                if 'meals' in mp:
                    app.logger.info(f"   meals keys: {list(mp['meals'].keys()) if isinstance(mp['meals'], dict) else 'NOT_DICT'}")
                    app.logger.info(f"   meals count: {len(mp['meals']) if mp['meals'] else 0}")
            app.logger.info(f"   Full response structure: {list(response.keys())}")
            app.logger.info(f"   === END RESPONSE DEBUG ===")
            
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
                
                # Format meals for frontend
                formatted_day_meals = {}
                for meal_name, meal_data in day_meals.items():
                    formatted_meal = meal_data.copy()
                    if 'ingredients' in formatted_meal:
                        formatted_meal['ingredients'] = format_ingredients_for_frontend(meal_data['ingredients'])
                    formatted_day_meals[meal_name] = formatted_meal
                
                week_plan[day_name] = formatted_day_meals
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
        
        # Deduct credits for multi-day plans
        # More fair pricing: 1 credit for 1-3 days, 2 credits for 4-7 days
        if days <= 3:
            credits_used = 1
        else:
            credits_used = 2
        
        # Only deduct if not premium
        if not current_user.is_premium():
            success = deduct_credit(current_user, credits_used)
            if not success:
                return jsonify({
                    'error': 'Insufficient credits',
                    'message': f'You need {credits_used} credits for a {days}-day plan',
                    'credits_remaining': current_user.credits_balance
                }), 403
        
        usage_log = UsageLog(
            user_id=current_user.id,
            action_type='generate_plan',
            credits_used=credits_used if not current_user.is_premium() else 0,
            extra_data={
                'diet_type': diet_type,
                'calories': calories,
                'days': days,
                'pattern': pattern
            }
        )
        db.session.add(usage_log)
        db.session.commit()
        
        app.logger.info("[SUCCESS] Meal plan generation completed")
        return jsonify(response)
        
    except Exception as e:
        app.logger.error("[FAILED] Meal plan generation failed")
        app.logger.error(f"   Error: {str(e)}")
        app.logger.error(f"   Exception type: {type(e).__name__}")
        import traceback
        app.logger.error(f"   Full traceback: {traceback.format_exc()}")
        
        return jsonify({
            'error': 'Failed to generate meal plan',
            'details': str(e) if app.debug else 'An error occurred during meal plan generation',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/api/generate-video', methods=['POST'])
@validate_request(VideoGenerationRequestSchema)
def generate_video(validated_data=None):
    """API endpoint to generate video from meal plan"""
    try:
        # Use validated data from middleware
        meal_plan = validated_data.get('meal_plan')
        platforms = validated_data.get('platforms', ['youtube_shorts'])
        voice = validated_data.get('voice', 'christopher')
        auto_upload = validated_data.get('auto_upload', False)
        
        if not video_service:
            return jsonify({'error': 'Video service not available'}), 503
        
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
            
            response_data = {
                'success': True,
                'video_urls': video_urls,
                'upload_results': results['upload'],
                'summary': results['summary'],
                'message': f"Generated {results['summary']['successful_generations']} videos"
            }
            
            # Add upload capability info
            if not video_service.upload_enabled:
                response_data['upload_info'] = {
                    'status': 'disabled',
                    'reason': 'Social media credentials not configured',
                    'setup_url': '/api/video/upload-status'
                }
            
            return jsonify(response_data)
            
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
@validate_request(ExportGroceryListSchema)
def export_grocery_list(validated_data=None):
    """API endpoint to export grocery list"""
    try:
        # Use validated data from middleware
        meal_plan = validated_data.get('meal_plan')
        export_format = validated_data.get('format', 'pdf')
        
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

@app.route('/test')
def test_page():
    """Test page for debugging click issues"""
    return render_template('test.html')

@app.route('/minimal-test', methods=['GET', 'POST'])
def minimal_test():
    """Minimal test page with no JavaScript"""
    if request.method == 'POST':
        test_input = request.form.get('test_input', '')
        flash(f'Form submitted successfully! Input: {test_input}', 'success')
    return render_template('minimal_test.html')

@app.route('/emergency-test')
def emergency_test():
    """Emergency test page with absolute minimal dependencies"""
    return render_template('emergency_test.html')

@app.route('/api/video/platforms')
def get_video_platforms():
    """Get available video platforms"""
    if not video_service:
        return jsonify({'error': 'Video service not available'}), 503
    return jsonify(video_service.get_platform_info())

@app.route('/api/video/stats')
def get_video_stats():
    """Get video generation statistics"""
    if not video_service:
        return jsonify({'error': 'Video service not available'}), 503
    return jsonify(video_service.get_video_stats())

@app.route('/api/video/upload-status')
def get_upload_status():
    """Get video upload capabilities and setup guidance"""
    if not video_service:
        return jsonify({'error': 'Video service not available'}), 503
    
    credentials_exist = os.path.exists('social_credentials.json')
    status = {
        'upload_enabled': video_service.upload_enabled if video_service else False,
        'credentials_configured': credentials_exist,
        'setup_instructions': {
            'step1': 'Copy social_credentials_template.json to social_credentials.json',
            'step2': 'Configure your social media API credentials',
            'step3': 'Restart the application to enable uploads',
            'supported_platforms': ['YouTube', 'Facebook', 'Instagram', 'TikTok']
        }
    }
    
    if credentials_exist:
        status['message'] = 'Video uploads are enabled'
    else:
        status['message'] = 'Video uploads disabled - credentials not configured'
    
    return jsonify(status)

@app.route('/api/video/test-voice', methods=['POST'])
@validate_request(TestVoiceSchema)
def test_voice(validated_data=None):
    """Test voice generation"""
    if not video_service:
        return jsonify({'error': 'Video service not available'}), 503
        
    try:
        # Use validated data from middleware
        text = validated_data.get('text', 'Hello! This is a test of Edge TTS Christopher voice.')
        voice_gender = validated_data.get('voice_gender', 'female')
        language = validated_data.get('language', 'en-US')
        
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
        # Validate and secure the filename
        safe_filename = validate_video_filename(filename)
        video_path = secure_path_join('videos', safe_filename)
        
        if os.path.exists(video_path):
            return send_file(video_path, mimetype='video/mp4')
        else:
            return jsonify({'error': 'Video not found'}), 404
    except SecurityError as e:
        return jsonify({'error': 'Invalid filename', 'details': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error serving video: {e}")
        return jsonify({'error': 'Failed to serve video'}), 500

@app.route('/api/save-meal-plan', methods=['POST'])
@login_required
@validate_request(SaveMealPlanSchema)
def save_meal_plan(validated_data=None):
    """Save meal plan to storage"""
    try:
        # Use validated data from middleware
        meal_plan = validated_data.get('meal_plan')
        name = validated_data.get('name', f'meal_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        description = validated_data.get('description', '')
        
        # Sanitize filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_name = safe_name[:50]  # Limit length
        
        # Create user-specific saved_plans directory if it doesn't exist
        user_dir = f'saved_plans/user_{current_user.id}'
        os.makedirs(user_dir, exist_ok=True)
        
        # Save to JSON file
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filename = validate_json_filename(filename)
        filepath = secure_path_join(user_dir, filename)
        
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
    
    except SecurityError as e:
        return jsonify({'error': 'Invalid filename', 'details': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error saving meal plan: {e}")
        return jsonify({
            'error': 'Failed to save meal plan'
        }), 500

@app.route('/api/load-meal-plans')
@login_required
def load_meal_plans():
    """Load list of saved meal plans"""
    try:
        # Load only the current user's plans
        user_dir = f'saved_plans/user_{current_user.id}'
        if not os.path.exists(user_dir):
            return jsonify({'plans': []})
        
        plans = []
        for filename in os.listdir(user_dir):
            if filename.endswith('.json'):
                try:
                    safe_filename = validate_json_filename(filename)
                    filepath = secure_path_join(user_dir, safe_filename)
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
                    app.logger.error(f"Error reading {filename}: {e}")
        
        # Sort by creation date (newest first)
        plans.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({'plans': plans})
        
    except Exception as e:
        app.logger.error(f"Error loading meal plans: {e}")
        return jsonify({
            'error': 'Failed to load meal plans',
            'details': str(e) if app.debug else 'An error occurred'
        }), 500

@app.route('/api/load-meal-plan/<filename>')
@login_required
def load_meal_plan(filename):
    """Load a specific meal plan"""
    try:
        # Validate and secure the filename
        safe_filename = validate_json_filename(filename)
        user_dir = f'saved_plans/user_{current_user.id}'
        filepath = secure_path_join(user_dir, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Meal plan not found'}), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': data
        })
    
    except SecurityError as e:
        return jsonify({'error': 'Invalid filename', 'details': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error loading meal plan: {e}")
        return jsonify({
            'error': 'Failed to load meal plan'
        }), 500

@app.route('/api/delete-meal-plan/<filename>', methods=['DELETE'])
@login_required
def delete_meal_plan(filename):
    """Delete a saved meal plan"""
    try:
        # Validate and secure the filename
        safe_filename = validate_json_filename(filename)
        user_dir = f'saved_plans/user_{current_user.id}'
        filepath = secure_path_join(user_dir, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Meal plan not found'}), 404
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': 'Meal plan deleted successfully'
        })
    
    except SecurityError as e:
        return jsonify({'error': 'Invalid filename', 'details': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error deleting meal plan: {e}")
        return jsonify({
            'error': 'Failed to delete meal plan'
        }), 500

@app.route('/api/export-pdf', methods=['POST'])
@login_required
@validate_request(ExportPDFSchema)
def export_pdf(validated_data=None):
    """Export meal plan as PDF"""
    try:
        # Use validated data from middleware
        meal_plan = validated_data.get('meal_plan')
        export_format = validated_data.get('format', 'detailed')
        include_recipes = validated_data.get('include_recipes', True)
        
        if not pdf_generator:
            return jsonify({'error': 'PDF generation service not available'}), 503
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == 'grocery_list':
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
            safe_filename = validate_pdf_filename(filename)
            filepath = secure_path_join('pdfs', safe_filename)
            pdf_generator.generate_grocery_list_pdf(formatted_list, filepath, days)
            
        else:
            # Export full meal plan
            filename = f'meal_plan_{timestamp}.pdf'
            safe_filename = validate_pdf_filename(filename)
            filepath = secure_path_join('pdfs', safe_filename)
            pdf_generator.generate_meal_plan_pdf(meal_plan, filepath)
        
        # Return file for download
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename
        )
    
    except SecurityError as e:
        return jsonify({'error': 'Invalid filename', 'details': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error exporting PDF: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to export PDF'
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
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
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

# Frontend logging sync endpoint
frontend_logs = []

@app.route('/api/logs/sync', methods=['POST'])
@csrf.exempt
@validate_request(FrontendLogsSchema)
def sync_frontend_logs(validated_data=None):
    """Receive and store frontend logs"""
    try:
        # Use validated data from middleware
        session_id = validated_data.get('session_id')
        logs = validated_data.get('logs', [])
        
        # Store logs with timestamp
        for log in logs:
            log['received_at'] = datetime.now(timezone.utc).isoformat()
            frontend_logs.append(log)
        
        # Keep only last 5000 logs in memory
        if len(frontend_logs) > 5000:
            frontend_logs[:] = frontend_logs[-5000:]
        
        app.logger.info(f"[FRONTEND] Received {len(logs)} logs from session {session_id}")
        
        # Log errors to backend logger
        for log in logs:
            if log.get('level') == 'ERROR':
                app.logger.error(f"[FRONTEND ERROR] {log.get('message')} - URL: {log.get('url')}")
        
        return jsonify({'success': True, 'received': len(logs)})
    except Exception as e:
        app.logger.error(f"Failed to sync frontend logs: {str(e)}")
        return jsonify({'error': 'Failed to sync logs'}), 500

@app.route('/logs')
@login_required
def logs_page():
    """Log viewer page (admin only)"""
    if current_user.email not in ['admin', 'dev@cibozer.com'] and not current_user.is_premium():
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    return render_template('logs.html')

@app.route('/api/logs/view')
@login_required
def view_frontend_logs():
    """View frontend logs (admin only)"""
    # Check if user is admin or dev
    if current_user.email not in ['admin', 'dev@cibozer.com'] and not current_user.is_premium():
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Filter logs by query parameters
    level = request.args.get('level')
    session_id = request.args.get('session_id')
    limit = int(request.args.get('limit', 100))
    
    filtered_logs = frontend_logs
    
    if level:
        filtered_logs = [log for log in filtered_logs if log.get('level') == level]
    
    if session_id:
        filtered_logs = [log for log in filtered_logs if log.get('sessionId') == session_id]
    
    # Get most recent logs
    filtered_logs = filtered_logs[-limit:]
    
    return jsonify({
        'logs': filtered_logs,
        'total': len(frontend_logs),
        'filtered': len(filtered_logs)
    })

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch all exceptions and log them"""
    app.logger.error(f"[EXCEPTION] Unhandled exception: {str(e)}")
    app.logger.error(f"[EXCEPTION] Type: {type(e).__name__}")
    app.logger.error(f"[EXCEPTION] Request URL: {request.url}")
    app.logger.error(f"[EXCEPTION] Request endpoint: {request.endpoint}")
    app.logger.error(f"[EXCEPTION] Request method: {request.method}")
    
    # Check if it's a BuildError (url_for error)
    if "BuildError" in type(e).__name__:
        app.logger.error(f"[BUILD ERROR] Failed to build URL for endpoint: {str(e)}")
        app.logger.error(f"[BUILD ERROR] Available endpoints: {[rule.endpoint for rule in app.url_map.iter_rules()]}")
    
    # Rollback any database changes
    db.session.rollback()
    
    return render_template('error.html', error=str(e)), 500

# CSRF exemptions - must be done after route definitions
csrf.exempt(receive_debug_logs)

@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    try:
        return send_file('static/favicon.ico', mimetype='image/vnd.microsoft.icon')
    except FileNotFoundError:
        # Return a 204 No Content instead of 404 to prevent browser errors
        return '', 204


if __name__ == '__main__':
    print("Starting Cibozer Web Application...")
    print("Visit: http://localhost:5001")
    print("TROUBLESHOOT: Running on port 5001 to avoid conflicts")
    app.run(debug=config.flask.DEBUG, host='127.0.0.1', port=5001)