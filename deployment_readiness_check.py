#!/usr/bin/env python
"""
Deployment Readiness Check for Cibozer
Final verification before production deployment
"""
import sys
import os
import json
import subprocess
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

def deployment_readiness_check():
    """Comprehensive deployment readiness verification"""
    print("=== CIBOZER DEPLOYMENT READINESS CHECK ===")
    print(f"Check time: {datetime.now()}")
    print()
    
    readiness_results = {
        "timestamp": datetime.now().isoformat(),
        "overall_ready": False,
        "categories": {}
    }
    
    # 1. Environment Configuration
    env_ready = check_environment_configuration()
    readiness_results["categories"]["environment"] = env_ready
    
    # 2. Database Readiness
    db_ready = check_database_readiness()
    readiness_results["categories"]["database"] = db_ready
    
    # 3. Application Functionality  
    app_ready = check_application_functionality()
    readiness_results["categories"]["application"] = app_ready
    
    # 4. Security Readiness
    security_ready = check_security_readiness()
    readiness_results["categories"]["security"] = security_ready
    
    # 5. Performance Readiness
    performance_ready = check_performance_readiness()
    readiness_results["categories"]["performance"] = performance_ready
    
    # 6. Deployment Infrastructure
    infra_ready = check_deployment_infrastructure()
    readiness_results["categories"]["infrastructure"] = infra_ready
    
    # Calculate overall readiness
    all_ready = all(cat["ready"] for cat in readiness_results["categories"].values())
    readiness_results["overall_ready"] = all_ready
    
    # Print summary
    print("\n=== DEPLOYMENT READINESS SUMMARY ===")
    
    for category, results in readiness_results["categories"].items():
        status = "🟢 READY" if results["ready"] else "🔴 NOT READY"
        print(f"{category.replace('_', ' ').title()}: {status}")
        if not results["ready"] and results.get("blockers"):
            for blocker in results["blockers"]:
                print(f"  ❌ {blocker}")
        if results.get("warnings"):
            for warning in results["warnings"]:
                print(f"  ⚠️  {warning}")
    
    overall_status = "🟢 READY FOR DEPLOYMENT" if all_ready else "🔴 NOT READY FOR DEPLOYMENT"
    print(f"\nOverall Status: {overall_status}")
    
    if all_ready:
        print("\n🎉 Cibozer is ready for production deployment!")
        print("Next steps:")
        print("1. Set up production environment variables")
        print("2. Configure production database")
        print("3. Set up domain and SSL certificate")
        print("4. Deploy to your chosen platform")
        print("5. Run post-deployment verification")
    else:
        print("\n⚠️  Please address the blockers above before deployment.")
    
    return readiness_results

