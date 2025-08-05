#!/usr/bin/env python3
"""
Comprehensive health check script for Cibozer
Used for container health checks and monitoring
"""

import sys
import json
import time
from datetime import datetime

try:
    from app import create_app
    from app.extensions import db
    from app.models import User
    import redis
    import requests
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

class HealthChecker:
    def __init__(self):
        self.app = create_app()
        self.checks = []
        self.start_time = time.time()
        
    def check_database(self):
        """Check database connectivity and basic operations"""
        try:
            with self.app.app_context():
                # Test connection
                db.session.execute('SELECT 1')
                
                # Test table access
                user_count = User.query.count()
                
                self.checks.append({
                    'name': 'database',
                    'status': 'healthy',
                    'details': f'Connected, {user_count} users',
                    'duration_ms': round((time.time() - self.start_time) * 1000)
                })
                return True
        except Exception as e:
            self.checks.append({
                'name': 'database',
                'status': 'unhealthy',
                'error': str(e),
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return False
    
    def check_redis(self):
        """Check Redis connectivity"""
        try:
            r = redis.from_url(self.app.config.get('REDIS_URL', 'redis://localhost:6379'))
            r.ping()
            
            # Test basic operations
            test_key = 'health_check_test'
            r.set(test_key, 'ok', ex=10)
            value = r.get(test_key)
            
            self.checks.append({
                'name': 'redis',
                'status': 'healthy',
                'details': 'Connected and operational',
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return True
        except Exception as e:
            self.checks.append({
                'name': 'redis',
                'status': 'unhealthy',
                'error': str(e),
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return False
    
    def check_filesystem(self):
        """Check filesystem access for uploads"""
        try:
            import os
            
            # Check required directories exist and are writable
            directories = ['logs', 'static/uploads', 'static/pdfs', 'static/videos']
            
            for directory in directories:
                path = os.path.join(self.app.root_path, '..', directory)
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                
                # Test write access
                test_file = os.path.join(path, '.health_check')
                with open(test_file, 'w') as f:
                    f.write('ok')
                os.remove(test_file)
            
            self.checks.append({
                'name': 'filesystem',
                'status': 'healthy',
                'details': 'All directories accessible',
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return True
        except Exception as e:
            self.checks.append({
                'name': 'filesystem',
                'status': 'unhealthy',
                'error': str(e),
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return False
    
    def check_external_services(self):
        """Check external service connectivity"""
        services = []
        
        # Check Stripe API
        if self.app.config.get('STRIPE_SECRET_KEY'):
            try:
                import stripe
                stripe.api_key = self.app.config['STRIPE_SECRET_KEY']
                # Use a lightweight API call
                stripe.Balance.retrieve()
                services.append({'name': 'stripe', 'status': 'healthy'})
            except Exception as e:
                services.append({'name': 'stripe', 'status': 'unhealthy', 'error': str(e)})
        
        # Check email service
        if self.app.config.get('MAIL_SERVER'):
            try:
                import smtplib
                server = smtplib.SMTP(
                    self.app.config['MAIL_SERVER'],
                    self.app.config.get('MAIL_PORT', 587)
                )
                server.quit()
                services.append({'name': 'email', 'status': 'healthy'})
            except Exception as e:
                services.append({'name': 'email', 'status': 'unhealthy', 'error': str(e)})
        
        self.checks.append({
            'name': 'external_services',
            'status': 'healthy' if all(s['status'] == 'healthy' for s in services) else 'degraded',
            'services': services,
            'duration_ms': round((time.time() - self.start_time) * 1000)
        })
        
        return True
    
    def check_application(self):
        """Check application responsiveness"""
        try:
            with self.app.app_context():
                # Test route handling
                with self.app.test_client() as client:
                    response = client.get('/api/health')
                    
                    if response.status_code == 200:
                        self.checks.append({
                            'name': 'application',
                            'status': 'healthy',
                            'details': 'Routes responding',
                            'duration_ms': round((time.time() - self.start_time) * 1000)
                        })
                        return True
                    else:
                        raise Exception(f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.checks.append({
                'name': 'application',
                'status': 'unhealthy',
                'error': str(e),
                'duration_ms': round((time.time() - self.start_time) * 1000)
            })
            return False
    
    def run_all_checks(self):
        """Run all health checks"""
        # Run checks in order of importance
        db_healthy = self.check_database()
        redis_healthy = self.check_redis()
        fs_healthy = self.check_filesystem()
        app_healthy = self.check_application()
        self.check_external_services()
        
        # Determine overall health
        critical_checks = [db_healthy, app_healthy]
        if all(critical_checks):
            if redis_healthy and fs_healthy:
                overall_status = 'healthy'
            else:
                overall_status = 'degraded'
        else:
            overall_status = 'unhealthy'
        
        total_duration = round((time.time() - self.start_time) * 1000)
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': total_duration,
            'checks': self.checks,
            'version': '1.0.0',
            'environment': self.app.config.get('ENV', 'unknown')
        }

def main():
    """Run health check and output results"""
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    # Output JSON results
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results['status'] == 'healthy':
        sys.exit(0)
    elif results['status'] == 'degraded':
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == '__main__':
    main()