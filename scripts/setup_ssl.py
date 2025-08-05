#!/usr/bin/env python3
"""
SSL Setup Script for Cibozer

This script automates SSL certificate setup for self-hosted Cibozer deployments.
It handles Let's Encrypt certificate generation, Nginx configuration, and renewal setup.

Usage:
    python scripts/setup_ssl.py --domain yourdomain.com [options]
    
Options:
    --domain DOMAIN     Primary domain name (required)
    --email EMAIL       Email for Let's Encrypt registration
    --nginx-config      Update Nginx configuration
    --test-cert         Use Let's Encrypt staging server (for testing)
    --renew             Renew existing certificates
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import tempfile
import shutil

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

class SSLSetup:
    """Handles SSL certificate setup and configuration."""
    
    def __init__(self, domain, email=None, test_cert=False):
        self.domain = domain
        self.www_domain = f"www.{domain}"
        self.email = email or f"admin@{domain}"
        self.test_cert = test_cert
        self.project_root = project_root
        
        self.nginx_sites_available = Path('/etc/nginx/sites-available')
        self.nginx_sites_enabled = Path('/etc/nginx/sites-enabled')
        self.letsencrypt_dir = Path('/etc/letsencrypt')
        
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
    
    def run_command(self, command, description=None, check=True):
        """Run a shell command with error handling."""
        if description:
            self.log_info(description)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=check,
                capture_output=True,
                text=True
            )
            
            if description and result.returncode == 0:
                self.log_success(description)
            
            return result
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {command}"
            if description:
                error_msg = f"{description} failed"
            
            self.log_error(f"{error_msg}\nError: {e.stderr}")
            return None
    
    def check_prerequisites(self):
        """Check system prerequisites for SSL setup."""
        self.log_info("Checking prerequisites...")
        
        # Check if running as root
        if os.geteuid() != 0:
            self.log_error("This script must be run as root (use sudo)")
            return False
        
        # Check if nginx is installed
        nginx_check = self.run_command("nginx -v", check=False)
        if nginx_check is None or nginx_check.returncode != 0:
            self.log_error("Nginx is not installed")
            return False
        
        self.log_success("Nginx is installed")
        
        # Check if certbot is installed
        certbot_check = self.run_command("certbot --version", check=False)
        if certbot_check is None or certbot_check.returncode != 0:
            self.log_warning("Certbot not installed, installing...")
            if not self.install_certbot():
                return False
        else:
            self.log_success("Certbot is installed")
        
        return True
    
    def install_certbot(self):
        """Install certbot and nginx plugin."""
        self.log_info("Installing certbot...")
        
        # Detect OS and install certbot
        os_release = Path('/etc/os-release')
        if os_release.exists():
            with open(os_release) as f:
                os_info = f.read().lower()
            
            if 'ubuntu' in os_info or 'debian' in os_info:
                install_cmd = "apt update && apt install -y certbot python3-certbot-nginx"
            elif 'centos' in os_info or 'rhel' in os_info or 'fedora' in os_info:
                install_cmd = "yum install -y certbot python3-certbot-nginx || dnf install -y certbot python3-certbot-nginx"
            else:
                self.log_error("Unsupported operating system for automatic certbot installation")
                return False
        else:
            self.log_error("Cannot detect operating system")
            return False
        
        result = self.run_command(install_cmd, "Installing certbot")
        return result is not None
    
    def validate_domain(self):
        """Validate domain configuration."""
        self.log_info(f"Validating domain: {self.domain}")
        
        # Check if domain resolves to this server
        import socket
        try:
            domain_ip = socket.gethostbyname(self.domain)
            self.log_success(f"Domain {self.domain} resolves to {domain_ip}")
        except socket.gaierror:
            self.log_error(f"Domain {self.domain} does not resolve")
            return False
        
        return True
    
    def backup_nginx_config(self):
        """Create backup of current nginx configuration."""
        backup_dir = Path('/etc/nginx/backup')
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()
        
        try:
            if self.nginx_sites_available.exists():
                shutil.copytree(
                    self.nginx_sites_available,
                    backup_dir / f"sites-available_{timestamp}"
                )
                self.log_success(f"Nginx configuration backed up to {backup_dir}")
                return True
        except Exception as e:
            self.log_error(f"Failed to backup nginx configuration: {e}")
            return False
    
    def create_nginx_config(self):
        """Create nginx configuration for the domain."""
        self.log_info("Creating nginx configuration...")
        
        config_content = f'''# Cibozer SSL Configuration for {self.domain}
# Generated automatically by SSL setup script

# HTTP server (redirect to HTTPS)
server {{
    listen 80;
    server_name {self.domain} {self.www_domain};
    
    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {{
        root /var/www/certbot;
    }}
    
    # Redirect all other traffic to HTTPS
    location / {{
        return 301 https://$server_name$request_uri;
    }}
}}

# HTTPS server
server {{
    listen 443 ssl http2;
    server_name {self.domain} {self.www_domain};
    
    # SSL certificate paths (will be updated after certificate generation)
    ssl_certificate /etc/letsencrypt/live/{self.domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{self.domain}/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Proxy to Cibozer application
    location / {{
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
    
    # Static files
    location /static/ {{
        alias /var/www/cibozer/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }}
    
    # Error pages
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
}}
'''
        
        config_file = self.nginx_sites_available / 'cibozer'
        try:
            with open(config_file, 'w') as f:
                f.write(config_content)
            
            self.log_success(f"Nginx configuration created: {config_file}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to create nginx configuration: {e}")
            return False
    
    def enable_nginx_site(self):
        """Enable the nginx site configuration."""
        source = self.nginx_sites_available / 'cibozer'
        target = self.nginx_sites_enabled / 'cibozer'
        
        try:
            if target.exists():
                target.unlink()
            
            target.symlink_to(source)
            self.log_success("Nginx site configuration enabled")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to enable nginx site: {e}")
            return False
    
    def test_nginx_config(self):
        """Test nginx configuration."""
        result = self.run_command("nginx -t", "Testing nginx configuration")
        return result is not None
    
    def obtain_ssl_certificate(self):
        """Obtain SSL certificate from Let's Encrypt."""
        self.log_info("Obtaining SSL certificate from Let's Encrypt...")
        
        # Create webroot directory
        webroot_dir = Path('/var/www/certbot')
        webroot_dir.mkdir(parents=True, exist_ok=True)
        
        # Build certbot command
        certbot_cmd = [
            "certbot", "certonly",
            "--webroot", "-w", str(webroot_dir),
            "--email", self.email,
            "-d", self.domain,
            "-d", self.www_domain,
            "--agree-tos",
            "--non-interactive"
        ]
        
        if self.test_cert:
            certbot_cmd.append("--staging")
            self.log_info("Using Let's Encrypt staging server (test certificate)")
        
        result = self.run_command(" ".join(certbot_cmd), "Obtaining SSL certificate")
        
        if result and result.returncode == 0:
            self.log_success("SSL certificate obtained successfully")
            return True
        else:
            self.log_error("Failed to obtain SSL certificate")
            return False
    
    def setup_auto_renewal(self):
        """Setup automatic certificate renewal."""
        self.log_info("Setting up automatic certificate renewal...")
        
        # Create renewal script
        renewal_script = Path('/usr/local/bin/renew-cibozer-ssl.sh')
        script_content = f'''#!/bin/bash
# Automatic SSL renewal script for Cibozer
# Generated by SSL setup script

/usr/bin/certbot renew --quiet --post-hook "systemctl reload nginx"

# Log renewal attempt
echo "$(date): SSL renewal check completed" >> /var/log/cibozer-ssl-renewal.log
'''
        
        try:
            with open(renewal_script, 'w') as f:
                f.write(script_content)
            
            renewal_script.chmod(0o755)
            self.log_success("Renewal script created")
            
        except Exception as e:
            self.log_error(f"Failed to create renewal script: {e}")
            return False
        
        # Add to crontab
        cron_entry = "0 12 * * * /usr/local/bin/renew-cibozer-ssl.sh"
        
        result = self.run_command(
            f'(crontab -l 2>/dev/null; echo "{cron_entry}") | crontab -',
            "Adding SSL renewal to crontab"
        )
        
        return result is not None
    
    def reload_nginx(self):
        """Reload nginx configuration."""
        result = self.run_command("systemctl reload nginx", "Reloading nginx")
        return result is not None
    
    def verify_ssl_setup(self):
        """Verify SSL certificate installation."""
        self.log_info("Verifying SSL setup...")
        
        # Test SSL certificate
        test_cmd = f"openssl s_client -connect {self.domain}:443 -servername {self.domain} < /dev/null"
        result = self.run_command(test_cmd, check=False)
        
        if result and "Verify return code: 0 (ok)" in result.stdout:
            self.log_success("SSL certificate verification successful")
            return True
        else:
            self.log_warning("SSL certificate verification had issues")
            return False
    
    def setup_ssl(self, update_nginx=True):
        """Run complete SSL setup process."""
        print(f"{Colors.BOLD}{Colors.BLUE}🔒 SSL Setup for {self.domain}{Colors.END}\n")
        
        steps = [
            ("Check Prerequisites", self.check_prerequisites),
            ("Validate Domain", self.validate_domain),
            ("Backup Nginx Config", self.backup_nginx_config),
        ]
        
        if update_nginx:
            steps.extend([
                ("Create Nginx Config", self.create_nginx_config),
                ("Enable Nginx Site", self.enable_nginx_site),
                ("Test Nginx Config", self.test_nginx_config),
                ("Reload Nginx", self.reload_nginx),
            ])
        
        steps.extend([
            ("Obtain SSL Certificate", self.obtain_ssl_certificate),
            ("Setup Auto-Renewal", self.setup_auto_renewal),
            ("Reload Nginx", self.reload_nginx),
            ("Verify SSL Setup", self.verify_ssl_setup),
        ])
        
        for step_name, step_function in steps:
            print(f"\n{Colors.BOLD}📋 {step_name}{Colors.END}")
            try:
                success = step_function()
                if not success:
                    self.log_error(f"Critical step failed: {step_name}")
                    break
            except Exception as e:
                self.log_error(f"Exception in {step_name}: {str(e)}")
                break
        
        # Print summary
        print(f"\n{Colors.BOLD}📊 SSL Setup Summary{Colors.END}")
        print("=" * 50)
        print(f"{Colors.GREEN}Completed: {len(self.completed_tasks)}{Colors.END}")
        if self.warnings:
            print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.END}")
        if self.errors:
            print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.END}")
        
        if self.errors:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SSL SETUP FAILED{Colors.END}")
            print("Review the errors above and try again.")
            return False
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ SSL SETUP SUCCESSFUL{Colors.END}")
            print(f"🌐 Your domain: https://{self.domain}")
            print(f"🔒 SSL certificate: Valid")
            print(f"🔄 Auto-renewal: Configured")
            
            if not self.test_cert:
                print(f"\n{Colors.BLUE}📋 Next Steps:{Colors.END}")
                print("1. Test your site: https://{self.domain}")
                print("2. Check SSL grade: https://www.ssllabs.com/ssltest/")
                print("3. Monitor certificate expiry")
            else:
                print(f"\n{Colors.YELLOW}⚠️  Test Certificate Notice:{Colors.END}")
                print("This is a staging certificate. For production, run without --test-cert")
            
            return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Setup SSL certificates for Cibozer')
    parser.add_argument('--domain', required=True, help='Primary domain name')
    parser.add_argument('--email', help='Email for Let\'s Encrypt registration')
    parser.add_argument('--nginx-config', action='store_true',
                       help='Update Nginx configuration')
    parser.add_argument('--test-cert', action='store_true',
                       help='Use Let\'s Encrypt staging server (test certificate)')
    parser.add_argument('--renew', action='store_true',
                       help='Renew existing certificates')
    
    args = parser.parse_args()
    
    if args.renew:
        # Simple renewal
        result = subprocess.run(['certbot', 'renew'], check=False)
        if result.returncode == 0:
            subprocess.run(['systemctl', 'reload', 'nginx'])
            print("✅ Certificate renewal completed")
        else:
            print("❌ Certificate renewal failed")
        sys.exit(result.returncode)
    
    ssl_setup = SSLSetup(
        domain=args.domain,
        email=args.email,
        test_cert=args.test_cert
    )
    
    success = ssl_setup.setup_ssl(update_nginx=args.nginx_config)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()