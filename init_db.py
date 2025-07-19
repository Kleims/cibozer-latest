from app import app, db
from models import User, Payment, PricingPlan, UsageLog, SavedMealPlan

print("Initializing database...")

with app.app_context():
    # Drop all tables
    db.drop_all()
    print("Dropped existing tables")
    
    # Create all tables
    db.create_all()
    print("Created new tables")
    
    # Verify tables exist
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables created: {tables}")
    
    # Check User columns
    columns = [col['name'] for col in inspector.get_columns('users')]
    print(f"User table columns: {columns}")
    
    if 'reset_token' in columns:
        print("✓ Password reset columns added successfully!")
    else:
        print("✗ Password reset columns missing!")

print("Database initialization complete!")