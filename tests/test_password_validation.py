from auth import validate_password

# Test password validation directly
test_passwords = [
    "TestPass123!",
    "short",
    "alllowercase123",
    "ALLUPPERCASE123",
    "NoNumbers!",
    "NoSpecialChars123"
]

for password in test_passwords:
    errors = validate_password(password)
    print(f"Password: {password}")
    print(f"Errors: {errors if errors else 'None (valid)'}")
    print("-" * 40)