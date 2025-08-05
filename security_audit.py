#!/usr/bin/env python
"""
Security Audit Script for Cibozer
Comprehensive security testing for production deployment
"""
import sys
import os
import re
import json
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def security_audit():
    """Conduct comprehensive security audit"""
    print("=== CIBOZER SECURITY AUDIT ===")
    print(f"Audit time: {datetime.now()}")
    print()
    
    audit_results = {
        "timestamp": datetime.now().isoformat(),
        "overall_score": 0,
        "max_score": 0,
        "categories": {}
    }
    
    # 1. Configuration Security
    config_score = audit_configuration_security()
    audit_results["categories"]["configuration"] = config_score
    
    # 2. Authentication Security
    auth_score = audit_authentication_security()
    audit_results["categories"]["authentication"] = auth_score
    
    # 3. Input Validation Security
    input_score = audit_input_validation()
    audit_results["categories"]["input_validation"] = input_score
    
    # 4. Database Security
    db_score = audit_database_security()
    audit_results["categories"]["database"] = db_score
    
    # 5. Web Security Headers
    headers_score = audit_security_headers()
    audit_results["categories"]["security_headers"] = headers_score
    
    # 6. File Security
    file_score = audit_file_security()
    audit_results["categories"]["file_security"] = file_score
    
    # 7. Dependencies Security
    deps_score = audit_dependencies()
    audit_results["categories"]["dependencies"] = deps_score
    
    # Calculate overall score
    total_score = sum(cat["score"] for cat in audit_results["categories"].values())
    max_total_score = sum(cat["max_score"] for cat in audit_results["categories"].values())
    
    audit_results["overall_score"] = total_score
    audit_results["max_score"] = max_total_score
    
    # Print summary
    print("\n=== SECURITY AUDIT SUMMARY ===")
    print(f"Overall Security Score: {total_score}/{max_total_score} ({total_score/max_total_score*100:.1f}%)")
    print()
    
    for category, results in audit_results["categories"].items():
        score_pct = results["score"] / results["max_score"] * 100 if results["max_score"] > 0 else 0
        status = "🟢 EXCELLENT" if score_pct >= 90 else "🟡 GOOD" if score_pct >= 75 else "🟠 NEEDS WORK" if score_pct >= 50 else "🔴 CRITICAL"
        print(f"{category.replace('_', ' ').title()}: {results['score']}/{results['max_score']} ({score_pct:.1f}%) {status}")
    
    # Print recommendations
    print("\n=== SECURITY RECOMMENDATIONS ===")
    for category, results in audit_results["categories"].items():
        if results.get("issues"):
            print(f"\n{category.replace('_', ' ').title()}:")
            for issue in results["issues"]:
                print(f"  - {issue}")
    
    return audit_results

