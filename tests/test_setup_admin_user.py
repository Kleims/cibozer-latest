"""Tests for setup_admin_user.py"""

import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock

import setup_admin_user
from setup_admin_user import create_admin_user


def test_create_admin_user_success():
    """Test create_admin_user with valid inputs"""
    result = create_admin_user()
    assert result is not None

def test_create_admin_user_error_handling():
    """Test create_admin_user error handling"""
    # Test with invalid inputs or mocked exceptions
    with pytest.raises((ValueError, TypeError, Exception)):
        create_admin_user(None)  # or other invalid input
