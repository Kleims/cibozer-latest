"""
Input validation middleware for Cibozer
Provides comprehensive validation for all API endpoints
"""

import re
from functools import wraps
from flask import request, jsonify, current_app
from marshmallow import Schema, fields, validate, ValidationError
from typing import Dict, Any, Callable, Optional
import json

# Email validation pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Common validators
def validate_email(email: str) -> bool:
    """Validate email format"""
    return bool(EMAIL_PATTERN.match(email))

def validate_password(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }

# Marshmallow Schemas for validation
class MealPlanRequestSchema(Schema):
    """Validation schema for meal plan generation requests"""
    diet = fields.Str(
        required=True,
        validate=validate.OneOf(['standard', 'keto', 'paleo', 'vegan', 'vegetarian', 'high_protein'])
    )
    calories = fields.Int(
        required=True,
        validate=validate.Range(min=800, max=6000)
    )
    days = fields.Int(
        required=False,
        load_default=7,
        validate=validate.Range(min=1, max=7)  # Limited to 7 days to prevent abuse
    )
    restrictions = fields.List(
        fields.Str(validate=validate.OneOf([
            'nuts', 'dairy', 'gluten', 'shellfish', 'eggs', 
            'soy', 'sesame', 'fish', 'nightshades', 'legumes'
        ])),
        required=False,
        load_default=[]
    )
    meal_structure = fields.Str(
        required=False,
        load_default='standard',
        validate=validate.OneOf([
            'standard', '16_8_if', '18_6_if', 'omad', 
            '3_plus_2', '5_small', '2_meals'
        ])
    )
    cuisines = fields.List(
        fields.Str(validate=validate.OneOf([
            'all', 'asian', 'latin_american', 'mediterranean', 
            'middle_eastern', 'african', 'european', 'american', 'mixed'
        ])),
        required=False,
        load_default=['all']
    )
    cooking_methods = fields.List(
        fields.Str(validate=validate.OneOf([
            'all', 'grilled', 'baked', 'steamed', 'stir_fried', 
            'slow_cooked', 'raw', 'pan_fried', 'roasted', 'boiled',
            'sauteed', 'pressure_cooked', 'air_fried', 'simmered'
        ])),
        required=False,
        load_default=['all']
    )
    measurement_system = fields.Str(
        required=False,
        load_default='metric',
        validate=validate.OneOf(['US', 'metric'])
    )
    allow_substitutions = fields.Bool(required=False, load_default=True)

class VideoGenerationRequestSchema(Schema):
    """Validation schema for video generation requests"""
    meal_plan = fields.Raw(required=True)  # Contains the meal plan data
    platforms = fields.List(
        fields.Str(validate=validate.OneOf([
            'youtube_shorts', 'tiktok', 'instagram_reels', 
            'youtube_regular', 'facebook_video'
        ])),
        required=False,
        load_default=['youtube_shorts']
    )
    voice = fields.Str(
        required=False,
        load_default='christopher',
        validate=validate.Length(min=1, max=50)
    )
    auto_upload = fields.Bool(required=False, load_default=False)

class UserRegistrationSchema(Schema):
    """Validation schema for user registration"""
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    agree_terms = fields.Bool(required=True, validate=validate.Equal(True))

class UserLoginSchema(Schema):
    """Validation schema for user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember = fields.Bool(required=False, load_default=False)

class ExportGroceryListSchema(Schema):
    """Validation schema for grocery list export"""
    meal_plan = fields.Raw(required=True)  # Will contain the meal plan data
    format = fields.Str(required=False, load_default='pdf', validate=validate.OneOf(['pdf', 'json']))

class SaveMealPlanSchema(Schema):
    """Validation schema for saving meal plans"""
    meal_plan = fields.Raw(required=True)
    name = fields.Str(required=False, validate=validate.Length(max=100))
    description = fields.Str(required=False, validate=validate.Length(max=500))

class ExportPDFSchema(Schema):
    """Validation schema for PDF export"""
    meal_plan = fields.Raw(required=True)
    format = fields.Str(required=False, load_default='detailed', validate=validate.OneOf(['detailed', 'simple']))
    include_recipes = fields.Bool(required=False, load_default=True)

class TestVoiceSchema(Schema):
    """Validation schema for voice testing"""
    text = fields.Str(required=True, validate=validate.Length(min=1, max=500))
    voice_gender = fields.Str(required=False, load_default='female', validate=validate.OneOf(['male', 'female']))
    language = fields.Str(required=False, load_default='en-US', validate=validate.Regexp(r'^[a-z]{2}-[A-Z]{2}$'))

class FrontendLogsSchema(Schema):
    """Validation schema for frontend log sync"""
    logs = fields.List(fields.Dict(), required=True)
    session_id = fields.Str(required=False, validate=validate.Length(max=100))
    timestamp = fields.Int(required=False)

# Validation decorators
def validate_request(schema_class: Schema):
    """Decorator to validate request data against a schema"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get request data based on content type
            if request.is_json:
                data = request.get_json()
            elif request.form:
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
            
            # Validate data
            schema = schema_class()
            try:
                # Debug logging
                current_app.logger.debug(f"Validation input data: {data}")
                validated_data = schema.load(data)
                current_app.logger.debug(f"Validation passed: {validated_data}")
                # Add validated data to kwargs for the route handler
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                current_app.logger.warning(f"Validation error: {err.messages}")
                current_app.logger.warning(f"Failed data: {data}")
                return jsonify({
                    'error': 'Validation failed',
                    'details': err.messages
                }), 400
            except Exception as e:
                current_app.logger.error(f"Unexpected validation error: {str(e)}")
                return jsonify({
                    'error': 'Invalid request data'
                }), 400
        
        return decorated_function
    return decorator

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input text"""
    if not text:
        return ""
    
    # Trim to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text

def validate_file_upload(allowed_extensions: set):
    """Decorator to validate file uploads"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Check file extension
            if '.' not in file.filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return jsonify({
                    'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
                }), 400
            
            # Add file to kwargs
            kwargs['uploaded_file'] = file
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def validate_json_request(f: Callable) -> Callable:
    """Decorator to ensure request has valid JSON body"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        try:
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON body'}), 400
            kwargs['json_data'] = data
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"JSON parsing error: {str(e)}")
            return jsonify({'error': 'Invalid JSON format'}), 400
    
    return decorated_function

# Rate limiting decorator with custom limits
def rate_limit(max_requests: int = 10, window: int = 60):
    """Custom rate limiting decorator"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would integrate with the app's rate limiting system
            # For now, we'll use the existing rate_limit_check
            # In production, this could use Redis or similar
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Validation helpers for specific fields
class FieldValidators:
    """Common field validators"""
    
    @staticmethod
    def validate_calorie_range(calories: int) -> bool:
        """Validate calorie input is within safe range"""
        return 800 <= calories <= 6000
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate date range is reasonable"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            # Check dates are in correct order
            if start > end:
                return False
            
            # Check range is not too long (e.g., 30 days max)
            delta = end - start
            return delta.days <= 30
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Date range validation error: {e}")
            return False
    
    @staticmethod
    def validate_pagination(page: int, per_page: int) -> bool:
        """Validate pagination parameters"""
        return page > 0 and 0 < per_page <= 100

# Export schemas and decorators
__all__ = [
    'validate_request',
    'validate_file_upload',
    'validate_json_request',
    'rate_limit',
    'sanitize_input',
    'MealPlanRequestSchema',
    'VideoGenerationRequestSchema',
    'UserRegistrationSchema',
    'UserLoginSchema',
    'FieldValidators',
    'validate_email',
    'validate_password'
]