"""Add performance indexes for user-related queries

This migration adds critical indexes to improve query performance,
especially for N+1 query problems and dashboard statistics.
"""

from alembic import op
import sqlalchemy as sa

def upgrade():
    """Add performance indexes"""
    # Add indexes for foreign key relationships to prevent N+1 queries
    op.create_index('idx_usage_logs_user_id', 'usage_logs', ['user_id'])
    op.create_index('idx_usage_logs_user_timestamp', 'usage_logs', ['user_id', 'timestamp'])
    
    op.create_index('idx_payments_user_id', 'payments', ['user_id'])
    op.create_index('idx_payments_user_created', 'payments', ['user_id', 'created_at'])
    op.create_index('idx_payments_subscription_id', 'payments', ['stripe_subscription_id'])
    
    op.create_index('idx_saved_meal_plans_user_id', 'saved_meal_plans', ['user_id'])
    op.create_index('idx_saved_meal_plans_user_created', 'saved_meal_plans', ['user_id', 'created_at'])
    
    # Add index for user queries by subscription tier
    op.create_index('idx_users_subscription_tier', 'users', ['subscription_tier'])
    op.create_index('idx_users_subscription_status', 'users', ['subscription_status'])
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    
    # Composite index for common admin dashboard queries
    op.create_index('idx_users_active_tier', 'users', ['is_active', 'subscription_tier'])

def downgrade():
    """Remove performance indexes"""
    op.drop_index('idx_usage_logs_user_id', 'usage_logs')
    op.drop_index('idx_usage_logs_user_timestamp', 'usage_logs')
    
    op.drop_index('idx_payments_user_id', 'payments')
    op.drop_index('idx_payments_user_created', 'payments')
    op.drop_index('idx_payments_subscription_id', 'payments')
    
    op.drop_index('idx_saved_meal_plans_user_id', 'saved_meal_plans')
    op.drop_index('idx_saved_meal_plans_user_created', 'saved_meal_plans')
    
    op.drop_index('idx_users_subscription_tier', 'users')
    op.drop_index('idx_users_subscription_status', 'users')
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_active_tier', 'users')