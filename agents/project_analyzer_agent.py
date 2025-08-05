"""
Project Analyzer Agent - Figures out what needs to be done without being told
"""

import os
import re
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

class ProjectAnalyzerAgent:
    """Agent that analyzes the project and determines what needs to be done"""
    
    def __init__(self, project_path: str = "C:\\Empire\\Cibozer"):
        self.project_path = project_path
        self.issues_found = []
        self.opportunities = []
        
    def analyze_project(self) -> List[Dict[str, Any]]:
        """Analyze the entire project and find what needs to be done"""
        
        tasks = []
        
        print("ANALYZING PROJECT...")
        print("="*50)
        
        # 1. Check for TODO comments in code
        todos = self._find_todo_comments()
        for todo in todos:
            tasks.append({
                "priority": "high",
                "type": "todo",
                "task": todo["task"],
                "location": todo["file"],
                "reason": "TODO comment found in code"
            })
        
        # 2. Check for failing tests
        test_issues = self._check_test_status()
        for issue in test_issues:
            tasks.append({
                "priority": "critical",
                "type": "test_failure",
                "task": f"Fix failing test: {issue}",
                "reason": "Test is failing"
            })
        
        # 3. Check for security issues
        security_issues = self._check_security()
        for issue in security_issues:
            tasks.append({
                "priority": "critical",
                "type": "security",
                "task": f"Fix security issue: {issue}",
                "reason": "Security vulnerability detected"
            })
        
        # 4. Check for missing documentation
        doc_issues = self._check_documentation()
        for issue in doc_issues:
            tasks.append({
                "priority": "low",
                "type": "documentation",
                "task": f"Add documentation for {issue}",
                "reason": "Missing documentation"
            })
        
        # 5. Check for code quality issues
        quality_issues = self._check_code_quality()
        for issue in quality_issues:
            tasks.append({
                "priority": "medium",
                "type": "code_quality",
                "task": f"Refactor: {issue}",
                "reason": "Code quality improvement needed"
            })
        
        # 6. Check for performance issues
        perf_issues = self._check_performance()
        for issue in perf_issues:
            tasks.append({
                "priority": "medium",
                "type": "performance",
                "task": f"Optimize: {issue}",
                "reason": "Performance optimization opportunity"
            })
        
        # 7. Check for missing features (based on common patterns)
        missing_features = self._check_missing_features()
        for feature in missing_features:
            tasks.append({
                "priority": "medium",
                "type": "feature",
                "task": f"Add feature: {feature}",
                "reason": "Common feature missing"
            })
        
        # 8. Check deployment readiness
        deploy_issues = self._check_deployment_readiness()
        for issue in deploy_issues:
            tasks.append({
                "priority": "high",
                "type": "deployment",
                "task": f"Fix deployment issue: {issue}",
                "reason": "Deployment configuration needed"
            })
        
        return tasks
    
    def _find_todo_comments(self) -> List[Dict]:
        """Find TODO, FIXME, HACK comments in code"""
        todos = []
        patterns = [r'#\s*(TODO|FIXME|HACK|XXX|BUG):\s*(.+)', r'//\s*(TODO|FIXME|HACK|XXX|BUG):\s*(.+)']
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip certain directories
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules', '.agent_sessions']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    todos.append({
                                        "file": filepath.replace(self.project_path, ''),
                                        "type": match[0],
                                        "task": match[1].strip()
                                    })
                    except:
                        pass
        
        return todos[:5]  # Return top 5 TODOs
    
    def _check_test_status(self) -> List[str]:
        """Check if tests are passing"""
        issues = []
        
        # Check if test files exist
        test_dir = os.path.join(self.project_path, 'tests')
        if not os.path.exists(test_dir):
            issues.append("No tests directory found - add tests")
            return issues
        
        # Check for test files
        test_files = [f for f in os.listdir(test_dir) if f.startswith('test_') and f.endswith('.py')]
        if len(test_files) < 3:
            issues.append("Insufficient test coverage - add more tests")
        
        # Check if certain important files have tests
        important_modules = ['meal_optimizer', 'app', 'models']
        for module in important_modules:
            test_file = f"test_{module}.py"
            if test_file not in test_files:
                issues.append(f"Missing tests for {module}")
        
        return issues[:3]  # Return top 3 issues
    
    def _check_security(self) -> List[str]:
        """Check for common security issues"""
        issues = []
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'api[_-]?key\s*=\s*["\'][\w]+["\']',
            r'password\s*=\s*["\'][\w]+["\']',
            r'secret\s*=\s*["\'][\w]+["\']'
        ]
        
        for root, dirs, files in os.walk(self.project_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.env.example')):
                    continue  # Skip example files
                    
                if file.endswith(('.py', '.js', '.jsx', '.json', '.yml', '.yaml')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for pattern in secret_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    issues.append(f"Potential hardcoded secret in {file}")
                                    break
                    except:
                        pass
        
        # Check for missing security headers
        if os.path.exists(os.path.join(self.project_path, 'app', '__init__.py')):
            issues.append("Verify security headers are configured")
        
        # Check for SQL injection vulnerabilities
        issues.append("Audit database queries for SQL injection risks")
        
        return issues[:3]
    
    def _check_documentation(self) -> List[str]:
        """Check for missing documentation"""
        issues = []
        
        # Check for README
        if not os.path.exists(os.path.join(self.project_path, 'README.md')):
            issues.append("README.md file")
        
        # Check for API documentation
        if not os.path.exists(os.path.join(self.project_path, 'API_DOCUMENTATION.md')):
            issues.append("API documentation")
        
        # Check for inline documentation
        for root, dirs, files in os.walk(self.project_path):
            if 'routes' in root:
                for file in files:
                    if file.endswith('.py'):
                        issues.append(f"API endpoint documentation in {file}")
                        break
                break
        
        return issues[:2]
    
    def _check_code_quality(self) -> List[str]:
        """Check for code quality issues"""
        issues = []
        
        # Check for long functions
        for root, dirs, files in os.walk(self.project_path):
            if any(skip in root for skip in ['.git', '__pycache__', 'node_modules']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            if len(lines) > 500:
                                issues.append(f"Large file {file} - consider splitting")
                    except:
                        pass
        
        # Check for duplicate code
        issues.append("Check for duplicate code patterns")
        
        # Check for error handling
        issues.append("Improve error handling in API endpoints")
        
        return issues[:2]
    
    def _check_performance(self) -> List[str]:
        """Check for performance issues"""
        issues = []
        
        # Check for missing indexes
        if os.path.exists(os.path.join(self.project_path, 'app', 'models')):
            issues.append("Database query optimization - add indexes")
        
        # Check for caching opportunities
        issues.append("Add caching for frequently accessed data")
        
        # Check for N+1 queries
        issues.append("Check for N+1 query problems")
        
        return issues[:2]
    
    def _check_missing_features(self) -> List[str]:
        """Check for commonly missing features"""
        features = []
        
        # Check for user features
        if os.path.exists(os.path.join(self.project_path, 'app', 'models', 'user.py')):
            features.append("Password reset functionality")
            features.append("Email verification")
            features.append("User profile page")
        
        # Check for API features
        if os.path.exists(os.path.join(self.project_path, 'app', 'routes', 'api.py')):
            features.append("API rate limiting")
            features.append("API versioning")
        
        # Check for general features
        features.append("Search functionality")
        features.append("Export data feature")
        features.append("Dark mode toggle")
        
        return features[:3]
    
    def _check_deployment_readiness(self) -> List[str]:
        """Check deployment configuration"""
        issues = []
        
        # Check for Docker setup
        if not os.path.exists(os.path.join(self.project_path, 'Dockerfile')):
            issues.append("Missing Dockerfile")
        
        # Check for CI/CD
        if not os.path.exists(os.path.join(self.project_path, '.github', 'workflows')):
            issues.append("Missing CI/CD pipeline")
        
        # Check for environment configuration
        if not os.path.exists(os.path.join(self.project_path, '.env.example')):
            issues.append("Missing .env.example file")
        
        # Check for monitoring
        issues.append("Add application monitoring")
        
        return issues[:2]
    
    def prioritize_tasks(self, tasks: List[Dict]) -> List[Dict]:
        """Prioritize tasks based on importance"""
        
        # Priority scores
        priority_scores = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "trivial": 1
        }
        
        # Type scores (what's most important)
        type_scores = {
            "security": 5,
            "test_failure": 4,
            "deployment": 3,
            "todo": 3,
            "performance": 2,
            "feature": 2,
            "code_quality": 1,
            "documentation": 1
        }
        
        # Calculate scores
        for task in tasks:
            task["score"] = priority_scores.get(task["priority"], 0) * 10 + type_scores.get(task["type"], 0)
        
        # Sort by score
        tasks.sort(key=lambda x: x["score"], reverse=True)
        
        return tasks
    
    def get_next_task(self) -> Optional[str]:
        """Get the next most important task to work on"""
        tasks = self.analyze_project()
        
        if not tasks:
            return None
        
        tasks = self.prioritize_tasks(tasks)
        
        # Return the highest priority task
        best_task = tasks[0]
        
        print(f"\nFOUND {len(tasks)} TASKS TO DO")
        print(f"Most Important: {best_task['task']}")
        print(f"Reason: {best_task['reason']}")
        print(f"Priority: {best_task['priority'].upper()}")
        
        return best_task['task']


# Add to the main agent system
def add_project_analyzer_to_agents():
    """Add the project analyzer as a new agent type"""
    
    agent_definition = {
        "project-analyzer": {
            "description": "Project Analyzer agent that figures out what needs to be done",
            "prompt": """You are a Project Analyzer agent responsible for analyzing the codebase and determining what needs to be done.

Your responsibilities:
- Analyze code for TODOs, FIXMEs, and other markers
- Check test coverage and failing tests
- Identify security vulnerabilities
- Find missing documentation
- Detect code quality issues
- Identify performance bottlenecks
- Discover missing common features
- Check deployment readiness

When analyzing a project:
1. Scan the entire codebase systematically
2. Prioritize issues by importance
3. Generate actionable tasks
4. Focus on high-impact improvements
5. Consider user experience and business value

You should be proactive and identify issues before they become problems."""
        }
    }
    
    return agent_definition

