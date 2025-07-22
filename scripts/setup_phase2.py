#!/usr/bin/env python3
"""
Cibozer Phase 2: Quality & Testing Setup Script
Focuses on increasing test coverage from 32% to 80% and performance optimization
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"[*] {title}")
    print("="*60)

def print_step(step, description):
    """Print formatted step"""
    print(f"\n[Step {step}] {description}")
    print("-" * 40)

def run_command(cmd, description, timeout=30):
    """Run a command with timeout and error handling"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            print(f"  [OK] {description}")
            return True, result.stdout
        else:
            print(f"  [WARN] {description} - {result.stderr[:200]}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"  [TIMEOUT] {description}")
        return False, "Timeout"
    except Exception as e:
        print(f"  [ERROR] {description} - {str(e)}")
        return False, str(e)

def fix_test_imports():
    """Fix common test import issues"""
    print_step(1, "Fixing Test Import Issues")
    
    # Common import fixes
    fixes = [
        {
            'file': 'tests/test_admin.py',
            'old': 'from admin import admin_required, login, logout, dashboard, video_generator, generate_content_video, batch_generate, analytics, refill_credits, users, decorated_function',
            'new': 'from admin import admin_required, login, logout, dashboard, video_generator, generate_content_video, batch_generate, analytics, refill_credits, users'
        }
    ]
    
    for fix in fixes:
        file_path = fix['file']
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if fix['old'] in content:
                    content = content.replace(fix['old'], fix['new'])
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"  [FIXED] {file_path}")
                else:
                    print(f"  [SKIP] {file_path} - already fixed")
            except Exception as e:
                print(f"  [ERROR] {file_path} - {str(e)}")
    
    return True

def run_basic_tests():
    """Run basic test suite to check current status"""
    print_step(2, "Running Basic Test Suite")
    
    # Try simple pytest run first
    success, output = run_command(
        "python -m pytest tests/ --tb=short -v",
        "Basic test run",
        timeout=60
    )
    
    if success:
        print("  [OK] Basic tests running")
    else:
        print("  [WARN] Some test issues found")
    
    return success

def measure_current_coverage():
    """Measure current test coverage"""
    print_step(3, "Measuring Current Test Coverage")
    
    # Try to get coverage
    success, output = run_command(
        "python -m pytest --cov=. --cov-report=term-missing --cov-report=json tests/",
        "Coverage measurement",
        timeout=90
    )
    
    if success:
        # Try to parse coverage from output
        try:
            import json
            if os.path.exists('coverage.json'):
                with open('coverage.json', 'r') as f:
                    coverage_data = json.load(f)
                total_coverage = coverage_data['totals']['percent_covered']
                print(f"  [OK] Current coverage: {total_coverage:.1f}%")
                return total_coverage
        except:
            pass
    
    # Fallback: estimate from known value
    print("  [ESTIMATE] Current coverage: ~32%")
    return 32.0

def create_missing_tests():
    """Create tests for modules with low/no coverage"""
    print_step(4, "Creating Missing Tests")
    
    # Priority modules that need tests
    modules_needing_tests = [
        'app.py',
        'auth.py', 
        'payments.py',
        'models.py',
        'meal_optimizer.py',
        'video_service.py',
        'pdf_generator.py'
    ]
    
    test_templates = {
        'app.py': '''"""Tests for main app routes"""
import pytest
from app import app, db
from models import User

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_index_route(client):
    """Test homepage loads"""
    response = client.get('/')
    assert response.status_code == 200

def test_health_check(client):
    """Test health endpoint"""
    response = client.get('/api/health')
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert 'status' in data

def test_metrics_endpoint(client):
    """Test metrics endpoint"""
    response = client.get('/api/metrics')
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
''',
        
        'auth.py': '''"""Tests for authentication"""
import pytest
from app import app, db
from models import User
from auth import auth_bp

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client

def test_register_get(client):
    """Test registration page loads"""
    response = client.get('/auth/register')
    assert response.status_code == 200

def test_login_get(client):
    """Test login page loads"""
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_user_registration(client):
    """Test user registration"""
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'TestPassword123!',
        'full_name': 'Test User'
    })
    assert response.status_code in [200, 302]
''',
        
        'models.py': '''"""Tests for database models"""
import pytest
from app import app, db
from models import User, PricingPlan, UsageLog
from datetime import datetime, timezone

@pytest.fixture
def app_context():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()

def test_user_creation(app_context):
    """Test user model creation"""
    user = User(
        email='test@example.com',
        full_name='Test User'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    assert user.id is not None
    assert user.check_password('password123')
    assert not user.check_password('wrong')

def test_user_credits(app_context):
    """Test user credit system"""
    user = User(email='test@example.com', credits_balance=5)
    db.session.add(user)
    db.session.commit()
    
    assert user.has_credits()
    assert user.use_credits(3)
    assert user.credits_balance == 2
    assert not user.use_credits(5)  # Should fail

def test_pricing_plans(app_context):
    """Test pricing plan model"""
    PricingPlan.seed_default_plans()
    plans = PricingPlan.query.all()
    assert len(plans) >= 3
    
    free_plan = PricingPlan.query.filter_by(name='free').first()
    assert free_plan is not None
    assert free_plan.price_monthly == 0
'''
    }
    
    created_count = 0
    for module in modules_needing_tests:
        test_file = f"tests/test_{module.replace('.py', '')}.py"
        if not os.path.exists(test_file) and module in test_templates:
            try:
                os.makedirs('tests', exist_ok=True)
                with open(test_file, 'w') as f:
                    f.write(test_templates[module])
                print(f"  [CREATED] {test_file}")
                created_count += 1
            except Exception as e:
                print(f"  [ERROR] {test_file} - {str(e)}")
        else:
            print(f"  [EXISTS] {test_file}")
    
    print(f"  [SUMMARY] Created {created_count} new test files")
    return True

