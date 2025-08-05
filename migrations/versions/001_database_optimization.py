"""Database optimization - Add missing indexes and constraints

Revision ID: db_optimization_001
Revises: ad9359b9ce48
Create Date: 2025-07-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'db_optimization_001'
down_revision = 'ad9359b9ce48'
branch_labels = None
depends_on = None


def upgrade():
    """Add missing indexes and constraints for optimal performance."""
    
    # Users table optimizations
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Add indexes for frequently queried fields
        batch_op.create_index('idx_users_subscription_tier', ['subscription_tier'])
        batch_op.create_index('idx_users_subscription_status', ['subscription_status'])
        batch_op.create_index('idx_users_created_at', ['created_at'])
        batch_op.create_index('idx_users_last_login', ['last_login'])
        batch_op.create_index('idx_users_email_verified', ['email_verified'])
        batch_op.create_index('idx_users_is_active', ['is_active'])
        batch_op.create_index('idx_users_stripe_customer_id', ['stripe_customer_id'])
        
        # Composite indexes for common query patterns
        batch_op.create_index('idx_users_tier_status', ['subscription_tier', 'subscription_status'])
        batch_op.create_index('idx_users_active_verified', ['is_active', 'email_verified'])
        
        # Add check constraints for data integrity
        batch_op.create_check_constraint(
            'ck_users_subscription_tier',
            "subscription_tier IN ('free', 'pro', 'premium')"
        )
        batch_op.create_check_constraint(
            'ck_users_subscription_status',
            "subscription_status IN ('active', 'cancelled', 'expired', 'trialing')"
        )
        batch_op.create_check_constraint(
            'ck_users_credits_balance',
            'credits_balance >= 0'
        )
        batch_op.create_check_constraint(
            'ck_users_failed_login_attempts',
            'failed_login_attempts >= 0'
        )
    
    # Saved meal plans optimizations
    with op.batch_alter_table('saved_meal_plans', schema=None) as batch_op:
        # Add foreign key index (critical for joins)
        batch_op.create_index('idx_saved_meal_plans_user_id', ['user_id'])
        
        # Add indexes for frequently queried fields
        batch_op.create_index('idx_saved_meal_plans_created_at', ['created_at'])
        batch_op.create_index('idx_saved_meal_plans_diet_type', ['diet_type'])
        batch_op.create_index('idx_saved_meal_plans_is_public', ['is_public'])
        batch_op.create_index('idx_saved_meal_plans_share_token', ['share_token'])
        
        # Composite indexes for common queries
        batch_op.create_index('idx_saved_meal_plans_user_created', ['user_id', 'created_at'])
        batch_op.create_index('idx_saved_meal_plans_public_diet', ['is_public', 'diet_type'])
        
        # Add check constraints
        batch_op.create_check_constraint(
            'ck_saved_meal_plans_days',
            'days >= 1 AND days <= 30'
        )
        batch_op.create_check_constraint(
            'ck_saved_meal_plans_total_calories',
            'total_calories IS NULL OR (total_calories >= 800 AND total_calories <= 5000)'
        )
    
    # Usage logs optimizations
    with op.batch_alter_table('usage_logs', schema=None) as batch_op:
        # Add foreign key index
        batch_op.create_index('idx_usage_logs_user_id', ['user_id'])
        
        # Add indexes for analytics queries
        batch_op.create_index('idx_usage_logs_action', ['action'])
        batch_op.create_index('idx_usage_logs_resource_type', ['resource_type'])
        batch_op.create_index('idx_usage_logs_status_code', ['status_code'])
        batch_op.create_index('idx_usage_logs_endpoint', ['endpoint'])
        
        # Composite indexes for common analytics queries
        batch_op.create_index('idx_usage_logs_user_action_created', ['user_id', 'action', 'created_at'])
        batch_op.create_index('idx_usage_logs_action_created', ['action', 'created_at'])
        batch_op.create_index('idx_usage_logs_user_created', ['user_id', 'created_at'])
        
        # Add check constraints
        batch_op.create_check_constraint(
            'ck_usage_logs_credits_used',
            'credits_used >= 0'
        )
        batch_op.create_check_constraint(
            'ck_usage_logs_response_time',
            'response_time_ms IS NULL OR response_time_ms >= 0'
        )
    
    # API keys optimizations
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        # Add foreign key index
        batch_op.create_index('idx_api_keys_user_id', ['user_id'])
        
        # Add indexes for API key lookup
        batch_op.create_index('idx_api_keys_is_active', ['is_active'])
        batch_op.create_index('idx_api_keys_expires_at', ['expires_at'])
        
        # Composite index for key validation
        batch_op.create_index('idx_api_keys_key_active', ['key', 'is_active'])
        
        # Add check constraints
        batch_op.create_check_constraint(
            'ck_api_keys_rate_limit',
            'rate_limit > 0'
        )
        batch_op.create_check_constraint(
            'ck_api_keys_total_requests',
            'total_requests >= 0'
        )
    
    # Shared meal plans optimizations
    with op.batch_alter_table('shared_meal_plans', schema=None) as batch_op:
        # Add foreign key index
        batch_op.create_index('idx_shared_meal_plans_creator_id', ['creator_id'])
        
        # Add indexes for public sharing
        batch_op.create_index('idx_shared_meal_plans_is_active', ['is_active'])
        batch_op.create_index('idx_shared_meal_plans_diet_type', ['diet_type'])
        batch_op.create_index('idx_shared_meal_plans_created_at', ['created_at'])
        batch_op.create_index('idx_shared_meal_plans_expires_at', ['expires_at'])
        
        # Composite indexes
        batch_op.create_index('idx_shared_meal_plans_active_diet', ['is_active', 'diet_type'])
        batch_op.create_index('idx_shared_meal_plans_active_created', ['is_active', 'created_at'])
        
        # Add check constraints
        batch_op.create_check_constraint(
            'ck_shared_meal_plans_view_count',
            'view_count >= 0'
        )
        batch_op.create_check_constraint(
            'ck_shared_meal_plans_download_count',
            'download_count >= 0'
        )
    
    # Meal plan shares optimizations
    with op.batch_alter_table('meal_plan_shares', schema=None) as batch_op:
        # Add foreign key indexes
        batch_op.create_index('idx_meal_plan_shares_meal_plan_id', ['meal_plan_id'])
        batch_op.create_index('idx_meal_plan_shares_shared_by_id', ['shared_by_id'])
        
        # Add indexes for analytics
        batch_op.create_index('idx_meal_plan_shares_share_method', ['share_method'])
        batch_op.create_index('idx_meal_plan_shares_created_at', ['created_at'])
        batch_op.create_index('idx_meal_plan_shares_recipient_email', ['recipient_email'])
        
        # Add check constraints
        batch_op.create_check_constraint(
            'ck_meal_plan_shares_access_count',
            'access_count >= 0'
        )

    # Check if payments table exists and add indexes
    try:
        with op.batch_alter_table('payments', schema=None) as batch_op:
            # Add foreign key index
            batch_op.create_index('idx_payments_user_id', ['user_id'])
            
            # Add indexes for payment processing
            batch_op.create_index('idx_payments_stripe_payment_id', ['stripe_payment_id'])
            batch_op.create_index('idx_payments_status', ['status'])
            batch_op.create_index('idx_payments_created_at', ['created_at'])
            
            # Composite indexes
            batch_op.create_index('idx_payments_user_status', ['user_id', 'status'])
            batch_op.create_index('idx_payments_status_created', ['status', 'created_at'])
    except:
        # Payments table might not exist yet
        pass

    # Check if error_logs table exists and add indexes
    try:
        with op.batch_alter_table('error_logs', schema=None) as batch_op:
            # Add indexes for error tracking
            batch_op.create_index('idx_error_logs_level', ['level'])
            batch_op.create_index('idx_error_logs_created_at', ['created_at'])
            batch_op.create_index('idx_error_logs_user_id', ['user_id'])
            
            # Composite indexes for error analysis
            batch_op.create_index('idx_error_logs_level_created', ['level', 'created_at'])
    except:
        # Error logs table might not exist yet
        pass


def downgrade():
    """Remove optimization indexes and constraints."""
    
    # Users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Drop indexes
        batch_op.drop_index('idx_users_subscription_tier')
        batch_op.drop_index('idx_users_subscription_status')
        batch_op.drop_index('idx_users_created_at')
        batch_op.drop_index('idx_users_last_login')
        batch_op.drop_index('idx_users_email_verified')
        batch_op.drop_index('idx_users_is_active')
        batch_op.drop_index('idx_users_stripe_customer_id')
        batch_op.drop_index('idx_users_tier_status')
        batch_op.drop_index('idx_users_active_verified')
        
        # Drop constraints
        batch_op.drop_constraint('ck_users_subscription_tier')
        batch_op.drop_constraint('ck_users_subscription_status')
        batch_op.drop_constraint('ck_users_credits_balance')
        batch_op.drop_constraint('ck_users_failed_login_attempts')
    
    # Saved meal plans
    with op.batch_alter_table('saved_meal_plans', schema=None) as batch_op:
        batch_op.drop_index('idx_saved_meal_plans_user_id')
        batch_op.drop_index('idx_saved_meal_plans_created_at')
        batch_op.drop_index('idx_saved_meal_plans_diet_type')
        batch_op.drop_index('idx_saved_meal_plans_is_public')
        batch_op.drop_index('idx_saved_meal_plans_share_token')
        batch_op.drop_index('idx_saved_meal_plans_user_created')
        batch_op.drop_index('idx_saved_meal_plans_public_diet')
        batch_op.drop_constraint('ck_saved_meal_plans_days')
        batch_op.drop_constraint('ck_saved_meal_plans_total_calories')
    
    # Usage logs
    with op.batch_alter_table('usage_logs', schema=None) as batch_op:
        batch_op.drop_index('idx_usage_logs_user_id')
        batch_op.drop_index('idx_usage_logs_action')
        batch_op.drop_index('idx_usage_logs_resource_type')
        batch_op.drop_index('idx_usage_logs_status_code')
        batch_op.drop_index('idx_usage_logs_endpoint')
        batch_op.drop_index('idx_usage_logs_user_action_created')
        batch_op.drop_index('idx_usage_logs_action_created')
        batch_op.drop_index('idx_usage_logs_user_created')
        batch_op.drop_constraint('ck_usage_logs_credits_used')
        batch_op.drop_constraint('ck_usage_logs_response_time')
    
    # API keys
    with op.batch_alter_table('api_keys', schema=None) as batch_op:
        batch_op.drop_index('idx_api_keys_user_id')
        batch_op.drop_index('idx_api_keys_is_active')
        batch_op.drop_index('idx_api_keys_expires_at')
        batch_op.drop_index('idx_api_keys_key_active')
        batch_op.drop_constraint('ck_api_keys_rate_limit')
        batch_op.drop_constraint('ck_api_keys_total_requests')
    
    # Shared meal plans
    with op.batch_alter_table('shared_meal_plans', schema=None) as batch_op:
        batch_op.drop_index('idx_shared_meal_plans_creator_id')
        batch_op.drop_index('idx_shared_meal_plans_is_active')
        batch_op.drop_index('idx_shared_meal_plans_diet_type')
        batch_op.drop_index('idx_shared_meal_plans_created_at')
        batch_op.drop_index('idx_shared_meal_plans_expires_at')
        batch_op.drop_index('idx_shared_meal_plans_active_diet')
        batch_op.drop_index('idx_shared_meal_plans_active_created')
        batch_op.drop_constraint('ck_shared_meal_plans_view_count')
        batch_op.drop_constraint('ck_shared_meal_plans_download_count')
    
    # Meal plan shares
    with op.batch_alter_table('meal_plan_shares', schema=None) as batch_op:
        batch_op.drop_index('idx_meal_plan_shares_meal_plan_id')
        batch_op.drop_index('idx_meal_plan_shares_shared_by_id')
        batch_op.drop_index('idx_meal_plan_shares_share_method')
        batch_op.drop_index('idx_meal_plan_shares_created_at')
        batch_op.drop_index('idx_meal_plan_shares_recipient_email')
        batch_op.drop_constraint('ck_meal_plan_shares_access_count')
    
    # Payments (if exists)
    try:
        with op.batch_alter_table('payments', schema=None) as batch_op:
            batch_op.drop_index('idx_payments_user_id')
            batch_op.drop_index('idx_payments_stripe_payment_id')
            batch_op.drop_index('idx_payments_status')
            batch_op.drop_index('idx_payments_created_at')
            batch_op.drop_index('idx_payments_user_status')
            batch_op.drop_index('idx_payments_status_created')
    except:
        pass
    
    # Error logs (if exists)
    try:
        with op.batch_alter_table('error_logs', schema=None) as batch_op:
            batch_op.drop_index('idx_error_logs_level')
            batch_op.drop_index('idx_error_logs_created_at')
            batch_op.drop_index('idx_error_logs_user_id')
            batch_op.drop_index('idx_error_logs_level_created')
    except:
        pass