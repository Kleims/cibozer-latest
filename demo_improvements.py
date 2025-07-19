"""
Demo script to showcase the improvements made to Cibozer
"""

import json
from app_config import get_app_config, validate_config
from middleware import MealPlanRequestSchema, ValidationError, validate_password, sanitize_input

def demo_centralized_config():
    """Demonstrate centralized configuration"""
    print("\n=== CENTRALIZED CONFIGURATION DEMO ===")
    
    # Validate and load config
    if validate_config():
        config = get_app_config()
        
        print(f"\nApp Name: {config.APP_NAME} v{config.APP_VERSION}")
        print(f"Debug Mode: {config.flask.DEBUG}")
        print(f"Database: {config.database.DATABASE_URL}")
        print(f"Rate Limiting: {config.security.RATE_LIMIT_ENABLED}")
        print(f"Rate Limit: {config.security.RATE_LIMIT_DEFAULT}")
        print(f"Payments Enabled: {config.payment.STRIPE_ENABLED}")
        print(f"Pro Plan Price: ${config.payment.PRO_PRICE}")
        print(f"Premium Plan Price: ${config.payment.PREMIUM_PRICE}")
        print(f"Max File Upload: {config.security.MAX_CONTENT_LENGTH / 1024 / 1024}MB")
        print(f"Allowed Extensions: {', '.join(config.security.ALLOWED_EXTENSIONS)}")

def demo_input_validation():
    """Demonstrate input validation middleware"""
    print("\n\n=== INPUT VALIDATION DEMO ===")
    
    schema = MealPlanRequestSchema()
    
    # Valid request
    print("\n1. Valid Request:")
    valid_data = {
        "diet": "keto",
        "calories": 2000,
        "days": 7,
        "restrictions": ["nuts", "dairy"],
        "meal_structure": "16_8_if",
        "cuisines": ["mediterranean", "asian"]
    }
    
    try:
        result = schema.load(valid_data)
        print(f"[PASS] Validation passed: {json.dumps(result, indent=2)}")
    except ValidationError as e:
        print(f"[FAIL] Validation failed: {e.messages}")
    
    # Invalid diet type
    print("\n2. Invalid Diet Type:")
    invalid_diet = {
        "diet": "invalid_diet",
        "calories": 2000
    }
    
    try:
        result = schema.load(invalid_diet)
        print(f"[PASS] Validation passed: {result}")
    except ValidationError as e:
        print(f"[FAIL] Validation failed: {e.messages}")
    
    # Invalid calorie range
    print("\n3. Invalid Calorie Range:")
    invalid_calories = {
        "diet": "vegan",
        "calories": 10000  # Too high
    }
    
    try:
        result = schema.load(invalid_calories)
        print(f"[PASS] Validation passed: {result}")
    except ValidationError as e:
        print(f"[FAIL] Validation failed: {e.messages}")
    
    # Invalid restrictions
    print("\n4. Invalid Dietary Restriction:")
    invalid_restriction = {
        "diet": "paleo",
        "calories": 2500,
        "restrictions": ["nuts", "invalid_restriction"]
    }
    
    try:
        result = schema.load(invalid_restriction)
        print(f"[PASS] Validation passed: {result}")
    except ValidationError as e:
        print(f"[FAIL] Validation failed: {e.messages}")

def demo_password_validation():
    """Demonstrate password validation"""
    print("\n\n=== PASSWORD VALIDATION DEMO ===")
    
    passwords = [
        "weak",
        "password123",
        "StrongP@ssw0rd!",
        "NoSpecialChars123",
        "no_uppercase_123!"
    ]
    
    for pwd in passwords:
        result = validate_password(pwd)
        if result['valid']:
            print(f"\n[PASS] Password '{pwd}' is valid")
        else:
            print(f"\n[FAIL] Password '{pwd}' is invalid:")
            for issue in result['issues']:
                print(f"   - {issue}")

def demo_input_sanitization():
    """Demonstrate input sanitization"""
    print("\n\n=== INPUT SANITIZATION DEMO ===")
    
    test_inputs = [
        "Normal text",
        "Text with\x00null bytes",
        "Text with <script>alert('xss')</script> HTML",
        "   Text with extra spaces   ",
        "Very " + "long " * 500 + "text",
        "Text\nwith\nnewlines\tand\ttabs"
    ]
    
    for text in test_inputs:
        sanitized = sanitize_input(text, max_length=50)
        print(f"\nOriginal: {repr(text[:50])}{'...' if len(text) > 50 else ''}")
        print(f"Sanitized: {repr(sanitized)}")

def demo_rate_limiting():
    """Demonstrate rate limiting configuration"""
    print("\n\n=== RATE LIMITING CONFIGURATION ===")
    
    config = get_app_config()
    
    print(f"Rate Limiting Enabled: {config.security.RATE_LIMIT_ENABLED}")
    print(f"Default Limit: {config.security.RATE_LIMIT_DEFAULT}")
    print(f"Storage Backend: {config.security.RATE_LIMIT_STORAGE_URL}")
    print("\nRate limiting is now fully configurable via environment variables!")
    print("Set RATE_LIMIT_ENABLED=False to disable during development")
    print("Set RATE_LIMIT_DEFAULT='20 per minute' to increase limits")

def main():
    """Run all demos"""
    print("=" * 60)
    print("CIBOZER IMPROVEMENTS DEMONSTRATION")
    print("=" * 60)
    
    demo_centralized_config()
    demo_input_validation()
    demo_password_validation()
    demo_input_sanitization()
    demo_rate_limiting()
    
    print("\n\n" + "=" * 60)
    print("SUMMARY OF IMPROVEMENTS:")
    print("=" * 60)
    print("1. [PASS] Centralized configuration management")
    print("2. [PASS] Comprehensive input validation with Marshmallow")
    print("3. [PASS] Password strength validation")
    print("4. [PASS] Input sanitization for security")
    print("5. [PASS] Configurable rate limiting")
    print("6. [PASS] Better error messages for users")
    print("7. [PASS] Type-safe validation schemas")
    print("8. [PASS] Reusable validation decorators")

if __name__ == "__main__":
    main()