"""Simple models tests without Flask app context."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_models_import():
    """Test that models module can be imported."""
    import models
    assert models is not None


def test_user_model_exists():
    """Test that User model class exists."""
    from models import User
    assert User is not None


def test_payment_model_exists():
    """Test that Payment model exists."""
    from models import Payment 
    assert Payment is not None


def test_usage_log_model_exists():
    """Test that UsageLog model exists."""
    from models import UsageLog
    assert UsageLog is not None


def test_saved_meal_plan_model_exists():
    """Test that SavedMealPlan model exists."""
    from models import SavedMealPlan
    assert SavedMealPlan is not None


def test_basic_model_attributes():
    """Test that models have basic expected attributes."""
    from models import User
    
    # Check that User has expected attributes
    assert hasattr(User, 'email')
    assert hasattr(User, 'password_hash')
    assert hasattr(User, 'subscription_tier')
    assert hasattr(User, 'credits_balance')


if __name__ == "__main__":
    # Run tests directly
    test_models_import()
    test_user_model_exists()
    test_payment_model_exists()
    test_usage_log_model_exists()
    test_saved_meal_plan_model_exists()
    test_basic_model_attributes()
    print("All model tests passed!")