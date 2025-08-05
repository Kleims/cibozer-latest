#!/usr/bin/env python3
"""
Cibozer Security Bulletproofing Script
Systematically identifies and fixes security vulnerabilities
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Color codes for output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class SecurityAuditor:
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.project_root = Path(os.path.dirname(os.path.abspath(__file__)))
        
    def log_issue(self, severity, category, description, file_path=None, line_num=None):
        """Log a security issue"""
        issue = {
            'severity': severity,
            'category': category,
            'description': description,
            'file_path': file_path,
            'line_num': line_num,
            'timestamp': datetime.now().isoformat()
        }
        self.issues.append(issue)
        
        # Print immediately
        color = RED if severity == 'CRITICAL' else YELLOW
        print(f"{color}[{severity}] {category}: {description}{RESET}")
        if file_path:
            print(f"  File: {file_path}:{line_num if line_num else ''}")
    
    def log_fix(self, description, file_path=None):
        """Log a fix that was applied"""
        fix = {
            'description': description,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        self.fixes_applied.append(fix)
        print(f"{GREEN}[FIXED] {description}{RESET}")
        if file_path:
            print(f"  File: {file_path}")
    
    def generate_report(self):
        """Generate security audit report"""
        report = {
            'audit_date': datetime.now().isoformat(),
            'total_issues': len(self.issues),
            'total_fixes': len(self.fixes_applied),
            'issues_by_severity': {},
            'issues_by_category': {},
            'issues': self.issues,
            'fixes_applied': self.fixes_applied
        }
        
        # Count by severity
        for issue in self.issues:
            severity = issue['severity']
            report['issues_by_severity'][severity] = report['issues_by_severity'].get(severity, 0) + 1
            
            category = issue['category']
            report['issues_by_category'][category] = report['issues_by_category'].get(category, 0) + 1
        
        # Save report
        report_path = self.project_root / 'security_audit_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{BLUE}Security Audit Report saved to: {report_path}{RESET}")
        print(f"\nSummary:")
        print(f"  Total Issues Found: {len(self.issues)}")
        print(f"  Total Fixes Applied: {len(self.fixes_applied)}")
        print(f"\nIssues by Severity:")
        for severity, count in report['issues_by_severity'].items():
            print(f"  {severity}: {count}")

def main():
    print(f"{BLUE}Starting Cibozer Security Bulletproofing...{RESET}\n")
    
    auditor = SecurityAuditor()
    
    # Import fix functions
    from security_fixes import (
        fix_authentication_vulnerabilities,
        fix_input_validation,
        fix_api_security,
        fix_cors_configuration,
        fix_error_handling,
        fix_database_security,
        fix_file_operations,
        fix_session_security,
        fix_rate_limiting,
        fix_logging_security,
        add_security_headers,
        add_dependency_scanning,
        add_security_middleware
    )
    
    # Run security fixes
    print(f"{YELLOW}1. Fixing Authentication Vulnerabilities...{RESET}")
    fix_authentication_vulnerabilities(auditor)
    
    print(f"\n{YELLOW}2. Fixing Input Validation...{RESET}")
    fix_input_validation(auditor)
    
    print(f"\n{YELLOW}3. Fixing API Security...{RESET}")
    fix_api_security(auditor)
    
    print(f"\n{YELLOW}4. Fixing CORS Configuration...{RESET}")
    fix_cors_configuration(auditor)
    
    print(f"\n{YELLOW}5. Fixing Error Handling...{RESET}")
    fix_error_handling(auditor)
    
    print(f"\n{YELLOW}6. Fixing Database Security...{RESET}")
    fix_database_security(auditor)
    
    print(f"\n{YELLOW}7. Fixing File Operations...{RESET}")
    fix_file_operations(auditor)
    
    print(f"\n{YELLOW}8. Fixing Session Security...{RESET}")
    fix_session_security(auditor)
    
    print(f"\n{YELLOW}9. Fixing Rate Limiting...{RESET}")
    fix_rate_limiting(auditor)
    
    print(f"\n{YELLOW}10. Fixing Logging Security...{RESET}")
    fix_logging_security(auditor)
    
    print(f"\n{YELLOW}11. Adding Security Headers...{RESET}")
    add_security_headers(auditor)
    
    print(f"\n{YELLOW}12. Adding Dependency Scanning...{RESET}")
    add_dependency_scanning(auditor)
    
    print(f"\n{YELLOW}13. Adding Security Middleware...{RESET}")
    add_security_middleware(auditor)
    
    # Generate report
    auditor.generate_report()
    
    print(f"\n{GREEN}Security bulletproofing complete!{RESET}")

if __name__ == '__main__':
    main()