#!/usr/bin/env python3
"""Setup notification system for meal reminders and updates"""

import os
import sys
from pathlib import Path

def create_notification_models():
    """Create notification database models"""
    
    project_root = Path(__file__).parent.parent
    models_file = project_root / 'models.py'
    
    # Check if models.py exists
    if not models_file.exists():
        print("Error: models.py not found")
        return False
    
    # Read current models
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if notification models already exist
    if 'class Notification' in content:
        print("Notification models already exist")
        return True
    
    # Add notification models
    notification_models = '''

# Notification Models
class Notification(db.Model):
    """User notifications for meal planning reminders"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # meal_reminder, weekly_plan, achievement
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_for = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def mark_as_read(self):
        self.read = True
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat(),
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None
        }

class NotificationPreferences(db.Model):
    """User preferences for notifications"""
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    email_enabled = db.Column(db.Boolean, default=True)
    push_enabled = db.Column(db.Boolean, default=True)
    meal_reminders = db.Column(db.Boolean, default=True)
    weekly_planning = db.Column(db.Boolean, default=True)
    achievements = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.Time, default=datetime.strptime('18:00', '%H:%M').time())
    
    user = db.relationship('User', backref=db.backref('notification_preferences', uselist=False))
'''
    
    # Add import for datetime if not present
    if 'from datetime import datetime' not in content:
        import_pos = content.find('from flask_sqlalchemy import SQLAlchemy')
        if import_pos != -1:
            end_of_line = content.find('\n', import_pos)
            content = content[:end_of_line+1] + 'from datetime import datetime\n' + content[end_of_line+1:]
    
    # Append models to file
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(content + notification_models)
    
    print("Added notification models to models.py")
    return True

def create_notification_routes():
    """Create notification API routes"""
    
    project_root = Path(__file__).parent.parent
    routes_file = project_root / 'notification_routes.py'
    
    notification_routes = '''"""Notification routes and handlers"""

from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from models import db, Notification, NotificationPreferences
from datetime import datetime, timedelta
from sqlalchemy import and_

notifications_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notifications_bp.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Notification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(read=False)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'notifications': [n.to_dict() for n in notifications.items],
        'total': notifications.total,
        'page': page,
        'pages': notifications.pages,
        'unread_count': Notification.query.filter_by(
            user_id=current_user.id, read=False
        ).count()
    })

@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_read(notification_id):
    """Mark notification as read"""
    notification = Notification.query.filter_by(
        id=notification_id, 
        user_id=current_user.id
    ).first_or_404()
    
    notification.mark_as_read()
    return jsonify({'success': True})

@notifications_bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read"""
    Notification.query.filter_by(
        user_id=current_user.id, 
        read=False
    ).update({'read': True})
    db.session.commit()
    
    return jsonify({'success': True})

@notifications_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    """Get or update notification preferences"""
    prefs = NotificationPreferences.query.filter_by(user_id=current_user.id).first()
    
    if not prefs:
        prefs = NotificationPreferences(user_id=current_user.id)
        db.session.add(prefs)
        db.session.commit()
    
    if request.method == 'POST':
        data = request.get_json()
        
        prefs.email_enabled = data.get('email_enabled', prefs.email_enabled)
        prefs.push_enabled = data.get('push_enabled', prefs.push_enabled)
        prefs.meal_reminders = data.get('meal_reminders', prefs.meal_reminders)
        prefs.weekly_planning = data.get('weekly_planning', prefs.weekly_planning)
        prefs.achievements = data.get('achievements', prefs.achievements)
        
        if 'reminder_time' in data:
            prefs.reminder_time = datetime.strptime(data['reminder_time'], '%H:%M').time()
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Preferences updated'})
    
    return jsonify({
        'email_enabled': prefs.email_enabled,
        'push_enabled': prefs.push_enabled,
        'meal_reminders': prefs.meal_reminders,
        'weekly_planning': prefs.weekly_planning,
        'achievements': prefs.achievements,
        'reminder_time': prefs.reminder_time.strftime('%H:%M')
    })

def send_meal_reminder(user_id):
    """Send meal planning reminder to user"""
    notification = Notification(
        user_id=user_id,
        type='meal_reminder',
        title='Time to plan tomorrow\'s meals!',
        message='Don\'t forget to plan your meals for tomorrow. Tap here to start.',
        scheduled_for=datetime.utcnow() + timedelta(days=1)
    )
    db.session.add(notification)
    db.session.commit()
    
    # TODO: Implement actual email/push sending
    return notification

def send_achievement_notification(user_id, achievement_type, achievement_data):
    """Send achievement notification"""
    messages = {
        'streak_7': 'You\'ve planned meals for 7 days in a row! 🎉',
        'meals_50': 'You\'ve created 50 meal plans! Amazing progress! 🌟',
        'saved_recipes_25': 'You\'ve saved 25 recipes to your collection! 📚'
    }
    
    notification = Notification(
        user_id=user_id,
        type='achievement',
        title='New Achievement Unlocked!',
        message=messages.get(achievement_type, 'Congratulations on your achievement!')
    )
    db.session.add(notification)
    db.session.commit()
    
    return notification
'''
    
    with open(routes_file, 'w', encoding='utf-8') as f:
        f.write(notification_routes)
    
    print(f"Created notification routes: {routes_file}")
    return True

