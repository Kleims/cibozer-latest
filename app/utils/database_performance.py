"""Database performance monitoring and optimization utilities."""
import time
import logging
from contextlib import contextmanager
from functools import wraps
from flask import current_app
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from app.extensions import db


# Performance metrics storage
query_metrics = {
    'slow_queries': [],
    'query_counts': {},
    'total_queries': 0,
    'total_time': 0.0
}


@event.listens_for(Engine, 'before_cursor_execute')
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    conn.info.setdefault('query_start_time', []).append(time.time())


@event.listens_for(Engine, 'after_cursor_execute')
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query execution time and log slow queries."""
    total = time.time() - conn.info['query_start_time'].pop(-1)
    
    # Update metrics
    query_metrics['total_queries'] += 1
    query_metrics['total_time'] += total
    
    # Count query types
    query_type = statement.strip().split()[0].upper()
    query_metrics['query_counts'][query_type] = query_metrics['query_counts'].get(query_type, 0) + 1
    
    # Log slow queries (>1 second)
    if total > 1.0:
        # Truncate long statements for logging
        truncated_statement = statement[:500] + '...' if len(statement) > 500 else statement
        
        slow_query = {
            'statement': truncated_statement,
            'parameters': str(parameters)[:200] if parameters else None,
            'duration': total,
            'timestamp': time.time()
        }
        
        query_metrics['slow_queries'].append(slow_query)
        
        # Keep only last 50 slow queries
        if len(query_metrics['slow_queries']) > 50:
            query_metrics['slow_queries'] = query_metrics['slow_queries'][-50:]
        
        current_app.logger.warning(
            f"Slow query detected ({total:.2f}s): {truncated_statement}"
        )


class DatabaseProfiler:
    """Database performance profiler."""
    
    def __init__(self):
        self.enabled = False
        self.queries = []
        self.start_time = None
    
    def start(self):
        """Start profiling database queries."""
        self.enabled = True
        self.queries = []
        self.start_time = time.time()
        current_app.logger.info("Database profiling started")
    
    def stop(self):
        """Stop profiling and return results."""
        self.enabled = False
        total_time = time.time() - self.start_time if self.start_time else 0
        
        results = {
            'total_queries': len(self.queries),
            'total_time': total_time,
            'queries': self.queries,
            'average_query_time': sum(q['duration'] for q in self.queries) / len(self.queries) if self.queries else 0,
            'slowest_query': max(self.queries, key=lambda q: q['duration']) if self.queries else None
        }
        
        current_app.logger.info(f"Database profiling stopped. {len(self.queries)} queries in {total_time:.2f}s")
        return results


# Global profiler instance
db_profiler = DatabaseProfiler()


@contextmanager
def profile_queries():
    """Context manager for profiling database queries."""
    db_profiler.start()
    try:
        yield db_profiler
    finally:
        results = db_profiler.stop()
        return results


def log_query_performance(func):
    """Decorator to log query performance for a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Record initial query count
        initial_queries = query_metrics['total_queries']
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            queries_executed = query_metrics['total_queries'] - initial_queries
            
            if duration > 0.5 or queries_executed > 10:  # Log if slow or many queries
                current_app.logger.info(
                    f"Function {func.__name__} executed {queries_executed} queries in {duration:.2f}s"
                )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            queries_executed = query_metrics['total_queries'] - initial_queries
            current_app.logger.error(
                f"Function {func.__name__} failed after {queries_executed} queries in {duration:.2f}s: {str(e)}"
            )
            raise
    
    return wrapper


