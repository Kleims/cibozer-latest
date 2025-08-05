# Test Patterns and Guidelines for Cibozer

This document outlines the comprehensive testing patterns implemented in the Cibozer application, providing guidance for maintaining and extending the test suite.

## Overview

The Cibozer test suite implements a multi-layered testing approach covering:

- **Unit Tests**: Individual component testing
- **Integration Tests**: API and service integration
- **End-to-End Tests**: Complete user workflow testing
- **Performance Tests**: Response time, scalability, and load testing
- **Security Tests**: Authentication, authorization, and vulnerability testing
- **Edge Case Tests**: Boundary conditions and error scenarios

## Test Structure

### Directory Layout

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── test_app.py                # Core application tests
├── test_api_integration.py    # API integration tests
├── test_e2e_workflows.py      # End-to-end workflow tests
├── test_edge_cases.py         # Edge case and boundary testing
├── test_performance.py        # Performance benchmarking
├── test_security_comprehensive.py  # Security vulnerability tests
├── test_web_security.py       # Web application security tests
└── TEST_PATTERNS.md           # This documentation
```

### Key Fixtures (conftest.py)

- `app`: Flask application with test configuration
- `client`: Test client for HTTP requests
- `test_user`: Standard test user
- `admin_user`: Admin user for authorization testing
- `auth_client`: Pre-authenticated test client
- `sample_meal_plan`: Standard meal plan data structure

## Test Categories

### 1. Integration Tests (`test_api_integration.py`)

**Purpose**: Test API endpoints and their interactions

**Key Patterns**:
- Test public endpoints (health, metrics)
- Verify protected endpoints require authentication
- Test proper HTTP status codes and content types
- Validate JSON response structures
- Test rate limiting behavior

**Example**:
```python
def test_health_check_endpoint(self, client):
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
```

### 2. End-to-End Tests (`test_e2e_workflows.py`)

**Purpose**: Test complete user workflows from start to finish

**Key Patterns**:
- Test user registration → login → feature usage
- Test complete meal plan creation workflow
- Test admin workflows
- Test error recovery scenarios
- Test concurrent user scenarios

**Example**:
```python
def test_complete_user_registration_flow(self, client):
    # Step 1: Register
    response = client.post('/auth/register', data={...})
    # Step 2: Login
    response = client.post('/auth/login', data={...})
    # Step 3: Use features
    response = client.get('/auth/profile')
```

### 3. Edge Case Tests (`test_edge_cases.py`)

**Purpose**: Test boundary conditions, unusual inputs, and error scenarios

**Key Patterns**:
- Test with extreme values (very long strings, large numbers)
- Test with malformed data
- Test with special characters and Unicode
- Test database constraint violations
- Test XSS and SQL injection prevention

**Example**:
```python
def test_user_with_extremely_long_email(self, app):
    long_email = 'a' * 240 + '@example.com'
    user = User(email=long_email, full_name='Test User')
    # Test that system handles long emails properly
```

### 4. Performance Tests (`test_performance.py`)

**Purpose**: Ensure application meets performance requirements

**Key Patterns**:
- Test response times for critical endpoints
- Test database query performance
- Test concurrent request handling
- Test memory usage and efficiency
- Test scalability with increasing load

**Example**:
```python
def test_health_check_response_time(self, client):
    times = []
    for _ in range(10):
        start_time = time.time()
        response = client.get('/api/health')
        end_time = time.time()
        times.append((end_time - start_time) * 1000)
    
    avg_time = mean(times)
    assert avg_time < 100, f"Average response time {avg_time:.2f}ms exceeds 100ms"
```

### 5. Security Tests (`test_security_comprehensive.py`, `test_web_security.py`)

**Purpose**: Test security vulnerabilities and protections

**Key Patterns**:
- Test authentication and authorization
- Test input validation and sanitization
- Test XSS and SQL injection prevention
- Test security headers
- Test CSRF protection
- Test rate limiting and brute force protection

**Example**:
```python
def test_sql_injection_prevention(self, client):
    sql_payloads = ["'; DROP TABLE users; --", "' OR '1'='1"]
    for payload in sql_payloads:
        response = client.post('/auth/login', data={
            'email': payload,
            'password': 'password123'
        })
        assert response.status_code in [200, 302, 400, 401]
```

## Testing Best Practices

### 1. Test Organization

- **One test class per logical component/feature**
- **Descriptive test method names** that explain what is being tested
- **Group related tests** in the same class
- **Use docstrings** to explain complex test scenarios

### 2. Fixture Usage

- **Use shared fixtures** from `conftest.py` for common setup
- **Scope fixtures appropriately** (function, class, module, session)
- **Clean up resources** in fixture teardown
- **Parameterize tests** for multiple similar scenarios

### 3. Assertion Strategies

- **Test multiple acceptable outcomes** for flexible systems
- **Use specific assertions** rather than generic ones
- **Include meaningful error messages** in assertions
- **Test both positive and negative cases**

### 4. Data Management

- **Use isolated test data** that doesn't affect other tests
- **Create realistic test data** that mimics production scenarios
- **Test with edge case data** (empty, null, extreme values)
- **Clean up test data** to prevent test interference

### 5. Error Handling

- **Test expected error conditions**
- **Verify error messages and status codes**
- **Test graceful degradation**
- **Test recovery from error states**

## Test Execution Patterns

### Running Individual Test Categories

```bash
# Integration tests
python -m pytest tests/test_api_integration.py -v

