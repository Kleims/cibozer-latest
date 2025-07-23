"""Authentication routes."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db, limiter
from app.utils.validators import validate_email, validate_password
from app.utils.security import generate_confirmation_token, confirm_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Validate input
        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('auth/login.html')
        
        # Find user
        user = db.session.query(User).filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been disabled. Please contact support.', 'error')
                return render_template('auth/login.html')
            
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
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def register():
    """User registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        full_name = request.form.get('full_name', '').strip()
        
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
        
        # Check if user exists
        if db.session.query(User).filter_by(email=email).first():
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
        
        # Send confirmation email (TODO)
        # token = generate_confirmation_token(user.email)
        # send_confirmation_email(user.email, token)
        
        # Log in user
        login_user(user)
        
        flash('Welcome to Cibozer! Your account has been created successfully.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit("3 per minute")
def forgot_password():
    """Password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        
        if not validate_email(email):
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/forgot_password.html')
        
        user = db.session.query(User).filter_by(email=email).first()
        if user:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # Send reset email (TODO)
            # send_password_reset_email(user.email, token)
            
        # Always show success message to prevent email enumeration
        flash('If an account exists with that email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Find user with token
    user = db.session.query(User).filter_by(reset_token=token).first()
    
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