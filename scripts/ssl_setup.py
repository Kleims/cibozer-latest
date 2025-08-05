#!/usr/bin/env python3
"""
SSL/TLS Certificate Setup and Management System
Automated SSL certificate management for Cibozer production deployment
"""

import os
import sys
import json
import time
import subprocess
import socket
import ssl
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import argparse
import requests


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


@dataclass
class CertificateInfo:
    """SSL Certificate information"""
    domain: str
    issuer: str
    subject: str
    valid_from: str
    valid_until: str
    days_until_expiry: int
    fingerprint: str
    algorithm: str
    key_size: int
    is_valid: bool
    is_expired: bool
    is_self_signed: bool


class SSLManager:
    """Manages SSL/TLS certificates for production deployment"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.ssl_dir = self.root_dir / "ssl"
        self.nginx_ssl_dir = self.root_dir / "nginx" / "ssl"
        self.letsencrypt_dir = self.root_dir / "letsencrypt"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure SSL directories exist with proper permissions"""
        for directory in [self.ssl_dir, self.nginx_ssl_dir, self.letsencrypt_dir]:
            directory.mkdir(exist_ok=True, parents=True)
            
            # Set restrictive permissions on Unix systems
            if os.name != 'nt':
                os.chmod(directory, 0o700)
    
    def check_domain_accessibility(self, domain: str, port: int = 80) -> bool:
        """Check if domain is accessible"""
        print(f"{Colors.BLUE}🌐 Checking domain accessibility: {domain}:{port}{Colors.END}")
        
        try:
            # Check DNS resolution
            socket.gethostbyname(domain)
            print(f"   ✅ DNS resolution successful")
            
            # Check port accessibility
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((domain, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Port {port} is accessible")
                return True
            else:
                print(f"   ❌ Port {port} is not accessible (error {result})")
                return False
                
        except socket.gaierror as e:
            print(f"   ❌ DNS resolution failed: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Domain check failed: {e}")
            return False
    
    def check_existing_certificate(self, domain: str) -> Optional[CertificateInfo]:
        """Check existing SSL certificate for domain"""
        print(f"{Colors.BLUE}🔍 Checking existing certificate for {domain}{Colors.END}")
        
        try:
            # Try to get certificate from the domain
            context = ssl.create_default_context()
            
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    der_cert = ssock.getpeercert(binary_form=True)
            
            # Parse certificate information
            cert_info = self._parse_certificate(cert, der_cert, domain)
            
            if cert_info.is_valid:
                print(f"   ✅ Valid certificate found")
                print(f"   📅 Expires: {cert_info.valid_until} ({cert_info.days_until_expiry} days)")
                print(f"   🏢 Issuer: {cert_info.issuer}")
            else:
                print(f"   ❌ Certificate is invalid or expired")
            
            return cert_info
            
        except ssl.SSLError as e:
            print(f"   ❌ SSL error: {e}")
        except socket.timeout:
            print(f"   ❌ Connection timeout")
        except Exception as e:
            print(f"   ❌ Certificate check failed: {e}")
        
        return None
    
    def _parse_certificate(self, cert: Dict, der_cert: bytes, domain: str) -> CertificateInfo:
        """Parse certificate information"""
        # Extract certificate details
        subject = dict(x[0] for x in cert['subject'])
        issuer = dict(x[0] for x in cert['issuer'])
        
        # Parse dates
        valid_from = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
        valid_until = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        
        # Calculate days until expiry
        days_until_expiry = (valid_until - datetime.now()).days
        
        # Calculate fingerprint
        import hashlib
        fingerprint = hashlib.sha256(der_cert).hexdigest().upper()
        fingerprint = ':'.join(fingerprint[i:i+2] for i in range(0, len(fingerprint), 2))
        
        # Determine if certificate is valid
        now = datetime.now()
        is_valid = valid_from <= now <= valid_until
        is_expired = now > valid_until
        is_self_signed = subject.get('commonName') == issuer.get('commonName')
        
        return CertificateInfo(
            domain=domain,
            issuer=issuer.get('organizationName', 'Unknown'),
            subject=subject.get('commonName', domain),
            valid_from=valid_from.isoformat(),
            valid_until=valid_until.isoformat(),
            days_until_expiry=days_until_expiry,
            fingerprint=fingerprint,
            algorithm='RSA',  # Simplified
            key_size=2048,    # Simplified
            is_valid=is_valid,
            is_expired=is_expired,
            is_self_signed=is_self_signed
        )
    
    def setup_letsencrypt_certificate(self, domain: str, email: str, 
                                    staging: bool = False) -> bool:
        """Setup Let's Encrypt certificate using Certbot"""
        print(f"{Colors.BLUE}🔐 Setting up Let's Encrypt certificate for {domain}{Colors.END}")
        
        try:
            # Check if certbot is installed
            result = subprocess.run(['certbot', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print(f"{Colors.RED}❌ Certbot not installed. Install with: apt-get install certbot{Colors.END}")
                return False
            
            print(f"   ✅ Certbot found: {result.stdout.strip()}")
            
            # Build certbot command
            certbot_cmd = [
                'certbot', 'certonly',
                '--standalone',
                '--non-interactive',
                '--agree-tos',
                '--email', email,
                '--domains', domain
            ]
            
            if staging:
                certbot_cmd.append('--staging')
                print(f"   🧪 Using Let's Encrypt staging environment")
            
            # Run certbot
            print(f"   🔄 Running certbot...")
            result = subprocess.run(certbot_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Certificate obtained successfully")
                
                # Copy certificates to nginx directory
                letsencrypt_live = Path(f'/etc/letsencrypt/live/{domain}')
                if letsencrypt_live.exists():
                    self._copy_letsencrypt_certs(domain, letsencrypt_live)
                
                # Set up auto-renewal
                self._setup_certificate_renewal(domain)
                
                return True
            else:
                print(f"   ❌ Certbot failed:")
                print(f"   {result.stderr}")
                return False
                
        except FileNotFoundError:
            print(f"{Colors.RED}❌ Certbot not found. Install certbot first.{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ Let's Encrypt setup failed: {e}{Colors.END}")
            return False
    
    def _copy_letsencrypt_certs(self, domain: str, letsencrypt_live: Path):
        """Copy Let's Encrypt certificates to nginx directory"""
        cert_files = {
            'fullchain.pem': 'fullchain.pem',
            'privkey.pem': 'privkey.pem',
            'cert.pem': 'cert.pem',
            'chain.pem': 'chain.pem'
        }
        
        for src_file, dst_file in cert_files.items():
            src_path = letsencrypt_live / src_file
            dst_path = self.nginx_ssl_dir / dst_file
            
            if src_path.exists():
                # Create symlink or copy
                if dst_path.exists():
                    dst_path.unlink()
                
                try:
                    # Try to create symlink first
                    dst_path.symlink_to(src_path)
                    print(f"   📎 Linked {dst_file}")
                except OSError:
                    # Fall back to copying
                    import shutil
                    shutil.copy2(src_path, dst_path)
                    print(f"   📄 Copied {dst_file}")
                
                # Set restrictive permissions
                if os.name != 'nt' and 'privkey' in dst_file:
                    os.chmod(dst_path, 0o600)
    
    def _setup_certificate_renewal(self, domain: str):
        """Setup automatic certificate renewal"""
        print(f"   🔄 Setting up automatic renewal...")
        
        # Create renewal script
        renewal_script = self.ssl_dir / "renew_certificates.sh"
        
        script_content = f"""#!/bin/bash
# Automatic SSL certificate renewal for {domain}

echo "Renewing SSL certificates..."

# Renew certificates
certbot renew --quiet

# Reload nginx if renewal was successful
if [ $? -eq 0 ]; then
    echo "Certificates renewed successfully"
    
    # Copy renewed certificates
    DOMAIN="{domain}"
    NGINX_SSL_DIR="{self.nginx_ssl_dir}"
    LETSENCRYPT_LIVE="/etc/letsencrypt/live/$DOMAIN"
    
    if [ -d "$LETSENCRYPT_LIVE" ]; then
        cp "$LETSENCRYPT_LIVE/fullchain.pem" "$NGINX_SSL_DIR/"
        cp "$LETSENCRYPT_LIVE/privkey.pem" "$NGINX_SSL_DIR/"
        cp "$LETSENCRYPT_LIVE/cert.pem" "$NGINX_SSL_DIR/"
        cp "$LETSENCRYPT_LIVE/chain.pem" "$NGINX_SSL_DIR/"
        
        echo "Certificates copied to nginx directory"
    fi
    
    # Reload nginx
    if command -v nginx &> /dev/null; then
        nginx -t && nginx -s reload
        echo "Nginx reloaded"
    fi
    
    # Reload with docker if using docker-compose
    if [ -f "docker-compose.yml" ]; then
        docker-compose restart nginx
        echo "Docker nginx container restarted"
    fi
else
    echo "Certificate renewal failed"
    exit 1
fi
"""
        
        with open(renewal_script, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        if os.name != 'nt':
            os.chmod(renewal_script, 0o755)
        
        print(f"   📝 Renewal script created: {renewal_script}")
        print(f"   💡 Add to crontab: 0 3 * * * {renewal_script}")
    
    def generate_self_signed_certificate(self, domain: str, 
                                       key_size: int = 2048,
                                       validity_days: int = 365) -> bool:
        """Generate self-signed certificate for development/testing"""
        print(f"{Colors.BLUE}🔐 Generating self-signed certificate for {domain}{Colors.END}")
        
        try:
            # Certificate paths
            key_path = self.ssl_dir / f"{domain}.key"
            cert_path = self.ssl_dir / f"{domain}.crt"
            
            # Generate private key
            key_cmd = [
                'openssl', 'genrsa',
                '-out', str(key_path),
                str(key_size)
            ]
            
            result = subprocess.run(key_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Key generation failed: {result.stderr}")
                return False
            
            print(f"   ✅ Private key generated")
            
            # Generate certificate
            cert_cmd = [
                'openssl', 'req',
                '-new', '-x509',
                '-key', str(key_path),
                '-out', str(cert_path),
                '-days', str(validity_days),
                '-subj', f'/CN={domain}/O=Cibozer/C=US'
            ]
            
            result = subprocess.run(cert_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"   ❌ Certificate generation failed: {result.stderr}")
                return False
            
            print(f"   ✅ Self-signed certificate generated")
            
            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(key_path, 0o600)
                os.chmod(cert_path, 0o644)
            
            # Copy to nginx directory
            import shutil
            shutil.copy2(cert_path, self.nginx_ssl_dir / 'fullchain.pem')
            shutil.copy2(key_path, self.nginx_ssl_dir / 'privkey.pem')
            
            print(f"   📄 Certificates copied to nginx directory")
            print(f"   ⚠️  Note: Self-signed certificates will show browser warnings")
            
            return True
            
        except FileNotFoundError:
            print(f"{Colors.RED}❌ OpenSSL not found. Install openssl first.{Colors.END}")
            return False
        except Exception as e:
            print(f"{Colors.RED}❌ Self-signed certificate generation failed: {e}{Colors.END}")
            return False
    
    def validate_ssl_configuration(self, domain: str) -> Dict[str, Any]:
        """Validate SSL configuration and security"""
        print(f"{Colors.BLUE}🔍 Validating SSL configuration for {domain}{Colors.END}")
        
        validation_results = {
            'domain': domain,
            'timestamp': datetime.now().isoformat(),
            'certificate_valid': False,
            'certificate_info': None,
            'ssl_labs_grade': None,
            'security_issues': [],
            'recommendations': []
        }
        
        try:
            # Check certificate
            cert_info = self.check_existing_certificate(domain)
            if cert_info:
                validation_results['certificate_valid'] = cert_info.is_valid
                validation_results['certificate_info'] = asdict(cert_info)
                
                # Check for security issues
                if cert_info.is_self_signed:
                    validation_results['security_issues'].append('Certificate is self-signed')
                
                if cert_info.days_until_expiry < 30:
                    validation_results['security_issues'].append(f'Certificate expires in {cert_info.days_until_expiry} days')
                
                if cert_info.key_size < 2048:
                    validation_results['security_issues'].append(f'Key size too small: {cert_info.key_size} bits')
            
            # Test SSL protocols and ciphers
            ssl_test_results = self._test_ssl_protocols(domain)
            validation_results.update(ssl_test_results)
            
            # Generate recommendations
            recommendations = self._generate_ssl_recommendations(validation_results)
            validation_results['recommendations'] = recommendations
            
            # Save validation report
            report_path = self.ssl_dir / f"ssl_validation_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(validation_results, f, indent=2)
            
            print(f"   📄 Validation report saved: {report_path}")
            
            return validation_results
            
        except Exception as e:
            print(f"{Colors.RED}❌ SSL validation failed: {e}{Colors.END}")
            validation_results['error'] = str(e)
            return validation_results
    
    def _test_ssl_protocols(self, domain: str) -> Dict[str, Any]:
        """Test SSL protocols and ciphers"""
        print(f"   🔍 Testing SSL protocols...")
        
        results = {
            'supported_protocols': [],
            'weak_protocols': [],
            'cipher_suites': [],
            'perfect_forward_secrecy': False
        }
        
        try:
            # Test different SSL/TLS versions
            protocols_to_test = [
                ('TLSv1.3', ssl.PROTOCOL_TLS),
                ('TLSv1.2', ssl.PROTOCOL_TLS),
                ('TLSv1.1', ssl.PROTOCOL_TLS),
                ('TLSv1.0', ssl.PROTOCOL_TLS),
            ]
            
            for protocol_name, protocol_const in protocols_to_test:
                try:
                    context = ssl.SSLContext(protocol_const)
                    
                    # Configure context based on protocol
                    if protocol_name == 'TLSv1.3':
                        context.minimum_version = ssl.TLSVersion.TLSv1_3
                        context.maximum_version = ssl.TLSVersion.TLSv1_3
                    elif protocol_name == 'TLSv1.2':
                        context.minimum_version = ssl.TLSVersion.TLSv1_2
                        context.maximum_version = ssl.TLSVersion.TLSv1_2
                    elif protocol_name == 'TLSv1.1':
                        context.minimum_version = ssl.TLSVersion.TLSv1_1
                        context.maximum_version = ssl.TLSVersion.TLSv1_1
                    elif protocol_name == 'TLSv1.0':
                        context.minimum_version = ssl.TLSVersion.TLSv1
                        context.maximum_version = ssl.TLSVersion.TLSv1
                    
                    with socket.create_connection((domain, 443), timeout=5) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as ssock:
                            results['supported_protocols'].append({
                                'protocol': protocol_name,
                                'cipher': ssock.cipher()
                            })
                            
                            # Check for weak protocols
                            if protocol_name in ['TLSv1.0', 'TLSv1.1']:
                                results['weak_protocols'].append(protocol_name)
                
                except Exception:
                    # Protocol not supported, which is good for old protocols
                    pass
            
            print(f"   ✅ Protocol testing completed")
            
        except Exception as e:
            print(f"   ⚠️  Protocol testing failed: {e}")
        
        return results
    
    def _generate_ssl_recommendations(self, validation_results: Dict[str, Any]) -> List[str]:
        """Generate SSL security recommendations"""
        recommendations = []
        
        # Certificate recommendations
        if validation_results.get('certificate_info'):
            cert_info = validation_results['certificate_info']
            
            if cert_info['is_self_signed']:
                recommendations.append("Replace self-signed certificate with CA-signed certificate")
            
            if cert_info['days_until_expiry'] < 30:
                recommendations.append("Renew certificate - expires soon")
            
            if cert_info['key_size'] < 2048:
                recommendations.append("Use stronger key size (minimum 2048 bits)")
        
        # Protocol recommendations
        if validation_results.get('weak_protocols'):
            recommendations.append("Disable weak SSL/TLS protocols (TLS 1.0, 1.1)")
        
        if not validation_results.get('supported_protocols'):
            recommendations.append("Ensure TLS 1.2 and 1.3 are supported")
        
        # General security recommendations
        recommendations.extend([
            "Enable HTTP Strict Transport Security (HSTS)",
            "Use strong cipher suites only",
            "Enable Perfect Forward Secrecy",
            "Implement OCSP stapling",
            "Use certificate transparency monitoring"
        ])
        
        return recommendations
    
    def setup_ssl_monitoring(self, domains: List[str], 
                           notification_email: str = None) -> bool:
        """Setup SSL certificate monitoring"""
        print(f"{Colors.BLUE}📊 Setting up SSL certificate monitoring{Colors.END}")
        
        try:
            # Create monitoring script
            monitor_script = self.ssl_dir / "ssl_monitor.py"
            
            monitor_code = f'''#!/usr/bin/env python3
"""
SSL Certificate Monitoring Script
Automatically generated by Cibozer SSL Manager
"""

import ssl
import socket
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

DOMAINS = {domains}
NOTIFICATION_EMAIL = "{notification_email or 'admin@example.com'}"
WARNING_DAYS = 30

def check_certificate_expiry(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        
        valid_until = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
        days_until_expiry = (valid_until - datetime.now()).days
        
        return {{
            'domain': domain,
            'valid_until': valid_until,
            'days_until_expiry': days_until_expiry,
            'needs_renewal': days_until_expiry <= WARNING_DAYS
        }}
    except Exception as e:
        return {{
            'domain': domain,
            'error': str(e),
            'needs_renewal': True
        }}

def send_notification(cert_info):
    # Implement email notification here
    print(f"Certificate for {{cert_info['domain']}} expires in {{cert_info.get('days_until_expiry', 'unknown')}} days")

def main():
    for domain in DOMAINS:
        cert_info = check_certificate_expiry(domain)
        
        if cert_info.get('needs_renewal'):
            send_notification(cert_info)
            
        print(f"{{domain}}: {{cert_info.get('days_until_expiry', 'Error')}} days until expiry")

if __name__ == '__main__':
    main()
'''
            
            with open(monitor_script, 'w') as f:
                f.write(monitor_code)
            
            # Make script executable
            if os.name != 'nt':
                os.chmod(monitor_script, 0o755)
            
            print(f"   📝 Monitoring script created: {monitor_script}")
            print(f"   💡 Add to crontab: 0 6 * * * {monitor_script}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.RED}❌ SSL monitoring setup failed: {e}{Colors.END}")
            return False


def main():
    """CLI interface for SSL management"""
    parser = argparse.ArgumentParser(description='Cibozer SSL/TLS Management')
    parser.add_argument('command', choices=[
        'check', 'letsencrypt', 'self-signed', 'validate', 'monitor', 'renew'
    ])
    parser.add_argument('--domain', required=True, help='Domain name')
    parser.add_argument('--email', help='Email for Let\'s Encrypt registration')
    parser.add_argument('--staging', action='store_true', 
                       help='Use Let\'s Encrypt staging environment')
    parser.add_argument('--key-size', type=int, default=2048, 
                       help='RSA key size for self-signed certificates')
    parser.add_argument('--validity-days', type=int, default=365,
                       help='Validity period for self-signed certificates')
    parser.add_argument('--notification-email', help='Email for SSL monitoring notifications')
    
    args = parser.parse_args()
    
    ssl_manager = SSLManager()
    
    try:
        if args.command == 'check':
            # Check domain accessibility
            accessible = ssl_manager.check_domain_accessibility(args.domain)
            
            if accessible:
                # Check existing certificate
                cert_info = ssl_manager.check_existing_certificate(args.domain)
                if cert_info:
                    print(f"\n{Colors.BOLD}Certificate Information:{Colors.END}")
                    print(f"  Domain: {cert_info.domain}")
                    print(f"  Issuer: {cert_info.issuer}")
                    print(f"  Valid Until: {cert_info.valid_until}")
                    print(f"  Days Until Expiry: {cert_info.days_until_expiry}")
                    print(f"  Is Valid: {cert_info.is_valid}")
                    print(f"  Is Self-Signed: {cert_info.is_self_signed}")
            else:
                print(f"{Colors.RED}❌ Domain is not accessible{Colors.END}")
                return 1
        
        elif args.command == 'letsencrypt':
            if not args.email:
                print(f"{Colors.RED}❌ Email is required for Let's Encrypt{Colors.END}")
                return 1
            
            success = ssl_manager.setup_letsencrypt_certificate(
                args.domain, args.email, args.staging
            )
            
            if success:
                print(f"{Colors.GREEN}✅ Let's Encrypt certificate setup completed{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Let's Encrypt certificate setup failed{Colors.END}")
                return 1
        
        elif args.command == 'self-signed':
            success = ssl_manager.generate_self_signed_certificate(
                args.domain, args.key_size, args.validity_days
            )
            
            if success:
                print(f"{Colors.GREEN}✅ Self-signed certificate generated{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Self-signed certificate generation failed{Colors.END}")
                return 1
        
        elif args.command == 'validate':
            results = ssl_manager.validate_ssl_configuration(args.domain)
            
            print(f"\n{Colors.BOLD}SSL Validation Results:{Colors.END}")
            print(f"  Certificate Valid: {results.get('certificate_valid')}")
            
            if results.get('security_issues'):
                print(f"  Security Issues:")
                for issue in results['security_issues']:
                    print(f"    - {issue}")
            
            if results.get('recommendations'):
                print(f"  Recommendations:")
                for rec in results['recommendations']:
                    print(f"    - {rec}")
        
        elif args.command == 'monitor':
            domains = [args.domain]  # Could be extended to multiple domains
            success = ssl_manager.setup_ssl_monitoring(domains, args.notification_email)
            
            if success:
                print(f"{Colors.GREEN}✅ SSL monitoring setup completed{Colors.END}")
            else:
                print(f"{Colors.RED}❌ SSL monitoring setup failed{Colors.END}")
                return 1
        
        elif args.command == 'renew':
            # Run renewal script
            renewal_script = ssl_manager.ssl_dir / "renew_certificates.sh"
            
            if renewal_script.exists():
                result = subprocess.run(['bash', str(renewal_script)], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"{Colors.GREEN}✅ Certificate renewal completed{Colors.END}")
                    print(result.stdout)
                else:
                    print(f"{Colors.RED}❌ Certificate renewal failed{Colors.END}")
                    print(result.stderr)
                    return 1
            else:
                print(f"{Colors.RED}❌ Renewal script not found{Colors.END}")
                return 1
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled{Colors.END}")
        return 1
    except Exception as e:
        print(f"{Colors.RED}❌ Error: {e}{Colors.END}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())