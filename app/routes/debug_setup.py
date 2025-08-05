"""Debug setup route for fixing database issues"""
from flask import Blueprint, jsonify
from app.models import db, User

debug_bp = Blueprint('debug', __name__, url_prefix='/debug')

@debug_bp.route('/setup-db')
def setup_database():
    """Setup database and admin user"""
    try:
        # Create all tables
        db.create_all()
        
        # Create or update admin user
        admin = User.query.filter_by(email='admin@cibozer.com').first()
        if not admin:
            admin = User(
                email='admin@cibozer.com',
                full_name='Administrator',
                subscription_tier='premium',
                subscription_status='active',
                credits_balance=1000,
                is_active=True,
                email_verified=True
            )
            admin.set_password('Admin123!')
            db.session.add(admin)
            result = 'Admin user created'
        else:
            admin.set_password('Admin123!')
            result = 'Admin password updated'
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': result,
            'admin_email': 'admin@cibozer.com',
            'admin_password': 'Admin123!'
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'message': str(e),
            'traceback': traceback.format_exc()
        }), 500