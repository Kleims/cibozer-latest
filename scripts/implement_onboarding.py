#!/usr/bin/env python3
"""Implement user onboarding flow"""

import os
import sys
from pathlib import Path

def create_onboarding_templates():
    """Create onboarding templates and routes"""
    
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates'
    
    # Create onboarding directory
    onboarding_dir = templates_dir / 'onboarding'
    onboarding_dir.mkdir(exist_ok=True)
    
    # Create welcome template
    welcome_template = """{% extends "base.html" %}
{% block title %}Welcome to Cibozer!{% endblock %}

{% block content %}
<div class="onboarding-container">
    <div class="progress-bar">
        <div class="progress" style="width: 20%"></div>
    </div>
    
    <h1>Welcome to Cibozer! 🎉</h1>
    <p class="lead">Let's get you started with personalized meal planning</p>
    
    <div class="onboarding-step">
        <h2>What brings you here?</h2>
        <form method="POST" action="{{ url_for('onboarding.goals') }}">
            {{ form.csrf_token }}
            <div class="goal-options">
                <label class="goal-card">
                    <input type="radio" name="goal" value="weight_loss" required>
                    <div class="card-content">
                        <h3>🎯 Weight Loss</h3>
                        <p>Healthy meals for sustainable weight loss</p>
                    </div>
                </label>
                
                <label class="goal-card">
                    <input type="radio" name="goal" value="healthy_eating" required>
                    <div class="card-content">
                        <h3>🥗 Healthy Eating</h3>
                        <p>Balanced nutrition for better health</p>
                    </div>
                </label>
                
                <label class="goal-card">
                    <input type="radio" name="goal" value="save_time" required>
                    <div class="card-content">
                        <h3>⏰ Save Time</h3>
                        <p>Quick and easy meal planning</p>
                    </div>
                </label>
                
                <label class="goal-card">
                    <input type="radio" name="goal" value="variety" required>
                    <div class="card-content">
                        <h3>🌈 More Variety</h3>
                        <p>Discover new recipes and cuisines</p>
                    </div>
                </label>
            </div>
            
            <button type="submit" class="btn btn-primary btn-lg mt-4">Continue</button>
        </form>
    </div>
</div>
{% endblock %}
"""
    
    with open(onboarding_dir / 'welcome.html', 'w', encoding='utf-8') as f:
        f.write(welcome_template)
    
    # Create dietary preferences template
    preferences_template = """{% extends "base.html" %}
{% block title %}Dietary Preferences - Cibozer{% endblock %}

{% block content %}
<div class="onboarding-container">
    <div class="progress-bar">
        <div class="progress" style="width: 40%"></div>
    </div>
    
    <h1>Tell us about your dietary preferences</h1>
    
    <div class="onboarding-step">
        <form method="POST" action="{{ url_for('onboarding.preferences') }}">
            {{ form.csrf_token }}
            
            <div class="form-group">
                <label>Do you follow any specific diet?</label>
                <select name="diet_type" class="form-control">
                    <option value="none">No specific diet</option>
                    <option value="vegetarian">Vegetarian</option>
                    <option value="vegan">Vegan</option>
                    <option value="keto">Keto</option>
                    <option value="paleo">Paleo</option>
                    <option value="mediterranean">Mediterranean</option>
                    <option value="gluten_free">Gluten-Free</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>Any allergies or foods to avoid?</label>
                <textarea name="allergies" class="form-control" rows="3" 
                    placeholder="e.g., nuts, dairy, shellfish..."></textarea>
            </div>
            
            <div class="form-group">
                <label>How many people are you cooking for?</label>
                <input type="number" name="servings" class="form-control" 
                    min="1" max="10" value="2" required>
            </div>
            
            <div class="d-flex justify-content-between mt-4">
                <a href="{{ url_for('onboarding.welcome') }}" class="btn btn-secondary">Back</a>
                <button type="submit" class="btn btn-primary">Continue</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}
"""
    
    with open(onboarding_dir / 'preferences.html', 'w', encoding='utf-8') as f:
        f.write(preferences_template)
    
    print(f"Created onboarding templates in: {onboarding_dir}")
    
    # Create onboarding routes file
    onboarding_routes = '''"""Onboarding routes for new users"""

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import RadioField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from models import db, User, UserPreferences

onboarding_bp = Blueprint('onboarding', __name__, url_prefix='/onboarding')

class GoalForm(FlaskForm):
    goal = RadioField('Goal', choices=[
        ('weight_loss', 'Weight Loss'),
        ('healthy_eating', 'Healthy Eating'),
        ('save_time', 'Save Time'),
        ('variety', 'More Variety')
    ], validators=[DataRequired()])

class PreferencesForm(FlaskForm):
    diet_type = SelectField('Diet Type', choices=[
        ('none', 'No specific diet'),
        ('vegetarian', 'Vegetarian'),
        ('vegan', 'Vegan'),
        ('keto', 'Keto'),
        ('paleo', 'Paleo'),
        ('mediterranean', 'Mediterranean'),
        ('gluten_free', 'Gluten-Free')
    ])
    allergies = TextAreaField('Allergies')
    servings = IntegerField('Servings', default=2)

@onboarding_bp.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome():
    """Welcome step of onboarding"""
    # Check if user already completed onboarding
    if current_user.onboarding_completed:
        return redirect(url_for('index'))
    
    form = GoalForm()
    if form.validate_on_submit():
        # Save goal to user profile
        current_user.primary_goal = form.goal.data
        db.session.commit()
        return redirect(url_for('onboarding.preferences'))
    
    return render_template('onboarding/welcome.html', form=form)

@onboarding_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Dietary preferences step"""
    if current_user.onboarding_completed:
        return redirect(url_for('index'))
    
    form = PreferencesForm()
    if form.validate_on_submit():
        # Create or update user preferences
        prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=current_user.id)
        
        prefs.diet_type = form.diet_type.data
        prefs.allergies = form.allergies.data
        prefs.default_servings = form.servings.data
        
        db.session.add(prefs)
        current_user.onboarding_completed = True
        db.session.commit()
        
        flash('Welcome aboard! Let\\'s create your first meal plan.', 'success')
        return redirect(url_for('index'))
    
    return render_template('onboarding/preferences.html', form=form)

@onboarding_bp.route('/skip')
@login_required
def skip():
    """Skip onboarding"""
    current_user.onboarding_completed = True
    db.session.commit()
    return redirect(url_for('index'))
'''
    
    routes_file = project_root / 'onboarding_routes.py'
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(onboarding_routes)
    
    print(f"Created onboarding routes: {routes_file}")
    
    # Add CSS for onboarding
    css_content = """
/* Onboarding Styles */
.onboarding-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
}

.progress-bar {
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    margin-bottom: 2rem;
}

.progress {
    height: 100%;
    background: #007bff;
    border-radius: 4px;
    transition: width 0.3s ease;
}

.goal-options {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 1.5rem;
}

.goal-card {
    cursor: pointer;
    position: relative;
}

.goal-card input[type="radio"] {
    position: absolute;
    opacity: 0;
}

.goal-card .card-content {
    border: 2px solid #dee2e6;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.2s ease;
}

.goal-card input[type="radio"]:checked + .card-content {
    border-color: #007bff;
    background: #f0f8ff;
}

.goal-card:hover .card-content {
    border-color: #6c757d;
}

.goal-card h3 {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
}

.goal-card p {
    font-size: 0.875rem;
    color: #6c757d;
    margin: 0;
}
"""
    
    css_file = project_root / 'static' / 'css' / 'onboarding.css'
    css_file.parent.mkdir(parents=True, exist_ok=True)
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    
    print(f"Created onboarding CSS: {css_file}")
    print("OK")
    return True

def main():
    """Main function"""
    try:
        success = create_onboarding_templates()
        return 0 if success else 1
    except Exception as e:
        print(f"Error implementing onboarding: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())