"""Database utilities to reduce repetitive session management code"""

from app.extensions import db


class DatabaseHelper:
    """Helper class for common database operations in tests"""
    
    @staticmethod
    def commit_user(user):
        """Add user to session and commit"""
        db.session.add(user)
        db.session.commit()
        return user
    
    @staticmethod
    def commit_multiple(*objects):
        """Add multiple objects to session and commit"""
        for obj in objects:
            db.session.add(obj)
        db.session.commit()
        return objects
    
    @staticmethod
    def refresh_object(obj):
        """Refresh object from database"""
        db.session.refresh(obj)
        return obj
    
    @staticmethod
    def rollback():
        """Rollback current transaction"""
        db.session.rollback()
    
    @staticmethod
    def clean_session():
        """Remove all objects from session"""
        db.session.remove()


def with_db_transaction(func):
    """Decorator to wrap test functions with database transaction handling"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            raise e
    return wrapper