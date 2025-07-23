"""
Tests for meal plan sharing functionality
"""

import pytest
from app import create_app
from app.extensions import db
from models import User, SharedMealPlan
from datetime import datetime, timedelta, timezone
import json
import bcrypt


@pytest.fixture
def client():
    """Test client fixture"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def app():
    """Create test app"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


@pytest.fixture
def authenticated_user(client, app):
    """Create and authenticate a test user"""
    with app.app_context():
        # Create test user
        user = User(
            email='test@example.com',
            full_name='Test User',
            subscription_tier='pro'
        )
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        return user


def test_shared_meal_plan_model(app):
    """Test SharedMealPlan model functionality"""
    with app.app_context():
        db.create_all()
        # Create a shared meal plan
        meal_data = {
            'meals': [
                {'name': 'Breakfast', 'calories': 400, 'items': ['Oatmeal', 'Berries']},
                {'name': 'Lunch', 'calories': 600, 'items': ['Salad', 'Chicken']}
            ]
        }
        
        shared_plan = SharedMealPlan(
            user_id=1,
            meal_plan_data=meal_data,
            title='My Healthy Meal Plan',
            description='A balanced meal plan for the week',
            calorie_target=2000,
            diet_type='balanced',
            days_count=7
        )
        
        # Test share code generation
        assert shared_plan.share_code is not None
        assert len(shared_plan.share_code) <= 32
        
        # Test default values
        assert shared_plan.is_public is True
        assert shared_plan.allow_copying is True
        assert shared_plan.view_count == 0
        assert shared_plan.copy_count == 0
        
        # Test expiration check
        assert shared_plan.is_expired() is False
        
        # Test with expiration
        shared_plan.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        assert shared_plan.is_expired() is True


def test_create_share_endpoint(client, authenticated_user, app):
    """Test creating a shareable meal plan"""
    meal_plan_data = {
        'day1': {
            'breakfast': {'name': 'Oatmeal', 'calories': 350},
            'lunch': {'name': 'Chicken Salad', 'calories': 450},
            'dinner': {'name': 'Grilled Salmon', 'calories': 500}
        }
    }
    
    response = client.post('/share/create',
                          json={
                              'meal_plan_data': meal_plan_data,
                              'title': 'My 7-Day Plan',
                              'description': 'Healthy eating plan',
                              'calorie_target': 2000,
                              'diet_type': 'balanced',
                              'days_count': 7,
                              'expires_in_days': 30
                          },
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'share_code' in data
    assert 'share_url' in data
    assert data['share_url'].endswith(data['share_code'])


def test_create_share_with_password(client, authenticated_user, app):
    """Test creating a password-protected share"""
    response = client.post('/share/create',
                          json={
                              'meal_plan_data': {'test': 'data'},
                              'password': 'secret123'
                          },
                          content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify password was set
    with app.app_context():
        shared_plan = SharedMealPlan.query.filter_by(share_code=data['share_code']).first()
        assert shared_plan.password_hash is not None
        assert shared_plan.verify_password('secret123') is True
        assert shared_plan.verify_password('wrongpass') is False


def test_view_shared_plan(client, app):
    """Test viewing a shared meal plan"""
    with app.app_context():
        # Create a shared plan
        shared_plan = SharedMealPlan(
            user_id=1,
            meal_plan_data={'test': 'data'},
            title='Test Plan'
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    # View the shared plan
    response = client.get(f'/share/{share_code}')
    assert response.status_code == 200
    
    # Verify view count was incremented
    with app.app_context():
        shared_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        assert shared_plan.view_count == 1


def test_expired_share_access(client, app):
    """Test accessing an expired share"""
    with app.app_context():
        # Create an expired share
        shared_plan = SharedMealPlan(
            user_id=1,
            meal_plan_data={'test': 'data'},
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    response = client.get(f'/share/{share_code}', follow_redirects=True)
    assert b'expired' in response.data


def test_copy_shared_plan(client, authenticated_user, app):
    """Test copying a shared meal plan"""
    with app.app_context():
        # Create a shared plan
        meal_data = {'meals': ['breakfast', 'lunch', 'dinner']}
        shared_plan = SharedMealPlan(
            user_id=2,  # Different user
            meal_plan_data=meal_data,
            title='Copyable Plan',
            allow_copying=True
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    # Copy the plan
    response = client.post(f'/share/{share_code}/copy')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['meal_plan_data'] == meal_data
    
    # Verify copy count
    with app.app_context():
        shared_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        assert shared_plan.copy_count == 1


def test_copy_disabled(client, authenticated_user, app):
    """Test copying when disabled"""
    with app.app_context():
        shared_plan = SharedMealPlan(
            user_id=2,
            meal_plan_data={'test': 'data'},
            allow_copying=False
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    response = client.post(f'/share/{share_code}/copy')
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'cannot be copied' in data['error']


def test_my_shares_page(client, authenticated_user, app):
    """Test viewing user's shared plans"""
    with app.app_context():
        # Create multiple shares for the user
        for i in range(3):
            shared_plan = SharedMealPlan(
                user_id=authenticated_user.id,
                meal_plan_data={'plan': i},
                title=f'Plan {i}'
            )
            db.session.add(shared_plan)
        db.session.commit()
    
    response = client.get('/share/my-shares')
    assert response.status_code == 200
    assert b'Plan 0' in response.data
    assert b'Plan 1' in response.data
    assert b'Plan 2' in response.data


def test_delete_share(client, authenticated_user, app):
    """Test deleting a shared plan"""
    with app.app_context():
        shared_plan = SharedMealPlan(
            user_id=authenticated_user.id,
            meal_plan_data={'test': 'data'}
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    # Delete the share
    response = client.post(f'/share/{share_code}/delete')
    assert response.status_code == 200
    
    # Verify it was deleted
    with app.app_context():
        deleted_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        assert deleted_plan is None


def test_delete_unauthorized(client, authenticated_user, app):
    """Test deleting someone else's share"""
    with app.app_context():
        # Create share owned by different user
        shared_plan = SharedMealPlan(
            user_id=999,  # Different user
            meal_plan_data={'test': 'data'}
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    response = client.post(f'/share/{share_code}/delete')
    assert response.status_code == 404


def test_share_code_uniqueness(app):
    """Test that share codes are unique"""
    with app.app_context():
        codes = set()
        for _ in range(100):
            code = SharedMealPlan.generate_share_code()
            assert code not in codes
            codes.add(code)


def test_password_verification(client, app):
    """Test password verification for protected shares"""
    with app.app_context():
        # Create password-protected share
        shared_plan = SharedMealPlan(
            user_id=1,
            meal_plan_data={'test': 'data'},
            password_hash=bcrypt.hashpw(b'secret123', bcrypt.gensalt()).decode('utf-8')
        )
        db.session.add(shared_plan)
        db.session.commit()
        share_code = shared_plan.share_code
    
    # Try to access without password
    response = client.get(f'/share/{share_code}')
    assert response.status_code == 200
    assert b'password' in response.data.lower()
    
    # Verify with wrong password
    response = client.post(f'/share/{share_code}/verify',
                          data={'password': 'wrongpass'},
                          follow_redirects=True)
    assert b'Incorrect password' in response.data
    
    # Verify with correct password
    response = client.post(f'/share/{share_code}/verify',
                          data={'password': 'secret123'},
                          follow_redirects=True)
    assert b'Incorrect password' not in response.data