# End-to-end tests
python -m pytest tests/test_e2e_workflows.py -v

# Performance tests
python -m pytest tests/test_performance.py -v

# Security tests
python -m pytest tests/test_security_comprehensive.py -v

# Edge case tests
python -m pytest tests/test_edge_cases.py -v
```

### Running Tests with Coverage

```bash
python -m pytest tests/ --cov=app --cov-report=html
```

### Running Specific Test Patterns

```bash
# Run all tests containing "security"
python -m pytest -k "security" -v

# Run all tests for a specific class
python -m pytest tests/test_api_integration.py::TestAPIIntegration -v

# Run a specific test method
python -m pytest tests/test_performance.py::TestResponseTimePerformance::test_health_check_response_time -v
```

## Test Data Patterns

### 1. User Data

```python
# Standard test user
test_user = {
    'email': 'test@example.com',
    'full_name': 'Test User',
    'password': 'testpassword123'
}

# Edge case users
edge_users = [
    {'email': 'very.long.email.address@example.com', 'full_name': 'Edge Case User'},
    {'email': 'unicode@测试.com', 'full_name': 'Unicode User'},
    {'email': 'special@example.com', 'full_name': 'José María García-López'}
]
```

### 2. Meal Plan Data

```python
# Standard meal plan
sample_meal_plan = {
    'diet_type': 'standard',
    'calories': 2000,
    'meals': [
        {
            'name': 'Breakfast',
            'items': [
                {
                    'food': 'Oatmeal',
                    'quantity': '1 cup',
                    'calories': 300
                }
            ]
        }
    ]
}
```

### 3. Security Test Data

```python
# XSS payloads
xss_payloads = [
    '<script>alert("xss")</script>',
    '"><script>alert("xss")</script>',
    '<img src=x onerror=alert("xss")>'
]

# SQL injection payloads
sql_payloads = [
    "'; DROP TABLE users; --",
    "' OR '1'='1",
    "admin'--"
]
```

## Maintenance Guidelines

### 1. Adding New Tests

1. **Identify the test category** (unit, integration, e2e, performance, security, edge case)
2. **Choose the appropriate test file** or create a new one if needed
3. **Follow existing naming conventions** and patterns
4. **Add appropriate fixtures** if new setup is required
5. **Document complex test scenarios** with docstrings

### 2. Updating Tests

1. **Update tests when API contracts change**
2. **Add new edge cases** as they are discovered
3. **Update performance thresholds** as system performance improves
4. **Add security tests** for new vulnerabilities
5. **Refactor tests** to reduce duplication

### 3. Test Debugging

1. **Use verbose output** (`-v` flag) to see detailed test results
2. **Run individual tests** to isolate failures
3. **Check test data setup** and cleanup
4. **Verify application context** for database operations
5. **Use print statements** or logging for complex debugging

## Performance Benchmarks

### Current Performance Targets

- **Health check endpoint**: < 100ms average response time
- **Home page load**: < 500ms average response time
- **Login page**: < 300ms average response time
- **Database queries**: < 50ms for single record queries
- **Concurrent requests**: Handle 10+ simultaneous requests
- **Memory efficiency**: No memory leaks over 100+ operations

### Security Standards

- **Password hashing**: Use bcrypt with minimum 12 rounds
- **Session security**: HttpOnly and Secure flags in production
- **Rate limiting**: Protect against brute force attacks
- **Input validation**: Sanitize all user inputs
- **CSRF protection**: Protect state-changing operations
- **Security headers**: Include X-Frame-Options, X-Content-Type-Options

## Continuous Integration

### Pre-commit Checks

1. **Run all tests**: Ensure no regressions
2. **Check test coverage**: Maintain > 90% coverage
3. **Run security tests**: Verify no new vulnerabilities
4. **Performance regression tests**: Ensure performance hasn't degraded

### Test Environment Setup

```python
# Test configuration
app.config.update({
    'TESTING': True,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
    'WTF_CSRF_ENABLED': False,
    'SECRET_KEY': 'test-secret-key-only-for-testing',
    'RATELIMIT_ENABLED': False
})
```

## Contributing to Tests

When contributing new tests or modifying existing ones:

1. **Follow the established patterns** in this document
2. **Write descriptive test names** and docstrings
3. **Test both success and failure cases**
4. **Include edge cases** and boundary conditions
5. **Ensure tests are isolated** and don't depend on external state
6. **Update this documentation** if introducing new patterns

## Conclusion

The Cibozer test suite provides comprehensive coverage across multiple dimensions:

- **Functional correctness** through integration and unit tests
- **User experience** through end-to-end workflow tests  
- **System reliability** through edge case and error condition tests
- **Performance standards** through benchmark and load tests
- **Security posture** through vulnerability and penetration tests

This multi-layered approach ensures that the application maintains high quality, performance, and security standards as it evolves.