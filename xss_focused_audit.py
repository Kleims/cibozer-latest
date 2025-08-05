#!/usr/bin/env python3
"""
Focused XSS Vulnerability Audit Script - Only Real Vulnerabilities
Checks for actual user-controlled data being output without escaping
"""

import os
import re
from pathlib import Path

def scan_for_real_xss(file_path):
    """Scan for actual XSS vulnerabilities (user data without escaping)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        vulnerabilities = []
        
        # Check for direct user data output without escaping
        patterns = [
            # User-controlled data patterns
            (r'\{\{\s*[^}]*\.name\s*\}\}(?!\|e)', 'User name without escaping'),
            (r'\{\{\s*[^}]*\.message\s*\}\}(?!\|e)', 'Message without escaping'),
            (r'\{\{\s*[^}]*\.content\s*\}\}(?!\|e)', 'Content without escaping'),
            (r'\{\{\s*[^}]*\.description\s*\}\}(?!\|e)', 'Description without escaping'),
            (r'\{\{\s*[^}]*\.title\s*\}\}(?!\|e)', 'Title without escaping'),
            (r'\{\{\s*request\.[^}]*\}\}(?!\|e\s*\}\})', 'Request data without escaping'),
            (r'\{\{\s*[^}]*\|safe\s*\}\}(?<!tojson\s*\|safe\s*\}\})', 'Direct |safe usage'),
            (r'\{\{\s*[^}]*\|raw\s*\}\}', 'Raw output usage'),
        ]
        
        for pattern, description in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                context_start = max(0, match.start() - 50)
                context_end = min(len(content), match.end() + 50)
                context = content[context_start:context_end].replace('\n', ' ')
                
                vulnerabilities.append({
                    'type': description,
                    'line': line_num,
                    'context': context,
                    'match': match.group(0)
                })
        
        return vulnerabilities
            
    except Exception as e:
        print(f'Error reading {file_path}: {e}')
        return []

def main():
    """Main audit function"""
    template_dir = Path('templates')
    if not template_dir.exists():
        print('Templates directory not found')
        return 1

    all_vulnerabilities = []
    scanned_files = 0

    # Scan all HTML files
    for html_file in template_dir.rglob('*.html'):
        scanned_files += 1
        vulnerabilities = scan_for_real_xss(html_file)
        
        if vulnerabilities:
            all_vulnerabilities.append({
                'file': str(html_file),
                'vulnerabilities': vulnerabilities
            })

    print(f'=== FOCUSED XSS VULNERABILITY AUDIT ===')
    print(f'Scanned {scanned_files} template files')
    print(f'Found REAL vulnerabilities in {len(all_vulnerabilities)} files')
    print()

    if all_vulnerabilities:
        for file_data in all_vulnerabilities:
            print(f'CRITICAL: {file_data["file"]}')
            for vuln in file_data['vulnerabilities']:
                print(f'   - {vuln["type"]} (line {vuln["line"]})')
                print(f'     Match: {vuln["match"]}')
                print(f'     Context: {vuln["context"][:100]}...')
            print()
        
        return 1  # Exit code 1 for vulnerabilities found
    else:
        print('SUCCESS: No real XSS vulnerabilities found!')
        print('All user-controlled data appears to be properly escaped.')
        return 0

if __name__ == '__main__':
    exit(main())