# Project Context - Cibozer (Python/Flask)
# Auto-detected on $(date)

# Test command - runs pytest with coverage
TEST_CMD="python -m pytest -v --tb=short"

# Build command - for Python, we'll use a validation check
BUILD_CMD="python -m py_compile app.py models.py"

# Coverage command - get coverage percentage
COVERAGE_CMD="python -m pytest --cov=. --cov-report=term-missing"

# Security audit command - check for vulnerabilities
AUDIT_CMD="pip list --outdated | grep -E 'critical|high' || echo 'No critical updates'"

# File pattern for main code files
FILE_PATTERN="*.py"

# Pattern that indicates test failure
TEST_FAIL_PATTERN="FAILED|AssertionError|Exception|ERROR|KeyError|TypeError"

# Pattern that indicates test pass
TEST_PASS_PATTERN="passed|PASSED|[0-9]+ passed"

# Pattern to extract coverage number
COVERAGE_PATTERN="TOTAL.*\s([0-9]+)%"

# Project type
PROJECT_TYPE="Python/Flask Web Application"

# Main test framework
TEST_FRAMEWORK="pytest"

# Package manager
PACKAGE_MANAGER="pip"

# Requirements file
REQUIREMENTS_FILE="requirements.txt"

# Additional project info
DEPLOYMENT_PLATFORMS="Heroku, Railway, Vercel, Render"
DATABASE="SQLAlchemy with SQLite/PostgreSQL"
AUTH_SYSTEM="Flask-Login with bcrypt"
PAYMENT_SYSTEM="Stripe"