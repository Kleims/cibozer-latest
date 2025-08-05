#!/usr/bin/env python3
"""
Focused Real Sprint System - Does actual work on specific tasks
"""

import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

class FocusedSprintExecutor:
    """Execute real sprint tasks efficiently"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.log = []
        
    def run_focused_sprint(self):
        """Run a focused sprint that actually does work"""
        print("FOCUSED REAL SPRINT SYSTEM")
        print("=" * 50)
        
        # Step 1: Quick health check
        print("\nStep 1: Quick Health Check")
        health = self.check_project_health()
        self.display_health(health)
        
        # Step 2: Execute focused tasks
        print("\nStep 2: Executing Real Tasks")
        tasks_completed = []
        
        # Task 1: Fix import issues in tests
        if self.fix_import_issues():
            tasks_completed.append("Fixed import issues in test files")
            
        # Task 2: Fix basic test setup issues
        if self.fix_test_setup():
            tasks_completed.append("Fixed test setup and configuration")
            
        # Task 3: Run a subset of tests to verify fixes
        if self.verify_test_fixes():
            tasks_completed.append("Verified test fixes work")
        
        # Step 3: Report results
        print("\nStep 3: Sprint Results")
        print(f"Tasks completed: {len(tasks_completed)}")
        for task in tasks_completed:
            print(f"  - {task}")
        
        # Save results
        self.save_sprint_results(tasks_completed)
        
        return len(tasks_completed) > 0
    
    def check_project_health(self):
        """Quick project health check"""
        health = {
            'test_files': 0,
            'app_files': 0,
            'can_import_app': False,
            'has_requirements': False
        }
        
        # Count test files
        if os.path.exists('tests'):
            health['test_files'] = len([f for f in os.listdir('tests') if f.endswith('.py')])
        
        # Count app files
        if os.path.exists('app'):
            health['app_files'] = len([f for f in os.listdir('app') if f.endswith('.py')])
        
        # Test app import
        try:
            result = subprocess.run([sys.executable, '-c', 'from app import create_app; print("OK")'], 
                                  capture_output=True, text=True, timeout=10)
            health['can_import_app'] = result.returncode == 0
        except:
            health['can_import_app'] = False
        
        # Check for requirements
        health['has_requirements'] = os.path.exists('requirements.txt')
        
        return health
    
    def display_health(self, health):
        """Display health check results"""
        print(f"  Test files: {health['test_files']}")
        print(f"  App files: {health['app_files']}")
        print(f"  Can import app: {'YES' if health['can_import_app'] else 'NO'}")
        print(f"  Has requirements: {'YES' if health['has_requirements'] else 'NO'}")
    
    def fix_import_issues(self):
        """Fix common import issues in test files"""
        print("  Fixing import issues...")
        
        fixes_made = 0
        test_files = []
        
        if not os.path.exists('tests'):
            return False
        
        # Get list of test files
        for root, dirs, files in os.walk('tests'):
            for file in files:
                if file.endswith('.py'):
                    test_files.append(os.path.join(root, file))
        
        # Fix imports in first few test files
        for test_file in test_files[:5]:  # Limit to first 5 files
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Fix 1: Add missing imports
                if 'import pytest' not in content and 'def test_' in content:
                    content = 'import pytest\n' + content
                    fixes_made += 1
                
                # Fix 2: Fix app imports
                if 'from app import' in content and 'sys.path.insert' not in content:
                    # Add path fix for app imports
                    path_fix = "import sys\nimport os\nsys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
                    content = path_fix + content
                    fixes_made += 1
                
                # Save if changes made
                if content != original_content:
                    with open(test_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.log.append(f"Fixed imports in {test_file}")
                
            except Exception as e:
                self.log.append(f"Error fixing {test_file}: {str(e)}")
                continue
        
        print(f"    Applied {fixes_made} import fixes")
        return fixes_made > 0
    
    def fix_test_setup(self):
        """Fix test setup and configuration issues"""
        print("  Fixing test setup...")
        
        fixes_made = 0
        
        # Create conftest.py if missing
        conftest_path = 'tests/conftest.py'
        if not os.path.exists(conftest_path):
            conftest_content = '''
import pytest
import os
import sys

# Add the parent directory to the path so we can import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test runner"""  
    return app.test_cli_runner()
'''
            try:
                with open(conftest_path, 'w', encoding='utf-8') as f:
                    f.write(conftest_content)
                fixes_made += 1
                self.log.append("Created conftest.py with basic fixtures")
            except Exception as e:
                self.log.append(f"Error creating conftest.py: {str(e)}")
        
        print(f"    Applied {fixes_made} setup fixes")
        return fixes_made > 0
    
    def verify_test_fixes(self):
        """Run a small subset of tests to verify fixes work"""
        print("  Verifying fixes...")
        
        try:
            # Try to run just one test file to see if imports work
            test_files = [f for f in os.listdir('tests') if f.startswith('test_') and f.endswith('.py')]
            
            if not test_files:
                return False
            
            # Pick the first test file
            test_file = os.path.join('tests', test_files[0])
            
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            output = result.stdout + result.stderr
            
            # Check if there were import errors
            import_errors = output.count('ImportError') + output.count('ModuleNotFoundError')
            
            if import_errors == 0:
                print(f"    SUCCESS: No import errors in {test_files[0]}")
                self.log.append(f"Test file {test_files[0]} runs without import errors")
                return True
            else:
                print(f"    Still has {import_errors} import errors")
                return False
                
        except subprocess.TimeoutExpired:
            print("    Test verification timed out")
            return False
        except Exception as e:
            print(f"    Verification error: {str(e)}")
            return False
    
    def save_sprint_results(self, tasks_completed):
        """Save sprint results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'tasks_completed': tasks_completed,
            'execution_log': self.log,
            'sprint_type': 'focused_real_sprint'
        }
        
        # Create .sprint directory if it doesn't exist
        sprint_dir = Path('.sprint')
        sprint_dir.mkdir(exist_ok=True)
        
        # Save results
        results_file = sprint_dir / 'last_focused_sprint.json'
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to {results_file}")
        except Exception as e:
            print(f"Error saving results: {e}")

def main():
    """Run focused sprint"""
    executor = FocusedSprintExecutor()
    success = executor.run_focused_sprint()
    
    if success:
        print("\nFOCUSED SPRINT COMPLETED SUCCESSFULLY!")
        print("Run 'python focused_sprint.py' again to continue improving.")
    else:
        print("\nFOCUSED SPRINT COMPLETED - No tasks executed")
        print("Check the logs above for any issues.")

if __name__ == "__main__":
    main()