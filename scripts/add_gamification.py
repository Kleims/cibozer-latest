#!/usr/bin/env python3
"""Add gamification features to increase user engagement"""

import os
import sys
from pathlib import Path

def add_gamification_models():
    """Add gamification models to the database"""
    
    project_root = Path(__file__).parent.parent
    models_file = project_root / 'models.py'
    
    if not models_file.exists():
        print("Error: models.py not found")
        return False
    
    # Read current models
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if gamification models already exist
    if 'class Achievement' in content:
        print("Gamification models already exist")
        return True
    
    # Add gamification models
    gamification_models = '''

# Gamification Models
class Achievement(db.Model):
    """Achievement definitions"""
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(10), nullable=False)  # emoji icon
    points = db.Column(db.Integer, default=10)
    category = db.Column(db.String(50), nullable=False)  # planning, cooking, social, health
    requirement_type = db.Column(db.String(50), nullable=False)  # count, streak, milestone
    requirement_value = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'points': self.points,
            'category': self.category
        }

class UserAchievement(db.Model):
    """User's earned achievements"""
    __tablename__ = 'user_achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))
    achievement = db.relationship('Achievement', backref='users')
    
    __table_args__ = (db.UniqueConstraint('user_id', 'achievement_id'),)

class UserStats(db.Model):
    """Track user statistics for gamification"""
    __tablename__ = 'user_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    meals_planned = db.Column(db.Integer, default=0)
    recipes_saved = db.Column(db.Integer, default=0)
    recipes_shared = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_meal_planned = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('stats', uselist=False))
    
    def add_points(self, points):
        """Add points and check for level up"""
        self.total_points += points
        new_level = self.calculate_level()
        if new_level > self.level:
            self.level = new_level
            return True  # Level up!
        return False
    
    def calculate_level(self):
        """Calculate user level based on points"""
        # Level up every 100 points, with increasing requirements
        if self.total_points < 100:
            return 1
        elif self.total_points < 300:
            return 2
        elif self.total_points < 600:
            return 3
        elif self.total_points < 1000:
            return 4
        else:
            return 5 + (self.total_points - 1000) // 500
    
    def update_streak(self):
        """Update meal planning streak"""
        now = datetime.utcnow()
        if self.last_meal_planned:
            days_diff = (now.date() - self.last_meal_planned.date()).days
            if days_diff == 1:
                self.current_streak += 1
                self.longest_streak = max(self.current_streak, self.longest_streak)
            elif days_diff > 1:
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        self.last_meal_planned = now
        db.session.commit()
'''
    
    # Append models to file
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(content + gamification_models)
    
    print("Added gamification models to models.py")
    return True

