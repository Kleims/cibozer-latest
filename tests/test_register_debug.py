from app import app, db
from models import User
from auth import validate_password
import bcrypt

# Test registration directly
with app.app_context():
    try:
        # Test password validation
        password = "TestPass123!"
        errors = validate_password(password)
        print(f"Password validation result: {errors}")
        
        # Test user creation
        email = "debug_test@example.com"
        
        # Delete if exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print("Deleted existing test user")
        
        # Create new user
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(
            email=email,
            password_hash=hashed.decode('utf-8'),
            full_name="Debug Test User"
        )
        
        db.session.add(user)
        db.session.commit()
        
        print(f"User created successfully with ID: {user.id}")
        
        # Test password check
        check = bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8'))
        print(f"Password check: {check}")
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()