#!/usr/bin/env python3
"""
Sprint Manager - Focused Development System
Replaces agent-based approach with prompt-driven sprints
"""

import subprocess
import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class SprintManager:
    """Manages sprint-based development with focused prompts"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.sprint_file = self.root / '.sprint' / 'current_sprint.json'
        self.sprint_file.parent.mkdir(exist_ok=True)
        self.vision_file = self.root / 'PRODUCT_VISION.md'
        self.sprint_system_file = self.root / 'SPRINT_SYSTEM.md'
        
        # Load current sprint data
        self.current_sprint = self._load_sprint_data()
        
    def _load_sprint_data(self) -> Dict:
        """Load current sprint data"""
        if self.sprint_file.exists():
            with open(self.sprint_file, 'r') as f:
                return json.load(f)
        return {
            'number': 0,
            'name': 'Foundation',
            'started': datetime.now().isoformat(),
            'goal': 'Stabilize codebase, reach 200+ passing tests',
            'tasks': [],
            'completed': [],
            'metrics': {}
        }
    
    def _save_sprint_data(self):
        """Save current sprint data"""
        with open(self.sprint_file, 'w') as f:
            json.dump(self.current_sprint, f, indent=2)
    
    def status(self) -> Dict:
        """Get current sprint status"""
        print("\n" + "="*60)
        print(f"📊 SPRINT {self.current_sprint['number']}: {self.current_sprint['name']}")
        print("="*60)
        
        # Run tests
        print("\n🧪 Running tests...")
        test_result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-q', '--tb=no'],
            capture_output=True,
            text=True
        )
        
        # Parse test results
        output = test_result.stdout + test_result.stderr
        passed = len(re.findall(r'\.', output))
        failed = len(re.findall(r'F', output))
        errors = len(re.findall(r'E', output))
        total = passed + failed + errors
        
        # Check for critical issues
        critical_issues = self._check_critical_issues()
        
        # Performance metrics
        performance = self._check_performance()
        
        # Update metrics
        self.current_sprint['metrics'] = {
            'tests_total': total,
            'tests_passing': passed,
            'tests_failing': failed + errors,
            'coverage': round((passed / total * 100) if total > 0 else 0, 1),
            'critical_issues': len(critical_issues),
            'performance': performance
        }
        
        # Display status
        print(f"\n✅ Tests: {passed}/{total} passing ({self.current_sprint['metrics']['coverage']}%)")
        if failed + errors > 0:
            print(f"❌ Failures: {failed + errors} tests failing")
        
        if critical_issues:
            print(f"\n🔴 Critical Issues: {len(critical_issues)}")
            for issue in critical_issues[:3]:
                print(f"  - {issue}")
        
        print(f"\n🎯 Sprint Goal: {self.current_sprint['goal']}")
        
        # Task progress
        total_tasks = len(self.current_sprint['tasks']) + len(self.current_sprint['completed'])
        if total_tasks > 0:
            progress = len(self.current_sprint['completed']) / total_tasks * 100
            print(f"\n📈 Progress: {len(self.current_sprint['completed'])}/{total_tasks} tasks ({progress:.0f}%)")
            
            if self.current_sprint['tasks']:
                print("\n📋 Remaining Tasks:")
                for task in self.current_sprint['tasks'][:5]:
                    print(f"  - {task}")
        
        self._save_sprint_data()
        return self.current_sprint['metrics']
    
    def _check_critical_issues(self) -> List[str]:
        """Check for critical issues in the codebase"""
        issues = []
        
        # Security issues
        security_patterns = [
            (r"password\s*=\s*['\"]", "Hardcoded password found"),
            (r"SECRET_KEY\s*=\s*['\"](?!os\.)", "Hardcoded secret key"),
            (r"eval\(", "Dangerous eval() usage"),
            (r"\.execute\(.+%s", "Potential SQL injection"),
        ]
        
        for py_file in self.root.rglob('*.py'):
            if 'test' in str(py_file) or 'venv' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                for pattern, issue_desc in security_patterns:
                    if re.search(pattern, content):
                        issues.append(f"{issue_desc} in {py_file.name}")
            except:
                pass
        
        return issues
    
    def _check_performance(self) -> Dict:
        """Check basic performance metrics"""
        # Simple performance check - can be enhanced
        return {
            'startup_time': 'Not measured',
            'avg_response': 'Not measured',
            'database_queries': 'Not measured'
        }
    
    def plan(self, sprint_number: int = None):
        """Plan a new sprint"""
        if sprint_number is None:
            sprint_number = self.current_sprint['number'] + 1
        
        sprint_goals = {
            0: ("Foundation", "Stabilize codebase, reach 200+ passing tests"),
            1: ("Payment Integration", "Complete Stripe integration with subscription tiers"),
            2: ("User Experience", "Polish UI/UX for production quality"),
            3: ("Performance & Scale", "Optimize for 100+ concurrent users"),
            4: ("Analytics & Admin", "Complete admin dashboard with metrics"),
            5: ("Marketing Features", "SEO, social sharing, referral system"),
            6: ("Production Hardening", "99.9% uptime, automated everything")
        }
        
        name, goal = sprint_goals.get(sprint_number, ("Custom", "Define your goal"))
        
        print("\n" + "="*60)
        print(f"📋 PLANNING SPRINT {sprint_number}: {name}")
        print("="*60)
        
        # Analyze current state
        current_status = self.status()
        
        # Generate tasks based on current issues
        tasks = self._generate_sprint_tasks(sprint_number, current_status)
        
        # Create new sprint
        self.current_sprint = {
            'number': sprint_number,
            'name': name,
            'started': datetime.now().isoformat(),
            'goal': goal,
            'tasks': tasks,
            'completed': [],
            'metrics': current_status
        }
        
        self._save_sprint_data()
        
        print(f"\n🎯 Sprint Goal: {goal}")
        print(f"\n📋 Sprint Backlog ({len(tasks)} tasks):")
        for i, task in enumerate(tasks[:10], 1):
            print(f"  {i}. {task}")
        
        print("\n✅ Sprint planned! Run 'python sprint_manager.py execute' to start.")
    
    def _generate_sprint_tasks(self, sprint_number: int, status: Dict) -> List[str]:
        """Generate tasks for the sprint based on current state"""
        tasks = []
        
        # Sprint 0: Foundation
        if sprint_number == 0:
            if status['tests_failing'] > 0:
                tasks.append(f"Fix {status['tests_failing']} failing tests")
            if status['critical_issues'] > 0:
                tasks.append(f"Fix {status['critical_issues']} critical security issues")
            tasks.extend([
                "Ensure all models have proper relationships",
                "Fix database migration issues",
                "Verify all routes are accessible",
                "Add missing error handlers",
                "Clean up deprecated code"
            ])
        
        # Sprint 1: Payments
        elif sprint_number == 1:
            tasks.extend([
                "Configure Stripe API keys",
                "Create checkout session endpoint",
                "Implement webhook handlers",
                "Add subscription management",
                "Create billing dashboard",
                "Add payment history",
                "Test payment flows"
            ])
        
        # Sprint 2: UX
        elif sprint_number == 2:
            tasks.extend([
                "Implement responsive design",
                "Add loading states",
                "Improve error messages",
                "Add form validation feedback",
                "Optimize images",
                "Add progress indicators",
                "Improve navigation"
            ])
        
        return tasks
    
    def execute(self):
        """Execute current sprint tasks"""
        if not self.current_sprint['tasks']:
            print("✅ No tasks remaining in current sprint!")
            return
        
        # Get next task
        task = self.current_sprint['tasks'][0]
        
        print("\n" + "="*60)
        print(f"🚀 EXECUTING: {task}")
        print("="*60)
        
        # Execute based on task type
        if "failing test" in task.lower():
            self._fix_failing_tests()
        elif "security" in task.lower():
            self._fix_security_issues()
        elif "database" in task.lower():
            self._fix_database_issues()
        elif "route" in task.lower():
            self._verify_routes()
        else:
            print(f"\n📝 Manual task: {task}")
            print("\nGuidance:")
            print("1. Analyze the requirement")
            print("2. Write tests first")
            print("3. Implement the solution")
            print("4. Verify tests pass")
            print("5. Mark task complete when done")
        
        print(f"\n✅ Task addressed. Run 'python sprint_manager.py complete \"{task}\"' when done.")
    
    def _fix_failing_tests(self):
        """Fix failing tests"""
        print("\n🔧 Analyzing failing tests...")
        
        # Run tests with verbose output
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            capture_output=True,
            text=True
        )
        
        # Find specific failures
        failures = re.findall(r'FAILED (.*?) - (.*)', result.stdout)
        
        if failures:
            print(f"\n Found {len(failures)} failing tests:")
            for test, error in failures[:5]:
                print(f"\n❌ {test}")
                print(f"   Error: {error[:100]}...")
            
            print("\n💡 Common fixes:")
            print("  - Update imports if modules moved")
            print("  - Fix database setup in conftest.py")
            print("  - Update mocked responses")
            print("  - Check for missing fixtures")
    
    def _fix_security_issues(self):
        """Fix security vulnerabilities"""
        print("\n🔒 Scanning for security issues...")
        
        issues_found = []
        
        for py_file in self.root.rglob('*.py'):
            if 'test' in str(py_file) or 'venv' in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                # Check for hardcoded secrets
                if re.search(r"password\s*=\s*['\"]", content):
                    issues_found.append((py_file, "hardcoded password"))
                
                # Check for SQL injection
                if '.execute(' in content and '%s' not in content:
                    if '.format(' in content or 'f"' in content:
                        issues_found.append((py_file, "potential SQL injection"))
            except:
                pass
        
        if issues_found:
            print(f"\n🔴 Found {len(issues_found)} security issues:")
            for file, issue in issues_found[:5]:
                print(f"  - {file.name}: {issue}")
            
            print("\n💡 Fixes:")
            print("  - Move secrets to environment variables")
            print("  - Use parameterized queries")
            print("  - Add input validation")
    
    def _fix_database_issues(self):
        """Fix database related issues"""
        print("\n🗄️ Checking database setup...")
        
        # Check if models exist
        models_file = self.root / 'app' / 'models' / '__init__.py'
        if not models_file.exists():
            print("❌ Models not properly organized")
            print("💡 Create app/models/ directory with proper structure")
        
        # Check migrations
        migrations_dir = self.root / 'migrations'
        if not migrations_dir.exists():
            print("❌ No migrations directory")
            print("💡 Run: flask db init")
        
        print("\n📝 Database checklist:")
        print("  1. Ensure all models are imported in __init__.py")
        print("  2. Run: flask db migrate -m 'Initial migration'")
        print("  3. Run: flask db upgrade")
        print("  4. Verify with: python verify_database.py")
    
    def _verify_routes(self):
        """Verify all routes are accessible"""
        print("\n🌐 Checking routes...")
        
        # Get all route files
        routes_dir = self.root / 'app' / 'routes'
        if routes_dir.exists():
            route_files = list(routes_dir.glob('*.py'))
            print(f"Found {len(route_files)} route modules")
            
            for route_file in route_files:
                print(f"  ✓ {route_file.name}")
        
        print("\n💡 Route verification:")
        print("  1. Start server: python wsgi.py")
        print("  2. Test each endpoint with curl or browser")
        print("  3. Check for 404s and 500s")
        print("  4. Verify authentication required where needed")
    
    def complete(self, task_description: str):
        """Mark a task as complete"""
        if task_description in self.current_sprint['tasks']:
            self.current_sprint['tasks'].remove(task_description)
            self.current_sprint['completed'].append(task_description)
            self._save_sprint_data()
            
            print(f"✅ Task completed: {task_description}")
            print(f"📊 Sprint progress: {len(self.current_sprint['completed'])}/{len(self.current_sprint['completed']) + len(self.current_sprint['tasks'])} tasks")
            
            if not self.current_sprint['tasks']:
                print("\n🎉 Sprint complete! Run 'python sprint_manager.py review' to see results.")
        else:
            print(f"❌ Task not found in current sprint")
    
    def review(self):
        """Review current sprint"""
        print("\n" + "="*60)
        print(f"📊 SPRINT {self.current_sprint['number']} REVIEW: {self.current_sprint['name']}")
        print("="*60)
        
        # Get current metrics
        current_metrics = self.status()
        
        # Compare with start
        start_metrics = self.current_sprint.get('metrics', {})
        
        print("\n📈 Progress:")
        print(f"  Tests: {start_metrics.get('tests_passing', 0)} → {current_metrics['tests_passing']} "
              f"(+{current_metrics['tests_passing'] - start_metrics.get('tests_passing', 0)})")
        print(f"  Coverage: {start_metrics.get('coverage', 0)}% → {current_metrics['coverage']}%")
        print(f"  Critical Issues: {start_metrics.get('critical_issues', 0)} → {current_metrics['critical_issues']}")
        
        print(f"\n✅ Completed Tasks ({len(self.current_sprint['completed'])}):")
        for task in self.current_sprint['completed'][:10]:
            print(f"  - {task}")
        
        if self.current_sprint['tasks']:
            print(f"\n⏳ Remaining Tasks ({len(self.current_sprint['tasks'])}):")
            for task in self.current_sprint['tasks'][:5]:
                print(f"  - {task}")
        
        print("\n📝 Next Steps:")
        print("  1. Address remaining tasks")
        print("  2. Plan next sprint: python sprint_manager.py plan")
        print("  3. Continue execution: python sprint_manager.py execute")


def main():
    """Main entry point"""
    manager = SprintManager()
    
    if len(sys.argv) < 2:
        manager.status()
        return
    
    command = sys.argv[1]
    
    if command == 'status':
        manager.status()
    elif command == 'plan':
        sprint_num = int(sys.argv[2]) if len(sys.argv) > 2 else None
        manager.plan(sprint_num)
    elif command == 'execute':
        manager.execute()
    elif command == 'complete':
        if len(sys.argv) > 2:
            task = ' '.join(sys.argv[2:])
            manager.complete(task)
        else:
            print("Usage: python sprint_manager.py complete \"task description\"")
    elif command == 'review':
        manager.review()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, plan, execute, complete, review")


if __name__ == '__main__':
    main()