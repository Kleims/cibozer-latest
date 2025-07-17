"""
Cibozer Web Application
Flask-based web interface for AI meal planning and video generation
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
import os
import json
import time
import asyncio
from datetime import datetime
import traceback
import meal_optimizer as mo
import tempfile
import shutil
from pathlib import Path
from video_service import VideoService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# SECURITY FIX: Proper secret key handling
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    print("ERROR: SECRET_KEY environment variable not set!")
    import secrets
    SECRET_KEY = secrets.token_urlsafe(32)
    print(f"Generated temporary key: {SECRET_KEY}")
    print("IMPORTANT: Set SECRET_KEY in your .env file!")

app.secret_key = SECRET_KEY
app.debug = False  # NEVER True in production
CORS(app)

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

# Create necessary directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('static/generated', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('videos', exist_ok=True)
os.makedirs('logs', exist_ok=True)

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/create')
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
def generate_meal_plan():
    """API endpoint to generate meal plan"""
    
    # SECURITY: Check rate limit first
    if not rate_limit_check():
        return jsonify({'error': 'Rate limit exceeded. Please wait a minute.'}), 429
    
    try:
        # Get form data
        data = request.get_json() if request.is_json else request.form
        
        # Extract parameters
        diet_type = data.get('diet_type', 'standard')
        calories = int(data.get('calories', 2000))
        pattern = data.get('pattern', 'standard')
        restrictions = data.get('restrictions', [])
        
        # Validate inputs
        if diet_type not in optimizer.diet_profiles:
            return jsonify({'error': 'Invalid diet type'}), 400
        
        if not (800 <= calories <= 5000):
            return jsonify({'error': 'Calories must be between 800 and 5000'}), 400
        
        if pattern not in optimizer.meal_patterns:
            return jsonify({'error': 'Invalid meal pattern'}), 400
        
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
        
        # Generate meal plan
        start_time = time.time()
        day_meals, metrics = optimizer.generate_single_day_plan(preferences)
        generation_time = time.time() - start_time
        
        # Calculate totals
        totals = optimizer.calculate_day_totals(day_meals)
        
        # Create response
        response = {
            'success': True,
            'meal_plan': {
                'meals': day_meals,
                'totals': totals,
                'preferences': preferences,
                'metrics': {
                    'generation_time': round(generation_time, 2),
                    'accuracy': metrics.get('final_accuracy', 0),
                    'iterations': metrics.get('iterations', 0),
                    'convergence_achieved': metrics.get('convergence_achieved', False)
                }
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error generating meal plan: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to generate meal plan',
            'details': str(e)
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
        meals = meal_plan.get('meals', {})
        grocery_list = {}
        
        for meal_name, meal_data in meals.items():
            for ingredient in meal_data.get('ingredients', []):
                item = ingredient.get('item', '')
                amount = ingredient.get('amount', 0)
                unit = ingredient.get('unit', 'g')
                
                if item not in grocery_list:
                    grocery_list[item] = {'amount': 0, 'unit': unit}
                grocery_list[item]['amount'] += amount
        
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
            'grocery_list': formatted_list
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

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting Cibozer Web Application...")
    print("Visit: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)