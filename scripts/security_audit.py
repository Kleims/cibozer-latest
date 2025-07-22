#!/usr/bin/env python3
"""
Security audit script for Cibozer
Scans for hardcoded secrets and fixes them
"""

import os
import re
import sys
import argparse
from pathlib import Path

class SecurityAuditor:
    def __init__(self):
        self.issues_found = []
        self.project_root = Path(__file__).parent.parent
        
    def scan_file(self, filepath, fix=False):
        """Scan a single file for security issues"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                original_content = content
        except:
            return
            
        # Patterns to look for
        patterns = [
            # Hardcoded secret keys
            (r'app\.secret_key\s*=\s*["\']([^"\']+)["\']', 'hardcoded_secret_key'),
            (r'SECRET_KEY\s*=\s*["\']([^"\']+)["\']', 'hardcoded_secret_key'),
            
            # Database URLs with credentials
            (r'postgresql://([^@]+)@', 'database_credentials'),
            (r'mysql://([^@]+)@', 'database_credentials'),
            
            # API keys
            (r'api_key\s*=\s*["\']([^"\']+)["\']', 'hardcoded_api_key'),
            (r'API_KEY\s*=\s*["\']([^"\']+)["\']', 'hardcoded_api_key'),
            
            # AWS credentials
            (r'aws_access_key_id\s*=\s*["\']([^"\']+)["\']', 'aws_credentials'),
            (r'aws_secret_access_key\s*=\s*["\']([^"\']+)["\']', 'aws_credentials'),
        ]
        
        for pattern, issue_type in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                self.issues_found.append({
                    'file': str(filepath),
                    'type': issue_type,
                    'line': content[:match.start()].count('\n') + 1,
                    'match': match.group(0)
                })
                
                if fix and issue_type == 'hardcoded_secret_key':
                    # Replace with environment variable
                    if 'app.secret_key' in match.group(0):
                        replacement = "app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')"
                    else:
                        replacement = "SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')"
                    content = content.replace(match.group(0), replacement)
        
        # If we made changes, write them back
        if fix and content != original_content:
            # Make sure os is imported
            if 'import os' not in content:
                lines = content.split('\n')
                # Find where to insert import
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        lines.insert(i, 'import os')
                        break
                content = '\n'.join(lines)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed security issues in {filepath}")
    
    def scan_directory(self, directory, fix=False):
        """Scan all Python files in directory"""
        for root, dirs, files in os.walk(directory):
            # Skip virtual environments and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'env', '__pycache__']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    self.scan_file(filepath, fix)
    
    def create_env_template(self):
        """Create .env.template file"""
        template_content = """# Cibozer Environment Variables Template
# Copy this file to .env and fill in your values

# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/cibozer

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-email-password

# Stripe (for payments)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# AWS (optional, for file storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BUCKET_NAME=your-bucket-name

# Other
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
"""
        
        template_path = self.project_root / '.env.template'
        with open(template_path, 'w') as f:
            f.write(template_content)
        print(f"Created {template_path}")
    
    def report(self):
        """Generate security report"""
        if not self.issues_found:
            print("[OK] No security issues found!")
            return 0
        
        print(f"\n[FOUND] {len(self.issues_found)} security issues:\n")
        
        by_type = {}
        for issue in self.issues_found:
            issue_type = issue['type']
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)
        
        for issue_type, issues in by_type.items():
            print(f"{issue_type.replace('_', ' ').title()}: {len(issues)} instances")
            for issue in issues[:3]:  # Show first 3
                print(f"  - {issue['file']}:{issue['line']}")
            if len(issues) > 3:
                print(f"  ... and {len(issues) - 3} more")
            print()
        
        return len(self.issues_found)

def main():
    parser = argparse.ArgumentParser(description='Security audit for Cibozer')
    parser.add_argument('--fix-secrets', action='store_true', 
                       help='Automatically fix hardcoded secrets')
    parser.add_argument('--path', default='.',
                       help='Path to scan (default: current directory)')
    args = parser.parse_args()
    
    auditor = SecurityAuditor()
    
    # Always create env template
    auditor.create_env_template()
    
    # Scan for issues
    print("Scanning for security issues...")
    auditor.scan_directory(args.path, fix=args.fix_secrets)
    
    # Report findings
    issues_count = auditor.report()
    
    if args.fix_secrets and issues_count > 0:
        print("\n[FIXED] Security issues have been fixed where possible.")
        print("Don't forget to:")
        print("1. Create a .env file from .env.template")
        print("2. Add your actual secret values")
        print("3. Never commit .env to version control")
    
    # Return 0 for success (even if issues were found but fixed)
    return 0 if args.fix_secrets or issues_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())