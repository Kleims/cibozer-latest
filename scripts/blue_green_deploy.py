#!/usr/bin/env python3
"""
Blue-Green Deployment Script for Cibozer
Ensures zero-downtime deployment with automatic rollback
"""

import os
import sys
import time
import subprocess
import requests
import json
from datetime import datetime
from pathlib import Path

class BlueGreenDeployer:
    def __init__(self):
        self.deployment_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.app_dir = Path('/home/cibozer/app')
        self.blue_dir = self.app_dir / 'blue'
        self.green_dir = self.app_dir / 'green'
        self.current_link = self.app_dir / 'current'
        self.health_endpoint = 'http://localhost:8000/api/health'
        self.backup_dir = Path('/home/cibozer/backups')
        
    def log(self, message, level='INFO'):
        """Log deployment messages"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
        
        # Also log to file
        log_file = self.backup_dir / f'deployment_{self.deployment_id}.log'
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    
    def run_command(self, command, cwd=None):
        """Run shell command and capture output"""
        self.log(f"Running: {command}")
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            self.log(f"Command failed: {result.stderr}", 'ERROR')
            raise Exception(f"Command failed: {command}")
        
        return result.stdout
    
    def check_health(self, retries=5, delay=5):
        """Check application health with retries"""
        for i in range(retries):
            try:
                response = requests.get(self.health_endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        self.log("Health check passed")
                        return True
                    else:
                        self.log(f"Health check returned: {data.get('status')}", 'WARNING')
                else:
                    self.log(f"Health check returned status {response.status_code}", 'WARNING')
            except Exception as e:
                self.log(f"Health check failed: {str(e)}", 'WARNING')
            
            if i < retries - 1:
                self.log(f"Retrying health check in {delay} seconds...")
                time.sleep(delay)
        
        return False
    
    def backup_database(self):
        """Create database backup before deployment"""
        self.log("Creating database backup...")
        
        backup_file = self.backup_dir / f'db_backup_{self.deployment_id}.sql'
        
        # Get database URL from environment
        db_url = os.environ.get('DATABASE_URL')
        if db_url and db_url.startswith('postgresql://'):
            # PostgreSQL backup
            self.run_command(f"pg_dump {db_url} > {backup_file}")
        else:
            # SQLite backup
            db_path = self.app_dir / 'instance' / 'cibozer.db'
            if db_path.exists():
                import shutil
                shutil.copy(db_path, backup_file)
        
        self.log(f"Database backed up to {backup_file}")
        return backup_file
    
    def get_current_color(self):
        """Determine which color is currently active"""
        if self.current_link.exists() and self.current_link.is_symlink():
            target = self.current_link.resolve()
            if target == self.blue_dir:
                return 'blue'
            elif target == self.green_dir:
                return 'green'
        
        # Default to blue if no current deployment
        return 'blue'
    
    def prepare_new_deployment(self, new_color_dir):
        """Prepare new deployment directory"""
        self.log(f"Preparing {new_color_dir.name} deployment...")
        
        # Remove old deployment if exists
        if new_color_dir.exists():
            self.run_command(f"rm -rf {new_color_dir}")
        
        # Clone repository
        self.run_command(
            f"git clone https://github.com/yourusername/cibozer.git {new_color_dir}"
        )
        
        # Copy production environment
        env_file = self.app_dir / '.env.production'
        if env_file.exists():
            self.run_command(f"cp {env_file} {new_color_dir}/.env")
        
        # Create virtual environment
        self.run_command(
            f"python3 -m venv {new_color_dir}/venv",
            cwd=new_color_dir
        )
        
        # Activate venv and install dependencies
        venv_python = new_color_dir / 'venv' / 'bin' / 'python'
        venv_pip = new_color_dir / 'venv' / 'bin' / 'pip'
        
        self.run_command(
            f"{venv_pip} install --upgrade pip",
            cwd=new_color_dir
        )
        
        self.run_command(
            f"{venv_pip} install -r requirements.txt",
            cwd=new_color_dir
        )
        
        # Install production dependencies
        self.run_command(
            f"{venv_pip} install gunicorn psycopg2-binary",
            cwd=new_color_dir
        )
        
        # Build static assets
        self.run_command("npm install", cwd=new_color_dir)
        self.run_command("npm run build", cwd=new_color_dir)
        
        # Run database migrations
        self.run_command(
            f"FLASK_APP=app.py {venv_python} -m flask db upgrade",
            cwd=new_color_dir
        )
        
        self.log(f"{new_color_dir.name} deployment prepared")
    
    def switch_deployment(self, new_color):
        """Switch traffic to new deployment"""
        self.log(f"Switching to {new_color} deployment...")
        
        new_dir = self.blue_dir if new_color == 'blue' else self.green_dir
        
        # Update symlink atomically
        temp_link = self.app_dir / 'current_new'
        self.run_command(f"ln -sf {new_dir} {temp_link}")
        self.run_command(f"mv -Tf {temp_link} {self.current_link}")
        
        # Reload application
        self.run_command("sudo supervisorctl restart cibozer")
        
        self.log(f"Switched to {new_color}")
    
    def rollback(self, backup_file, old_color):
        """Rollback to previous deployment"""
        self.log("Starting rollback...", 'WARNING')
        
        # Restore database if needed
        if backup_file and backup_file.exists():
            self.log("Restoring database backup...")
            db_url = os.environ.get('DATABASE_URL')
            if db_url and db_url.startswith('postgresql://'):
                self.run_command(f"psql {db_url} < {backup_file}")
            else:
                db_path = self.app_dir / 'instance' / 'cibozer.db'
                import shutil
                shutil.copy(backup_file, db_path)
        
        # Switch back to old deployment
        self.switch_deployment(old_color)
        
        self.log("Rollback completed")
    
    def deploy(self):
        """Execute blue-green deployment"""
        self.log(f"Starting deployment {self.deployment_id}")
        
        try:
            # Pre-deployment health check
            if not self.check_health():
                self.log("Pre-deployment health check failed", 'ERROR')
                return False
            
            # Backup database
            backup_file = self.backup_database()
            
            # Determine colors
            current_color = self.get_current_color()
            new_color = 'green' if current_color == 'blue' else 'blue'
            new_color_dir = self.green_dir if new_color == 'green' else self.blue_dir
            
            self.log(f"Current: {current_color}, Deploying to: {new_color}")
            
            # Prepare new deployment
            self.prepare_new_deployment(new_color_dir)
            
            # Test new deployment before switching
            test_port = 8001
            test_process = subprocess.Popen(
                [
                    str(new_color_dir / 'venv' / 'bin' / 'gunicorn'),
                    '-b', f'127.0.0.1:{test_port}',
                    'wsgi:app'
                ],
                cwd=new_color_dir
            )
            
            time.sleep(10)  # Give it time to start
            
            # Test the new deployment
            try:
                test_response = requests.get(f'http://localhost:{test_port}/api/health')
                if test_response.status_code != 200:
                    raise Exception("New deployment health check failed")
            finally:
                test_process.terminate()
                test_process.wait()
            
            # Switch to new deployment
            self.switch_deployment(new_color)
            
            # Post-deployment health check
            if not self.check_health(retries=10):
                self.log("Post-deployment health check failed", 'ERROR')
                self.rollback(backup_file, current_color)
                return False
            
            # Run smoke tests
            if not self.run_smoke_tests():
                self.log("Smoke tests failed", 'ERROR')
                self.rollback(backup_file, current_color)
                return False
            
            self.log("Deployment completed successfully!", 'SUCCESS')
            
            # Clean up old backup files (keep last 10)
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            self.log(f"Deployment failed: {str(e)}", 'ERROR')
            self.rollback(backup_file, current_color)
            return False
    
    def run_smoke_tests(self):
        """Run basic smoke tests on the deployed application"""
        self.log("Running smoke tests...")
        
        tests = [
            ('GET', '/'),
            ('GET', '/api/health'),
            ('GET', '/auth/login'),
            ('GET', '/static/css/style.css'),
        ]
        
        for method, path in tests:
            try:
                url = f'http://localhost:8000{path}'
                response = requests.request(method, url, timeout=10)
                if response.status_code >= 500:
                    self.log(f"Smoke test failed: {method} {path} returned {response.status_code}", 'ERROR')
                    return False
                else:
                    self.log(f"Smoke test passed: {method} {path}")
            except Exception as e:
                self.log(f"Smoke test failed: {method} {path} - {str(e)}", 'ERROR')
                return False
        
        return True
    
    def cleanup_old_backups(self):
        """Clean up old backup files"""
        self.log("Cleaning up old backups...")
        
        # Keep only the last 10 backups
        backup_files = sorted(self.backup_dir.glob('db_backup_*.sql'))
        if len(backup_files) > 10:
            for old_backup in backup_files[:-10]:
                old_backup.unlink()
                self.log(f"Removed old backup: {old_backup.name}")

def main():
    """Main deployment function"""
    deployer = BlueGreenDeployer()
    
    # Create necessary directories
    deployer.backup_dir.mkdir(exist_ok=True)
    deployer.blue_dir.parent.mkdir(exist_ok=True)
    
    # Run deployment
    success = deployer.deploy()
    
    if success:
        print("\n✅ Deployment successful!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()