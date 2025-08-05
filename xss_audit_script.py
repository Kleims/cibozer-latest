#!/usr/bin/env python3
"""
XSS Vulnerability Audit Script for Jinja2 Templates
Scans all HTML templates for potential XSS vulnerabilities
"""

import os
import re
from pathlib import Path

# XSS vulnerability patterns to check for
patterns = {
    'unsafe_output': r'\{\{\s*[^|]*(?:\|safe|\|raw)\s*\}\}',  # {{ variable|safe }} or {{ variable|raw }}
    'direct_output': r'\{\{\s*request\.[^}]*\}\}',  # {{ request.args.something }}
    'unescaped_html': r'<[^>]*\{\{[^}]*\}\}[^>]*>',  # HTML attributes with Jinja
    'javascript_injection': r'<script[^>]*>\s*.*\{\{.*\}\}.*</script>',  # JS with Jinja
    'style_injection': r'<style[^>]*>.*\{\{.*\}\}.*</style>',  # CSS with Jinja
    'onclick_injection': r'on\w+\s*=\s*[\'\"]\s*\{\{.*\}\}',  # onclick="{{ variable }}"
    'href_injection': r'href\s*=\s*[\'\"]\s*\{\{.*\}\}',  # href="{{ variable }}"
    'src_injection': r'src\s*=\s*[\'\"]\s*\{\{.*\}\}',  # src="{{ variable }}"
}

def scan_file(file_path):
    """Scan a single file for XSS vulnerabilities"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_vulns = []
        for vuln_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context = match.group(0)[:100]  # First 100 chars of match
                file_vulns.append({
                    'type': vuln_type,
                    'line': line_num,
                    'context': context,
                    'match': match.group(0)
                })
        
        return file_vulns
            
    except Exception as e:
        print(f'Error reading {file_path}: {e}')
        return []

def main():
    """Main audit function"""
    # Find all HTML template files
    template_dir = Path('templates')
    if not template_dir.exists():
        print('Templates directory not found')
        return 1

    vulnerabilities = []
    scanned_files = 0

    # Scan all HTML files
    for html_file in template_dir.rglob('*.html'):
        scanned_files += 1
        file_vulns = scan_file(html_file)
        
        if file_vulns:
            vulnerabilities.append({
                'file': str(html_file),
                'vulnerabilities': file_vulns
            })

    print(f'=== XSS VULNERABILITY AUDIT RESULTS ===')
    print(f'Scanned {scanned_files} template files')
    print(f'Found vulnerabilities in {len(vulnerabilities)} files')
    print()

    if vulnerabilities:
        for file_data in vulnerabilities:
            print(f'ALERT FILE: {file_data["file"]}')
            for vuln in file_data['vulnerabilities']:
                print(f'   ERROR {vuln["type"].upper()} (line {vuln["line"]})')
                print(f'      Context: {vuln["context"]}')
            print()
        
        # Summary of vulnerability types
        vuln_types = {}
        for file_data in vulnerabilities:
            for vuln in file_data['vulnerabilities']:
                vuln_type = vuln['type']
                if vuln_type not in vuln_types:
                    vuln_types[vuln_type] = 0
                vuln_types[vuln_type] += 1
        
        print('=== VULNERABILITY SUMMARY ===')
        for vuln_type, count in sorted(vuln_types.items()):
            print(f'{vuln_type}: {count} instances')
        
        return 1  # Exit code 1 for vulnerabilities found
    else:
        print('SUCCESS: No obvious XSS vulnerabilities found!')
        return 0

if __name__ == '__main__':
    exit(main())