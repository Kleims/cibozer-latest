"""
Log Aggregation and Analysis Service for Cibozer
Centralizes logging, provides log analysis, and structured logging
"""

import json
import logging
import logging.handlers
import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from contextlib import contextmanager
import traceback
import os

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: float
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    extra_fields: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra_fields is None:
            self.extra_fields = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        return data


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def __init__(self, include_trace_info=True):
        super().__init__()
        self.include_trace_info = include_trace_info
    
    def format(self, record):
        # Get Flask request context if available
        user_id = None
        session_id = None
        request_id = None
        trace_id = None
        span_id = None
        
        if self.include_trace_info:
            try:
                from flask import g, request
                user_id = getattr(g, 'user_id', None)
                session_id = getattr(g, 'session_id', None)
                request_id = getattr(g, 'request_id', None)
                trace_id = getattr(g, 'trace_id', None)
                span_id = getattr(g, 'span_id', None)
                
                # Generate request ID if not present
                if not request_id and hasattr(request, 'method'):
                    request_id = f"{request.method}_{int(time.time() * 1000)}"
                    g.request_id = request_id
                    
            except (ImportError, RuntimeError):
                # Not in Flask context
                pass
        
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=record.created,
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            extra_fields=getattr(record, 'extra_fields', {})
        )
        
        # Add exception info if present
        if record.exc_info:
            log_entry.extra_fields['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry.to_dict(), default=str)


class LogAggregator:
    """Aggregates and analyzes log entries"""
    
    def __init__(self, max_entries=100000):
        self.max_entries = max_entries
        self.log_entries = deque(maxlen=max_entries)
        self.log_stats = defaultdict(lambda: {
            'count': 0, 'levels': defaultdict(int),
            'errors': deque(maxlen=1000), 'warnings': deque(maxlen=1000)
        })
        self.error_patterns = defaultdict(int)
        self.performance_logs = deque(maxlen=10000)
        self._lock = threading.RLock()
        
    def add_log_entry(self, entry: LogEntry):
        """Add a log entry to the aggregator"""
        with self._lock:
            self.log_entries.append(entry)
            
            # Update statistics
            stats = self.log_stats[entry.logger_name]
            stats['count'] += 1
            stats['levels'][entry.level] += 1
            
            # Track errors and warnings
            if entry.level == 'ERROR':
                stats['errors'].append(entry)
                # Track error patterns
                error_key = f"{entry.module}.{entry.function}"
                self.error_patterns[error_key] += 1
            elif entry.level == 'WARNING':
                stats['warnings'].append(entry)
            
            # Track performance-related logs
            if 'duration' in entry.extra_fields or 'response_time' in entry.extra_fields:
                self.performance_logs.append(entry)
    
    def get_recent_logs(self, limit: int = 100, level: str = None, 
                       logger_name: str = None, since: datetime = None) -> List[LogEntry]:
        """Get recent log entries with optional filtering"""
        with self._lock:
            logs = list(self.log_entries)
        
        # Apply filters
        if level:
            logs = [log for log in logs if log.level == level]
        
        if logger_name:
            logs = [log for log in logs if log.logger_name == logger_name]
        
        if since:
            since_timestamp = since.timestamp()
            logs = [log for log in logs if log.timestamp >= since_timestamp]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        since = datetime.utcnow() - timedelta(hours=hours)
        errors = self.get_recent_logs(level='ERROR', since=since)
        
        # Group errors by type
        error_types = defaultdict(int)
        recent_errors = []
        
        for error in errors:
            error_types[error.message[:100]] += 1
            if len(recent_errors) < 20:
                recent_errors.append({
                    'timestamp': datetime.fromtimestamp(error.timestamp).isoformat(),
                    'message': error.message,
                    'module': error.module,
                    'function': error.function,
                    'user_id': error.user_id,
                    'trace_id': error.trace_id
                })
        
        return {
            'total_errors': len(errors),
            'error_rate_per_hour': len(errors) / max(hours, 1),
            'error_types': dict(error_types),
            'recent_errors': recent_errors,
            'top_error_sources': dict(sorted(
                self.error_patterns.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10])
        }
    
    def get_logger_stats(self) -> Dict[str, Any]:
        """Get statistics for all loggers"""
        with self._lock:
            return {
                logger: {
                    'total_logs': stats['count'],
                    'levels': dict(stats['levels']),
                    'recent_errors': len(stats['errors']),
                    'recent_warnings': len(stats['warnings'])
                }
                for logger, stats in self.log_stats.items()
            }
    
    def search_logs(self, query: str, limit: int = 100) -> List[LogEntry]:
        """Search logs by message content"""
        with self._lock:
            matching_logs = []
            query_lower = query.lower()
            
            for log in reversed(list(self.log_entries)):
                if query_lower in log.message.lower():
                    matching_logs.append(log)
                    if len(matching_logs) >= limit:
                        break
            
            return matching_logs
    
    def analyze_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze log patterns and anomalies"""
        since = datetime.utcnow() - timedelta(hours=hours)
        recent_logs = self.get_recent_logs(since=since)
        
        # Analyze by hour
        hourly_counts = defaultdict(lambda: defaultdict(int))
        for log in recent_logs:
            hour = datetime.fromtimestamp(log.timestamp).strftime('%Y-%m-%d %H:00')
            hourly_counts[hour][log.level] += 1
        
        # Find anomalies (error spikes)
        error_hours = [(hour, counts['ERROR']) for hour, counts in hourly_counts.items()]
        error_hours.sort(key=lambda x: x[1], reverse=True)
        
        # Module activity
        module_activity = defaultdict(int)
        for log in recent_logs:
            module_activity[log.module] += 1
        
        return {
            'total_logs': len(recent_logs),
            'hourly_breakdown': dict(hourly_counts),
            'top_error_hours': error_hours[:5],
            'most_active_modules': dict(sorted(
                module_activity.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]),
            'unique_loggers': len({log.logger_name for log in recent_logs}),
            'unique_users': len({log.user_id for log in recent_logs if log.user_id}),
            'traced_requests': len({log.trace_id for log in recent_logs if log.trace_id})
        }


class LoggingService:
    """Main logging service for centralized log management"""
    
    def __init__(self, app=None):
        self.app = app
        self.aggregator = LogAggregator()
        self.handlers = []
        self.is_initialized = False
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize logging service with Flask app"""
        self.app = app
        
        # Create logs directory
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Setup structured logging
        self.setup_structured_logging()
        
        # Setup log aggregation
        self.setup_log_aggregation()
        
        # Register custom logger
        self.register_custom_loggers()
        
        self.is_initialized = True
        app.logger.info('Logging service initialized')
    
    def setup_structured_logging(self):
        """Setup structured JSON logging"""
        if not self.app:
            return
            
        # Create structured formatter
        formatter = StructuredFormatter()
        
        # Setup file handler for structured logs
        structured_handler = logging.handlers.RotatingFileHandler(
            'logs/structured.log',
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10
        )
        structured_handler.setFormatter(formatter)
        structured_handler.setLevel(logging.INFO)
        
        # Setup error-only handler
        error_handler = logging.handlers.RotatingFileHandler(
            'logs/errors.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Add handlers to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(structured_handler)
        root_logger.addHandler(error_handler)
        
        # Add handlers to app logger
        self.app.logger.addHandler(structured_handler)
        self.app.logger.addHandler(error_handler)
        
        self.handlers.extend([structured_handler, error_handler])
    
    def setup_log_aggregation(self):
        """Setup log aggregation with custom handler"""
        class AggregationHandler(logging.Handler):
            def __init__(self, aggregator):
                super().__init__()
                self.aggregator = aggregator
            
            def emit(self, record):
                try:
                    # Create LogEntry from logging record
                    entry = LogEntry(
                        timestamp=record.created,
                        level=record.levelname,
                        logger_name=record.name,
                        message=record.getMessage(),
                        module=record.module,
                        function=record.funcName,
                        line_number=record.lineno,
                        thread_id=record.thread,
                        process_id=record.process,
                        extra_fields=getattr(record, 'extra_fields', {})
                    )
                    
                    self.aggregator.add_log_entry(entry)
                except Exception:
                    # Don't let logging errors crash the app
                    pass
        
        # Add aggregation handler
        agg_handler = AggregationHandler(self.aggregator)
        agg_handler.setLevel(logging.INFO)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(agg_handler)
        
        if self.app:
            self.app.logger.addHandler(agg_handler)
        
        self.handlers.append(agg_handler)
    
    def register_custom_loggers(self):
        """Register custom loggers for different components"""
        loggers = {
            'cibozer.security': logging.INFO,
            'cibozer.performance': logging.INFO,
            'cibozer.business': logging.INFO,
            'cibozer.api': logging.INFO,
            'cibozer.database': logging.WARNING,
            'cibozer.monitoring': logging.INFO
        }
        
        for logger_name, level in loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a configured logger"""
        return logging.getLogger(f'cibozer.{name}')
    
    def log_security_event(self, event_type: str, user_id: str = None, 
                          details: Dict[str, Any] = None):
        """Log security-related events"""
        logger = self.get_logger('security')
        logger.warning(f"Security event: {event_type}", extra={
            'extra_fields': {
                'event_type': event_type,
                'user_id': user_id,
                'details': details or {}
            }
        })
    
    def log_performance_metric(self, metric_name: str, value: Union[int, float], 
                             unit: str = 'ms', details: Dict[str, Any] = None):
        """Log performance metrics"""
        logger = self.get_logger('performance')
        logger.info(f"Performance metric: {metric_name} = {value}{unit}", extra={
            'extra_fields': {
                'metric_name': metric_name,
                'value': value,
                'unit': unit,
                'details': details or {}
            }
        })
    
    def log_business_event(self, event_type: str, user_id: str = None, 
                          details: Dict[str, Any] = None):
        """Log business-related events"""
        logger = self.get_logger('business')
        logger.info(f"Business event: {event_type}", extra={
            'extra_fields': {
                'event_type': event_type,
                'user_id': user_id,
                'details': details or {}
            }
        })
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       duration_ms: float, user_id: str = None):
        """Log API requests"""
        logger = self.get_logger('api')
        logger.info(f"API {method} {endpoint} -> {status_code} ({duration_ms:.1f}ms)", extra={
            'extra_fields': {
                'method': method,
                'endpoint': endpoint,
                'status_code': status_code,
                'duration_ms': duration_ms,
                'user_id': user_id
            }
        })
    
    @contextmanager
    def log_context(self, **context_fields):
        """Context manager to add fields to all logs within the context"""
        # This would need integration with Flask's g object
        try:
            from flask import g
            old_context = getattr(g, 'log_context', {})
            g.log_context = {**old_context, **context_fields}
            yield
        finally:
            if 'g' in locals():
                g.log_context = old_context
    
    def cleanup_old_logs(self, days: int = 30):
        """Clean up old log files"""
        logs_dir = Path('logs')
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for log_file in logs_dir.glob('*.log*'):
            try:
                if log_file.stat().st_mtime < cutoff_time:
                    log_file.unlink()
                    if self.app:
                        self.app.logger.info(f'Cleaned up old log file: {log_file}')
            except Exception as e:
                if self.app:
                    self.app.logger.error(f'Error cleaning up log file {log_file}: {e}')
    
    def export_logs(self, format: str = 'json', filters: Dict[str, Any] = None) -> str:
        """Export logs in specified format"""
        filters = filters or {}
        
        logs = self.aggregator.get_recent_logs(
            limit=filters.get('limit', 1000),
            level=filters.get('level'),
            logger_name=filters.get('logger_name'),
            since=filters.get('since')
        )
        
        if format == 'json':
            return json.dumps([log.to_dict() for log in logs], indent=2, default=str)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'timestamp_iso', 'level', 'logger_name', 'message', 
                'module', 'function', 'user_id', 'trace_id'
            ])
            writer.writeheader()
            
            for log in logs:
                row = log.to_dict()
                # Simplify complex fields for CSV
                writer.writerow({
                    'timestamp_iso': row['timestamp_iso'],
                    'level': row['level'],
                    'logger_name': row['logger_name'],
                    'message': row['message'][:200],  # Truncate long messages
                    'module': row['module'],
                    'function': row['function'],
                    'user_id': row['user_id'],
                    'trace_id': row['trace_id']
                })
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global logging service instance
_logging_service = None
_logging_lock = threading.Lock()


def get_logging_service() -> LoggingService:
    """Get the global logging service instance"""
    global _logging_service
    if _logging_service is None:
        with _logging_lock:
            if _logging_service is None:
                _logging_service = LoggingService()
    return _logging_service


def init_logging_service(app):
    """Initialize logging service with Flask app"""
    logging_service = get_logging_service()
    logging_service.init_app(app)
    return logging_service


# Convenience functions
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger"""
    return get_logging_service().get_logger(name)


def log_security_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None):
    """Log security-related events"""
    get_logging_service().log_security_event(event_type, user_id, details)


def log_performance_metric(metric_name: str, value: Union[int, float], 
                          unit: str = 'ms', details: Dict[str, Any] = None):
    """Log performance metrics"""
    get_logging_service().log_performance_metric(metric_name, value, unit, details)


def log_business_event(event_type: str, user_id: str = None, details: Dict[str, Any] = None):
    """Log business-related events"""
    get_logging_service().log_business_event(event_type, user_id, details)