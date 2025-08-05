"""Database administration routes for monitoring and management."""
from flask import Blueprint, render_template, jsonify, request, current_app
from flask_login import login_required
from datetime import datetime, timezone, timedelta
import json

from app.utils.database_performance import (
    get_database_stats, analyze_query_patterns, optimize_connection_pool,
    run_database_maintenance, clear_query_metrics, get_table_sizes
)
from app.utils.database_validation import run_database_validation, fix_database_issues
from app.utils.decorators import admin_required

db_admin_bp = Blueprint('db_admin', __name__)


@db_admin_bp.route('/database')
@login_required
@admin_required
def database_dashboard():
    """Database administration dashboard."""
    try:
        # Get basic database statistics
        db_stats = get_database_stats()
        
        # Get table information
        table_sizes = get_table_sizes()
        
        # Analyze query patterns
        query_analysis = analyze_query_patterns()
        
        # Get connection pool info
        pool_analysis = optimize_connection_pool()
        
        return render_template('admin/database_dashboard.html',
                             db_stats=db_stats,
                             table_sizes=table_sizes,
                             query_analysis=query_analysis,
                             pool_analysis=pool_analysis)
                             
    except Exception as e:
        current_app.logger.error(f"Database dashboard error: {str(e)}")
        return render_template('error.html', error="Failed to load database dashboard"), 500


@db_admin_bp.route('/api/database/stats')
@login_required
@admin_required
def api_database_stats():
    """API endpoint for real-time database statistics."""
    try:
        stats = get_database_stats()
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Database stats API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/validation')
@login_required
@admin_required
def api_database_validation():
    """API endpoint for database validation."""
    try:
        validation_result = run_database_validation()
        return jsonify(validation_result)
    except Exception as e:
        current_app.logger.error(f"Database validation API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/fix-issues', methods=['POST'])
@login_required
@admin_required
def api_fix_database_issues():
    """API endpoint to fix common database issues."""
    try:
        fixes = fix_database_issues()
        return jsonify({
            'success': True,
            'fixes_applied': fixes,
            'count': len(fixes)
        })
    except Exception as e:
        current_app.logger.error(f"Database fix API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/maintenance', methods=['POST'])
@login_required
@admin_required
def api_database_maintenance():
    """API endpoint to run database maintenance."""
    try:
        results = run_database_maintenance()
        return jsonify({
            'success': True,
            'maintenance_results': results
        })
    except Exception as e:
        current_app.logger.error(f"Database maintenance API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/clear-metrics', methods=['POST'])
@login_required
@admin_required
def api_clear_query_metrics():
    """API endpoint to clear query performance metrics."""
    try:
        clear_query_metrics()
        return jsonify({'success': True, 'message': 'Query metrics cleared'})
    except Exception as e:
        current_app.logger.error(f"Clear metrics API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/query-analysis')
@login_required
@admin_required
def api_query_analysis():
    """API endpoint for query pattern analysis."""
    try:
        analysis = analyze_query_patterns()
        return jsonify(analysis)
    except Exception as e:
        current_app.logger.error(f"Query analysis API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/connection-pool')
@login_required
@admin_required
def api_connection_pool():
    """API endpoint for connection pool analysis."""
    try:
        pool_info = optimize_connection_pool()
        return jsonify(pool_info)
    except Exception as e:
        current_app.logger.error(f"Connection pool API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/backup', methods=['POST'])
@login_required
@admin_required
def api_create_backup():
    """API endpoint to create database backup."""
    try:
        from scripts.database_backup import DatabaseBackupManager
        
        backup_type = request.json.get('type', 'manual')
        compress = request.json.get('compress', True)
        
        manager = DatabaseBackupManager()
        result = manager.create_backup(backup_type, compress)
        
        return jsonify({
            'success': True,
            'backup_name': result['metadata']['backup_name'],
            'file_size_mb': round(result['metadata']['file_size'] / (1024 * 1024), 2),
            'created_at': result['metadata']['created_at']
        })
        
    except Exception as e:
        current_app.logger.error(f"Backup API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/backups')
@login_required
@admin_required
def api_list_backups():
    """API endpoint to list available backups."""
    try:
        from scripts.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        backups = manager.list_backups()
        
        return jsonify({
            'success': True,
            'backups': backups,
            'count': len(backups)
        })
        
    except Exception as e:
        current_app.logger.error(f"List backups API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/backup/<backup_name>/verify')
@login_required
@admin_required
def api_verify_backup(backup_name):
    """API endpoint to verify backup integrity."""
    try:
        from scripts.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        result = manager.verify_backup(backup_name)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Verify backup API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/backup/cleanup', methods=['POST'])
@login_required
@admin_required
def api_cleanup_backups():
    """API endpoint to cleanup old backups."""
    try:
        from scripts.database_backup import DatabaseBackupManager
        
        manager = DatabaseBackupManager()
        result = manager.cleanup_old_backups()
        
        return jsonify({
            'success': True,
            'deleted_count': result['deleted_count'],
            'freed_space_mb': result['freed_space_mb'],
            'remaining_backups': result['remaining_backups']
        })
        
    except Exception as e:
        current_app.logger.error(f"Cleanup backups API error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@db_admin_bp.route('/api/database/health')
@login_required
@admin_required
def api_database_health():
    """Comprehensive database health check API."""
    try:
        # Get multiple health indicators
        stats = get_database_stats()
        validation = run_database_validation()
        query_analysis = analyze_query_patterns()
        pool_analysis = optimize_connection_pool()
        
        # Calculate overall health score
        health_score = 100
        
        # Deduct points for errors and warnings
        if validation.get('errors'):
            health_score -= len(validation['errors']) * 10
        if validation.get('warnings'):
            health_score -= len(validation['warnings']) * 2
        
        # Deduct points for performance issues
        if query_analysis.get('performance_issues'):
            health_score -= len(query_analysis['performance_issues']) * 5
        
        # Connection pool utilization
        pool_settings = pool_analysis.get('current_settings', {})
        utilization = pool_settings.get('utilization', '0%')
        if utilization and float(utilization.rstrip('%')) > 90:
            health_score -= 10
        
        health_score = max(0, health_score)
        
        # Determine status
        if health_score >= 90:
            status = 'excellent'
        elif health_score >= 75:
            status = 'good'
        elif health_score >= 50:
            status = 'fair'
        else:
            status = 'poor'
        
        return jsonify({
            'status': status,
            'health_score': health_score,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'details': {
                'database_stats': stats,
                'validation': validation,
                'query_analysis': query_analysis,
                'connection_pool': pool_analysis
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Database health API error: {str(e)}")
        return jsonify({
            'status': 'error',
            'health_score': 0,
            'error': str(e)
        }), 500