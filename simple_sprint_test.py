#!/usr/bin/env python3
"""
Simple test of the real sprint executor without emojis
"""

import subprocess
import sys
import os

def test_real_execution():
    """Test real task execution"""
    print("Testing Real Sprint System")
    print("=" * 40)
    
    # Test 1: Fix failing tests
    print("\n1. Testing: Fix failing tests")
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '--tb=no', '-q'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        print(f"   Test result: {result.returncode}")
        print(f"   Output length: {len(output)} chars")
        
        # Count failures
        failures = output.count('FAILED')
        passed = output.count('passed')
        
        print(f"   Tests passed: {passed}")
        print(f"   Tests failed: {failures}")
        
    except Exception as e:
        print(f"   Error: {str(e)}")
    
    # Test 2: Check test files exist
    print("\n2. Testing: Check test directory")
    test_dir = 'tests'
    if os.path.exists(test_dir):
        test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
        print(f"   Found {len(test_files)} test files")
        for f in test_files[:3]:
            print(f"   - {f}")
    else:
        print("   No tests directory found")
    
    # Test 3: Check app files
    print("\n3. Testing: Check app directory")
    app_dir = 'app'
    if os.path.exists(app_dir):
        py_files = [f for f in os.listdir(app_dir) if f.endswith('.py')]
        print(f"   Found {len(py_files)} Python files in app/")
        for f in py_files[:3]:
            print(f"   - {f}")
    else:
        print("   No app directory found")
    
    print("\nDone!")

if __name__ == "__main__":
    test_real_execution()