def create_gamification_routes():
    """Create gamification API routes"""
    
    project_root = Path(__file__).parent.parent
    routes_file = project_root / 'gamification_routes.py'
    
    gamification_routes = '''"""Gamification routes and achievement system"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Achievement, UserAchievement, UserStats, Notification
from sqlalchemy import and_

gamification_bp = Blueprint('gamification', __name__, url_prefix='/api/gamification')

def get_or_create_user_stats(user_id):
    """Get or create user stats"""
    stats = UserStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserStats(user_id=user_id)
        db.session.add(stats)
        db.session.commit()
    return stats

@gamification_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get current user's gamification stats"""
    stats = get_or_create_user_stats(current_user.id)
    
    # Get earned achievements
    earned_achievements = db.session.query(Achievement).join(
        UserAchievement
    ).filter(
        UserAchievement.user_id == current_user.id
    ).all()
    
    # Calculate progress to next level
    current_level_points = [0, 100, 300, 600, 1000][min(stats.level - 1, 4)]
    next_level_points = [100, 300, 600, 1000, 1500][min(stats.level - 1, 4)]
    if stats.level > 5:
        current_level_points = 1000 + (stats.level - 5) * 500
        next_level_points = current_level_points + 500
    
    progress = ((stats.total_points - current_level_points) / 
                (next_level_points - current_level_points) * 100)
    
    return jsonify({
        'level': stats.level,
        'total_points': stats.total_points,
        'next_level_points': next_level_points,
        'progress_percentage': round(progress, 1),
        'current_streak': stats.current_streak,
        'longest_streak': stats.longest_streak,
        'meals_planned': stats.meals_planned,
        'recipes_saved': stats.recipes_saved,
        'achievements_earned': len(earned_achievements),
        'recent_achievements': [a.to_dict() for a in earned_achievements[-3:]]
    })

@gamification_bp.route('/achievements', methods=['GET'])
@login_required
def get_achievements():
    """Get all achievements and user's progress"""
    all_achievements = Achievement.query.all()
    
    # Get user's earned achievements
    earned_ids = db.session.query(UserAchievement.achievement_id).filter_by(
        user_id=current_user.id
    ).all()
    earned_ids = [id[0] for id in earned_ids]
    
    # Get user stats for progress calculation
    stats = get_or_create_user_stats(current_user.id)
    
    achievements_data = []
    for achievement in all_achievements:
        data = achievement.to_dict()
        data['earned'] = achievement.id in earned_ids
        
        # Calculate progress
        if achievement.requirement_type == 'count':
            if 'meal' in achievement.name.lower():
                current = stats.meals_planned
            elif 'recipe' in achievement.name.lower() and 'save' in achievement.name.lower():
                current = stats.recipes_saved
            elif 'share' in achievement.name.lower():
                current = stats.recipes_shared
            else:
                current = 0
            
            data['progress'] = min(100, (current / achievement.requirement_value) * 100)
            data['current'] = current
            data['required'] = achievement.requirement_value
        
        elif achievement.requirement_type == 'streak':
            data['progress'] = min(100, (stats.current_streak / achievement.requirement_value) * 100)
            data['current'] = stats.current_streak
            data['required'] = achievement.requirement_value
        
        achievements_data.append(data)
    
    # Sort by category, then by earned status
    achievements_data.sort(key=lambda x: (x['category'], not x['earned']))
    
    return jsonify({
        'achievements': achievements_data,
        'categories': ['planning', 'cooking', 'social', 'health']
    })

@gamification_bp.route('/check-achievements', methods=['POST'])
@login_required
def check_achievements():
    """Check and award any new achievements"""
    stats = get_or_create_user_stats(current_user.id)
    awarded = []
    
    # Get all achievements not yet earned
    earned_ids = db.session.query(UserAchievement.achievement_id).filter_by(
        user_id=current_user.id
    ).all()
    earned_ids = [id[0] for id in earned_ids]
    
    unearned = Achievement.query.filter(~Achievement.id.in_(earned_ids)).all()
    
    for achievement in unearned:
        earned = False
        
        if achievement.requirement_type == 'count':
            if 'meal' in achievement.name.lower() and stats.meals_planned >= achievement.requirement_value:
                earned = True
            elif 'recipe' in achievement.name.lower() and 'save' in achievement.name.lower() and stats.recipes_saved >= achievement.requirement_value:
                earned = True
            elif 'share' in achievement.name.lower() and stats.recipes_shared >= achievement.requirement_value:
                earned = True
        
        elif achievement.requirement_type == 'streak':
            if stats.current_streak >= achievement.requirement_value:
                earned = True
        
        if earned:
            # Award achievement
            user_achievement = UserAchievement(
                user_id=current_user.id,
                achievement_id=achievement.id
            )
            db.session.add(user_achievement)
            
            # Add points
            level_up = stats.add_points(achievement.points)
            
            # Create notification
            notification = Notification(
                user_id=current_user.id,
                type='achievement',
                title='Achievement Unlocked! ' + achievement.icon,
                message=f'You earned "{achievement.name}" - {achievement.description}'
            )
            db.session.add(notification)
            
            awarded.append({
                'achievement': achievement.to_dict(),
                'level_up': level_up,
                'new_level': stats.level if level_up else None
            })
    
    db.session.commit()
    
    return jsonify({
        'awarded': awarded,
        'total_points': stats.total_points,
        'level': stats.level
    })

@gamification_bp.route('/record-action', methods=['POST'])
@login_required
def record_action():
    """Record a user action for statistics"""
    data = request.get_json()
    action = data.get('action')
    
    stats = get_or_create_user_stats(current_user.id)
    
    if action == 'meal_planned':
        stats.meals_planned += 1
        stats.update_streak()
    elif action == 'recipe_saved':
        stats.recipes_saved += 1
    elif action == 'recipe_shared':
        stats.recipes_shared += 1
    
    db.session.commit()
    
    # Check for new achievements
    return check_achievements()

def initialize_achievements():
    """Initialize default achievements in database"""
    default_achievements = [
        # Planning achievements
        {'name': 'First Steps', 'description': 'Plan your first meal', 'icon': '🌱', 
         'points': 10, 'category': 'planning', 'requirement_type': 'count', 'requirement_value': 1},
        {'name': 'Week Warrior', 'description': 'Plan 7 meals', 'icon': '📅', 
         'points': 25, 'category': 'planning', 'requirement_type': 'count', 'requirement_value': 7},
        {'name': 'Month Master', 'description': 'Plan 30 meals', 'icon': '📆', 
         'points': 50, 'category': 'planning', 'requirement_type': 'count', 'requirement_value': 30},
        
        # Streak achievements
        {'name': 'Consistent Chef', 'description': '3-day planning streak', 'icon': '🔥', 
         'points': 15, 'category': 'planning', 'requirement_type': 'streak', 'requirement_value': 3},
        {'name': 'Habit Former', 'description': '7-day planning streak', 'icon': '⚡', 
         'points': 35, 'category': 'planning', 'requirement_type': 'streak', 'requirement_value': 7},
        {'name': 'Planning Pro', 'description': '30-day planning streak', 'icon': '🏆', 
         'points': 100, 'category': 'planning', 'requirement_type': 'streak', 'requirement_value': 30},
        
        # Collection achievements
        {'name': 'Recipe Collector', 'description': 'Save 10 recipes', 'icon': '📖', 
         'points': 20, 'category': 'cooking', 'requirement_type': 'count', 'requirement_value': 10},
        {'name': 'Recipe Library', 'description': 'Save 50 recipes', 'icon': '📚', 
         'points': 50, 'category': 'cooking', 'requirement_type': 'count', 'requirement_value': 50},
        
        # Social achievements
        {'name': 'Sharing is Caring', 'description': 'Share your first recipe', 'icon': '💝', 
         'points': 15, 'category': 'social', 'requirement_type': 'count', 'requirement_value': 1},
        {'name': 'Community Chef', 'description': 'Share 10 recipes', 'icon': '👨‍🍳', 
         'points': 40, 'category': 'social', 'requirement_type': 'count', 'requirement_value': 10},
    ]
    
    for achievement_data in default_achievements:
        if not Achievement.query.filter_by(name=achievement_data['name']).first():
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    
    db.session.commit()
'''
    
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(gamification_routes)
    
    print(f"Created gamification routes: {routes_file}")
    return True

