"""
Test SQL injection protection mechanisms.
"""

import pytest
from app import create_app
from app.extensions import db
from app.utils.sql_injection_protection import (
    validate_table_name,
    validate_column_name, 
    safe_table_count,
    safe_table_exists,
    execute_safe_query,
    get_table_statistics,
    validate_sql_identifier,
    audit_query_security
)
from sqlalchemy import text


@pytest.fixture
def app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestTableValidation:
    """Test table name validation."""
    
    def test_valid_table_names(self, app):
        """Test that valid table names are accepted."""
        with app.app_context():
            valid_tables = ['users', 'usage_logs', 'payments', 'saved_meal_plans']
            for table in valid_tables:
                assert validate_table_name(table), f"Table {table} should be valid"
    
    def test_invalid_table_names(self, app):
        """Test that invalid table names are rejected."""
        with app.app_context():
            invalid_tables = [
                'malicious_table',
                'users; DROP TABLE users; --',
                '../../../etc/passwd',
                'users UNION SELECT * FROM passwords',
                ''
            ]
            for table in invalid_tables:
                assert not validate_table_name(table), f"Table {table} should be invalid"


class TestColumnValidation:
    """Test column name validation."""
    
    def test_valid_column_names(self, app):
        """Test that valid column names are accepted."""
        with app.app_context():
            valid_columns = ['id', 'email', 'created_at', 'user_id', 'table.column']
            for column in valid_columns:
                assert validate_column_name(column), f"Column {column} should be valid"
    
    def test_invalid_column_names(self, app):
        """Test that invalid column names are rejected."""
        with app.app_context():
            invalid_columns = [
                'id; DROP TABLE users; --',
                'id UNION SELECT password FROM users',
                '../../etc/passwd',
                'id OR 1=1',
                ''
            ]
            for column in invalid_columns:
                assert not validate_column_name(column), f"Column {column} should be invalid"


class TestSafeQueries:
    """Test safe query execution."""
    
    def test_safe_table_count(self, app):
        """Test safe table counting."""
        with app.app_context():
            # Valid table
            count = safe_table_count('users')
            assert count is not None
            assert isinstance(count, int)
            
            # Invalid table
            count = safe_table_count('malicious_table')
            assert count is None
    
    def test_safe_table_exists(self, app):
        """Test safe table existence checking."""
        with app.app_context():
            # Valid table
            assert safe_table_exists('users')
            
            # Invalid table
            assert not safe_table_exists('malicious_table')
    
    def test_execute_safe_query(self, app):
        """Test safe query execution with parameters."""
        with app.app_context():
            # Safe parameterized query
            result = execute_safe_query(
                "SELECT COUNT(*) FROM users WHERE email = :email",
                {'email': 'test@example.com'}
            )
            assert result is not None
            
            # Test dangerous query rejection
            with pytest.raises(ValueError):
                execute_safe_query("SELECT * FROM users; DROP TABLE users; --")
            
            with pytest.raises(ValueError):
                execute_safe_query("SELECT * FROM users UNION SELECT * FROM passwords")


class TestSecurityAudit:
    """Test security auditing functionality."""
    
    def test_safe_queries_pass_audit(self, app):
        """Test that safe queries pass security audit."""
        with app.app_context():
            safe_queries = [
                "SELECT * FROM users WHERE email = :email",
                "INSERT INTO users (email, password_hash) VALUES (:email, :password)",
                "UPDATE users SET last_login = :timestamp WHERE id = :user_id"
            ]
            
            for query in safe_queries:
                audit = audit_query_security(query)
                assert audit['safe'], f"Query should be safe: {query}"
                assert len(audit['warnings']) == 0, f"Safe query should have no warnings: {query}"
    
    def test_unsafe_queries_fail_audit(self, app):
        """Test that unsafe queries fail security audit."""
        with app.app_context():
            unsafe_queries = [
                "SELECT * FROM users WHERE email = '%s'",  # % formatting placeholder
                "SELECT * FROM users WHERE email = '{}'.format('test')",  # .format() usage
                "SELECT * FROM users WHERE name = 'user' + ' test'",  # String concatenation
            ]
            
            for query in unsafe_queries:
                audit = audit_query_security(query)
                assert not audit['safe'], f"Query should be unsafe: {query}"
                assert len(audit['warnings']) > 0, f"Unsafe query should have warnings: {query}"
    
    def test_dangerous_keywords_detected(self, app):
        """Test that dangerous SQL keywords are detected."""
        with app.app_context():
            dangerous_queries = [
                "DROP TABLE users",
                "TRUNCATE TABLE users", 
                "ALTER TABLE users ADD COLUMN password TEXT",
                "DELETE FROM users",  # DELETE without WHERE
                "CREATE TABLE malicious (id INT)",
                "UPDATE users SET password = 'hacked'"  # UPDATE without WHERE
            ]
            
            for query in dangerous_queries:
                audit = audit_query_security(query)
                assert len(audit['warnings']) > 0, f"Dangerous query should have warnings: {query}"


