#!/usr/bin/env python3
import os
import subprocess

test_files = [f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
error_files = []
passing_files = []

for test_file in test_files:
    result = subprocess.run(
        ['python', '-m', 'pytest', f'tests/{test_file}', '--co', '-q'],
        capture_output=True, text=True
    )
    if 'error' in result.stdout.lower() or 'error' in result.stderr.lower() or result.returncode != 0:
        error_files.append(test_file)
    else:
        passing_files.append(test_file)

print(f'Files with collection errors: {len(error_files)}')
print(f'Files without errors: {len(passing_files)}')

if error_files:
    print('\nFiles with errors:')
    for f in error_files[:10]:
        print(f'  - {f}')