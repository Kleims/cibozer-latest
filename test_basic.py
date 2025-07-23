"""Basic test to verify testing framework works"""

def test_basic_math():
    """Simple test to verify pytest works"""
    assert 1 + 1 == 2

def test_python_version():
    """Test Python version is 3.6+"""
    import sys
    assert sys.version_info >= (3, 6)

if __name__ == "__main__":
    print("Running basic tests...")
    test_basic_math()
    print("OK - Basic math test passed")
    test_python_version()
    print("OK - Python version test passed")
    print("All tests passed!")