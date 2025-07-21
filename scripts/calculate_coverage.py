#!/usr/bin/env python3
"""
APEX Coverage Calculator
Parses pytest coverage output and calculates weighted coverage for the project
"""

import subprocess
import re
import sys
import json
from pathlib import Path

def run_coverage():
    """Run pytest with coverage and capture output"""
    try:
        result = subprocess.run(
            ['pytest', '--cov=.', '--cov-report=term'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout + result.stderr
    except Exception as e:
        print(f"Error running coverage: {e}")
        return None

def parse_coverage_output(output):
    """Parse coverage output to extract percentages"""
    if not output:
        return None
    
    # Look for the TOTAL line in coverage report
    total_pattern = r'TOTAL\s+\d+\s+\d+\s+(\d+)%'
    match = re.search(total_pattern, output)
    
    if match:
        return int(match.group(1))
    
    # Alternative pattern for different coverage formats
    alt_pattern = r'TOTAL.*?(\d+)%'
    match = re.search(alt_pattern, output)
    
    if match:
        return int(match.group(1))
    
    return None

def get_test_counts(output):
    """Extract test pass/fail counts from pytest output"""
    if not output:
        return None, None
    
    # Look for pytest summary line
    # Format: "X passed, Y failed" or "X passed" etc.
    passed_pattern = r'(\d+) passed'
    failed_pattern = r'(\d+) failed'
    
    passed_match = re.search(passed_pattern, output)
    failed_match = re.search(failed_pattern, output)
    
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    
    return passed, failed

def calculate_health(passed, failed, critical_failures=0):
    """Calculate health score based on APEX_CONFIG.md rules"""
    health = 100
    
    # Critical module failures (10 points each)
    health -= critical_failures * 10
    
    # Normal test failures (3 points each for medium test suite)
    total_tests = passed + failed
    if total_tests < 50:
        health -= failed * 5
    elif total_tests < 200:
        health -= failed * 3
    else:
        health -= failed * 2
    
    return max(0, min(100, health))

def main():
    """Main execution"""
    print("APEX Coverage Calculator")
    print("=" * 50)
    
    # Run coverage
    print("Running pytest with coverage...")
    output = run_coverage()
    
    if not output:
        print("Failed to run coverage")
        sys.exit(1)
    
    # Parse results
    coverage = parse_coverage_output(output)
    passed, failed = get_test_counts(output)
    
    # Calculate health
    health = calculate_health(passed, failed) if passed is not None else 0
    
    # Output results
    print(f"\nResults:")
    print(f"- Coverage: {coverage}%" if coverage else "- Coverage: Unable to determine")
    print(f"- Tests Passed: {passed}")
    print(f"- Tests Failed: {failed}")
    print(f"- Total Tests: {passed + failed}")
    print(f"- Health Score: {health}/100")
    
    # Output JSON for automation
    results = {
        'coverage': coverage,
        'passed': passed,
        'failed': failed,
        'total': passed + failed if passed is not None else 0,
        'health': health
    }
    
    # Save to file for other scripts
    with open('coverage_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to coverage_results.json")

if __name__ == "__main__":
    main()