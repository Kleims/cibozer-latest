"""
Authentication routes and logic for Cibozer
User registration, login, and account management
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app as app, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UsageLog
from datetime import datetime, timedelta, timezone
import re
import time
from functools import wraps
# from flask_wtf.csrf import csrf_exempt  # Not needed anymore

auth_bp = Blueprint('auth', __name__)

# Simple in-memory rate limiting (in production, use Redis)
login_attempts = {}
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_ATTEMPTS = 5  # Maximum attempts in window

def rate_limit(f):
    """Rate limiting decorator for authentication endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        identifier = request.remote_addr
        current_time = time.time()
        
        # Clean old attempts
        global login_attempts
        login_attempts = {k: v for k, v in login_attempts.items() 
                         if current_time - v['first_attempt'] < RATE_LIMIT_WINDOW}
        
        # Check rate limit
        if identifier in login_attempts:
            attempts = login_attempts[identifier]
            if attempts['count'] >= MAX_ATTEMPTS:
                time_left = int(RATE_LIMIT_WINDOW - (current_time - attempts['first_attempt']))
                flash(f'Too many attempts. Please try again in {time_left} seconds.', 'danger')
                return render_template('auth/login.html'), 429
        
        return f(*args, **kwargs)
    
    return decorated_function

def record_attempt(identifier):
    """Record a login attempt"""
    current_time = time.time()
    if identifier not in login_attempts:
        login_attempts[identifier] = {'count': 1, 'first_attempt': current_time}
    else:
        login_attempts[identifier]['count'] += 1

def clear_attempts(identifier):
    """Clear attempts on successful login"""
    if identifier in login_attempts:
        del login_attempts[identifier]

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain at least one number")
    
    return errors

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            full_name = request.form.get('full_name', '').strip()
            
            # Validation
            errors = []
            
            if not full_name:
                errors.append('Please enter your full name')
            
            if not email:
                errors.append('Please enter an email/username')
            elif not is_valid_email(email):
                errors.append('Please enter a valid email address')
            
            if not password:
                errors.append('Password is required')
            else:
                # Validate password strength
                password_errors = validate_password(password)
                errors.extend(password_errors)
            
            if password != password_confirm:
                errors.append('Passwords do not match')
            
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
                trial_ends_at=datetime.now(timezone.utc) + timedelta(days=7)  # 7-day trial for premium features
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Security: Clear session before login
            session.clear()
            
            # Log the user in
            login_user(user)
            
            # Add session security
            session.permanent = True
            session['_fresh'] = True
            
            # Log the registration
            usage_log = UsageLog(
                user_id=user.id,
                action_type='registration',
                extra_data={'source': 'web'}
            )
            db.session.add(usage_log)
            db.session.commit()
            
            flash('Welcome to Cibozer! You have 3 free meal plans to start.', 'success')
            return redirect(url_for('create_meal_plan'))
            
        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            import traceback
            app.logger.error(f"Traceback: {traceback.format_exc()}")
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
@rate_limit
def login():
    """User login"""
    app.logger.info(f"[AUTH] Login route accessed - Method: {request.method}")
    app.logger.info(f"[AUTH] Current user authenticated: {current_user.is_authenticated}")
    app.logger.info(f"[AUTH] Request args: {request.args}")
    app.logger.info(f"[AUTH] Next page: {request.args.get('next')}")
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        identifier = request.remote_addr
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                record_attempt(identifier)
                flash('Your account has been suspended. Please contact support.', 'danger')
                return render_template('auth/login.html')
            
            # Clear rate limiting on successful login
            clear_attempts(identifier)
            
            # Security: Clear session before login to prevent fixation
            session.clear()
            
            login_user(user, remember=remember)
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            # Add session security
            session.permanent = True
            session['_fresh'] = True
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # Prevent open redirect
                return redirect(next_page)
            
            return redirect(url_for('create_meal_plan'))
        else:
            record_attempt(identifier)
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
                         saved_plans_count=saved_plans_count,
                         now=datetime.now(timezone.utc))

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
    
    if current_user.trial_ends_at and current_user.trial_ends_at > datetime.now(timezone.utc):
        stats['trial_days_left'] = (current_user.trial_ends_at - datetime.now(timezone.utc)).days
    
    return jsonify(stats)

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Please enter your email address', 'danger')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = user.generate_reset_token()
            # In production, send email with reset link
            # For now, just show the link
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            flash(f'Password reset link: {reset_url}', 'info')
            app.logger.info(f"Password reset requested for {email}. Token: {token}")
        else:
            # Don't reveal if email exists
            flash('If an account exists with this email, you will receive a password reset link.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        errors = []
        
        if not password:
            errors.append('Password is required')
        else:
            password_errors = validate_password(password)
            errors.extend(password_errors)
        
        if password != password_confirm:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.set_password(password)
        user.clear_reset_token()
        
        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)