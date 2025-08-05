# 🤝 Contributing to Cibozer

Thank you for your interest in contributing to Cibozer! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## 📜 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Respect differing viewpoints and experiences
- Show empathy towards other community members

## 🚀 Getting Started

### 1. Fork the Repository

```bash
# Fork the repository on GitHub
# Clone your fork locally
git clone https://github.com/YOUR_USERNAME/cibozer.git
cd cibozer

# Add the upstream repository
git remote add upstream https://github.com/cibozer/cibozer.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with development settings
```

### 3. Create a Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create a feature branch
git checkout -b feature/your-feature-name
```

## 💻 Development Process

### 1. Code Style

We use several tools to maintain code quality:

```bash
# Format code with Black
black app/

# Sort imports with isort
isort app/

# Lint with flake8
flake8 app/

# Type check with mypy
mypy app/

# Security scan with bandit
bandit -r app/
```

### 2. Writing Code

#### Python Style Guide

```python
# Good: Clear, descriptive names
def calculate_daily_calories(user_profile: UserProfile) -> int:
    """Calculate daily caloric needs based on user profile."""
    bmr = calculate_bmr(user_profile)
    activity_factor = get_activity_factor(user_profile.activity_level)
    return int(bmr * activity_factor)

# Bad: Unclear names, no type hints
def calc(u):
    b = bmr(u)
    a = act(u.al)
    return b * a
```

#### JavaScript Style Guide

```javascript
// Good: Modern ES6+, clear naming
const generateMealPlan = async (preferences) => {
    try {
        const response = await fetch('/api/generate-meal-plan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(preferences)
        });
        return await response.json();
    } catch (error) {
        console.error('Meal plan generation failed:', error);
        throw error;
    }
};

// Bad: Callbacks, unclear names
function genMP(p, cb) {
    $.post('/api/generate-meal-plan', p, function(d) {
        cb(d);
    });
}
```

### 3. Database Changes

When making database changes:

```bash
# Create a new migration
flask db migrate -m "Add user preferences table"

# Review the generated migration
# Edit if necessary in migrations/versions/

# Apply the migration
flask db upgrade

# Test rollback
flask db downgrade
```

### 4. Adding Dependencies

```bash
# Add to requirements.txt (production dependencies)
echo "new-package==1.0.0" >> requirements.txt

# Add to requirements-dev.txt (development dependencies)
echo "pytest-mock==3.0.0" >> requirements-dev.txt

# Update lock file
pip-compile requirements.in
```

## 🧪 Testing Guidelines

### 1. Write Tests First

We encourage Test-Driven Development (TDD):

```python
# tests/test_meal_optimizer.py
def test_meal_plan_respects_calorie_limit():
    """Test that generated meal plans stay within calorie limits."""
    preferences = {
        'daily_calories': 2000,
        'meals_per_day': 3
    }
    
    meal_plan = generate_meal_plan(preferences)
    
    total_calories = sum(meal['calories'] for meal in meal_plan)
    assert 1900 <= total_calories <= 2100  # Allow 5% variance
```

### 2. Test Categories

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows
- **Performance Tests**: Test response times and load handling

### 3. Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_meal_optimizer.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py::test_user_registration

# Run with verbose output
pytest -v

# Run only marked tests
pytest -m "not slow"
```

### 4. Test Coverage

We aim for 90%+ test coverage:

```bash
# Generate coverage report
pytest --cov=app --cov-report=term-missing

# View HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 📤 Submitting Changes

### 1. Commit Messages

Follow the conventional commits specification:

```bash
# Format: <type>(<scope>): <subject>

# Examples:
git commit -m "feat(meal-plan): add vegetarian meal filtering"
git commit -m "fix(auth): resolve password reset token expiration"
git commit -m "docs(api): update meal plan endpoint documentation"
git commit -m "test(payments): add Stripe webhook tests"
git commit -m "refactor(models): simplify user preference handling"
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

### 2. Pull Request Process

1. **Update your branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**:
   ```bash
   # Run tests
   pytest
   
   # Run linters
   pre-commit run --all-files
   
   # Check for security issues
   bandit -r app/
   ```

3. **Push your changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Use a clear, descriptive title
   - Reference any related issues
   - Include screenshots for UI changes
   - List any breaking changes
   - Update documentation if needed

### 3. Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Updated documentation
- [ ] No new warnings
```

## 🐛 Reporting Issues

### 1. Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details

Example:
```markdown
**Title**: Meal plan generation fails for keto diet

**Steps to Reproduce**:
1. Log in as registered user
2. Select "Keto" diet type
3. Set calories to 1800
4. Click "Generate Plan"

**Expected**: Meal plan with <20g carbs per day
**Actual**: Error 500 returned

**Environment**:
- Browser: Chrome 120
- OS: Windows 11
- User tier: Free
```

### 2. Feature Requests

Include:
- Use case description
- Proposed solution
- Alternative solutions considered
- Additional context

## 🏗️ Project Structure

Understanding the codebase:

```
app/
├── __init__.py          # Application factory
├── models/              # Database models
│   ├── user.py         # User model
│   └── meal_plan.py    # Meal plan models
├── routes/              # Route blueprints
│   ├── auth.py         # Authentication routes
│   ├── api.py          # API endpoints
│   └── main.py         # Main app routes
├── services/            # Business logic
│   ├── meal_optimizer.py
│   └── email_service.py
├── utils/               # Utility functions
└── middleware/          # Custom middleware
```

## 📚 Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Python Style Guide (PEP 8)](https://www.python.org/dev/peps/pep-0008/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project website

Thank you for contributing to Cibozer! 🎉