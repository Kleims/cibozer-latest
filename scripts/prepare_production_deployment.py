#!/usr/bin/env python3
"""
Production Deployment Preparation Script

This script prepares the application for production deployment by:
1. Validating environment configuration
2. Setting up database migrations
3. Creating necessary directories
4. Validating critical dependencies
5. Running pre-deployment tests

Usage:
    python scripts/prepare_production_deployment.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ProductionDeploymentPreparation:
    """Handles production deployment preparation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.completed_tasks = []
    
    def log_success(self, message):
        """Log a successful task."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        self.completed_tasks.append(message)
    
    def log_error(self, message):
        """Log an error."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.errors.append(message)
    
    def log_warning(self, message):
        """Log a warning."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        self.warnings.append(message)
    
    def log_info(self, message):
        """Log information."""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    def run_command(self, command, description, cwd=None):
        """Run a shell command and handle errors."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root
            )
            self.log_success(f"{description}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            self.log_error(f"{description} failed: {e.stderr}")
            return None
    
    def validate_environment(self):
        """Validate production environment configuration."""
        self.log_info("Validating production environment...")
        
        # Run environment validation script
        validation_script = self.project_root / 'scripts' / 'validate_production_env.py'
        
        if not validation_script.exists():
            self.log_error("Environment validation script not found")
            return False
        
        try:
            result = subprocess.run([
                sys.executable, str(validation_script)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                self.log_success("Environment validation passed")
                return True
            else:
                self.log_error("Environment validation failed")
                print(result.stdout)
                print(result.stderr)
                return False
        except Exception as e:
            self.log_error(f"Failed to run environment validation: {e}")
            return False
    
    def create_required_directories(self):
        """Create directories required for production."""
        self.log_info("Creating required directories...")
        
        directories = [
            'logs',
            'static/uploads',
            'static/pdfs',
            'static/videos',
            'instance'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            self.log_success(f"Created directory: {directory}")
    
    def validate_dependencies(self):
        """Validate that all required dependencies are available."""
        self.log_info("Validating dependencies...")
        
        # Check if requirements.txt exists
        requirements_file = self.project_root / 'requirements.txt'
        if not requirements_file.exists():
            self.log_error("requirements.txt not found")
            return False
        
        # Try to import critical dependencies
        critical_deps = [
            'flask',
            'flask_sqlalchemy',
            'flask_login',
            'flask_wtf',
            'flask_mail',
            'psycopg2',
            'gunicorn'
        ]
        
        missing_deps = []
        for dep in critical_deps:
            try:
                __import__(dep.replace('-', '_'))
                self.log_success(f"Dependency available: {dep}")
            except ImportError:
                missing_deps.append(dep)
                self.log_error(f"Missing dependency: {dep}")
        
        if missing_deps:
            self.log_error(f"Install missing dependencies: pip install {' '.join(missing_deps)}")
            return False
        
        return True
    
    def setup_database_migrations(self):
        """Set up database migrations for production."""
        self.log_info("Setting up database migrations...")
        
        migrations_dir = self.project_root / 'migrations'
        
        # Initialize migrations if not exists
        if not migrations_dir.exists():
            result = self.run_command(
                "flask db init",
                "Initialize database migrations"
            )
            if result is None:
                return False
        
        # Create migration for current models
        result = self.run_command(
            "flask db migrate -m 'Production deployment migration'",
            "Create database migration"
        )
        
        if result is None:
            self.log_warning("Migration creation failed - may already be up to date")
        
        self.log_success("Database migrations prepared")
        return True
    
    def validate_configuration_files(self):
        """Validate that all configuration files are present and valid."""
        self.log_info("Validating configuration files...")
        
        required_files = [
            'config/default.py',
            'config/production.py',
            'app/__init__.py',
            'wsgi.py'
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                self.log_error(f"Required file missing: {file_path}")
                return False
            else:
                self.log_success(f"Configuration file found: {file_path}")
        
        return True
    
    def create_wsgi_file(self):
        """Ensure WSGI file is properly configured for production."""
        wsgi_file = self.project_root / 'wsgi.py'
        
        if not wsgi_file.exists():
            wsgi_content = '''"""
WSGI entry point for production deployment.
"""
import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Create application instance
app = create_app(os.environ.get('FLASK_ENV', 'production'))

if __name__ == "__main__":
    app.run()
'''
            with open(wsgi_file, 'w') as f:
                f.write(wsgi_content)
            self.log_success("Created wsgi.py file")
        else:
            self.log_success("wsgi.py file already exists")
    
    def create_procfile(self):
        """Create or update Procfile for deployment platforms."""
        procfile = self.project_root / 'Procfile'
        
        procfile_content = 'web: gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120\n'
        
        with open(procfile, 'w') as f:
            f.write(procfile_content)
        
        self.log_success("Created/updated Procfile")
    
    def update_requirements(self):
        """Ensure production dependencies are in requirements.txt."""
        requirements_file = self.project_root / 'requirements.txt'
        
        # Read current requirements
        if requirements_file.exists():
            with open(requirements_file, 'r') as f:
                current_requirements = f.read()
        else:
            current_requirements = ""
        
        # Essential production dependencies
        production_deps = [
            'gunicorn>=20.1.0',
            'psycopg2-binary>=2.9.0',
            'python-dotenv>=0.19.0'
        ]
        
        updated = False
        for dep in production_deps:
            dep_name = dep.split('>=')[0].split('==')[0]
            if dep_name not in current_requirements:
                current_requirements += f"{dep}\n"
                updated = True
                self.log_success(f"Added production dependency: {dep}")
        
        if updated:
            with open(requirements_file, 'w') as f:
                f.write(current_requirements)
            self.log_success("Updated requirements.txt with production dependencies")
    
    def run_basic_tests(self):
        """Run basic application tests."""
        self.log_info("Running basic application tests...")
        
        # Check if pytest is available and run basic tests
        try:
            import pytest
            
            # Run a subset of critical tests
            test_command = "python -m pytest tests/test_app.py tests/test_models.py -v --tb=short"
            result = self.run_command(
                test_command,
                "Run basic application tests"
            )
            
            if result is not None:
                self.log_success("Basic tests passed")
                return True
            else:
                self.log_warning("Some tests failed - review before deployment")
                return False
                
        except ImportError:
            self.log_warning("pytest not installed - skipping tests")
            return True
    
    def create_deployment_summary(self):
        """Create a summary of the deployment preparation."""
        summary = {
            'timestamp': str(subprocess.check_output(['date']).decode().strip()),
            'completed_tasks': self.completed_tasks,
            'warnings': self.warnings,
            'errors': self.errors,
            'deployment_ready': len(self.errors) == 0
        }
        
        summary_file = self.project_root / 'deployment_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log_success("Created deployment summary")
    
    def run_preparation(self):
        """Run the complete preparation process."""
        print(f"{Colors.BOLD}{Colors.BLUE}🚀 Cibozer Production Deployment Preparation{Colors.END}\n")
        
        steps = [
            ("Validate Configuration Files", self.validate_configuration_files),
            ("Create Required Directories", self.create_required_directories),
            ("Validate Dependencies", self.validate_dependencies),
            ("Update Requirements", self.update_requirements),
            ("Create WSGI File", self.create_wsgi_file),
            ("Create Procfile", self.create_procfile),
            ("Setup Database Migrations", self.setup_database_migrations),
            ("Run Basic Tests", self.run_basic_tests),
            ("Validate Environment", self.validate_environment),
            ("Create Deployment Summary", self.create_deployment_summary)
        ]
        
        for step_name, step_function in steps:
            print(f"\n{Colors.BOLD}📋 {step_name}{Colors.END}")
            try:
                success = step_function()
                if not success and step_name in ["Validate Environment", "Validate Dependencies"]:
                    self.log_error(f"Critical step failed: {step_name}")
                    break
            except Exception as e:
                self.log_error(f"Exception in {step_name}: {str(e)}")
        
        # Print final summary
        print(f"\n{Colors.BOLD}📊 Preparation Summary{Colors.END}")
        print("=" * 50)
        
        print(f"{Colors.GREEN}✅ Completed: {len(self.completed_tasks)}{Colors.END}")
        if self.warnings:
            print(f"{Colors.YELLOW}⚠️  Warnings: {len(self.warnings)}{Colors.END}")
        if self.errors:
            print(f"{Colors.RED}❌ Errors: {len(self.errors)}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ PREPARATION FAILED{Colors.END}")
            print("Fix the above errors before proceeding with deployment.")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ PREPARATION SUCCESSFUL{Colors.END}")
            print("Ready for production deployment!")
            return True

def main():
    """Main function."""
    preparator = ProductionDeploymentPreparation()
    success = preparator.run_preparation()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()