def create_notification_templates():
    """Create notification UI templates"""
    
    project_root = Path(__file__).parent.parent
    templates_dir = project_root / 'templates' / 'notifications'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    # Create notification center template
    notification_center = """{% extends "base.html" %}
{% block title %}Notifications - Cibozer{% endblock %}

{% block content %}
<div class="notification-center">
    <div class="header">
        <h1>Notifications</h1>
        <button id="mark-all-read" class="btn btn-sm btn-secondary">
            Mark all as read
        </button>
    </div>
    
    <div id="notification-list" class="notification-list">
        <!-- Notifications will be loaded here -->
    </div>
    
    <div id="load-more" class="text-center mt-3">
        <button class="btn btn-primary">Load More</button>
    </div>
</div>

<script>
let currentPage = 1;

function loadNotifications(page = 1) {
    fetch(`/api/notifications/?page=${page}`)
        .then(response => response.json())
        .then(data => {
            const list = document.getElementById('notification-list');
            if (page === 1) list.innerHTML = '';
            
            data.notifications.forEach(notification => {
                const item = createNotificationItem(notification);
                list.appendChild(item);
            });
            
            // Update unread count in navbar
            updateUnreadCount(data.unread_count);
            
            // Show/hide load more button
            if (currentPage >= data.pages) {
                document.getElementById('load-more').style.display = 'none';
            }
        });
}

function createNotificationItem(notification) {
    const div = document.createElement('div');
    div.className = `notification-item ${notification.read ? 'read' : 'unread'}`;
    div.innerHTML = `
        <div class="notification-icon">
            ${getNotificationIcon(notification.type)}
        </div>
        <div class="notification-content">
            <h4>${notification.title}</h4>
            <p>${notification.message}</p>
            <span class="time">${formatTime(notification.created_at)}</span>
        </div>
    `;
    
    if (!notification.read) {
        div.addEventListener('click', () => markAsRead(notification.id));
    }
    
    return div;
}

function getNotificationIcon(type) {
    const icons = {
        'meal_reminder': '🍽️',
        'weekly_plan': '📅',
        'achievement': '🏆'
    };
    return icons[type] || '📢';
}

function formatTime(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
}

function markAsRead(notificationId) {
    fetch(`/api/notifications/mark-read/${notificationId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
        }
    }).then(() => loadNotifications(1));
}

document.getElementById('mark-all-read').addEventListener('click', () => {
    fetch('/api/notifications/mark-all-read', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
        }
    }).then(() => loadNotifications(1));
});

document.getElementById('load-more').addEventListener('click', () => {
    currentPage++;
    loadNotifications(currentPage);
});

// Load initial notifications
loadNotifications();
</script>
{% endblock %}
"""
    
    with open(templates_dir / 'center.html', 'w', encoding='utf-8') as f:
        f.write(notification_center)
    
    # Create notification preferences template
    preferences_template = """{% extends "base.html" %}
{% block title %}Notification Preferences - Cibozer{% endblock %}

{% block content %}
<div class="notification-preferences">
    <h1>Notification Preferences</h1>
    
    <form id="preferences-form">
        <div class="preference-section">
            <h3>Notification Channels</h3>
            
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="email_enabled" name="email_enabled">
                <label class="form-check-label" for="email_enabled">
                    Email Notifications
                </label>
            </div>
            
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="push_enabled" name="push_enabled">
                <label class="form-check-label" for="push_enabled">
                    Push Notifications
                </label>
            </div>
        </div>
        
        <div class="preference-section">
            <h3>Notification Types</h3>
            
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="meal_reminders" name="meal_reminders">
                <label class="form-check-label" for="meal_reminders">
                    Daily Meal Planning Reminders
                </label>
            </div>
            
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="weekly_planning" name="weekly_planning">
                <label class="form-check-label" for="weekly_planning">
                    Weekly Planning Reminders
                </label>
            </div>
            
            <div class="form-check">
                <input type="checkbox" class="form-check-input" id="achievements" name="achievements">
                <label class="form-check-label" for="achievements">
                    Achievement Notifications
                </label>
            </div>
        </div>
        
        <div class="preference-section">
            <h3>Reminder Time</h3>
            <div class="form-group">
                <label for="reminder_time">Daily reminder time:</label>
                <input type="time" class="form-control" id="reminder_time" name="reminder_time" value="18:00">
                <small class="form-text text-muted">
                    We'll send you a reminder to plan tomorrow's meals at this time.
                </small>
            </div>
        </div>
        
        <button type="submit" class="btn btn-primary">Save Preferences</button>
    </form>
</div>

<script>
// Load current preferences
fetch('/api/notifications/preferences')
    .then(response => response.json())
    .then(data => {
        Object.keys(data).forEach(key => {
            const input = document.getElementById(key);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = data[key];
                } else {
                    input.value = data[key];
                }
            }
        });
    });

// Save preferences
document.getElementById('preferences-form').addEventListener('submit', (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {};
    
    // Handle checkboxes
    ['email_enabled', 'push_enabled', 'meal_reminders', 'weekly_planning', 'achievements'].forEach(key => {
        data[key] = formData.has(key);
    });
    
    // Handle time
    data.reminder_time = formData.get('reminder_time');
    
    fetch('/api/notifications/preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Preferences saved successfully!');
        }
    });
});
</script>
{% endblock %}
"""
    
    with open(templates_dir / 'preferences.html', 'w', encoding='utf-8') as f:
        f.write(preferences_template)
    
    print(f"Created notification templates in: {templates_dir}")
    return True

def main():
    """Main function"""
    try:
        # Create notification models
        if not create_notification_models():
            return 1
        
        # Create notification routes
        if not create_notification_routes():
            return 1
        
        # Create notification templates
        if not create_notification_templates():
            return 1
        
        print("OK")
        return 0
    except Exception as e:
        print(f"Error setting up notifications: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())