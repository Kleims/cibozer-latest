"""
Authentication routes and logic for Cibozer
User registration, login, and account management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UsageLog
from datetime import datetime, timedelta
import re

auth_bp = Blueprint('auth', __name__)

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        errors = []
        
        if not email:
            errors.append('Please enter an email/username')
        
        if not password:
            errors.append('Password is required')
        
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', email=email, full_name=full_name)
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            subscription_tier='free',
            credits_balance=3,  # Free users start with 3 credits
            trial_ends_at=datetime.utcnow() + timedelta(days=7)  # 7-day trial for premium features
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Log the user in
        login_user(user)
        
        # Log the registration
        usage_log = UsageLog(
            user_id=user.id,
            action_type='registration',
            metadata={'source': 'web'}
        )
        db.session.add(usage_log)
        db.session.commit()
        
        flash('Welcome to Cibozer! You have 3 free meal plans to start.', 'success')
        return redirect(url_for('create_meal_plan'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been suspended. Please contact support.', 'danger')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            return redirect(url_for('create_meal_plan'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/account')
@login_required
def account():
    """User account dashboard"""
    # Get user's usage stats
    monthly_usage = current_user.get_monthly_usage()
    saved_plans_count = current_user.meal_plans.count()
    
    return render_template('auth/account.html',
                         monthly_usage=monthly_usage,
                         saved_plans_count=saved_plans_count)

@auth_bp.route('/api/check-limits')
@login_required
def check_limits():
    """Check if user can perform action"""
    action = request.args.get('action', 'generate_plan')
    
    if action == 'generate_plan':
        can_generate = current_user.can_generate_plan()
        
        if not can_generate:
            if current_user.subscription_tier == 'free':
                return jsonify({
                    'allowed': False,
                    'reason': 'credit_limit',
                    'message': 'You have used all your free credits. Upgrade to Pro for unlimited meal plans!',
                    'credits_remaining': current_user.credits_balance
                })
        
        return jsonify({
            'allowed': True,
            'is_premium': current_user.is_premium(),
            'credits_remaining': current_user.credits_balance
        })
    
    elif action == 'export_pdf':
        if current_user.subscription_tier == 'free':
            return jsonify({
                'allowed': False,
                'reason': 'premium_feature',
                'message': 'PDF export is a Pro feature. Upgrade to access!'
            })
        
        return jsonify({'allowed': True})
    
    return jsonify({'allowed': True})

@auth_bp.route('/upgrade')
@login_required
def upgrade():
    """Upgrade subscription page"""
    return render_template('auth/upgrade.html')

@auth_bp.route('/api/user/stats')
@login_required
def user_stats():
    """Get user statistics for account page"""
    stats = {
        'email': current_user.email,
        'subscription_tier': current_user.subscription_tier,
        'credits_balance': current_user.credits_balance,
        'monthly_usage': current_user.get_monthly_usage(),
        'saved_plans': current_user.meal_plans.count(),
        'member_since': current_user.created_at.strftime('%B %Y'),
        'is_premium': current_user.is_premium()
    }
    
    if current_user.subscription_end_date:
        stats['subscription_ends'] = current_user.subscription_end_date.strftime('%B %d, %Y')
    
    if current_user.trial_ends_at and current_user.trial_ends_at > datetime.utcnow():
        stats['trial_days_left'] = (current_user.trial_ends_at - datetime.utcnow()).days
    
    return jsonify(stats)