def get_database_stats():
    """Get current database performance statistics."""
    try:
        # Get connection pool info
        engine = db.get_engine()
        pool = engine.pool
        
        # Get database size (SQLite specific)
        db_size = None
        table_count = None
        
        try:
            if 'sqlite' in str(engine.url):
                # SQLite specific queries
                result = db.session.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()"))
                db_size = result.scalar()
                
                result = db.session.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'"))
                table_count = result.scalar()
        except:
            pass
        
        return {
            'query_metrics': query_metrics.copy(),
            'connection_pool': {
                'size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            },
            'database_info': {
                'size_bytes': db_size,
                'table_count': table_count,
                'engine_url': str(engine.url).split('@')[0] + '@***'  # Hide credentials
            }
        }
    except Exception as e:
        current_app.logger.error(f"Failed to get database stats: {str(e)}")
        return {'error': str(e)}


def analyze_query_patterns():
    """Analyze query patterns to identify optimization opportunities."""
    analysis = {
        'recommendations': [],
        'patterns': {},
        'performance_issues': []
    }
    
    # Analyze query types
    total_queries = query_metrics['total_queries']
    if total_queries > 0:
        for query_type, count in query_metrics['query_counts'].items():
            percentage = (count / total_queries) * 100
            analysis['patterns'][query_type] = {
                'count': count,
                'percentage': percentage
            }
            
            # Add recommendations based on patterns
            if query_type == 'SELECT' and percentage > 80:
                analysis['recommendations'].append(
                    "High SELECT ratio - consider caching frequently accessed data"
                )
            elif query_type == 'UPDATE' and percentage > 20:
                analysis['recommendations'].append(
                    "High UPDATE ratio - ensure proper indexing on updated columns"
                )
    
    # Analyze slow queries
    if query_metrics['slow_queries']:
        avg_slow_time = sum(q['duration'] for q in query_metrics['slow_queries']) / len(query_metrics['slow_queries'])
        analysis['performance_issues'].append(
            f"Found {len(query_metrics['slow_queries'])} slow queries (avg: {avg_slow_time:.2f}s)"
        )
        
        # Common slow query patterns
        slow_statements = [q['statement'] for q in query_metrics['slow_queries']]
        
        if any('JOIN' in stmt for stmt in slow_statements):
            analysis['recommendations'].append(
                "Slow JOIN queries detected - verify foreign key indexes"
            )
        
        if any('ORDER BY' in stmt for stmt in slow_statements):
            analysis['recommendations'].append(
                "Slow ORDER BY queries detected - consider adding composite indexes"
            )
        
        if any('COUNT(*)' in stmt for stmt in slow_statements):
            analysis['recommendations'].append(
                "Slow COUNT queries detected - consider using approximate counts or caching"
            )
    
    return analysis


def optimize_connection_pool():
    """Optimize database connection pool settings."""
    try:
        engine = db.get_engine()
        pool = engine.pool
        
        # Check pool utilization
        utilization = pool.checkedout() / pool.size() if pool.size() > 0 else 0
        
        recommendations = []
        
        if utilization > 0.8:
            recommendations.append("Pool utilization high (>80%) - consider increasing pool size")
        elif utilization < 0.2:
            recommendations.append("Pool utilization low (<20%) - consider decreasing pool size")
        
        if pool.overflow() > pool.size() * 0.5:
            recommendations.append("High overflow usage - consider increasing base pool size")
        
        if pool.invalid() > 0:
            recommendations.append(f"Found {pool.invalid()} invalid connections - check connection stability")
        
        return {
            'current_settings': {
                'pool_size': pool.size(),
                'overflow': pool.overflow(),
                'checked_out': pool.checkedout(),
                'invalid': pool.invalid(),
                'utilization': f"{utilization:.1%}"
            },
            'recommendations': recommendations
        }
        
    except Exception as e:
        current_app.logger.error(f"Failed to analyze connection pool: {str(e)}")
        return {'error': str(e)}


def run_database_maintenance():
    """Run database maintenance tasks."""
    maintenance_results = []
    
    try:
        engine = db.get_engine()
        
        if 'sqlite' in str(engine.url):
            # SQLite specific maintenance
            try:
                # VACUUM to defragment database
                db.session.execute(text("VACUUM"))
                maintenance_results.append("Database vacuumed successfully")
                
                # ANALYZE to update statistics
                db.session.execute(text("ANALYZE"))
                maintenance_results.append("Database statistics updated")
                
                # Check integrity
                result = db.session.execute(text("PRAGMA integrity_check"))
                integrity = result.scalar()
                if integrity == 'ok':
                    maintenance_results.append("Database integrity check passed")
                else:
                    maintenance_results.append(f"Database integrity issues: {integrity}")
                
            except Exception as e:
                maintenance_results.append(f"SQLite maintenance error: {str(e)}")
        
        else:
            # PostgreSQL/MySQL maintenance would go here
            maintenance_results.append("Maintenance for this database type not implemented")
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        maintenance_results.append(f"Maintenance failed: {str(e)}")
        current_app.logger.error(f"Database maintenance failed: {str(e)}")
    
    return maintenance_results


def clear_query_metrics():
    """Clear accumulated query metrics."""
    global query_metrics
    query_metrics = {
        'slow_queries': [],
        'query_counts': {},
        'total_queries': 0,
        'total_time': 0.0
    }
    current_app.logger.info("Query metrics cleared")


def get_table_sizes():
    """Get size information for all tables."""
    try:
        tables = db.metadata.tables.keys()
        table_info = {}
        
        for table_name in tables:
            try:
                # Get row count - validate table name against known tables
                allowed_tables = ['users', 'usage_logs', 'payments', 'saved_meal_plans', 'api_keys', 'shared_meal_plans']
                if table_name not in allowed_tables:
                    current_app.logger.warning(f"Attempted to query unauthorized table: {table_name}")
                    continue
                result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                row_count = result.scalar()
                table_info[table_name] = {'row_count': row_count}
                
                # For SQLite, get approximate size
                if 'sqlite' in str(db.get_engine().url):
                    # This is approximate - SQLite doesn't have per-table size info
                    table_info[table_name]['estimated_size'] = 'Not available (SQLite)'
                
            except Exception as e:
                table_info[table_name] = {'error': str(e)}
        
        return table_info
        
    except Exception as e:
        current_app.logger.error(f"Failed to get table sizes: {str(e)}")
        return {'error': str(e)}