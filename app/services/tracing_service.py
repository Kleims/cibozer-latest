"""
Distributed Tracing Service for Cibozer
Provides request tracing, span tracking, and performance insights
"""

import time
import uuid
import json
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from functools import wraps
from flask import request, g, current_app
from contextlib import contextmanager


@dataclass
class Span:
    """Represents a single trace span"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: float
    end_time: Optional[float]
    duration_ms: Optional[float]
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    status: str  # 'ok', 'error', 'timeout'
    error_message: Optional[str]
    
    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


@dataclass
class Trace:
    """Represents a complete trace with multiple spans"""
    trace_id: str
    root_span_id: str
    spans: List[Span]
    start_time: float
    end_time: Optional[float]
    duration_ms: Optional[float]
    service_name: str
    operation_name: str
    status: str
    error_count: int
    span_count: int
    
    def __post_init__(self):
        if self.end_time and self.start_time:
            self.duration_ms = (self.end_time - self.start_time) * 1000


class TracingService:
    """Main distributed tracing service"""
    
    def __init__(self):
        self.traces = {}  # trace_id -> Trace
        self.active_spans = {}  # span_id -> Span
        self.trace_history = deque(maxlen=10000)  # Recent traces
        self.span_history = deque(maxlen=50000)  # Recent spans
        self.service_dependencies = defaultdict(set)  # service -> set of dependencies
        self.operation_stats = defaultdict(lambda: {
            'count': 0, 'total_duration': 0, 'error_count': 0,
            'min_duration': float('inf'), 'max_duration': 0
        })
        self._lock = threading.RLock()
        
        # Configuration
        self.enabled = True
        self.sample_rate = 1.0  # Sample 100% of traces by default
        self.max_trace_duration = 30000  # 30 seconds max trace duration
        
    def generate_trace_id(self) -> str:
        """Generate a new trace ID"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def generate_span_id(self) -> str:
        """Generate a new span ID"""
        return str(uuid.uuid4()).replace('-', '')[:8]
    
    def should_sample(self) -> bool:
        """Determine if a trace should be sampled"""
        import random
        return random.random() < self.sample_rate
    
    def start_trace(self, operation_name: str, service_name: str = 'cibozer') -> str:
        """Start a new trace"""
        if not self.enabled or not self.should_sample():
            return None
            
        trace_id = self.generate_trace_id()
        span_id = self.generate_span_id()
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=time.time(),
            end_time=None,
            duration_ms=None,
            tags={'service': service_name},
            logs=[],
            status='ok',
            error_message=None
        )
        
        trace = Trace(
            trace_id=trace_id,
            root_span_id=span_id,
            spans=[span],
            start_time=span.start_time,
            end_time=None,
            duration_ms=None,
            service_name=service_name,
            operation_name=operation_name,
            status='ok',
            error_count=0,
            span_count=1
        )
        
        with self._lock:
            self.traces[trace_id] = trace
            self.active_spans[span_id] = span
        
        return trace_id
    
    def start_span(self, operation_name: str, trace_id: str, parent_span_id: str = None, 
                   tags: Dict[str, Any] = None) -> str:
        """Start a new span within a trace"""
        if not self.enabled or not trace_id:
            return None
            
        span_id = self.generate_span_id()
        
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=time.time(),
            end_time=None,
            duration_ms=None,
            tags=tags or {},
            logs=[],
            status='ok',
            error_message=None
        )
        
        with self._lock:
            self.active_spans[span_id] = span
            if trace_id in self.traces:
                self.traces[trace_id].spans.append(span)
                self.traces[trace_id].span_count += 1
        
        return span_id
    
    def finish_span(self, span_id: str, status: str = 'ok', error_message: str = None,
                   tags: Dict[str, Any] = None):
        """Finish a span"""
        if not span_id or span_id not in self.active_spans:
            return
            
        with self._lock:
            span = self.active_spans[span_id]
            span.end_time = time.time()
            span.duration_ms = (span.end_time - span.start_time) * 1000
            span.status = status
            span.error_message = error_message
            
            if tags:
                span.tags.update(tags)
            
            # Update operation statistics
            op_stats = self.operation_stats[span.operation_name]
            op_stats['count'] += 1
            op_stats['total_duration'] += span.duration_ms
            op_stats['min_duration'] = min(op_stats['min_duration'], span.duration_ms)
            op_stats['max_duration'] = max(op_stats['max_duration'], span.duration_ms)
            
            if status == 'error':
                op_stats['error_count'] += 1
                # Update trace error count
                if span.trace_id in self.traces:
                    self.traces[span.trace_id].error_count += 1
            
            # Move to history
            self.span_history.append(span)
            del self.active_spans[span_id]
    
    def finish_trace(self, trace_id: str):
        """Finish a trace"""
        if not trace_id or trace_id not in self.traces:
            return
            
        with self._lock:
            trace = self.traces[trace_id]
            trace.end_time = time.time()
            trace.duration_ms = (trace.end_time - trace.start_time) * 1000
            
            # Set trace status based on span statuses
            if trace.error_count > 0:
                trace.status = 'error'
            elif any(span.status == 'timeout' for span in trace.spans):
                trace.status = 'timeout'
            else:
                trace.status = 'ok'
            
            # Move to history
            self.trace_history.append(trace)
            
            # Clean up any remaining active spans for this trace
            spans_to_remove = [sid for sid, span in self.active_spans.items() 
                             if span.trace_id == trace_id]
            for span_id in spans_to_remove:
                del self.active_spans[span_id]
            
            del self.traces[trace_id]
    
    def add_span_tag(self, span_id: str, key: str, value: Any):
        """Add a tag to a span"""
        if span_id in self.active_spans:
            self.active_spans[span_id].tags[key] = value
    
    def add_span_log(self, span_id: str, message: str, level: str = 'info', 
                    fields: Dict[str, Any] = None):
        """Add a log entry to a span"""
        if span_id in self.active_spans:
            log_entry = {
                'timestamp': time.time(),
                'message': message,
                'level': level,
                'fields': fields or {}
            }
            self.active_spans[span_id].logs.append(log_entry)
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        # Check active traces
        if trace_id in self.traces:
            return self.traces[trace_id]
        
        # Check history
        for trace in self.trace_history:
            if trace.trace_id == trace_id:
                return trace
        
        return None
    
    def get_traces(self, limit: int = 100, service: str = None, 
                  operation: str = None, status: str = None,
                  min_duration_ms: float = None) -> List[Trace]:
        """Get traces with optional filtering"""
        traces = list(self.trace_history)
        
        # Apply filters
        if service:
            traces = [t for t in traces if t.service_name == service]
        if operation:
            traces = [t for t in traces if t.operation_name == operation]
        if status:
            traces = [t for t in traces if t.status == status]
        if min_duration_ms:
            traces = [t for t in traces if t.duration_ms and t.duration_ms >= min_duration_ms]
        
        # Sort by start time (newest first)
        traces.sort(key=lambda t: t.start_time, reverse=True)
        
        return traces[:limit]
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get operation performance statistics"""
        stats = {}
        
        for operation, data in self.operation_stats.items():
            if data['count'] > 0:
                avg_duration = data['total_duration'] / data['count']
                error_rate = (data['error_count'] / data['count']) * 100
                
                stats[operation] = {
                    'count': data['count'],
                    'error_count': data['error_count'],
                    'error_rate_percent': error_rate,
                    'avg_duration_ms': avg_duration,
                    'min_duration_ms': data['min_duration'],
                    'max_duration_ms': data['max_duration']
                }
        
        return stats
    
    def get_service_dependencies(self) -> Dict[str, List[str]]:
        """Get service dependency map"""
        return {service: list(deps) for service, deps in self.service_dependencies.items()}
    
    def track_dependency(self, from_service: str, to_service: str):
        """Track a service dependency"""
        self.service_dependencies[from_service].add(to_service)
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old tracing data"""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        with self._lock:
            # Clean up old traces from history
            self.trace_history = deque([
                trace for trace in self.trace_history 
                if trace.start_time > cutoff_time
            ], maxlen=self.trace_history.maxlen)
            
            # Clean up old spans from history
            self.span_history = deque([
                span for span in self.span_history 
                if span.start_time > cutoff_time
            ], maxlen=self.span_history.maxlen)
            
            # Clean up stuck active spans (older than max_trace_duration)
            stuck_spans = [
                span_id for span_id, span in self.active_spans.items()
                if (time.time() - span.start_time) * 1000 > self.max_trace_duration
            ]
            
            for span_id in stuck_spans:
                self.finish_span(span_id, status='timeout', error_message='Trace timeout')
    
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get tracing system summary"""
        total_traces = len(self.trace_history)
        error_traces = len([t for t in self.trace_history if t.status == 'error'])
        
        # Calculate percentiles for trace durations
        durations = [t.duration_ms for t in self.trace_history if t.duration_ms]
        durations.sort()
        
        percentiles = {}
        if durations:
            percentiles = {
                'p50': durations[int(len(durations) * 0.5)] if durations else 0,
                'p95': durations[int(len(durations) * 0.95)] if durations else 0,
                'p99': durations[int(len(durations) * 0.99)] if durations else 0
            }
        
        return {
            'total_traces': total_traces,
            'error_traces': error_traces,
            'error_rate_percent': (error_traces / max(total_traces, 1)) * 100,
            'active_traces': len(self.traces),
            'active_spans': len(self.active_spans),
            'avg_spans_per_trace': sum(t.span_count for t in self.trace_history) / max(total_traces, 1),
            'duration_percentiles': percentiles,
            'unique_operations': len(self.operation_stats),
            'service_count': len(self.service_dependencies)
        }


# Global tracing service instance
_tracing_service = None
_tracing_lock = threading.Lock()


def get_tracing_service() -> TracingService:
    """Get the global tracing service instance"""
    global _tracing_service
    if _tracing_service is None:
        with _tracing_lock:
            if _tracing_service is None:
                _tracing_service = TracingService()
                
                # Start cleanup task
                import atexit
                def cleanup():
                    _tracing_service.cleanup_old_data()
                atexit.register(cleanup)
    
    return _tracing_service


# Flask integration
def init_tracing(app):
    """Initialize tracing for Flask app"""
    tracing = get_tracing_service()
    
    @app.before_request
    def start_request_trace():
        if not tracing.enabled:
            return
            
        # Extract trace ID from headers (for distributed tracing)
        trace_id = request.headers.get('X-Trace-ID')
        parent_span_id = request.headers.get('X-Parent-Span-ID')
        
        operation_name = f"{request.method} {request.endpoint or request.path}"
        
        if not trace_id:
            # Start new trace
            trace_id = tracing.start_trace(operation_name, service_name='cibozer-web')
            if trace_id:
                root_span = next(span for span in tracing.traces[trace_id].spans)
                g.trace_id = trace_id
                g.span_id = root_span.span_id
        else:
            # Continue existing trace
            span_id = tracing.start_span(operation_name, trace_id, parent_span_id)
            g.trace_id = trace_id
            g.span_id = span_id
        
        if hasattr(g, 'span_id'):
            # Add request tags
            tracing.add_span_tag(g.span_id, 'http.method', request.method)
            tracing.add_span_tag(g.span_id, 'http.url', request.url)
            tracing.add_span_tag(g.span_id, 'http.user_agent', request.headers.get('User-Agent', ''))
            tracing.add_span_tag(g.span_id, 'http.remote_addr', request.remote_addr)
    
    @app.after_request
    def end_request_trace(response):
        if hasattr(g, 'span_id'):
            tracing = get_tracing_service()
            
            # Add response tags
            tracing.add_span_tag(g.span_id, 'http.status_code', response.status_code)
            tracing.add_span_tag(g.span_id, 'http.response_size', len(response.get_data()))
            
            # Determine status
            status = 'ok'
            error_message = None
            
            if response.status_code >= 500:
                status = 'error'
                error_message = f'HTTP {response.status_code} error'
            elif response.status_code >= 400:
                status = 'error'
                error_message = f'HTTP {response.status_code} client error'
            
            tracing.finish_span(g.span_id, status=status, error_message=error_message)
            
            # If this is the root span, finish the trace
            if hasattr(g, 'trace_id') and g.trace_id in tracing.traces:
                trace = tracing.traces[g.trace_id]
                if len([s for s in trace.spans if s.end_time is None]) == 0:
                    tracing.finish_trace(g.trace_id)
        
        return response


# Decorators for tracing
def trace_function(operation_name: str = None, tags: Dict[str, Any] = None):
    """Decorator to trace function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracing = get_tracing_service()
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            trace_id = getattr(g, 'trace_id', None)
            parent_span_id = getattr(g, 'span_id', None)
            
            if not trace_id:
                # Start new trace if not in request context
                trace_id = tracing.start_trace(op_name, service_name='cibozer-function')
                span_id = next(span.span_id for span in tracing.traces[trace_id].spans)
                is_root = True
            else:
                span_id = tracing.start_span(op_name, trace_id, parent_span_id, tags)
                is_root = False
            
            if span_id:
                try:
                    result = func(*args, **kwargs)
                    tracing.finish_span(span_id, status='ok')
                    
                    if is_root:
                        tracing.finish_trace(trace_id)
                    
                    return result
                    
                except Exception as e:
                    tracing.add_span_log(span_id, f"Exception: {str(e)}", level='error')
                    tracing.finish_span(span_id, status='error', error_message=str(e))
                    
                    if is_root:
                        tracing.finish_trace(trace_id)
                    
                    raise
            else:
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


@contextmanager
def trace_context(operation_name: str, tags: Dict[str, Any] = None):
    """Context manager for tracing code blocks"""
    tracing = get_tracing_service()
    
    trace_id = getattr(g, 'trace_id', None)
    parent_span_id = getattr(g, 'span_id', None)
    
    if not trace_id:
        trace_id = tracing.start_trace(operation_name, service_name='cibozer-context')
        span_id = next(span.span_id for span in tracing.traces[trace_id].spans)
        is_root = True
    else:
        span_id = tracing.start_span(operation_name, trace_id, parent_span_id, tags)
        is_root = False
    
    try:
        yield span_id
        tracing.finish_span(span_id, status='ok')
        
        if is_root:
            tracing.finish_trace(trace_id)
            
    except Exception as e:
        if span_id:
            tracing.add_span_log(span_id, f"Exception: {str(e)}", level='error')
            tracing.finish_span(span_id, status='error', error_message=str(e))
        
        if is_root:
            tracing.finish_trace(trace_id)
        
        raise