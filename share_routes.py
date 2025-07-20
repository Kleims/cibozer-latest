"""
Routes for meal plan sharing functionality
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, SharedMealPlan, User
from datetime import datetime, timedelta, timezone
import bcrypt
import json
from logging_setup import get_logger

logger = get_logger(__name__)
share_bp = Blueprint('share', __name__, url_prefix='/share')


@share_bp.route('/create', methods=['POST'])
@login_required
def create_share():
    """Create a shareable link for a meal plan"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('meal_plan_data'):
            return jsonify({'error': 'Meal plan data is required'}), 400
        
        # Create new shared meal plan
        shared_plan = SharedMealPlan(
            user_id=current_user.id,
            meal_plan_data=data['meal_plan_data'],
            title=data.get('title', ''),
            description=data.get('description', ''),
            calorie_target=data.get('calorie_target'),
            diet_type=data.get('diet_type'),
            days_count=data.get('days_count', 1),
            is_public=data.get('is_public', True),
            allow_copying=data.get('allow_copying', True)
        )
        
        # Set expiration if provided
        expires_in_days = data.get('expires_in_days')
        if expires_in_days:
            shared_plan.expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        # Set password if provided
        password = data.get('password')
        if password:
            shared_plan.password_hash = bcrypt.hashpw(
                password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
        
        db.session.add(shared_plan)
        db.session.commit()
        
        # Generate full share URL
        share_url = url_for('share.view_shared_plan', 
                          share_code=shared_plan.share_code, 
                          _external=True)
        
        logger.info(f"User {current_user.id} created shared meal plan {shared_plan.share_code}")
        
        return jsonify({
            'success': True,
            'share_code': shared_plan.share_code,
            'share_url': share_url,
            'expires_at': shared_plan.expires_at.isoformat() if shared_plan.expires_at else None
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating shared meal plan: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create shareable link'}), 500


@share_bp.route('/<share_code>')
def view_shared_plan(share_code):
    """View a shared meal plan"""
    try:
        # Find the shared plan
        shared_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        
        if not shared_plan:
            flash('Shared meal plan not found', 'error')
            return redirect(url_for('index'))
        
        # Check if expired
        if shared_plan.is_expired():
            flash('This shared meal plan has expired', 'error')
            return redirect(url_for('index'))
        
        # Check if password protected
        if shared_plan.password_hash:
            # Check if already authenticated in session
            auth_key = f'shared_plan_auth_{share_code}'
            if not session.get(auth_key):
                return render_template('share_password.html', share_code=share_code)
        
        # Increment view count
        shared_plan.increment_view_count()
        
        # Get creator info
        creator = User.query.get(shared_plan.user_id)
        
        return render_template('view_shared_plan.html',
                             shared_plan=shared_plan,
                             creator=creator,
                             meal_plan=shared_plan.meal_plan_data)
        
    except Exception as e:
        logger.error(f"Error viewing shared meal plan {share_code}: {str(e)}")
        flash('Error loading shared meal plan', 'error')
        return redirect(url_for('index'))


@share_bp.route('/<share_code>/verify', methods=['POST'])
def verify_password(share_code):
    """Verify password for protected shared plans"""
    try:
        shared_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        
        if not shared_plan:
            return jsonify({'error': 'Shared plan not found'}), 404
        
        password = request.form.get('password')
        if not password:
            flash('Password is required', 'error')
            return redirect(url_for('share.view_shared_plan', share_code=share_code))
        
        if shared_plan.verify_password(password):
            # Store authentication in session
            session[f'shared_plan_auth_{share_code}'] = True
            return redirect(url_for('share.view_shared_plan', share_code=share_code))
        else:
            flash('Incorrect password', 'error')
            return render_template('share_password.html', share_code=share_code)
            
    except Exception as e:
        logger.error(f"Error verifying password for {share_code}: {str(e)}")
        flash('Error verifying password', 'error')
        return redirect(url_for('index'))


@share_bp.route('/<share_code>/copy', methods=['POST'])
@login_required
def copy_shared_plan(share_code):
    """Copy a shared meal plan to user's account"""
    try:
        shared_plan = SharedMealPlan.query.filter_by(share_code=share_code).first()
        
        if not shared_plan:
            return jsonify({'error': 'Shared plan not found'}), 404
        
        if not shared_plan.allow_copying:
            return jsonify({'error': 'This meal plan cannot be copied'}), 403
        
        if shared_plan.is_expired():
            return jsonify({'error': 'This shared meal plan has expired'}), 403
        
        # Increment copy count
        shared_plan.copy_count += 1
        db.session.commit()
        
        logger.info(f"User {current_user.id} copied shared meal plan {share_code}")
        
        return jsonify({
            'success': True,
            'meal_plan_data': shared_plan.meal_plan_data,
            'title': shared_plan.title,
            'calorie_target': shared_plan.calorie_target,
            'diet_type': shared_plan.diet_type
        }), 200
        
    except Exception as e:
        logger.error(f"Error copying shared meal plan {share_code}: {str(e)}")
        return jsonify({'error': 'Failed to copy meal plan'}), 500


@share_bp.route('/my-shares')
@login_required
def my_shares():
    """View all meal plans shared by the current user"""
    try:
        shared_plans = SharedMealPlan.query.filter_by(user_id=current_user.id)\
                                          .order_by(SharedMealPlan.created_at.desc())\
                                          .all()
        
        return render_template('my_shares.html', shared_plans=shared_plans)
        
    except Exception as e:
        logger.error(f"Error loading user's shared plans: {str(e)}")
        flash('Error loading your shared meal plans', 'error')
        return redirect(url_for('dashboard'))


@share_bp.route('/<share_code>/delete', methods=['POST'])
@login_required
def delete_share(share_code):
    """Delete a shared meal plan"""
    try:
        shared_plan = SharedMealPlan.query.filter_by(
            share_code=share_code,
            user_id=current_user.id
        ).first()
        
        if not shared_plan:
            return jsonify({'error': 'Shared plan not found or unauthorized'}), 404
        
        db.session.delete(shared_plan)
        db.session.commit()
        
        logger.info(f"User {current_user.id} deleted shared meal plan {share_code}")
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error(f"Error deleting shared meal plan {share_code}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete shared plan'}), 500