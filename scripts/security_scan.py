#!/usr/bin/env python3
"""Security scanning script for dependencies and code"""

import subprocess
import sys
import json
from datetime import datetime

def run_safety_check():
    """Run safety check on Python dependencies"""
    print("Running safety check on Python dependencies...")
    try:
        result = subprocess.run(['safety', 'check', '--json'], 
                              capture_output=True, text=True)
        vulnerabilities = json.loads(result.stdout)
        
        if vulnerabilities:
            print(f"Found {len(vulnerabilities)} vulnerabilities:")
            for vuln in vulnerabilities:
                print(f"  - {vuln['package']}: {vuln['installed_version']} - {vuln['vulnerability']}")
        else:
            print("No vulnerabilities found in Python dependencies")
        
        return vulnerabilities
    except Exception as e:
        print(f"Error running safety check: {e}")
        return []

def run_bandit_scan():
    """Run bandit security linter on Python code"""
    print("\nRunning bandit security scan on Python code...")
    try:
        result = subprocess.run(['bandit', '-r', '.', '-f', 'json'], 
                              capture_output=True, text=True)
        issues = json.loads(result.stdout)
        
        if issues['results']:
            print(f"Found {len(issues['results'])} security issues:")
            for issue in issues['results']:
                print(f"  - {issue['filename']}:{issue['line_number']} - {issue['issue_text']}")
        else:
            print("No security issues found in Python code")
        
        return issues
    except Exception as e:
        print(f"Error running bandit scan: {e}")
        return {}

def check_secrets():
    """Check for hardcoded secrets"""
    print("\nChecking for hardcoded secrets...")
    try:
        # Use detect-secrets or similar tool
        result = subprocess.run(['grep', '-r', '-E', 
                               '(api_key|password|secret|token)\s*=\s*["'][^"']+["']',
                               '.', '--include=*.py'], 
                              capture_output=True, text=True)
        
        if result.stdout:
            print("Potential secrets found:")
            print(result.stdout)
        else:
            print("No obvious secrets found")
        
        return result.stdout
    except Exception as e:
        print(f"Error checking for secrets: {e}")
        return ""

def main():
    """Run all security scans"""
    print(f"Security Scan Report - {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run all scans
    safety_results = run_safety_check()
    bandit_results = run_bandit_scan()
    secrets_results = check_secrets()
    
    # Generate report
    report = {
        'scan_date': datetime.now().isoformat(),
        'dependency_vulnerabilities': len(safety_results),
        'code_issues': len(bandit_results.get('results', [])),
        'potential_secrets': bool(secrets_results)
    }
    
    # Save report
    with open('security_scan_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("\nScan complete. Report saved to security_scan_report.json")
    
    # Exit with error if issues found
    if report['dependency_vulnerabilities'] > 0 or report['code_issues'] > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
