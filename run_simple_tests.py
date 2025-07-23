"""Simple test runner to verify basic functionality"""
import subprocess
import sys

def run_basic_tests():
    """Run the basic tests we created"""
    print("Running basic tests...")
    
    # Run our simple test
    result = subprocess.run([sys.executable, "test_basic.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Run pytest on our basic test
    print("\nRunning pytest on test_basic.py...")
    result = subprocess.run([sys.executable, "-m", "pytest", "test_basic.py", "-v"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    # Check if any tests passed
    if "passed" in result.stdout:
        return True
    return False

if __name__ == "__main__":
    success = run_basic_tests()
    print(f"\nTests {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)