#!/usr/bin/env python3
"""
Production Deployment Script

This script automates the deployment process for Cibozer to various platforms.
It performs pre-deployment checks, handles environment setup, and manages deployment.

Usage:
    python scripts/deploy_to_production.py [platform] [options]
    
Platforms:
    railway     Deploy to Railway
    render      Deploy to Render
    docker      Deploy using Docker
    
Options:
    --check-only        Only run pre-deployment checks
    --skip-checks       Skip pre-deployment validation
    --environment ENV   Specify environment (production, staging)
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ProductionDeployer:
    """Handles production deployment to various platforms."""
    
    def __init__(self, platform, environment='production'):
        self.platform = platform
        self.environment = environment
        self.project_root = project_root
        self.errors = []
        self.warnings = []
        self.completed_tasks = []
    
    def log_success(self, message):
        """Log successful operation."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
        self.completed_tasks.append(message)
    
    def log_error(self, message):
        """Log error."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
        self.errors.append(message)
    
    def log_warning(self, message):
        """Log warning."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
        self.warnings.append(message)
    
    def log_info(self, message):
        """Log information."""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    def run_command(self, command, description=None, cwd=None):
        """Run a shell command with error handling."""
        if description:
            self.log_info(description)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root
            )
            
            if description:
                self.log_success(description)
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {command}"
            if description:
                error_msg = f"{description} failed"
            
            self.log_error(f"{error_msg}\nError: {e.stderr}")
            return None
    
    def run_pre_deployment_checks(self):
        """Run comprehensive pre-deployment validation."""
        self.log_info("Running pre-deployment checks...")
        
        # Step 1: Environment validation
        validation_script = self.project_root / 'scripts' / 'validate_production_env.py'
        if not validation_script.exists():
            self.log_error("Environment validation script not found")
            return False
        
        env_result = self.run_command(
            f"python {validation_script}",
            "Validating environment configuration"
        )
        
        if env_result is None:
            return False
        
        # Step 2: Deployment preparation
        prep_script = self.project_root / 'scripts' / 'prepare_production_deployment.py'
        if prep_script.exists():
            prep_result = self.run_command(
                f"python {prep_script}",
                "Running deployment preparation"
            )
            
            if prep_result is None:
                return False
        
        # Step 3: Test suite
        test_result = self.run_command(
            "python -m pytest tests/ -x --tb=short",
            "Running critical tests"
        )
        
        if test_result is None:
            self.log_warning("Some tests failed - review before deployment")
        
        # Step 4: Security checks
        if self.environment == 'production':
            self.check_production_security()
        
        return len(self.errors) == 0
    
    def check_production_security(self):
        """Perform production security checks."""
        self.log_info("Checking production security settings...")
        
        # Check environment variables
        security_vars = [
            ('SECRET_KEY', lambda x: len(x) >= 32),
            ('DEBUG', lambda x: x.lower() == 'false'),
            ('FLASK_ENV', lambda x: x == 'production'),
            ('SESSION_COOKIE_SECURE', lambda x: x.lower() == 'true'),
        ]
        
        for var_name, validator in security_vars:
            value = os.environ.get(var_name)
            if not value:
                self.log_warning(f"Security variable not set: {var_name}")
            elif not validator(value):
                self.log_error(f"Security issue with {var_name}: invalid value")
            else:
                self.log_success(f"Security check passed: {var_name}")
    
    def deploy_to_railway(self):
        """Deploy to Railway platform."""
        self.log_info("Deploying to Railway...")
        
        # Check if Railway CLI is installed
        railway_check = self.run_command("railway --version", "Checking Railway CLI")
        if railway_check is None:
            self.log_error("Railway CLI not installed. Install with: npm install -g @railway/cli")
            return False
        
        # Check if logged in
        login_check = self.run_command("railway whoami", "Checking Railway login")
        if login_check is None:
            self.log_error("Not logged in to Railway. Run: railway login")
            return False
        
        # Deploy to Railway
        deploy_result = self.run_command("railway up --detach", "Deploying to Railway")
        if deploy_result is None:
            return False
        
        # Get deployment URL
        status_result = self.run_command("railway status", "Getting deployment status")
        if status_result:
            self.log_success("Railway deployment completed")
            self.log_info("Check Railway dashboard for deployment URL")
        
        return True
    
    def deploy_to_render(self):
        """Deploy to Render platform."""
        self.log_info("Deploying to Render...")
        
        # Verify render.yaml exists
        render_config = self.project_root / 'render.yaml'
        if not render_config.exists():
            self.log_error("render.yaml configuration not found")
            return False
        
        self.log_success("Render configuration found")
        self.log_info("Steps to deploy to Render:")
        self.log_info("1. Go to https://render.com")
        self.log_info("2. Click 'New' → 'Blueprint'")
        self.log_info("3. Connect your GitHub repository")
        self.log_info("4. Render will automatically detect render.yaml")
        self.log_info("5. Set required environment variables in dashboard")
        
        # Create deployment summary
        self.create_render_deployment_summary()
        
        return True
    
    def deploy_to_docker(self):
        """Deploy using Docker."""
        self.log_info("Deploying with Docker...")
        
        # Check if Docker is installed
        docker_check = self.run_command("docker --version", "Checking Docker installation")
        if docker_check is None:
            self.log_error("Docker not installed")
            return False
        
        # Check if docker-compose is available
        compose_check = self.run_command("docker-compose --version", "Checking Docker Compose")
        if compose_check is None:
            self.log_error("Docker Compose not installed")
            return False
        
        # Build Docker image
        build_result = self.run_command(
            "docker build -t cibozer:latest .",
            "Building Docker image"
        )
        
        if build_result is None:
            return False
        
        # Start production services
        start_result = self.run_command(
            "docker-compose -f docker-compose.yml --profile production up -d",
            "Starting production services"
        )
        
        if start_result is None:
            return False
        
        # Check service status
        status_result = self.run_command(
            "docker-compose ps",
            "Checking service status"
        )
        
        if status_result:
            self.log_success("Docker deployment completed")
            self.log_info("Application available at: http://localhost:5000")
        
        return True
    
    def create_render_deployment_summary(self):
        """Create deployment summary for Render."""
        summary = {
            "platform": "render",
            "timestamp": datetime.now().isoformat(),
            "required_env_vars": [
                "SECRET_KEY",
                "MAIL_PASSWORD", 
                "STRIPE_SECRET_KEY",
                "STRIPE_PUBLISHABLE_KEY",
                "STRIPE_WEBHOOK_SECRET",
                "STRIPE_PRICE_ID_PRO",
                "STRIPE_PRICE_ID_PREMIUM",
                "ADMIN_PASSWORD",
                "OPENAI_API_KEY"
            ],
            "automatic_vars": [
                "DATABASE_URL",
                "REDIS_URL"
            ],
            "services": [
                "cibozer-web",
                "cibozer-postgres", 
                "cibozer-redis"
            ]
        }
        
        summary_file = self.project_root / 'render_deployment_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.log_success(f"Deployment summary created: {summary_file.name}")
    
    def post_deployment_tasks(self):
        """Run post-deployment tasks."""
        self.log_info("Running post-deployment tasks...")
        
        if self.platform == 'docker':
            # For Docker, we can run tasks directly
            init_result = self.run_command(
                "docker-compose exec web python scripts/init_production_database.py",
                "Initializing production database"
            )
            
            if init_result:
                self.log_success("Database initialization completed")
        else:
            # For hosted platforms, provide instructions
            self.log_info("Manual post-deployment steps required:")
            self.log_info("1. Initialize database: python scripts/init_production_database.py")
            self.log_info("2. Configure Stripe webhooks")
            self.log_info("3. Set up domain and SSL")
            self.log_info("4. Configure monitoring")
    
    def deploy(self, check_only=False, skip_checks=False):
        """Execute the complete deployment process."""
        print(f"{Colors.BOLD}{Colors.BLUE}🚀 Cibozer Production Deployment{Colors.END}")
        print(f"Platform: {self.platform}")
        print(f"Environment: {self.environment}\n")
        
        # Pre-deployment checks
        if not skip_checks:
            if not self.run_pre_deployment_checks():
                self.log_error("Pre-deployment checks failed")
                return False
        
        if check_only:
            self.log_success("Pre-deployment checks completed successfully")
            return True
        
        # Platform-specific deployment
        deployment_methods = {
            'railway': self.deploy_to_railway,
            'render': self.deploy_to_render,
            'docker': self.deploy_to_docker
        }
        
        if self.platform not in deployment_methods:
            self.log_error(f"Unsupported platform: {self.platform}")
            return False
        
        deployment_success = deployment_methods[self.platform]()
        
        if not deployment_success:
            return False
        
        # Post-deployment tasks
        self.post_deployment_tasks()
        
        # Print summary
        print(f"\n{Colors.BOLD}📊 Deployment Summary{Colors.END}")
        print("=" * 50)
        print(f"{Colors.GREEN}Completed: {len(self.completed_tasks)}{Colors.END}")
        if self.warnings:
            print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        if self.errors:
            print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ DEPLOYMENT HAD ERRORS{Colors.END}")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ DEPLOYMENT SUCCESSFUL{Colors.END}")
            
            # Platform-specific success messages
            if self.platform == 'railway':
                print("🎉 Your application is being deployed to Railway!")
                print("📊 Monitor deployment: https://railway.app")
                
            elif self.platform == 'render':
                print("🎉 Ready to deploy to Render!")
                print("📊 Complete deployment: https://render.com")
                
            elif self.platform == 'docker':
                print("🎉 Docker services are running!")
                print("🌐 Application: http://localhost:5000")
                print("📊 Admin: http://localhost:5000/admin")
            
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Deploy Cibozer to production')
    parser.add_argument('platform', choices=['railway', 'render', 'docker'],
                       help='Deployment platform')
    parser.add_argument('--check-only', action='store_true',
                       help='Only run pre-deployment checks')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip pre-deployment validation')
    parser.add_argument('--environment', default='production',
                       choices=['production', 'staging'],
                       help='Deployment environment')
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(args.platform, args.environment)
    success = deployer.deploy(
        check_only=args.check_only,
        skip_checks=args.skip_checks
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()