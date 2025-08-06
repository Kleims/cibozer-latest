"""Authentication routes."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db, limiter
from app.utils.validators import validate_email, validate_password, sanitize_input
from app.services.email_service import email_service
from app.utils.security import generate_confirmation_token, confirm_token
try:
    from app.services.monitoring_service import monitoring_service, monitor_security
except ImportError:
    # Fallback to simple monitoring if psutil is not available
    from app.services.monitoring_service_simple import monitoring_service, monitor_security

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
@monitor_security('user_login', 'info')
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', ''), 120).lower().strip()
        password = request.form.get('password', '')  # Don't sanitize passwords
        remember = request.form.get('remember', False)
        
        # Validate input
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')
        
        # Find user - using SQLAlchemy ORM (safe from SQL injection)
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Check if account is locked
            if user.is_locked():
                flash('Account is locked due to too many failed login attempts. Please try again later.', 'error')
                return render_template('auth/login.html')
            
            if user.check_password(password):
                if not user.is_active:
                    flash('Your account has been disabled. Please contact support.', 'error')
                    return render_template('auth/login.html')
                
                # Reset failed login counter
                user.reset_failed_login()
                
                # Update last login
                user.last_login = datetime.now(timezone.utc)
                db.session.commit()
                
                # Log in user
                login_user(user, remember=remember)
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('main.dashboard'))
            else:
                # Increment failed login counter
                user.increment_failed_login()
                db.session.commit()
                flash('Invalid email or password.', 'error')
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', ''), 120).lower().strip()
        password = request.form.get('password', '')  # Don't sanitize passwords
        password_confirm = request.form.get('password_confirm', '')  # Don't sanitize passwords
        full_name = sanitize_input(request.form.get('full_name', ''), 100).strip()
        
        # Validate input
        errors = []
        
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        
        if not validate_password(password):
            errors.append('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.')
        
        if password != password_confirm:
            errors.append('Passwords do not match.')
        
        if not full_name:
            errors.append('Please enter your full name.')
        
        # Check if user exists - using SQLAlchemy ORM (safe from SQL injection)
        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            credits_balance=3  # Free credits for new users
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email to new user
        welcome_sent = email_service.send_welcome_email(user.email, user.full_name)
        if welcome_sent:
            flash('Welcome to Cibozer! Check your email for tips to get started.', 'success')
        else:
            flash('Welcome to Cibozer! Your account has been created successfully.', 'success')
        
        # Log in user
        login_user(user)
        
        # Redirect to onboarding instead of dashboard
        return redirect(url_for('main.onboarding'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def forgot_password():
    """Password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send reset email
            from app.services.email_service import email_service
            reset_link = url_for('auth.reset_password', token=token, _external=True)
            email_service.send_password_reset_email(user.email, user.full_name, reset_link)
            
        # Always show success message to prevent email enumeration
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find user with token - using SQLAlchemy ORM (safe from SQL injection)
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        if not validate_password(password):
            flash('Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        if password != password_confirm:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html', token=token)
        
        # Update password
        user.set_password(password)
        user.clear_reset_token()
        db.session.commit()
        
        flash('Your password has been reset successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('auth/profile.html')

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    full_name = request.form.get('full_name', '').strip()
    
    if not full_name:
        flash('Please enter your full name.', 'error')
        return redirect(url_for('auth.profile'))
    
    current_user.full_name = full_name
    db.session.commit()
    
    flash('Your profile has been updated successfully.', 'success')
    return redirect(url_for('auth.profile'))


@auth_bp.route('/upgrade')
def upgrade():
    """Upgrade subscription page"""
    return render_template('auth/upgrade.html')
@auth_bp.route('/verify/<token>')
def verify_email(token):
    """Email verification endpoint"""
    user = User.query.filter_by(email_verification_token=token).first()
    
    if user and user.verify_email(token):
        db.session.commit()
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Invalid or expired verification token.', 'error')
        return redirect(url_for('auth.login'))