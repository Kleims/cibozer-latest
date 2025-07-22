#!/usr/bin/env python3
"""Check if CI/CD is properly configured"""

import sys
from pathlib import Path

def check_cicd_setup():
    """Check if GitHub Actions workflows exist and are valid"""
    
    project_root = Path(__file__).parent.parent
    workflows_dir = project_root / '.github' / 'workflows'
    
    # Check if workflows directory exists
    if not workflows_dir.exists():
        print("FAIL: .github/workflows directory not found")
        print("Run: python scripts/setup_github_actions.py")
        return False
    
    # Check for CI workflow
    ci_file = workflows_dir / 'ci.yml'
    if not ci_file.exists():
        print("FAIL: CI workflow not found (.github/workflows/ci.yml)")
        return False
    
    # Check CI workflow content
    with open(ci_file, 'r') as f:
        ci_content = f.read()
        
    required_ci_elements = [
        'name: CI',
        'on:',
        'push:',
        'pull_request:',
        'jobs:',
        'test:',
        'pytest'
    ]
    
    missing_elements = []
    for element in required_ci_elements:
        if element not in ci_content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"FAIL: CI workflow missing elements: {', '.join(missing_elements)}")
        return False
    
    # Check for deployment workflow
    deploy_file = workflows_dir / 'deploy.yml'
    if not deploy_file.exists():
        print("Warning: Deploy workflow not found (.github/workflows/deploy.yml)")
        # Don't fail for missing deploy, as it's optional
    
    # Check for dependabot config
    dependabot_file = project_root / '.github' / 'dependabot.yml'
    if not dependabot_file.exists():
        print("Warning: Dependabot config not found (.github/dependabot.yml)")
        # Don't fail for missing dependabot, as it's optional
    
    print("OK")
    return True

def main():
    """Main function"""
    success = check_cicd_setup()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())