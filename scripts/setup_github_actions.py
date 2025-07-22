#!/usr/bin/env python3
"""Setup GitHub Actions CI/CD pipeline"""

import os
import sys
from pathlib import Path

def create_github_actions_workflow():
    """Create real GitHub Actions workflow file"""
    
    # Create .github/workflows directory
    workflows_dir = Path(__file__).parent.parent / '.github' / 'workflows'
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    # Define the CI workflow content
    ci_workflow = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: cibozer_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-flask
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/cibozer_test
        SECRET_KEY: test-secret-key
        FLASK_ENV: testing
      run: |
        pytest --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install linting tools
      run: |
        python -m pip install --upgrade pip
        pip install flake8 black isort
    
    - name: Run flake8
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Check formatting with black
      run: black --check .
    
    - name: Check import sorting
      run: isort --check-only .

  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security checks
      run: |
        pip install safety bandit
        safety check
        bandit -r . -ll
"""
    
    # Write the workflow file
    ci_file = workflows_dir / 'ci.yml'
    with open(ci_file, 'w', encoding='utf-8') as f:
        f.write(ci_workflow)
    
    print(f"Created GitHub Actions workflow: {ci_file}")
    
    # Create a simple deployment workflow
    deploy_workflow = """name: Deploy

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploy steps would go here"
        # Example: Deploy to Heroku, AWS, etc.
"""
    
    deploy_file = workflows_dir / 'deploy.yml'
    with open(deploy_file, 'w', encoding='utf-8') as f:
        f.write(deploy_workflow)
    
    print(f"Created deployment workflow: {deploy_file}")
    
    # Create .github/dependabot.yml for dependency updates
    dependabot_config = """version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
"""
    
    dependabot_file = workflows_dir.parent / 'dependabot.yml'
    with open(dependabot_file, 'w', encoding='utf-8') as f:
        f.write(dependabot_config)
    
    print(f"Created Dependabot config: {dependabot_file}")
    
    print("OK")
    return True

def main():
    """Main function"""
    try:
        success = create_github_actions_workflow()
        return 0 if success else 1
    except Exception as e:
        print(f"Error setting up GitHub Actions: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())