"""
SQL Injection Protection Utilities for Cibozer

This module provides utilities to safely execute database queries and prevent SQL injection attacks.
"""

import re
from typing import List, Optional, Dict, Any
from flask import current_app
from sqlalchemy import text
from app.extensions import db


# Whitelist of allowed table names
ALLOWED_TABLES = {
    'users',
    'usage_logs', 
    'payments',
    'saved_meal_plans',
    'api_keys',
    'shared_meal_plans',
    'error_logs'
}

# Whitelist of allowed column names (for common operations)
ALLOWED_COLUMNS = {
    'id', 'email', 'created_at', 'updated_at', 'user_id', 'name', 'amount',
    'status', 'subscription_tier', 'is_active', 'email_verified', 'credits_balance'
}


def validate_table_name(table_name: str) -> bool:
    """
    Validate that a table name is in the allowed whitelist.
    
    Args:
        table_name: The table name to validate
        
    Returns:
        bool: True if table name is allowed, False otherwise
    """
    return table_name in ALLOWED_TABLES


def validate_column_name(column_name: str) -> bool:
    """
    Validate that a column name contains only safe characters.
    
    Args:
        column_name: The column name to validate
        
    Returns:
        bool: True if column name is safe, False otherwise
    """
    # Allow alphanumeric characters, underscores, and dots for table.column references
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$', column_name))


def safe_table_count(table_name: str) -> Optional[int]:
    """
    Safely get count of records in a table using whitelist validation.
    
    Args:
        table_name: Name of the table to count
        
    Returns:
        int: Number of records in table, or None if validation fails
    """
    if not validate_table_name(table_name):
        current_app.logger.warning(f"Attempted to count unauthorized table: {table_name}")
        return None
    
    try:
        # Use quoted identifier to prevent injection
        result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
        return result.scalar()
    except Exception as e:
        current_app.logger.error(f"Error counting table {table_name}: {str(e)}")
        return None


def safe_table_exists(table_name: str) -> bool:
    """
    Safely check if a table exists using whitelist validation.
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        bool: True if table exists and is allowed, False otherwise
    """
    if not validate_table_name(table_name):
        return False
    
    try:
        safe_table_count(table_name)
        return True
    except:
        return False


def execute_safe_query(query: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Execute a parameterized query safely.
    
    Args:
        query: SQL query with parameter placeholders (:param_name)
        params: Dictionary of parameters for the query
        
    Returns:
        Query result
        
    Raises:
        ValueError: If query appears to contain unsafe constructs
    """
    # Basic safety checks
    if not query.strip():
        raise ValueError("Empty query not allowed")
    
    # Check for obvious SQL injection patterns
    dangerous_patterns = [
        r"';",  # Query termination
        r"--",  # SQL comments
        r"/\*", # SQL block comments  
        r"\bunion\b",  # UNION attacks
        r"\bdrop\b",   # DROP statements
        r"\bdelete\b", # DELETE without WHERE (dangerous)
        r"\btruncate\b", # TRUNCATE statements
        r"\balter\b",  # ALTER statements
        r"\bcreate\b", # CREATE statements
    ]
    
    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            current_app.logger.warning(f"Potentially dangerous SQL pattern detected: {pattern}")
            raise ValueError(f"Query contains potentially dangerous pattern: {pattern}")
    
    try:
        if params:
            return db.session.execute(text(query), params)
        else:
            return db.session.execute(text(query))
    except Exception as e:
        current_app.logger.error(f"Database query error: {str(e)}")
        raise


def get_table_statistics(table_names: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Get statistics for multiple tables safely.
    
    Args:
        table_names: List of table names to get statistics for
        
    Returns:
        Dict: Statistics for each valid table
    """
    stats = {}
    
    for table_name in table_names:
        if validate_table_name(table_name):
            count = safe_table_count(table_name)
            if count is not None:
                stats[table_name] = {
                    'record_count': count,
                    'exists': True
                }
            else:
                stats[table_name] = {
                    'record_count': 0,
                    'exists': False,
                    'error': 'Query failed'
                }
        else:
            stats[table_name] = {
                'record_count': 0,
                'exists': False,
                'error': 'Table not in whitelist'
            }
    
    return stats


def validate_sql_identifier(identifier: str) -> bool:
    """
    Validate that a string is a safe SQL identifier (table name, column name, etc.).
    
    Args:
        identifier: The identifier to validate
        
    Returns:
        bool: True if identifier is safe, False otherwise
    """
    # SQL identifiers should only contain alphanumeric characters and underscores
    # and should start with a letter or underscore
    return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))


# Security audit function
def audit_query_security(query: str) -> Dict[str, Any]:
    """
    Audit a query for potential security issues.
    
    Args:
        query: SQL query to audit
        
    Returns:
        Dict: Audit results with warnings and recommendations
    """
    audit_results = {
        'safe': True,
        'warnings': [],
        'recommendations': []
    }
    
    query_lower = query.lower().strip()
    
    # Check for f-string or % formatting - but be more specific
    if ('f"' in query and '{' in query) or ("f'" in query and '{' in query) or ('%s' in query) or ('%d' in query):
        audit_results['safe'] = False
        audit_results['warnings'].append("Query appears to use string formatting - use parameterized queries instead")
    
    # Check for concatenation
    if ' + ' in query or '.format(' in query:
        audit_results['safe'] = False
        audit_results['warnings'].append("Query appears to use string concatenation - use parameterized queries instead")
    
    # Check for unparameterized LIKE
    if 'like' in query_lower and '%' in query and ':' not in query:
        audit_results['warnings'].append("LIKE query may not be parameterized properly")
    
    # Check for dangerous keywords (only truly dangerous ones)
    dangerous_keywords = ['drop', 'truncate', 'alter', 'create']
    for keyword in dangerous_keywords:
        if keyword in query_lower:
            audit_results['warnings'].append(f"Query contains potentially dangerous keyword: {keyword}")
    
    # Check for DELETE without WHERE (dangerous)
    if 'delete from' in query_lower and 'where' not in query_lower:
        audit_results['warnings'].append("DELETE query without WHERE clause is dangerous")
    
    # Check for UPDATE without WHERE (dangerous)  
    if query_lower.startswith('update') and 'where' not in query_lower:
        audit_results['warnings'].append("UPDATE query without WHERE clause is dangerous")
    
    # Recommendations
    if not audit_results['safe']:
        audit_results['recommendations'].append("Use parameterized queries with sqlalchemy.text() and parameter dictionaries")
        audit_results['recommendations'].append("Validate all user inputs against whitelists before using in queries")
        audit_results['recommendations'].append("Use SQLAlchemy ORM methods when possible instead of raw SQL")
    
    return audit_results