def check_environment_configuration():
    """Check environment configuration readiness"""
    print("1. Environment Configuration Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        # Check .env file
        if not os.path.exists('.env'):
            blockers.append(".env file missing")
            ready = False
        else:
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Required environment variables
            required_vars = ['SECRET_KEY', 'ADMIN_USERNAME', 'ADMIN_PASSWORD']
            for var in required_vars:
                if f'{var}=' not in env_content:
                    blockers.append(f"Required environment variable {var} missing")
                    ready = False
            
            # Check SECRET_KEY strength
            if 'SECRET_KEY=' in env_content:
                secret_line = [line for line in env_content.split('\n') if line.startswith('SECRET_KEY=')]
                if secret_line:
                    secret_key = secret_line[0].split('=', 1)[1]
                    if len(secret_key) < 32:
                        warnings.append("SECRET_KEY should be at least 32 characters for production")
            
            # Check debug mode
            if 'DEBUG=True' in env_content or 'DEBUG=true' in env_content:
                blockers.append("Debug mode is enabled - must be disabled for production")
                ready = False
            
            # Check Stripe configuration
            stripe_keys = ['STRIPE_SECRET_KEY', 'STRIPE_PUBLISHABLE_KEY']
            stripe_configured = any(f'{key}=' in env_content and not line.startswith('#') 
                                  for line in env_content.split('\n') 
                                  for key in stripe_keys if f'{key}=' in line)
            
            if not stripe_configured:
                warnings.append("Stripe payment processing not configured")
        
        # Check config files
        config_files = ['config/production.py', 'config/development.py']
        config_exists = any(os.path.exists(f) for f in config_files)
        
        if not config_exists:
            blockers.append("Configuration files missing")
            ready = False
        
        print(f"   {'✓' if ready else '✗'} Environment configuration {'ready' if ready else 'has issues'}")
    
    except Exception as e:
        blockers.append(f"Environment check error: {str(e)}")
        ready = False
        print(f"   ✗ Environment check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

def check_database_readiness():
    """Check database readiness"""
    print("\n2. Database Readiness Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        from app import create_app
        from app.extensions import db
        from sqlalchemy import text
        
        # Use the proper environment configuration
        import os
        env = os.environ.get('FLASK_ENV', 'development')
        from config import get_config
        config_class = get_config()
        app = create_app(config_class)
        with app.app_context():
            # Test database connection
            try:
                db.session.execute(text('SELECT 1')).scalar()
                print("   ✓ Database connection successful")
            except Exception as e:
                blockers.append(f"Database connection failed: {str(e)}")
                ready = False
                print(f"   ✗ Database connection failed: {e}")
                return {"ready": ready, "blockers": blockers, "warnings": warnings}
            
            # Check tables exist
            required_tables = ['users', 'usage_logs', 'payments', 'saved_meal_plans']
            for table in required_tables:
                try:
                    # Validate table name against whitelist to prevent SQL injection
                    if table not in ['users', 'usage_logs', 'payments', 'saved_meal_plans']:
                        blockers.append(f"Table '{table}' not in allowed list")
                        ready = False
                        continue
                    count = db.session.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
                    print(f"   ✓ Table '{table}' exists with {count} records")
                except Exception as e:
                    blockers.append(f"Table '{table}' missing or inaccessible")
                    ready = False
            
            # Check for admin user (if needed)
            try:
                from app.models.user import User
                admin_count = User.query.filter_by(subscription_tier='premium').count()
                if admin_count == 0:
                    warnings.append("No admin users found - consider creating one")
                else:
                    print(f"   ✓ Found {admin_count} admin user(s)")
            except Exception as e:
                warnings.append(f"Could not check admin users: {str(e)}")
    
    except Exception as e:
        blockers.append(f"Database check error: {str(e)}")
        ready = False
        print(f"   ✗ Database check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

def check_application_functionality():
    """Check core application functionality"""
    print("\n3. Application Functionality Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        from app import create_app
        
        # Test app creation
        try:
            app = create_app()
            print("   ✓ Flask application creates successfully")
        except Exception as e:
            blockers.append(f"Flask app creation failed: {str(e)}")
            ready = False
            return {"ready": ready, "blockers": blockers, "warnings": warnings}
        
        with app.app_context():
            # Test meal optimization
            try:
                import meal_optimizer as mo
                optimizer = mo.MealPlanOptimizer(skip_validation=True)
                test_preferences = {
                    'diet': 'standard',
                    'calories': 2000,
                    'pattern': 'standard',
                    'restrictions': [],
                    'cuisines': ['all'],
                    'cooking_methods': ['all'],
                    'measurement_system': 'US',
                    'allow_substitutions': True,
                    'timestamp': datetime.now().isoformat()
                }
                day_meals, metrics = optimizer.generate_single_day_plan(test_preferences)
                if day_meals and len(day_meals) > 0:
                    print("   ✓ Meal plan generation working")
                else:
                    blockers.append("Meal plan generation returned empty results")
                    ready = False
            except Exception as e:
                blockers.append(f"Meal plan generation failed: {str(e)}")
                ready = False
            
            # Test PDF generation
            try:
                from pdf_generator import PDFGenerator
                pdf_gen = PDFGenerator()
                print("   ✓ PDF generator imports successfully")
            except Exception as e:
                warnings.append(f"PDF generation may have issues: {str(e)}")
            
            # Test video generation
            try:
                from video_service import VideoService
                video_service = VideoService(upload_enabled=False)
                print("   ✓ Video service imports successfully")
            except Exception as e:
                warnings.append(f"Video generation may have issues: {str(e)}")
            
            # Test routes
            try:
                client = app.test_client()
                
                # Test main page
                response = client.get('/')
                if response.status_code == 200:
                    print("   ✓ Main page accessible")
                else:
                    warnings.append(f"Main page returned status {response.status_code}")
                
                # Test auth pages
                response = client.get('/auth/login')
                if response.status_code == 200:
                    print("   ✓ Auth routes accessible")
                else:
                    warnings.append(f"Auth routes returned status {response.status_code}")
                
                # Test admin login page
                response = client.get('/admin/login')
                if response.status_code == 200:
                    print("   ✓ Admin routes accessible")
                else:
                    warnings.append(f"Admin routes returned status {response.status_code}")
                
            except Exception as e:
                warnings.append(f"Route testing failed: {str(e)}")
    
    except Exception as e:
        blockers.append(f"Application functionality check error: {str(e)}")
        ready = False
        print(f"   ✗ Application check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

def check_security_readiness():
    """Check security readiness based on previous audit"""
    print("\n4. Security Readiness Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        # Check if security audit was run
        if os.path.exists('security_audit_results.json'):
            with open('security_audit_results.json', 'r') as f:
                security_results = json.load(f)
            
            overall_score = security_results.get("overall_score", 0)
            max_score = security_results.get("max_score", 100)
            security_percentage = overall_score / max_score * 100 if max_score > 0 else 0
            
            print(f"   📊 Security audit score: {security_percentage:.1f}%")
            
            if security_percentage >= 70:
                print("   ✓ Security audit passed")
            else:
                blockers.append(f"Security audit score too low: {security_percentage:.1f}%")
                ready = False
            
            # Check for critical security issues
            for category, results in security_results.get("categories", {}).items():
                category_score = results.get("score", 0)
                category_max = results.get("max_score", 1)
                category_pct = category_score / category_max * 100 if category_max > 0 else 0
                
                if category_pct < 50:  # Critical threshold
                    blockers.append(f"Critical security issue in {category}: {category_pct:.1f}%")
                    ready = False
                elif category_pct < 70:  # Warning threshold
                    warnings.append(f"Security concern in {category}: {category_pct:.1f}%")
        else:
            warnings.append("Security audit not found - run security_audit.py")
        
        # Basic security file checks
        required_security_files = ['.gitignore']
        for file in required_security_files:
            if not os.path.exists(file):
                warnings.append(f"Security file missing: {file}")
    
    except Exception as e:
        warnings.append(f"Security check error: {str(e)}")
        print(f"   ⚠️ Security check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

def check_performance_readiness():
    """Check performance readiness"""
    print("\n5. Performance Readiness Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        # Check static files
        static_dirs = ['static/css', 'static/js']
        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                files = os.listdir(static_dir)
                if files:
                    print(f"   ✓ {static_dir} has {len(files)} files")
                else:
                    warnings.append(f"{static_dir} is empty")
            else:
                warnings.append(f"{static_dir} directory missing")
        
        # Check templates
        if os.path.exists('templates'):
            template_files = []
            for root, dirs, files in os.walk('templates'):
                template_files.extend([f for f in files if f.endswith('.html')])
            
            if len(template_files) >= 5:  # Should have at least basic templates
                print(f"   ✓ Found {len(template_files)} template files")
            else:
                warnings.append(f"Only {len(template_files)} template files found")
        else:
            blockers.append("Templates directory missing")
            ready = False
        
        # Check for production optimizations
        wsgi_files = ['wsgi.py', 'app.py']
        wsgi_exists = any(os.path.exists(f) for f in wsgi_files)
        
        if wsgi_exists:
            print("   ✓ WSGI entry point exists")
        else:
            warnings.append("WSGI entry point missing - may affect production deployment")
        
        # Check requirements.txt
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            production_packages = ['gunicorn', 'uwsgi', 'waitress']
            has_prod_server = any(pkg in requirements.lower() for pkg in production_packages)
            
            if has_prod_server:
                print("   ✓ Production server package found")
            else:
                warnings.append("No production WSGI server found in requirements")
        else:
            blockers.append("requirements.txt missing")
            ready = False
    
    except Exception as e:
        warnings.append(f"Performance check error: {str(e)}")
        print(f"   ⚠️ Performance check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

def check_deployment_infrastructure():
    """Check deployment infrastructure readiness"""
    print("\n6. Deployment Infrastructure Check...")
    ready = True
    blockers = []
    warnings = []
    
    try:
        # Check for deployment configuration files
        deployment_configs = [
            'Procfile',        # Heroku
            'railway.json',    # Railway
            'vercel.json',     # Vercel
            'render.yaml',     # Render
            'Dockerfile',      # Docker
            'docker-compose.yml'  # Docker Compose
        ]
        
        found_configs = [f for f in deployment_configs if os.path.exists(f)]
        
        if found_configs:
            print(f"   ✓ Found deployment configs: {', '.join(found_configs)}")
        else:
            warnings.append("No deployment configuration files found")
        
        # Check runtime specifications
        runtime_files = ['runtime.txt', 'python_version.txt']
        runtime_specified = any(os.path.exists(f) for f in runtime_files)
        
        if runtime_specified:
            print("   ✓ Python runtime specified")
        else:
            warnings.append("Python runtime version not specified")
        
        # Check for migrations
        if os.path.exists('migrations'):
            print("   ✓ Database migrations available")
        else:
            warnings.append("Database migrations not set up")
        
        # Check for environment separation
        config_files = os.listdir('config') if os.path.exists('config') else []
        env_configs = [f for f in config_files if 'production' in f or 'development' in f]
        
        if len(env_configs) >= 2:
            print("   ✓ Environment-specific configurations found")
        else:
            warnings.append("Environment-specific configurations missing")
        
        # Check for health check endpoint
        try:
            with open('app/routes/main.py', 'r') as f:
                main_routes = f.read()
            
            if '/health' in main_routes or '/status' in main_routes:
                print("   ✓ Health check endpoint found")
            else:
                warnings.append("Health check endpoint not found")
        except:
            warnings.append("Could not check for health endpoint")
        
        # Check for logging setup
        log_setup = os.path.exists('logs') or any('logging' in f.lower() for f in os.listdir('.') if f.endswith('.py'))
        
        if log_setup:
            print("   ✓ Logging configuration found")
        else:
            warnings.append("Logging not configured")
    
    except Exception as e:
        warnings.append(f"Infrastructure check error: {str(e)}")
        print(f"   ⚠️ Infrastructure check failed: {e}")
    
    return {"ready": ready, "blockers": blockers, "warnings": warnings}

if __name__ == '__main__':
    results = deployment_readiness_check()
    
    # Save results
    with open('deployment_readiness_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Deployment readiness check complete. Results saved to deployment_readiness_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_ready"] else 1)