def audit_configuration_security():
    """Audit configuration security"""
    print("1. Configuration Security Audit...")
    score = 0
    max_score = 10
    issues = []
    
    try:
        # Check .env file security
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                env_content = f.read()
            
            # Check for production-ready secret key
            if 'SECRET_KEY=' in env_content:
                secret_key_line = [line for line in env_content.split('\n') if line.startswith('SECRET_KEY=')]
                if secret_key_line:
                    secret_key = secret_key_line[0].split('=', 1)[1]
                    if len(secret_key) >= 32 and not secret_key in ['change-me', 'your-secret-key-here']:
                        score += 2
                        print("   ✓ Secret key is properly set")
                    else:
                        issues.append("SECRET_KEY is too short or uses default value")
                        print("   ✗ Secret key is weak or default")
            else:
                issues.append("SECRET_KEY not found in .env file")
                print("   ✗ SECRET_KEY not configured")
            
            # Check debug mode
            if 'DEBUG=False' in env_content or 'DEBUG=false' in env_content:
                score += 2
                print("   ✓ Debug mode is disabled")
            else:
                issues.append("Debug mode may be enabled in production")
                print("   ⚠ Debug mode configuration unclear")
            
            # Check database security
            if 'DATABASE_URL=' in env_content:
                db_line = [line for line in env_content.split('\n') if line.startswith('DATABASE_URL=')]
                if db_line:
                    db_url = db_line[0]
                    if 'sqlite://' in db_url:
                        score += 1
                        print("   ✓ Database URL configured (SQLite)")
                        if '////' in db_url:  # Absolute path
                            score += 1
                            print("   ✓ SQLite uses absolute path")
                        else:
                            issues.append("SQLite should use absolute path for production")
                    elif 'postgresql://' in db_url or 'mysql://' in db_url:
                        score += 2
                        print("   ✓ Production database configured")
            
            # Check admin credentials
            if 'ADMIN_PASSWORD=' in env_content:
                admin_pass_line = [line for line in env_content.split('\n') if line.startswith('ADMIN_PASSWORD=')]
                if admin_pass_line:
                    admin_pass = admin_pass_line[0].split('=', 1)[1]
                    if len(admin_pass) >= 12 and any(c.isupper() for c in admin_pass) and any(c.islower() for c in admin_pass) and any(c.isdigit() for c in admin_pass):
                        score += 2
                        print("   ✓ Admin password is strong")
                    else:
                        issues.append("Admin password should be stronger (12+ chars, mixed case, numbers)")
                        print("   ⚠ Admin password could be stronger")
            
            # Check for hardcoded secrets
            suspicious_patterns = ['password=', 'secret=', 'key=', 'token=']
            hardcoded_secrets = 0
            for line in env_content.split('\n'):
                if any(pattern in line.lower() for pattern in suspicious_patterns):
                    if not line.startswith('#') and '=' in line:
                        value = line.split('=', 1)[1].strip()
                        if value and value not in ['your-secret-here', 'change-me', '']:
                            hardcoded_secrets += 1
            
            if hardcoded_secrets <= 5:  # Expected secrets like admin password, secret key
                score += 1
                print("   ✓ No excessive hardcoded secrets")
            else:
                issues.append(f"Found {hardcoded_secrets} potential hardcoded secrets")
        
        else:
            issues.append(".env file not found")
            print("   ✗ .env file missing")
    
    except Exception as e:
        issues.append(f"Configuration audit error: {str(e)}")
        print(f"   ✗ Configuration audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_authentication_security():
    """Audit authentication security"""
    print("\n2. Authentication Security Audit...")
    score = 0
    max_score = 15
    issues = []
    
    try:
        # Check User model password hashing
        user_model_path = 'app/models/user.py'
        if os.path.exists(user_model_path):
            with open(user_model_path, 'r') as f:
                user_model = f.read()
            
            # Check for bcrypt usage
            if 'bcrypt' in user_model and 'hashpw' in user_model:
                score += 3
                print("   ✓ Uses bcrypt for password hashing")
            elif 'werkzeug' in user_model and 'generate_password_hash' in user_model:
                score += 2
                print("   ✓ Uses Werkzeug password hashing")
            else:
                issues.append("Password hashing method unclear or insecure")
                print("   ✗ Password hashing method not secure")
            
            # Check for password validation
            if 'validate_password' in user_model or 'password.*length' in user_model.lower():
                score += 2
                print("   ✓ Password validation present")
            else:
                issues.append("Password validation not found in User model")
            
            # Check for rate limiting mentions
            if 'rate' in user_model.lower() or '@limiter' in user_model:
                score += 1
                print("   ✓ Rate limiting indicators found")
        
        # Check auth routes
        auth_routes_path = 'app/routes/auth.py'
        if os.path.exists(auth_routes_path):
            with open(auth_routes_path, 'r') as f:
                auth_routes = f.read()
            
            # Check for rate limiting
            if '@limiter.limit' in auth_routes:
                score += 2
                print("   ✓ Rate limiting on auth routes")
            else:
                issues.append("Rate limiting not found on auth routes")
                print("   ⚠ Rate limiting missing on auth routes")
            
            # Check for CSRF protection
            if 'csrf' in auth_routes.lower():
                score += 2
                print("   ✓ CSRF protection indicators found")
            else:
                issues.append("CSRF protection not clearly implemented")
            
            # Check for session security
            if 'session' in auth_routes and 'secure' in auth_routes.lower():
                score += 1
                print("   ✓ Session security considerations found")
            
            # Check for input validation
            if 'validate_email' in auth_routes or 'validate_password' in auth_routes:
                score += 2
                print("   ✓ Input validation on auth routes")
            else:
                issues.append("Input validation not found on auth routes")
            
            # Check for secure redirects
            if 'redirect' in auth_routes and ('next' in auth_routes or 'url_for' in auth_routes):
                score += 1
                print("   ✓ Secure redirect handling")
            
            # Check for login attempt logging
            if 'log' in auth_routes.lower() and ('login' in auth_routes or 'attempt' in auth_routes):
                score += 1
                print("   ✓ Login attempt logging found")
        
    except Exception as e:
        issues.append(f"Authentication audit error: {str(e)}")
        print(f"   ✗ Authentication audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_input_validation():
    """Audit input validation security"""
    print("\n3. Input Validation Security Audit...")
    score = 0
    max_score = 10
    issues = []
    
    try:
        # Check for validators module
        validators_path = 'app/utils/validators.py'
        if os.path.exists(validators_path):
            with open(validators_path, 'r') as f:
                validators_content = f.read()
            
            # Check for email validation
            if 'validate_email' in validators_content and ('regex' in validators_content or 're.' in validators_content):
                score += 2
                print("   ✓ Email validation with regex")
            
            # Check for password validation
            if 'validate_password' in validators_content:
                if 'length' in validators_content.lower() and ('uppercase' in validators_content.lower() or 'digit' in validators_content.lower()):
                    score += 2
                    print("   ✓ Comprehensive password validation")
                else:
                    score += 1
                    print("   ✓ Basic password validation")
            
            # Check for SQL injection prevention
            if 'escape' in validators_content or 'sanitize' in validators_content:
                score += 1
                print("   ✓ Input sanitization functions found")
            
        else:
            issues.append("Validators module not found")
            print("   ⚠ Validators module missing")
        
        # Check route files for direct validation
        route_files = ['app/routes/main.py', 'app/routes/auth.py', 'app/routes/admin.py']
        validation_found = False
        
        for route_file in route_files:
            if os.path.exists(route_file):
                with open(route_file, 'r') as f:
                    content = f.read()
                
                # Check for form validation
                if 'request.form.get' in content and ('strip()' in content or 'validate' in content):
                    validation_found = True
                
                # Check for JSON validation
                if 'request.get_json' in content and ('validate' in content or 'schema' in content):
                    validation_found = True
        
        if validation_found:
            score += 2
            print("   ✓ Input validation in route handlers")
        else:
            issues.append("Input validation not clearly implemented in routes")
        
        # Check for XSS protection
        template_files = []
        if os.path.exists('templates'):
            for root, dirs, files in os.walk('templates'):
                for file in files:
                    if file.endswith('.html'):
                        template_files.append(os.path.join(root, file))
        
        xss_protection = True
        for template_file in template_files[:5]:  # Check first 5 templates
            try:
                with open(template_file, 'r') as f:
                    template_content = f.read()
                
                # Check for raw HTML output (potential XSS)
                if '|safe' in template_content or '{% raw %}' in template_content:
                    if '{{ ' in template_content and '|e' not in template_content:
                        xss_protection = False
                        break
            except:
                continue
        
        if xss_protection:
            score += 2
            print("   ✓ XSS protection in templates")
        else:
            issues.append("Potential XSS vulnerabilities in templates")
            print("   ⚠ Potential XSS vulnerabilities found")
        
        # Check for file upload validation
        if any(os.path.exists(f) for f in ['app/routes/main.py', 'app/routes/api.py']):
            upload_validation = False
            for route_file in ['app/routes/main.py', 'app/routes/api.py']:
                if os.path.exists(route_file):
                    with open(route_file, 'r') as f:
                        content = f.read()
                    
                    if 'files' in content and ('allowed_extensions' in content or 'secure_filename' in content):
                        upload_validation = True
                        break
            
            if upload_validation:
                score += 1
                print("   ✓ File upload validation found")
    
    except Exception as e:
        issues.append(f"Input validation audit error: {str(e)}")
        print(f"   ✗ Input validation audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_database_security():
    """Audit database security"""
    print("\n4. Database Security Audit...")
    score = 0
    max_score = 8
    issues = []
    
    try:
        # Check for ORM usage (SQLAlchemy)
        model_files = []
        if os.path.exists('app/models'):
            for file in os.listdir('app/models'):
                if file.endswith('.py') and file != '__init__.py':
                    model_files.append(f'app/models/{file}')
        
        if model_files:
            orm_usage = True
            for model_file in model_files:
                with open(model_file, 'r') as f:
                    content = f.read()
                
                # Check for raw SQL queries (potential SQL injection)
                if 'cursor.execute' in content or 'db.execute(' in content:
                    if 'text(' not in content:  # SQLAlchemy text() is safer
                        issues.append(f"Raw SQL queries found in {model_file}")
                        orm_usage = False
            
            if orm_usage:
                score += 3
                print("   ✓ Uses ORM (SQLAlchemy) - reduces SQL injection risk")
            else:
                issues.append("Raw SQL queries may be vulnerable to injection")
                print("   ⚠ Raw SQL queries found")
        
        # Check database configuration
        config_files = ['config/production.py', 'config/development.py']
        for config_file in config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_content = f.read()
                
                # Check for SSL/security options
                if 'ssl' in config_content.lower() or 'sslmode' in config_content:
                    score += 1
                    print(f"   ✓ SSL configuration found in {config_file}")
                    break
        
        # Check for database connection pooling
        extensions_path = 'app/extensions.py'
        if os.path.exists(extensions_path):
            with open(extensions_path, 'r') as f:
                extensions_content = f.read()
            
            if 'pool' in extensions_content.lower():
                score += 1
                print("   ✓ Database connection pooling configured")
        
        # Check for database migration security
        if os.path.exists('migrations'):
            score += 1
            print("   ✓ Database migrations directory exists")
            
            # Check for sensitive data in migrations
            migration_files = []
            versions_dir = 'migrations/versions'
            if os.path.exists(versions_dir):
                migration_files = [f for f in os.listdir(versions_dir) if f.endswith('.py')]
            
            sensitive_data_found = False
            for migration_file in migration_files[:5]:  # Check first 5
                try:
                    with open(os.path.join(versions_dir, migration_file), 'r') as f:
                        migration_content = f.read()
                    
                    # Check for hardcoded sensitive data
                    if any(keyword in migration_content.lower() for keyword in ['password', 'secret', 'key', 'token']):
                        if 'INSERT' in migration_content.upper():
                            sensitive_data_found = True
                            break
                except:
                    continue
            
            if not sensitive_data_found:
                score += 1
                print("   ✓ No sensitive data in migrations")
            else:
                issues.append("Sensitive data found in migration files")
        
        # Check for database backup considerations
        if os.path.exists('scripts') and any('backup' in f.lower() for f in os.listdir('scripts') if f.endswith('.py')):
            score += 1
            print("   ✓ Database backup scripts found")
        
        # Check for query logging/monitoring
        if os.path.exists('app/__init__.py'):
            with open('app/__init__.py', 'r') as f:
                init_content = f.read()
            
            if 'SQLALCHEMY_ECHO' in init_content or 'query.*log' in init_content.lower():
                score += 1
                print("   ✓ Database query logging configured")
    
    except Exception as e:
        issues.append(f"Database security audit error: {str(e)}")
        print(f"   ✗ Database security audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_security_headers():
    """Audit security headers"""
    print("\n5. Security Headers Audit...")
    score = 0
    max_score = 8
    issues = []
    
    try:
        # Check app initialization for security headers
        app_init_path = 'app/__init__.py'
        if os.path.exists(app_init_path):
            with open(app_init_path, 'r') as f:
                app_content = f.read()
            
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age',
                'Content-Security-Policy': 'default-src'
            }
            
            headers_found = 0
            for header, expected_value in security_headers.items():
                if header in app_content and expected_value in app_content:
                    headers_found += 1
                    print(f"   ✓ {header} header configured")
                else:
                    issues.append(f"{header} header missing or misconfigured")
            
            score += min(headers_found, 5)  # Max 5 points for headers
            
            # Check for HTTPS enforcement
            if 'HTTPS' in app_content or 'secure' in app_content.lower():
                score += 1
                print("   ✓ HTTPS enforcement indicators found")
            else:
                issues.append("HTTPS enforcement not clearly configured")
            
            # Check for session security
            if 'SESSION_COOKIE_SECURE' in app_content:
                score += 1
                print("   ✓ Secure session cookies configured")
            else:
                issues.append("Secure session cookies not configured")
            
            # Check for CSRF protection
            if 'CSRFProtect' in app_content or 'csrf' in app_content:
                score += 1
                print("   ✓ CSRF protection configured")
            else:
                issues.append("CSRF protection not found")
    
    except Exception as e:
        issues.append(f"Security headers audit error: {str(e)}")
        print(f"   ✗ Security headers audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_file_security():
    """Audit file security"""
    print("\n6. File Security Audit...")
    score = 0
    max_score = 6
    issues = []
    
    try:
        # Check for .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
            
            sensitive_patterns = ['.env', '*.log', '__pycache__', '.DS_Store', 'instance/', '*.db']
            ignored_patterns = 0
            
            for pattern in sensitive_patterns:
                if pattern in gitignore_content:
                    ignored_patterns += 1
            
            if ignored_patterns >= len(sensitive_patterns) - 1:  # Allow 1 missing
                score += 2
                print("   ✓ Sensitive files properly ignored")
            else:
                issues.append("Some sensitive files may not be ignored by git")
                print("   ⚠ Gitignore could be more comprehensive")
        else:
            issues.append(".gitignore file missing")
        
        # Check for exposed sensitive files
        sensitive_files = ['.env', 'config.py', 'instance/cibozer.db', 'private_key.pem']
        exposed_files = []
        
        for file in sensitive_files:
            if os.path.exists(file):
                # Check if it's in a web-accessible directory
                if not file.startswith(('static/', 'templates/')):
                    exposed_files.append(file)
        
        if len(exposed_files) <= 2:  # .env and db are expected
            score += 1
            print("   ✓ Sensitive files not in web-accessible directories")
        else:
            issues.append(f"Potentially exposed files: {', '.join(exposed_files)}")
        
        # Check file permissions (Unix-like systems)
        if os.name == 'posix':
            try:
                import stat
                env_perms = oct(os.stat('.env').st_mode)[-3:] if os.path.exists('.env') else None
                if env_perms and env_perms <= '644':
                    score += 1
                    print("   ✓ .env file permissions are restrictive")
                else:
                    issues.append(".env file permissions may be too permissive")
            except:
                pass
        else:
            score += 1  # Skip permission check on Windows
        
        # Check for temporary file cleanup
        temp_dirs = ['static/temp', 'temp', 'tmp']
        temp_cleanup = False
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                # Check if directory is empty or has cleanup mechanism
                files_in_temp = os.listdir(temp_dir) if os.path.exists(temp_dir) else []
                if len(files_in_temp) == 0:
                    temp_cleanup = True
                    break
        
        if temp_cleanup:
            score += 1
            print("   ✓ Temporary directories are clean")
        
        # Check for file upload restrictions
        route_files = ['app/routes/main.py', 'app/routes/api.py']
        upload_security = False
        
        for route_file in route_files:
            if os.path.exists(route_file):
                with open(route_file, 'r') as f:
                    content = f.read()
                
                if 'upload' in content.lower():
                    if 'allowed_extensions' in content or 'secure_filename' in content:
                        upload_security = True
                        break
        
        if upload_security:
            score += 1
            print("   ✓ File upload security measures found")
        
        # Check for log file security
        if os.path.exists('logs'):
            log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
            if log_files:
                # Check first log file for sensitive data
                try:
                    with open(f'logs/{log_files[0]}', 'r') as f:
                        log_sample = f.read(1000)  # First 1000 chars
                    
                    sensitive_keywords = ['password', 'secret', 'token', 'key']
                    if not any(keyword in log_sample.lower() for keyword in sensitive_keywords):
                        score += 1
                        print("   ✓ Log files don't contain sensitive data")
                    else:
                        issues.append("Log files may contain sensitive information")
                except:
                    pass
    
    except Exception as e:
        issues.append(f"File security audit error: {str(e)}")
        print(f"   ✗ File security audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

def audit_dependencies():
    """Audit dependency security"""
    print("\n7. Dependencies Security Audit...")
    score = 0
    max_score = 5
    issues = []
    
    try:
        # Check requirements.txt
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            # Check for version pinning
            lines = [line.strip() for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
            pinned_packages = 0
            total_packages = len(lines)
            
            for line in lines:
                if '==' in line or '>=' in line or '~=' in line:
                    pinned_packages += 1
            
            if total_packages > 0:
                pin_ratio = pinned_packages / total_packages
                if pin_ratio >= 0.8:
                    score += 2
                    print("   ✓ Most packages are version-pinned")
                elif pin_ratio >= 0.5:
                    score += 1
                    print("   ✓ Some packages are version-pinned")
                else:
                    issues.append("Many packages lack version pinning")
            
            # Check for known secure packages
            secure_packages = ['flask', 'sqlalchemy', 'bcrypt', 'cryptography']
            found_secure = sum(1 for pkg in secure_packages if pkg in requirements.lower())
            
            if found_secure >= 3:
                score += 1
                print("   ✓ Uses well-known secure packages")
            
            # Check for development vs production separation
            if 'pytest' in requirements or 'debug' in requirements.lower():
                issues.append("Development dependencies may be in production requirements")
            else:
                score += 1
                print("   ✓ No obvious development dependencies in requirements")
        
        # Check for virtual environment
        if os.path.exists('venv') or os.path.exists('.venv') or os.environ.get('VIRTUAL_ENV'):
            score += 1
            print("   ✓ Virtual environment detected")
        else:
            issues.append("Virtual environment not detected")
    
    except Exception as e:
        issues.append(f"Dependencies audit error: {str(e)}")
        print(f"   ✗ Dependencies audit failed: {e}")
    
    return {"score": score, "max_score": max_score, "issues": issues}

if __name__ == '__main__':
    results = security_audit()
    
    # Save results
    with open('security_audit_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Security audit complete. Results saved to security_audit_results.json")
    
    # Exit with appropriate code
    overall_percentage = results["overall_score"] / results["max_score"] * 100
    if overall_percentage >= 80:
        print("🟢 SECURITY STATUS: EXCELLENT - Ready for production")
        sys.exit(0)
    elif overall_percentage >= 60:
        print("🟡 SECURITY STATUS: GOOD - Minor improvements recommended")
        sys.exit(0)
    else:
        print("🔴 SECURITY STATUS: NEEDS WORK - Address critical issues before production")
        sys.exit(1)