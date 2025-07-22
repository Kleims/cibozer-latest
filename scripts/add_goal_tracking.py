#!/usr/bin/env python3
"""Add goal tracking features for user retention"""

import os
import sys
from pathlib import Path

def add_goal_tracking_models():
    """Add goal tracking models to the database"""
    
    project_root = Path(__file__).parent.parent
    models_file = project_root / 'models.py'
    
    if not models_file.exists():
        print("Error: models.py not found")
        return False
    
    # Read current models
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if goal tracking models already exist
    if 'class UserGoal' in content:
        print("Goal tracking models already exist")
        return True
    
    # Add goal tracking models
    goal_models = '''

# Goal Tracking Models
class UserGoal(db.Model):
    """User's health and nutrition goals"""
    __tablename__ = 'user_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)  # weight_loss, muscle_gain, health, energy
    target_value = db.Column(db.Float, nullable=True)  # e.g., target weight
    current_value = db.Column(db.Float, nullable=True)  # e.g., current weight
    target_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Nutrition targets
    daily_calories = db.Column(db.Integer, nullable=True)
    daily_protein = db.Column(db.Integer, nullable=True)
    daily_carbs = db.Column(db.Integer, nullable=True)
    daily_fat = db.Column(db.Integer, nullable=True)
    
    user = db.relationship('User', backref=db.backref('goals', lazy='dynamic'))
    
    def calculate_progress(self):
        """Calculate progress percentage"""
        if self.target_value and self.current_value:
            if self.goal_type == 'weight_loss':
                # For weight loss, progress is inverse
                initial_diff = self.target_value - self.current_value
                if initial_diff != 0:
                    return min(100, max(0, (1 - (self.current_value - self.target_value) / initial_diff) * 100))
            else:
                # For other goals, direct progress
                if self.target_value != 0:
                    return min(100, (self.current_value / self.target_value) * 100)
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'goal_type': self.goal_type,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'progress': self.calculate_progress(),
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'daily_calories': self.daily_calories,
            'daily_protein': self.daily_protein,
            'daily_carbs': self.daily_carbs,
            'daily_fat': self.daily_fat,
            'is_active': self.is_active
        }

class GoalProgress(db.Model):
    """Track progress updates for goals"""
    __tablename__ = 'goal_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('user_goals.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    goal = db.relationship('UserGoal', backref=db.backref('progress_entries', lazy='dynamic'))

class DailyNutrition(db.Model):
    """Track daily nutrition intake"""
    __tablename__ = 'daily_nutrition'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    calories = db.Column(db.Integer, default=0)
    protein = db.Column(db.Integer, default=0)
    carbs = db.Column(db.Integer, default=0)
    fat = db.Column(db.Integer, default=0)
    fiber = db.Column(db.Integer, default=0)
    
    user = db.relationship('User', backref=db.backref('daily_nutrition', lazy='dynamic'))
    
    __table_args__ = (db.UniqueConstraint('user_id', 'date'),)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'calories': self.calories,
            'protein': self.protein,
            'carbs': self.carbs,
            'fat': self.fat,
            'fiber': self.fiber
        }
'''
    
    # Add date import if needed
    if 'from datetime import datetime' in content and 'date' not in content:
        date_import_pos = content.find('from datetime import datetime')
        end_of_line = content.find('\n', date_import_pos)
        content = content[:date_import_pos] + 'from datetime import datetime, date' + content[end_of_line:]
    
    # Append models to file
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(content + goal_models)
    
    print("Added goal tracking models to models.py")
    return True

