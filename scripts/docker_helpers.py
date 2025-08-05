#!/usr/bin/env python3
"""
Docker Helper Scripts for Cibozer

This script provides convenient commands for Docker-based development and deployment.

Usage:
    python scripts/docker_helpers.py [command] [options]
    
Commands:
    dev-up          Start development environment
    dev-down        Stop development environment
    prod-up         Start production environment
    prod-down       Stop production environment
    build           Build Docker images
    logs            Show application logs
    shell           Open shell in web container
    db-shell        Open database shell
    redis-shell     Open Redis shell
    backup          Create database backup
    restore         Restore database from backup
    clean           Clean up Docker resources
    status          Show service status
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class DockerHelper:
    """Docker management helper for Cibozer."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.compose_file = self.project_root / 'docker-compose.yml'
        self.override_file = self.project_root / 'docker-compose.override.yml'
    
    def log_success(self, message):
        """Log successful operation."""
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    
    def log_error(self, message):
        """Log error."""
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    
    def log_warning(self, message):
        """Log warning."""
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    
    def log_info(self, message):
        """Log information."""
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")
    
    def run_command(self, command, cwd=None):
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                cwd=cwd or self.project_root,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.log_error(f"Command failed: {command}")
            return False
    
    def dev_up(self):
        """Start development environment."""
        self.log_info("Starting development environment...")
        
        # Check if .env file exists
        env_file = self.project_root / '.env'
        if not env_file.exists():
            self.log_warning(".env file not found, creating from template...")
            self.create_dev_env_file()
        
        # Start services
        command = "docker-compose up -d"
        if self.run_command(command):
            self.log_success("Development environment started")
            self.log_info("Services available at:")
            self.log_info("  Web: http://localhost:5000")
            self.log_info("  Database: postgresql://dev_user:dev_password_123@localhost:5432/cibozer_dev")
            self.log_info("  Redis: redis://localhost:6379")
            self.log_info("  MailHog: http://localhost:8025")
            self.log_info("  Adminer: http://localhost:8080")
            self.log_info("  Redis Commander: http://localhost:8081")
            return True
        return False
    
    def dev_down(self):
        """Stop development environment."""
        self.log_info("Stopping development environment...")
        
        command = "docker-compose down"
        if self.run_command(command):
            self.log_success("Development environment stopped")
            return True
        return False
    
    def prod_up(self):
        """Start production environment."""
        self.log_info("Starting production environment...")
        
        # Check if .env.production exists
        env_file = self.project_root / '.env.production'
        if not env_file.exists():
            self.log_error(".env.production file not found")
            self.log_info("Create .env.production from .env.example template")
            return False
        
        # Start production services (excluding development overrides)
        command = "docker-compose -f docker-compose.yml --profile production up -d"
        if self.run_command(command):
            self.log_success("Production environment started")
            return True
        return False
    
    def prod_down(self):
        """Stop production environment."""
        self.log_info("Stopping production environment...")
        
        command = "docker-compose -f docker-compose.yml --profile production down"
        if self.run_command(command):
            self.log_success("Production environment stopped")
            return True
        return False
    
    def build(self, no_cache=False):
        """Build Docker images."""
        self.log_info("Building Docker images...")
        
        cache_flag = "--no-cache" if no_cache else ""
        command = f"docker-compose build {cache_flag}"
        
        if self.run_command(command):
            self.log_success("Docker images built successfully")
            return True
        return False
    
    def logs(self, service=None, follow=False):
        """Show application logs."""
        service_name = service or "web"
        follow_flag = "-f" if follow else ""
        
        self.log_info(f"Showing logs for {service_name}...")
        command = f"docker-compose logs {follow_flag} {service_name}"
        
        # Don't use run_command for logs as it needs to stream
        subprocess.run(command, shell=True, cwd=self.project_root)
    
    def shell(self, service="web"):
        """Open shell in container."""
        self.log_info(f"Opening shell in {service} container...")
        
        command = f"docker-compose exec {service} /bin/bash"
        subprocess.run(command, shell=True, cwd=self.project_root)
    
    def db_shell(self):
        """Open database shell."""
        self.log_info("Opening database shell...")
        
        command = "docker-compose exec postgres psql -U dev_user -d cibozer_dev"
        subprocess.run(command, shell=True, cwd=self.project_root)
    
    def redis_shell(self):
        """Open Redis shell."""
        self.log_info("Opening Redis shell...")
        
        command = "docker-compose exec redis redis-cli"
        subprocess.run(command, shell=True, cwd=self.project_root)
    
    def backup(self):
        """Create database backup."""
        self.log_info("Creating database backup...")
        
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        backup_file = f"cibozer_backup_{timestamp}.sql"
        
        command = f"docker-compose exec postgres pg_dump -U dev_user cibozer_dev > backups/{backup_file}"
        
        if self.run_command(command):
            self.log_success(f"Database backup created: {backup_file}")
            return True
        return False
    
    def restore(self, backup_file):
        """Restore database from backup."""
        self.log_info(f"Restoring database from {backup_file}...")
        
        backup_path = self.project_root / 'backups' / backup_file
        if not backup_path.exists():
            self.log_error(f"Backup file not found: {backup_file}")
            return False
        
        command = f"docker-compose exec -T postgres psql -U dev_user cibozer_dev < backups/{backup_file}"
        
        if self.run_command(command):
            self.log_success("Database restored successfully")
            return True
        return False
    
    def clean(self):
        """Clean up Docker resources."""
        self.log_info("Cleaning up Docker resources...")
        
        commands = [
            "docker-compose down -v",  # Stop and remove volumes
            "docker system prune -f",  # Remove unused containers, networks, images
            "docker volume prune -f"   # Remove unused volumes
        ]
        
        for command in commands:
            self.run_command(command)
        
        self.log_success("Docker cleanup completed")
    
    def status(self):
        """Show service status."""
        self.log_info("Service status:")
        
        command = "docker-compose ps"
        subprocess.run(command, shell=True, cwd=self.project_root)
    
    def create_dev_env_file(self):
        """Create development .env file from template."""
        env_content = """# Development Environment Configuration
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-for-production

# Database
DATABASE_URL=postgresql://dev_user:dev_password_123@postgres:5432/cibozer_dev

# Email (using MailHog for development)
MAIL_SERVER=mailhog
MAIL_PORT=1025
MAIL_USE_TLS=False
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=dev@cibozer.local

# Redis
REDIS_URL=redis://redis:6379/0

# Admin
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@cibozer.local
ADMIN_PASSWORD=admin123

# Optional
OPENAI_API_KEY=
SENTRY_DSN=
"""
        
        env_file = self.project_root / '.env'
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        self.log_success("Created development .env file")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Docker helper for Cibozer')
    parser.add_argument('command', help='Command to run')
    parser.add_argument('--service', help='Service name for logs/shell commands')
    parser.add_argument('--follow', '-f', action='store_true', help='Follow logs')
    parser.add_argument('--no-cache', action='store_true', help='Build without cache')
    parser.add_argument('--backup-file', help='Backup file name for restore')
    
    args = parser.parse_args()
    
    helper = DockerHelper()
    
    # Command routing
    commands = {
        'dev-up': helper.dev_up,
        'dev-down': helper.dev_down,
        'prod-up': helper.prod_up,
        'prod-down': helper.prod_down,
        'build': lambda: helper.build(args.no_cache),
        'logs': lambda: helper.logs(args.service, args.follow),
        'shell': lambda: helper.shell(args.service or 'web'),
        'db-shell': helper.db_shell,
        'redis-shell': helper.redis_shell,
        'backup': helper.backup,
        'restore': lambda: helper.restore(args.backup_file),
        'clean': helper.clean,
        'status': helper.status
    }
    
    if args.command in commands:
        if args.command == 'restore' and not args.backup_file:
            helper.log_error("--backup-file required for restore command")
            sys.exit(1)
        
        success = commands[args.command]()
        sys.exit(0 if success is not False else 1)
    else:
        helper.log_error(f"Unknown command: {args.command}")
        helper.log_info("Available commands:")
        for cmd in commands.keys():
            print(f"  {cmd}")
        sys.exit(1)

if __name__ == '__main__':
    main()