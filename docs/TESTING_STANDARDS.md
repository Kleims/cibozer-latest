# Cibozer Testing Standards and Procedures

## Overview
This document outlines the testing standards, procedures, and best practices for the Cibozer application. All contributors must follow these guidelines to ensure code quality and maintainability.

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Organization](#test-organization)
3. [Test Types](#test-types)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Continuous Integration](#continuous-integration)
7. [Testing Tools](#testing-tools)
8. [Best Practices](#best-practices)

## Testing Philosophy

### Core Principles
- **Test First**: Write tests before implementing features (TDD when practical)
- **Comprehensive Coverage**: Aim for 90%+ code coverage
- **Fast Feedback**: Tests should run quickly to encourage frequent execution
- **Isolated Tests**: Each test should be independent and deterministic
- **Clear Failures**: Test failures should clearly indicate what went wrong

### Testing Pyramid
```
        /\
       /  \   E2E Tests (5%)
      /----\  
     /      \ Integration Tests (20%)
    /--------\
   /          \ Unit Tests (75%)
  /____________\
```

## Test Organization

### Directory Structure
```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_*.py                      # Test files (mirror app structure)
├── test_comprehensive_coverage.py # Gap-filling tests
├── test_error_conditions.py       # Error handling tests
├── test_integration_e2e.py        # Integration/E2E tests
├── test_performance_load.py       # Performance tests
└── test_security_comprehensive.py # Security tests
```

### Naming Conventions
- Test files: `test_<module_name>.py`
- Test classes: `Test<Feature>` (e.g., `TestUserAuthentication`)
- Test methods: `test_<specific_scenario>` (e.g., `test_login_with_invalid_credentials`)

## Test Types

### 1. Unit Tests
**Purpose**: Test individual functions, methods, and classes in isolation

**Example**:
```python
def test_user_password_hashing(self):
    """Test password hashing is secure."""
    user = User(email='test@example.com')
    user.set_password('MySecurePassword123!')
    
    assert user.password_hash != 'MySecurePassword123!'
    assert user.check_password('MySecurePassword123!')
    assert not user.check_password('WrongPassword')
```

**Guidelines**:
- Mock external dependencies
- Test one thing at a time
- Use descriptive test names
- Keep tests small and focused

### 2. Integration Tests
**Purpose**: Test interactions between components

**Example**:
```python
def test_meal_generation_workflow(self, auth_client, mock_openai):
    """Test complete meal generation workflow."""
    response = auth_client.post('/api/generate', json={
        'diet_type': 'standard',
        'calories': 2000
    })
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'meal_plan' in data
```

**Guidelines**:
- Test realistic scenarios
- Use test database
- Mock external services (APIs, email)
- Test error paths

### 3. End-to-End Tests
**Purpose**: Test complete user workflows

**Example**:
```python
def test_new_user_complete_flow(self, client):
    """Test complete flow from registration to meal plan."""
    # Register
    response = client.post('/auth/register', data={...})
    # Login
    response = client.post('/auth/login', data={...})
    # Generate meal plan
    response = client.post('/api/generate', json={...})
    # Save meal plan
    response = client.post('/api/save-meal-plan', json={...})
```

**Guidelines**:
- Test critical user paths
- Minimize use (expensive to maintain)
- Run in CI/CD pipeline
- Use real browser for UI tests (if applicable)

### 4. Performance Tests
**Purpose**: Ensure acceptable performance under load

**Example**:
```python
def test_concurrent_registrations(self, app):
    """Test handling concurrent user registrations."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(register_user, i) for i in range(20)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
```

**Guidelines**:
- Test response times
- Test concurrent operations
- Monitor resource usage
- Set performance thresholds

### 5. Security Tests
**Purpose**: Verify security measures are effective

**Example**:
```python
def test_sql_injection_protection(self, client):
    """Test SQL injection protection."""
    response = client.post('/auth/login', data={
        'email': "' OR '1'='1",
        'password': "' OR '1'='1"
    })
    assert b'Invalid email or password' in response.data
```

**Guidelines**:
- Test common attack vectors
- Verify authentication/authorization
- Check data isolation
- Test input validation

## Writing Tests

### Test Structure
```python
class TestFeatureName:
    """Test suite for specific feature."""
    
    def setup_method(self):
        """Set up test dependencies."""
        # Initialize test data
        
    def teardown_method(self):
        """Clean up after test."""
        # Reset state
        
    def test_specific_scenario(self, fixtures):
        """Test description."""
        # Arrange
        test_data = create_test_data()
        
        # Act
        result = perform_action(test_data)
        
        # Assert
        assert result == expected_value
```

### Using Fixtures
```python
@pytest.fixture
def sample_meal_plan():
    """Create sample meal plan data."""
    return {
        'diet_type': 'standard',
        'calories': 2000,
        'meals': [...]
    }

def test_save_meal_plan(auth_client, sample_meal_plan):
    """Test saving meal plan."""
    response = auth_client.post('/api/save-meal-plan', 
                               json={'meal_plan': sample_meal_plan})
    assert response.status_code == 200
```

### Mocking External Services
```python
@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI API calls."""
    def mock_create(*args, **kwargs):
        return MockResponse({'meals': [...]})
    
    monkeypatch.setattr('openai.ChatCompletion.create', mock_create)
```

## Test Coverage

### Coverage Requirements
- **Minimum**: 80% overall coverage
- **Target**: 90%+ coverage
- **Critical paths**: 100% coverage for authentication, payments, data security

### Running Coverage
```bash
# Run with coverage report
pytest --cov=app --cov-report=term-missing --cov-report=html

# Check coverage threshold
coverage report --fail-under=80
```

### Coverage Configuration
```ini
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */venv/*
    */__pycache__/*

[report]
precision = 2
show_missing = True
skip_covered = False
```

## Continuous Integration

### CI Pipeline Stages
1. **Lint**: Code quality checks
2. **Security**: Vulnerability scanning
3. **Test**: Run test suite with coverage
4. **Integration**: Run integration tests
5. **Performance**: Run performance tests
6. **Build**: Verify build process

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.12
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=120']
```

### GitHub Actions
See `.github/workflows/ci.yml` for complete CI configuration.

## Testing Tools

### Core Tools
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-xdist**: Parallel test execution
- **pytest-flask**: Flask testing utilities

### Additional Tools
- **factory-boy**: Test data generation
- **responses**: Mock HTTP requests
- **freezegun**: Time mocking
- **pytest-benchmark**: Performance testing

### Installation
```bash
pip install pytest pytest-cov pytest-xdist pytest-flask
pip install factory-boy responses freezegun pytest-benchmark
```

## Best Practices

### DO:
- ✅ Write descriptive test names
- ✅ Test both success and failure cases
- ✅ Use fixtures for reusable test data
- ✅ Keep tests independent
- ✅ Mock external dependencies
- ✅ Test edge cases
- ✅ Run tests before committing
- ✅ Update tests when changing code

### DON'T:
- ❌ Write tests that depend on test order
- ❌ Use production data in tests
- ❌ Make real API calls in unit tests
- ❌ Ignore flaky tests
- ❌ Comment out failing tests
- ❌ Test implementation details
- ❌ Use hard-coded values when fixtures would be better

### Test Data Management
```python
# Good: Use fixtures
@pytest.fixture
def test_user(db):
    user = User(email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

# Bad: Hard-coded in test
def test_something():
    user = User(email='test@example.com')  # Don't do this
```

### Assertion Best Practices
```python
# Good: Specific assertions
assert response.status_code == 200
assert 'error' not in response.json
assert len(results) == 5

# Bad: Generic assertions
assert response  # Too vague
assert result is not None  # Not specific enough
```

### Performance Considerations
- Use `pytest-xdist` for parallel execution
- Mock heavy operations (file I/O, network calls)
- Use `@pytest.mark.slow` for slow tests
- Run slow tests separately in CI

### Debugging Tests
```bash
# Run specific test with output
pytest tests/test_app.py::test_index_page -v -s

# Run tests matching pattern
pytest -k "test_login" -v

# Stop on first failure
pytest -x

# Debug with pdb
pytest --pdb
```

## Test Maintenance

### Regular Tasks
1. **Weekly**: Review and fix flaky tests
2. **Monthly**: Update test dependencies
3. **Quarterly**: Review coverage reports
4. **Before Release**: Run full test suite

### Handling Failures
1. Reproduce locally
2. Check for environment differences
3. Review recent changes
4. Fix root cause (not symptoms)
5. Add regression test

### Documentation
- Document complex test setups
- Explain non-obvious test scenarios
- Keep this guide updated
- Share testing knowledge

## Conclusion
Following these testing standards ensures Cibozer maintains high quality and reliability. Tests are not just about finding bugs—they're about building confidence in our code and enabling fearless refactoring.

Remember: **A feature without tests is not complete!**

---
*Last Updated: 2025-01-31*
*Version: 1.0*