def create_gamification_ui():
    """Create gamification UI components"""
    
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates' / 'gamification'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create achievements page template
    achievements_template = """{% extends "base.html" %}
{% block title %}Achievements - Cibozer{% endblock %}

{% block content %}
<div class="achievements-container">
    <div class="stats-header">
        <div class="level-info">
            <div class="level-badge">
                <span class="level-number">{{ level }}</span>
                <span class="level-label">Level</span>
            </div>
            <div class="level-progress">
                <div class="progress">
                    <div class="progress-bar" style="width: {{ progress }}%"></div>
                </div>
                <span class="points-text">{{ points }} / {{ next_level }} points</span>
            </div>
        </div>
        
        <div class="stats-summary">
            <div class="stat-item">
                <span class="stat-value">{{ current_streak }}</span>
                <span class="stat-label">Current Streak</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{{ meals_planned }}</span>
                <span class="stat-label">Meals Planned</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">{{ achievements_earned }}</span>
                <span class="stat-label">Achievements</span>
            </div>
        </div>
    </div>
    
    <div class="achievements-categories">
        <ul class="nav nav-tabs" role="tablist">
            <li class="nav-item">
                <a class="nav-link active" data-toggle="tab" href="#all">All</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" data-toggle="tab" href="#planning">Planning</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" data-toggle="tab" href="#cooking">Cooking</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" data-toggle="tab" href="#social">Social</a>
            </li>
        </ul>
        
        <div class="tab-content">
            <div id="achievements-grid" class="achievements-grid">
                <!-- Achievements will be loaded here -->
            </div>
        </div>
    </div>
</div>

<style>
.achievements-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.stats-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
}

.level-info {
    display: flex;
    align-items: center;
    gap: 2rem;
    margin-bottom: 1.5rem;
}

.level-badge {
    text-align: center;
    background: rgba(255, 255, 255, 0.2);
    padding: 1.5rem;
    border-radius: 50%;
    min-width: 100px;
}

.level-number {
    display: block;
    font-size: 2.5rem;
    font-weight: bold;
}

.level-progress {
    flex: 1;
}

.progress {
    height: 20px;
    background: rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-bar {
    height: 100%;
    background: white;
    transition: width 0.3s ease;
}

.stats-summary {
    display: flex;
    gap: 3rem;
    justify-content: center;
}

.stat-item {
    text-align: center;
}

.stat-value {
    display: block;
    font-size: 1.5rem;
    font-weight: bold;
}

.achievements-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1.5rem;
    padding: 2rem 0;
}

.achievement-card {
    background: white;
    border: 2px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    cursor: pointer;
}

.achievement-card.earned {
    border-color: #10b981;
    background: #f0fdf4;
}

.achievement-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.achievement-icon {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

.achievement-name {
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.achievement-description {
    font-size: 0.875rem;
    color: #6b7280;
    margin-bottom: 1rem;
}

.achievement-progress {
    margin-top: 1rem;
}

.achievement-progress .progress {
    height: 8px;
    margin-bottom: 0.25rem;
}

.achievement-progress-text {
    font-size: 0.75rem;
    color: #6b7280;
}

.achievement-points {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: #fbbf24;
    color: #78350f;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
}
</style>

<script>
// Load user stats
fetch('/api/gamification/stats')
    .then(response => response.json())
    .then(data => {
        document.querySelector('.level-number').textContent = data.level;
        document.querySelector('.progress-bar').style.width = data.progress_percentage + '%';
        document.querySelector('.points-text').textContent = `${data.total_points} / ${data.next_level_points} points`;
        document.querySelector('.stat-value:nth-child(1)').textContent = data.current_streak;
        document.querySelector('.stat-value:nth-child(2)').textContent = data.meals_planned;
        document.querySelector('.stat-value:nth-child(3)').textContent = data.achievements_earned;
    });

// Load achievements
function loadAchievements() {
    fetch('/api/gamification/achievements')
        .then(response => response.json())
        .then(data => {
            const grid = document.getElementById('achievements-grid');
            grid.innerHTML = '';
            
            data.achievements.forEach(achievement => {
                const card = createAchievementCard(achievement);
                grid.appendChild(card);
            });
        });
}

function createAchievementCard(achievement) {
    const div = document.createElement('div');
    div.className = `achievement-card ${achievement.earned ? 'earned' : ''}`;
    
    let progressHtml = '';
    if (!achievement.earned && achievement.progress !== undefined) {
        progressHtml = `
            <div class="achievement-progress">
                <div class="progress">
                    <div class="progress-bar bg-primary" style="width: ${achievement.progress}%"></div>
                </div>
                <div class="achievement-progress-text">${achievement.current} / ${achievement.required}</div>
            </div>
        `;
    }
    
    div.innerHTML = `
        <div class="achievement-points">+${achievement.points}</div>
        <div class="achievement-icon">${achievement.icon}</div>
        <div class="achievement-name">${achievement.name}</div>
        <div class="achievement-description">${achievement.description}</div>
        ${progressHtml}
    `;
    
    return div;
}

// Category filtering
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
        const category = e.target.getAttribute('href').substring(1);
        filterAchievements(category);
    });
});

function filterAchievements(category) {
    const cards = document.querySelectorAll('.achievement-card');
    cards.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

loadAchievements();
</script>
{% endblock %}
"""
    
    with open(templates_dir / 'achievements.html', 'w', encoding='utf-8') as f:
        f.write(achievements_template)
    
    print(f"Created gamification templates in: {templates_dir}")
    return True

def main():
    """Main function"""
    try:
        # Add gamification models
        if not add_gamification_models():
            return 1
        
        # Create gamification routes
        if not create_gamification_routes():
            return 1
        
        # Create gamification UI
        if not create_gamification_ui():
            return 1
        
        print("OK")
        return 0
    except Exception as e:
        print(f"Error adding gamification: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())