class TestStatistics:
    """Test statistics gathering."""
    
    def test_get_table_statistics(self, app):
        """Test getting statistics for multiple tables."""
        with app.app_context():
            tables = ['users', 'malicious_table', 'usage_logs']
            stats = get_table_statistics(tables)
            
            # Valid tables should have stats
            assert 'users' in stats
            assert stats['users']['exists']
            assert 'record_count' in stats['users']
            
            # Invalid tables should be blocked
            assert 'malicious_table' in stats
            assert not stats['malicious_table']['exists']
            assert 'error' in stats['malicious_table']
            assert stats['malicious_table']['error'] == 'Table not in whitelist'


class TestSQLIdentifierValidation:
    """Test SQL identifier validation."""
    
    def test_valid_identifiers(self, app):
        """Test that valid SQL identifiers are accepted."""
        with app.app_context():
            valid_identifiers = [
                'users',
                'user_id',
                'created_at',
                '_private_field',
                'table123'
            ]
            
            for identifier in valid_identifiers:
                assert validate_sql_identifier(identifier), f"Identifier should be valid: {identifier}"
    
    def test_invalid_identifiers(self, app):
        """Test that invalid SQL identifiers are rejected."""
        with app.app_context():
            invalid_identifiers = [
                '123invalid',  # Starts with number
                'user-id',     # Contains hyphen
                'user id',     # Contains space
                'user;id',     # Contains semicolon
                'user.id.extra',  # Too many dots
                '',            # Empty
                'user/**/id'   # Contains SQL comment
            ]
            
            for identifier in invalid_identifiers:
                assert not validate_sql_identifier(identifier), f"Identifier should be invalid: {identifier}"


# Integration tests with real SQL injection attempts
class TestSQLInjectionPrevention:
    """Test prevention of actual SQL injection attacks."""
    
    def test_union_attack_prevention(self, app):
        """Test prevention of UNION-based SQL injection."""
        with app.app_context():
            # This should be blocked by our security measures
            with pytest.raises(ValueError):
                execute_safe_query("SELECT * FROM users WHERE email = 'test@example.com' UNION SELECT password FROM admin")
    
    def test_comment_attack_prevention(self, app):
        """Test prevention of comment-based SQL injection."""
        with app.app_context():
            # This should be blocked by our security measures
            with pytest.raises(ValueError):
                execute_safe_query("SELECT * FROM users WHERE email = 'admin@example.com'; -- DROP TABLE users;")
    
    def test_boolean_attack_prevention(self, app):
        """Test prevention of boolean-based SQL injection."""
        with app.app_context():
            # Our parameterized queries should handle this safely
            result = execute_safe_query(
                "SELECT * FROM users WHERE email = :email",
                {'email': "' OR '1'='1"}
            )
            # The malicious input should be treated as a literal string, not SQL code
            assert result is not None
    
    def test_time_based_attack_prevention(self, app):
        """Test prevention of time-based SQL injection."""
        with app.app_context():
            # Time-based attacks typically use WAITFOR or similar
            with pytest.raises(ValueError):
                execute_safe_query("SELECT * FROM users WHERE email = 'test'; WAITFOR DELAY '00:00:05'; --")