def create_goal_tracking_routes():
    """Create goal tracking API routes"""
    
    project_root = Path(__file__).parent.parent
    routes_file = project_root / 'goal_tracking_routes.py'
    
    goal_routes = '''"""Goal tracking routes for user health and nutrition goals"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from models import db, UserGoal, GoalProgress, DailyNutrition
from datetime import datetime, date, timedelta
from sqlalchemy import and_, func

goals_bp = Blueprint('goals', __name__, url_prefix='/api/goals')

@goals_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage_goals():
    """Get or create user goals"""
    if request.method == 'POST':
        data = request.get_json()
        
        # Deactivate existing goals of same type
        if data.get('goal_type'):
            UserGoal.query.filter_by(
                user_id=current_user.id,
                goal_type=data['goal_type'],
                is_active=True
            ).update({'is_active': False})
        
        # Create new goal
        goal = UserGoal(
            user_id=current_user.id,
            goal_type=data.get('goal_type'),
            target_value=data.get('target_value'),
            current_value=data.get('current_value'),
            target_date=datetime.strptime(data['target_date'], '%Y-%m-%d').date() if data.get('target_date') else None,
            daily_calories=data.get('daily_calories'),
            daily_protein=data.get('daily_protein'),
            daily_carbs=data.get('daily_carbs'),
            daily_fat=data.get('daily_fat')
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'goal': goal.to_dict()
        })
    
    # GET - return active goals
    goals = UserGoal.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    return jsonify({
        'goals': [goal.to_dict() for goal in goals]
    })

@goals_bp.route('/<int:goal_id>/progress', methods=['POST'])
@login_required
def update_progress(goal_id):
    """Update goal progress"""
    goal = UserGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first_or_404()
    
    data = request.get_json()
    value = data.get('value')
    
    if value is None:
        return jsonify({'error': 'Value is required'}), 400
    
    # Update current value
    goal.current_value = value
    goal.updated_at = datetime.utcnow()
    
    # Create progress entry
    progress = GoalProgress(
        goal_id=goal.id,
        value=value,
        notes=data.get('notes')
    )
    
    db.session.add(progress)
    db.session.commit()
    
    # Check if goal is achieved
    if goal.calculate_progress() >= 100:
        # Trigger achievement notification
        from notification_routes import send_achievement_notification
        send_achievement_notification(
            current_user.id,
            'goal_achieved',
            {'goal_type': goal.goal_type}
        )
    
    return jsonify({
        'success': True,
        'goal': goal.to_dict(),
        'progress': goal.calculate_progress()
    })

@goals_bp.route('/<int:goal_id>/history', methods=['GET'])
@login_required
def get_progress_history(goal_id):
    """Get progress history for a goal"""
    goal = UserGoal.query.filter_by(
        id=goal_id,
        user_id=current_user.id
    ).first_or_404()
    
    progress_entries = GoalProgress.query.filter_by(
        goal_id=goal.id
    ).order_by(GoalProgress.recorded_at.desc()).limit(30).all()
    
    return jsonify({
        'goal': goal.to_dict(),
        'history': [{
            'value': entry.value,
            'notes': entry.notes,
            'date': entry.recorded_at.isoformat()
        } for entry in progress_entries]
    })

@goals_bp.route('/nutrition/today', methods=['GET', 'POST'])
@login_required
def today_nutrition():
    """Get or update today's nutrition"""
    today = date.today()
    
    if request.method == 'POST':
        data = request.get_json()
        
        # Get or create today's entry
        nutrition = DailyNutrition.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not nutrition:
            nutrition = DailyNutrition(
                user_id=current_user.id,
                date=today
            )
            db.session.add(nutrition)
        
        # Update values (add to existing)
        nutrition.calories += data.get('calories', 0)
        nutrition.protein += data.get('protein', 0)
        nutrition.carbs += data.get('carbs', 0)
        nutrition.fat += data.get('fat', 0)
        nutrition.fiber += data.get('fiber', 0)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'nutrition': nutrition.to_dict()
        })
    
    # GET - return today's nutrition and goals
    nutrition = DailyNutrition.query.filter_by(
        user_id=current_user.id,
        date=today
    ).first()
    
    # Get active nutrition goals
    goals = UserGoal.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()
    
    return jsonify({
        'date': today.isoformat(),
        'nutrition': nutrition.to_dict() if nutrition else {
            'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'fiber': 0
        },
        'goals': {
            'calories': goals.daily_calories if goals else None,
            'protein': goals.daily_protein if goals else None,
            'carbs': goals.daily_carbs if goals else None,
            'fat': goals.daily_fat if goals else None
        }
    })

@goals_bp.route('/nutrition/week', methods=['GET'])
@login_required
def week_nutrition():
    """Get nutrition data for the past week"""
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    
    nutrition_data = DailyNutrition.query.filter(
        and_(
            DailyNutrition.user_id == current_user.id,
            DailyNutrition.date >= start_date,
            DailyNutrition.date <= end_date
        )
    ).order_by(DailyNutrition.date).all()
    
    # Fill in missing days with zeros
    data_by_date = {n.date: n for n in nutrition_data}
    week_data = []
    
    current_date = start_date
    while current_date <= end_date:
        if current_date in data_by_date:
            week_data.append(data_by_date[current_date].to_dict())
        else:
            week_data.append({
                'date': current_date.isoformat(),
                'calories': 0,
                'protein': 0,
                'carbs': 0,
                'fat': 0,
                'fiber': 0
            })
        current_date += timedelta(days=1)
    
    return jsonify({
        'week_data': week_data,
        'averages': {
            'calories': sum(d['calories'] for d in week_data) / 7,
            'protein': sum(d['protein'] for d in week_data) / 7,
            'carbs': sum(d['carbs'] for d in week_data) / 7,
            'fat': sum(d['fat'] for d in week_data) / 7,
            'fiber': sum(d['fiber'] for d in week_data) / 7
        }
    })

@goals_bp.route('/insights', methods=['GET'])
@login_required
def get_insights():
    """Get personalized insights based on goals and progress"""
    goals = UserGoal.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).all()
    
    insights = []
    
    for goal in goals:
        progress = goal.calculate_progress()
        
        if progress >= 80:
            insights.append({
                'type': 'success',
                'message': f'Great job! You\'re {progress:.0f}% of the way to your {goal.goal_type.replace("_", " ")} goal!'
            })
        elif progress < 30 and goal.created_at < datetime.utcnow() - timedelta(days=7):
            insights.append({
                'type': 'suggestion',
                'message': f'Your {goal.goal_type.replace("_", " ")} goal might need adjustment. Consider breaking it into smaller milestones.'
            })
    
    # Nutrition insights
    week_nutrition = DailyNutrition.query.filter(
        and_(
            DailyNutrition.user_id == current_user.id,
            DailyNutrition.date >= date.today() - timedelta(days=7)
        )
    ).all()
    
    if len(week_nutrition) >= 5:
        avg_calories = sum(n.calories for n in week_nutrition) / len(week_nutrition)
        if goals and goals[0].daily_calories:
            if avg_calories < goals[0].daily_calories * 0.8:
                insights.append({
                    'type': 'warning',
                    'message': 'You\'ve been under your calorie target this week. Make sure you\'re eating enough!'
                })
            elif avg_calories > goals[0].daily_calories * 1.2:
                insights.append({
                    'type': 'info',
                    'message': 'You\'ve been over your calorie target. Consider portion control or more activity.'
                })
    
    return jsonify({'insights': insights})
'''
    
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(goal_routes)
    
    print(f"Created goal tracking routes: {routes_file}")
    return True

