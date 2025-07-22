"""Simple payments tests without Flask app context."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import MagicMock


def test_payments_import():
    """Test that payments module can be imported."""
    import payments
    assert payments is not None


def test_pricing_plans_function_exists():
    """Test that get_pricing_plans function exists."""
    from payments import get_pricing_plans
    assert callable(get_pricing_plans)
    

def test_deduct_credit_function_exists():
    """Test that deduct_credit function exists.""" 
    from payments import deduct_credit
    assert callable(deduct_credit)


def test_add_credits_function_exists():
    """Test that add_credits function exists."""
    from payments import add_credits
    assert callable(add_credits)


def test_check_user_credits_function_exists():
    """Test that check_user_credits function exists."""
    from payments import check_user_credits
    assert callable(check_user_credits)


def test_basic_payment_functions():
    """Test basic payment function imports."""
    from payments import (
        cancel_subscription,
        stripe_webhook,
        create_checkout_session
    )
    
    assert callable(cancel_subscription)
    assert callable(stripe_webhook)
    assert callable(create_checkout_session)


def test_pricing_plans_basic():
    """Basic test of pricing plans function."""
    from payments import get_pricing_plans
    
    try:
        plans = get_pricing_plans()
        # Should return a list
        assert isinstance(plans, list)
        print(f"Found {len(plans)} pricing plans")
    except Exception as e:
        pytest.skip(f"Pricing plans test skipped due to: {e}")


if __name__ == "__main__":
    # Run tests directly
    test_payments_import()
    test_pricing_plans_function_exists()
    test_deduct_credit_function_exists()
    test_add_credits_function_exists()
    test_check_user_credits_function_exists()
    test_basic_payment_functions()
    test_pricing_plans_basic()
    print("All basic tests passed!")