from middleware import MealPlanRequestSchema
from marshmallow import ValidationError
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Test data that might be sent from the form
test_data = {
    "calories": "2000",
    "days": "7",
    "diet": "standard",
    "meal_structure": "standard"
}

print("Testing meal plan validation...")
print(f"Input data: {test_data}")

schema = MealPlanRequestSchema()
try:
    result = schema.load(test_data)
    print(f"✅ Validation passed!")
    print(f"Validated data: {result}")
except ValidationError as e:
    print(f"❌ Validation failed!")
    print(f"Errors: {e.messages}")
    
# Test with missing required field
print("\n\nTesting with missing diet field...")
test_data2 = {
    "calories": "2000",
    "days": "7",
    "meal_structure": "standard"
}

try:
    result = schema.load(test_data2)
    print(f"✅ Validation passed!")
except ValidationError as e:
    print(f"❌ Validation failed!")
    print(f"Errors: {e.messages}")
    
# Test with all fields including optional ones
print("\n\nTesting with all fields...")
test_data3 = {
    "calories": "2000",
    "days": "7",
    "diet": "keto",
    "meal_structure": "16_8_if",
    "restrictions": ["nuts", "dairy"],
    "cuisines": ["mediterranean", "european"],
    "cooking_methods": ["grilled", "baked"],
    "measurement_system": "metric",
    "allow_substitutions": True
}

try:
    result = schema.load(test_data3)
    print(f"✅ Validation passed!")
    print(f"Validated data: {result}")
except ValidationError as e:
    print(f"❌ Validation failed!")
    print(f"Errors: {e.messages}")