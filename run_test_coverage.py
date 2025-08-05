#!/usr/bin/env python3
"""
Run comprehensive test coverage analysis for Cibozer application.
This script runs all test suites and generates a detailed coverage report.
"""

import subprocess
import sys
import os
import json
from pathlib import Path
from datetime import datetime


def run_test_coverage():
    """Run test coverage analysis and generate reports."""
    print("Running Cibozer Test Coverage Analysis")
    print("=" * 60)
    
    # Set environment variables for testing
    test_env = os.environ.copy()
    test_env.update({
        'FLASK_ENV': 'testing',
        'TESTING': '1',
        'SECRET_KEY': 'test-secret-key-for-coverage',
        'DATABASE_URL': 'sqlite:///:memory:',
        'OPENAI_API_KEY': 'test-key',
        'STRIPE_SECRET_KEY': 'sk_test_mock',
        'STRIPE_PUBLISHABLE_KEY': 'pk_test_mock',
    })
    
    # Test categories to run
    test_categories = [
        {
            'name': 'Unit Tests',
            'pattern': 'tests/test_app.py tests/test_models*.py tests/test_auth*.py',
            'description': 'Core functionality tests'
        },
        {
            'name': 'Integration Tests',
            'pattern': 'tests/test_integration*.py',
            'description': 'Component interaction tests'
        },
        {
            'name': 'Security Tests',
            'pattern': 'tests/test_security*.py',
            'description': 'Security vulnerability tests'
        },
        {
            'name': 'Performance Tests',
            'pattern': 'tests/test_performance*.py tests/test_load.py',
            'description': 'Performance and load tests'
        },
        {
            'name': 'All Tests',
            'pattern': 'tests/',
            'description': 'Complete test suite'
        }
    ]
    
    results = {}
    
    for category in test_categories:
        print(f"\nRunning {category['name']}")
        print(f"   {category['description']}")
        print("-" * 40)
        
        cmd = [
            sys.executable, '-m', 'pytest',
            category['pattern'],
            '--cov=app',
            '--cov-report=term-missing:skip-covered',
            '--cov-report=json',
            '--tb=short',
            '-v',
            '--maxfail=50',
            '--continue-on-collection-errors'
        ]
        
        try:
            result = subprocess.run(
                cmd,
                env=test_env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse results
            if result.returncode == 0:
                print(f"[PASS] {category['name']}: All tests passed!")
            else:
                print(f"[FAIL] {category['name']}: Some tests failed (exit code: {result.returncode})")
            
            # Try to extract coverage percentage
            coverage_line = None
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    coverage_line = line
                    break
            
            if coverage_line:
                parts = coverage_line.split()
                for part in parts:
                    if part.endswith('%'):
                        coverage_pct = part.rstrip('%')
                        results[category['name']] = {
                            'coverage': coverage_pct,
                            'status': 'passed' if result.returncode == 0 else 'failed'
                        }
                        print(f"Coverage: {coverage_pct}%")
                        break
            
        except subprocess.TimeoutExpired:
            print(f"[TIMEOUT] {category['name']}: Tests timed out")
            results[category['name']] = {'coverage': 'N/A', 'status': 'timeout'}
        except Exception as e:
            print(f"[ERROR] {category['name']}: Error running tests: {e}")
            results[category['name']] = {'coverage': 'N/A', 'status': 'error'}
    
    # Generate final report
    print("\n" + "=" * 60)
    print("COVERAGE SUMMARY")
    print("=" * 60)
    
    # Read coverage.json if it exists
    coverage_file = Path('coverage.json')
    if coverage_file.exists():
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)
        
        total_lines = coverage_data.get('totals', {}).get('num_statements', 0)
        covered_lines = coverage_data.get('totals', {}).get('covered_lines', 0)
        missing_lines = coverage_data.get('totals', {}).get('missing_lines', 0)
        coverage_percent = coverage_data.get('totals', {}).get('percent_covered', 0)
        
        print(f"Total Lines: {total_lines:,}")
        print(f"Covered Lines: {covered_lines:,}")
        print(f"Missing Lines: {missing_lines:,}")
        print(f"Overall Coverage: {coverage_percent:.1f}%")
        
        # Files with low coverage
        print("\nFiles with Low Coverage (<80%):")
        files_data = coverage_data.get('files', {})
        low_coverage_files = []
        
        for file_path, file_data in files_data.items():
            file_coverage = file_data.get('summary', {}).get('percent_covered', 0)
            if file_coverage < 80:
                low_coverage_files.append((file_path, file_coverage))
        
        low_coverage_files.sort(key=lambda x: x[1])
        for file_path, coverage in low_coverage_files[:10]:  # Top 10 worst
            print(f"  - {file_path}: {coverage:.1f}%")
    
    print("\nTest Category Results:")
    for category, result in results.items():
        status_icon = "[PASS]" if result['status'] == 'passed' else "[FAIL]"
        print(f"{status_icon} {category}: Coverage {result['coverage']}% - Status: {result['status']}")
    
    # Generate HTML report
    print("\nGenerating HTML coverage report...")
    subprocess.run([sys.executable, '-m', 'coverage', 'html'], check=False)
    print("HTML report generated in htmlcov/index.html")
    
    # Save summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'results': results,
        'overall_coverage': coverage_percent if 'coverage_percent' in locals() else 'N/A',
        'recommendations': []
    }
    
    # Add recommendations
    if 'coverage_percent' in locals():
        if coverage_percent < 80:
            summary['recommendations'].append("WARNING: Coverage below 80% - Add more tests")
        elif coverage_percent < 90:
            summary['recommendations'].append("Coverage below target 90% - Focus on untested code")
        else:
            summary['recommendations'].append("Coverage meets 90% target - Great job!")
    
    with open('test_coverage_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nCoverage analysis complete!")
    print(f"Summary saved to test_coverage_summary.json")
    
    return 0 if all(r['status'] == 'passed' for r in results.values()) else 1


def main():
    """Main entry point."""
    try:
        # Ensure we're in the project root
        if not Path('app').exists():
            print("Error: Must run from project root directory")
            return 1
        
        # Check dependencies
        required_packages = ['pytest', 'pytest-cov', 'pytest-flask']
        missing = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"Missing required packages: {', '.join(missing)}")
            print(f"   Run: pip install {' '.join(missing)}")
            return 1
        
        return run_test_coverage()
        
    except KeyboardInterrupt:
        print("\nCoverage analysis interrupted")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())