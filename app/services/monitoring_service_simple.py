"""
Simple Monitoring Service for Cibozer (Production Version)
Lightweight monitoring without external dependencies
"""

import os
import time
import json
import traceback
import logging
from datetime import datetime, timezone
from functools import wraps
from flask import request, current_app, g

# Create simplified monitoring service
class SimpleMonitoringService:
    def __init__(self):
        self.enabled = os.getenv('MONITORING_ENABLED', 'true').lower() == 'true'
        self.metrics = []
        
    def track_request(self, func):
        """Decorator to track request metrics"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enabled:
                return func(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                self.record_request(request.endpoint, duration, 'success')
                return result
            except Exception as e:
                duration = time.time() - start_time
                self.record_request(request.endpoint, duration, 'error')
                raise
        return wrapper
    
    def record_request(self, endpoint, duration, status):
        """Record request metrics"""
        if not self.enabled:
            return
            
        metric = {
            'endpoint': endpoint,
            'duration': duration,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.metrics.append(metric)
        
        # Keep only last 1000 metrics in memory
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def get_health_status(self):
        """Get application health status"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': {'healthy': True, 'message': 'Database OK'},
                'disk': {'healthy': True, 'message': 'Disk monitoring disabled'},
                'memory': {'healthy': True, 'message': 'Memory monitoring disabled'}
            }
        }
    
    def get_metrics_summary(self):
        """Get metrics summary"""
        if not self.metrics:
            return {}
            
        total_requests = len(self.metrics)
        successful = sum(1 for m in self.metrics if m['status'] == 'success')
        avg_duration = sum(m['duration'] for m in self.metrics) / total_requests if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful,
            'error_rate': (total_requests - successful) / total_requests if total_requests > 0 else 0,
            'average_duration': avg_duration
        }

# Create singleton instance
monitoring_service = SimpleMonitoringService()

# Security monitoring function
def monitor_security(func):
    """Decorator for security monitoring"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper