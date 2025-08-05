"""Input validation utilities."""
import re
from email_validator import validate_email as _validate_email, EmailNotValidError


def validate_email(email):
    """Validate email format."""
    try:
        # Validate and normalize email
        validation = _validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_password(password):
    """
    Validate password strength.
    Requirements:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[A-Z]', password):
        return False
    
    if not re.search(r'[a-z]', password):
        return False
    
    if not re.search(r'\d', password):
        return False
    
    return True


def validate_calories(calories):
    """Validate calorie input."""
    try:
        cal = int(calories)
        return 800 <= cal <= 6000
    except (ValueError, TypeError):
        return False


def validate_diet_type(diet_type):
    """Validate diet type."""
    valid_diets = [
        'standard', 'keto', 'paleo', 'vegan', 'vegetarian',
        'mediterranean', 'low-carb', 'high-protein'
    ]
    return diet_type in valid_diets


def validate_meal_structure(structure):
    """Validate meal structure."""
    valid_structures = [
        'standard', 'intermittent-fasting', 'omad', 
        '5-small-meals', 'bodybuilder'
    ]
    return structure in valid_structures


def sanitize_input(text, max_length=None):
    """Sanitize user input text."""
    if not text:
        return ''
    
    # Remove any potential HTML/script tags
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text