def create_goal_tracking_ui():
    """Create goal tracking UI templates"""
    
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates' / 'goals'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create goal dashboard template
    dashboard_template = """{% extends "base.html" %}
{% block title %}My Goals - Cibozer{% endblock %}

{% block content %}
<div class="goals-dashboard">
    <div class="header">
        <h1>My Health Goals</h1>
        <button class="btn btn-primary" data-toggle="modal" data-target="#newGoalModal">
            Set New Goal
        </button>
    </div>
    
    <div class="active-goals">
        <div id="goals-list" class="row">
            <!-- Goals will be loaded here -->
        </div>
    </div>
    
    <div class="nutrition-tracking">
        <h2>Today's Nutrition</h2>
        <div id="nutrition-summary" class="nutrition-cards">
            <!-- Nutrition data will be loaded here -->
        </div>
    </div>
    
    <div class="weekly-progress">
        <h2>Weekly Progress</h2>
        <canvas id="weeklyChart"></canvas>
    </div>
    
    <div class="insights-section">
        <h2>Insights & Tips</h2>
        <div id="insights-list">
            <!-- Insights will be loaded here -->
        </div>
    </div>
</div>

<!-- New Goal Modal -->
<div class="modal fade" id="newGoalModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Set a New Goal</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form id="goalForm">
                    <div class="form-group">
                        <label>Goal Type</label>
                        <select class="form-control" id="goalType" required>
                            <option value="">Select a goal</option>
                            <option value="weight_loss">Weight Loss</option>
                            <option value="muscle_gain">Muscle Gain</option>
                            <option value="healthy_eating">Healthy Eating</option>
                            <option value="energy_boost">Energy Boost</option>
                        </select>
                    </div>
                    
                    <div id="weightGoalFields" style="display: none;">
                        <div class="form-group">
                            <label>Current Weight (lbs)</label>
                            <input type="number" class="form-control" id="currentWeight" step="0.1">
                        </div>
                        <div class="form-group">
                            <label>Target Weight (lbs)</label>
                            <input type="number" class="form-control" id="targetWeight" step="0.1">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Target Date</label>
                        <input type="date" class="form-control" id="targetDate" 
                               min="{{ today }}" required>
                    </div>
                    
                    <h4>Daily Nutrition Targets</h4>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Calories</label>
                                <input type="number" class="form-control" id="dailyCalories" 
                                       placeholder="e.g., 2000">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Protein (g)</label>
                                <input type="number" class="form-control" id="dailyProtein" 
                                       placeholder="e.g., 50">
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Carbs (g)</label>
                                <input type="number" class="form-control" id="dailyCarbs" 
                                       placeholder="e.g., 250">
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-group">
                                <label>Fat (g)</label>
                                <input type="number" class="form-control" id="dailyFat" 
                                       placeholder="e.g., 65">
                            </div>
                        </div>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary" onclick="saveGoal()">Save Goal</button>
            </div>
        </div>
    </div>
</div>

<style>
.goals-dashboard {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
}

.goal-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
}

.goal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
}

.goal-type {
    font-size: 1.25rem;
    font-weight: bold;
    text-transform: capitalize;
}

.goal-progress {
    margin: 1rem 0;
}

.progress {
    height: 20px;
    background: #e9ecef;
    border-radius: 10px;
    overflow: hidden;
}

.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
    transition: width 0.3s ease;
}

.goal-stats {
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;
    font-size: 0.875rem;
    color: #6b7280;
}

.nutrition-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}

.nutrition-card {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.nutrition-value {
    font-size: 2rem;
    font-weight: bold;
    color: #1f2937;
}

.nutrition-label {
    font-size: 0.875rem;
    color: #6b7280;
    margin-top: 0.25rem;
}

.nutrition-target {
    font-size: 0.75rem;
    color: #9ca3af;
}

.insights-section {
    margin-top: 2rem;
}

.insight-item {
    background: #f3f4f6;
    border-left: 4px solid;
    padding: 1rem;
    margin-bottom: 1rem;
    border-radius: 4px;
}

.insight-item.success {
    border-color: #10b981;
    background: #f0fdf4;
}

.insight-item.warning {
    border-color: #f59e0b;
    background: #fffbeb;
}

.insight-item.info {
    border-color: #3b82f6;
    background: #eff6ff;
}
</style>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// Load goals
function loadGoals() {
    fetch('/api/goals/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('goals-list');
            container.innerHTML = '';
            
            data.goals.forEach(goal => {
                const card = createGoalCard(goal);
                container.appendChild(card);
            });
        });
}

function createGoalCard(goal) {
    const col = document.createElement('div');
    col.className = 'col-md-6';
    
    const card = document.createElement('div');
    card.className = 'goal-card';
    
    const targetDate = goal.target_date ? new Date(goal.target_date) : null;
    const daysLeft = targetDate ? Math.ceil((targetDate - new Date()) / (1000 * 60 * 60 * 24)) : null;
    
    card.innerHTML = `
        <div class="goal-header">
            <span class="goal-type">${goal.goal_type.replace('_', ' ')}</span>
            <span class="badge badge-primary">${daysLeft ? daysLeft + ' days left' : 'Ongoing'}</span>
        </div>
        <div class="goal-progress">
            <div class="progress">
                <div class="progress-bar" style="width: ${goal.progress}%"></div>
            </div>
        </div>
        <div class="goal-stats">
            <span>Current: ${goal.current_value || 'N/A'}</span>
            <span>Target: ${goal.target_value || 'N/A'}</span>
            <span>Progress: ${Math.round(goal.progress)}%</span>
        </div>
        <button class="btn btn-sm btn-outline-primary mt-2" 
                onclick="updateProgress(${goal.id})">Update Progress</button>
    `;
    
    col.appendChild(card);
    return col;
}

// Load today's nutrition
function loadNutrition() {
    fetch('/api/goals/nutrition/today')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('nutrition-summary');
            container.innerHTML = '';
            
            const nutrients = ['calories', 'protein', 'carbs', 'fat'];
            nutrients.forEach(nutrient => {
                const card = document.createElement('div');
                card.className = 'nutrition-card';
                
                const current = data.nutrition[nutrient];
                const target = data.goals[nutrient];
                const percentage = target ? (current / target * 100).toFixed(0) : 0;
                
                card.innerHTML = `
                    <div class="nutrition-value">${current}</div>
                    <div class="nutrition-label">${nutrient}</div>
                    ${target ? `<div class="nutrition-target">of ${target} (${percentage}%)</div>` : ''}
                `;
                
                container.appendChild(card);
            });
        });
}

// Load weekly chart
function loadWeeklyChart() {
    fetch('/api/goals/nutrition/week')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('weeklyChart').getContext('2d');
            const labels = data.week_data.map(d => new Date(d.date).toLocaleDateString('en', {weekday: 'short'}));
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Calories',
                        data: data.week_data.map(d => d.calories),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    height: 300
                }
            });
        });
}

// Load insights
function loadInsights() {
    fetch('/api/goals/insights')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('insights-list');
            container.innerHTML = '';
            
            data.insights.forEach(insight => {
                const item = document.createElement('div');
                item.className = `insight-item ${insight.type}`;
                item.textContent = insight.message;
                container.appendChild(item);
            });
        });
}

// Goal type change handler
document.getElementById('goalType').addEventListener('change', function() {
    const weightFields = document.getElementById('weightGoalFields');
    if (this.value === 'weight_loss' || this.value === 'muscle_gain') {
        weightFields.style.display = 'block';
    } else {
        weightFields.style.display = 'none';
    }
});

// Save goal
function saveGoal() {
    const formData = {
        goal_type: document.getElementById('goalType').value,
        target_date: document.getElementById('targetDate').value,
        daily_calories: parseInt(document.getElementById('dailyCalories').value) || null,
        daily_protein: parseInt(document.getElementById('dailyProtein').value) || null,
        daily_carbs: parseInt(document.getElementById('dailyCarbs').value) || null,
        daily_fat: parseInt(document.getElementById('dailyFat').value) || null
    };
    
    if (formData.goal_type === 'weight_loss' || formData.goal_type === 'muscle_gain') {
        formData.current_value = parseFloat(document.getElementById('currentWeight').value);
        formData.target_value = parseFloat(document.getElementById('targetWeight').value);
    }
    
    fetch('/api/goals/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            $('#newGoalModal').modal('hide');
            loadGoals();
        }
    });
}

// Update progress
function updateProgress(goalId) {
    const value = prompt('Enter current value:');
    if (value) {
        fetch(`/api/goals/${goalId}/progress`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            },
            body: JSON.stringify({ value: parseFloat(value) })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadGoals();
            }
        });
    }
}

// Set today's date as minimum for target date
document.getElementById('targetDate').min = new Date().toISOString().split('T')[0];

// Load all data
loadGoals();
loadNutrition();
loadWeeklyChart();
loadInsights();
</script>
{% endblock %}
"""
    
    with open(templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    print(f"Created goal tracking templates in: {templates_dir}")
    return True

def main():
    """Main function"""
    try:
        # Add goal tracking models
        if not add_goal_tracking_models():
            return 1
        
        # Create goal tracking routes
        if not create_goal_tracking_routes():
            return 1
        
        # Create goal tracking UI
        if not create_goal_tracking_ui():
            return 1
        
        print("OK")
        return 0
    except Exception as e:
        print(f"Error adding goal tracking: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())