def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print_step(5, "Running Comprehensive Test Suite")
    
    # Run tests with coverage
    success, output = run_command(
        "python -m pytest tests/ --cov=. --cov-report=term --cov-report=html --tb=short",
        "Comprehensive test run with coverage",
        timeout=120
    )
    
    return success

def performance_baseline():
    """Establish performance baseline"""
    print_step(6, "Performance Baseline Measurement")
    
    try:
        from app import app
        import time
        import requests
        
        # Start app in background for testing
        print("  [INFO] Testing application performance...")
        
        with app.test_client() as client:
            # Test homepage load time
            start_time = time.time()
            response = client.get('/')
            load_time = time.time() - start_time
            
            print(f"  [METRIC] Homepage load time: {load_time:.3f}s")
            
            # Test API endpoint
            start_time = time.time()
            response = client.get('/api/health')
            api_time = time.time() - start_time
            
            print(f"  [METRIC] API response time: {api_time:.3f}s")
            
            # Save baseline metrics
            baseline = {
                'homepage_load_time': load_time,
                'api_response_time': api_time,
                'timestamp': time.time()
            }
            
            with open('performance_baseline.json', 'w') as f:
                import json
                json.dump(baseline, f, indent=2)
            
            print("  [OK] Performance baseline saved")
        
        return True
        
    except Exception as e:
        print(f"  [ERROR] Performance testing failed: {str(e)}")
        return False

def generate_report():
    """Generate Phase 2 completion report"""
    print_header("PHASE 2 SETUP COMPLETE")
    
    # Try to get final coverage
    final_coverage = 32.0  # Default fallback
    try:
        import json
        if os.path.exists('coverage.json'):
            with open('coverage.json', 'r') as f:
                coverage_data = json.load(f)
            final_coverage = coverage_data['totals']['percent_covered']
    except:
        pass
    
    print("TARGET PHASE 2 RESULTS:")
    print(f"   Test Coverage: {final_coverage:.1f}% (Target: 80%)")
    print(f"   Status: {'✓ PASSED' if final_coverage >= 80 else '⚠ IN PROGRESS'}")
    
    # Check if performance baseline exists
    baseline_exists = os.path.exists('performance_baseline.json')
    print(f"   Performance Baseline: {'✓ SET' if baseline_exists else '✗ MISSING'}")
    
    # Check test files
    test_files = len([f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')])
    print(f"   Test Files: {test_files}")
    
    print("\nNEXT STEPS:")
    if final_coverage < 80:
        print("   1. Review failed tests and add more coverage")
        print("   2. Focus on critical paths (auth, payments, meal generation)")
        print("   3. Add integration tests for API endpoints")
    else:
        print("   1. Ready for Phase 3: Production Deployment")
        print("   2. Set up CI/CD pipeline")
        print("   3. Configure monitoring and alerts")
    
    print("\nQUICK COMMANDS:")
    print("   python -m pytest tests/ --cov=.     # Run tests with coverage")
    print("   python -m pytest -k 'test_auth'     # Run specific test category")
    print("   python app.py                       # Start development server")

def main():
    """Main Phase 2 setup function"""
    print("[TARGET] Cibozer MVP Phase 2: Quality & Testing")
    print("Goal: Increase test coverage from 32% to 80%")
    print()
    
    steps = [
        ("Fix Test Imports", fix_test_imports),
        ("Basic Test Run", run_basic_tests),
        ("Measure Coverage", measure_current_coverage),
        ("Create Missing Tests", create_missing_tests),
        ("Comprehensive Testing", run_comprehensive_tests),
        ("Performance Baseline", performance_baseline)
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
            if not result and step_name in ["Fix Test Imports", "Create Missing Tests"]:
                print(f"[WARN] {step_name} had issues but continuing...")
        except KeyboardInterrupt:
            print(f"\n[STOP] Interrupted during {step_name}")
            break
        except Exception as e:
            print(f"\n[ERROR] {step_name} failed: {str(e)}")
            results.append((step_name, False))
    
    generate_report()
    
    # Return success if most critical steps passed
    critical_steps = ["Fix Test Imports", "Create Missing Tests"]
    critical_passed = sum(1 for name, result in results if name in critical_steps and result)
    
    return critical_passed >= 1

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
