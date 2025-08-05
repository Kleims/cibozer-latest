#!/usr/bin/env python3
"""
Auto Sprint Runner - Automatically selects and runs MVP Week 1 sprint
"""

import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
try:
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
except:
    pass  # Fallback to default encoding

# Import the sprint manager
from new_sprint import UnifiedSprintManager

class AutoSprintRunner:
    """Automatically runs MVP Week 1 sprint"""
    
    def run(self):
        """Run MVP Week 1 sprint automatically"""
        print("\n" + "="*70)
        print("🚀 AUTO SPRINT RUNNER - MVP WEEK 1")
        print("="*70)
        
        manager = UnifiedSprintManager()
        
        # Step 1: Analyze status
        print("\n📊 STEP 1: ANALYZING CURRENT STATUS...")
        print("-"*50)
        status = manager._analyze_status()
        
        # Step 2: Auto-select MVP Week 1
        print("\n💡 STEP 2: AUTO-SELECTING MVP WEEK 1")
        print("-"*50)
        selected_focus = 'mvp_week1_fix'
        print(f"✅ Auto-selected: 🔧 MVP Week 1: Make It Not Broken")
        
        # Save recommendation
        recommendations = [{
            'id': 'mvp_week1_fix',
            'title': '🔧 MVP Week 1: Make It Not Broken',
            'description': 'Fix all failing tests, eliminate 500 errors, ensure all pages load',
            'priority': 'CRITICAL',
            'estimated_impact': 'REQUIRED: Zero crashes, all pages working'
        }]
        
        with open(manager.recommendations_file, 'w', encoding='utf-8') as f:
            json.dump({
                'selected': recommendations[0],
                'all_options': recommendations,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        
        # Step 3: Create sprint plan
        print("\n📋 STEP 3: CREATING SPRINT PLAN")
        print("-"*50)
        sprint_plan = manager._create_sprint_plan(selected_focus, status)
        
        # Step 4: Execute sprint (limited execution)
        print("\n⚡ STEP 4: EXECUTING SPRINT TASKS")
        print("-"*50)
        
        # Instead of full execution, we'll create a task list
        print("\n📝 Tasks to Complete:")
        tasks = [
            "Fix or disable 64 failing tests",
            "Find and fix ALL 500 errors on every page",
            "Ensure registration form works completely",
            "Ensure login persists session properly",
            "Fix meal plan generation (< 5 seconds)",
            "Fix save meal plan functionality",
            "Fix view saved plans page",
            "Ensure all pages load in < 3 seconds",
            "Test on Chrome, Firefox, Safari",
            "Test on mobile browsers",
            "Set up production deployment",
            "Configure production database"
        ]
        
        for i, task in enumerate(tasks[:5], 1):
            print(f"   {i}. {task}")
        print(f"   ... and {len(tasks) - 5} more tasks")
        
        # Create execution results
        execution_results = {
            'completed_tasks': [],
            'failed_tasks': [],
            'metrics_before': manager._capture_metrics(),
            'metrics_after': manager._capture_metrics(),
            'execution_log': ["Sprint created - manual execution required"]
        }
        
        # Step 5: Review
        print("\n🔍 STEP 5: REVIEWING SPRINT RESULTS")
        print("-"*50)
        review = manager._review_sprint(sprint_plan, execution_results)
        
        # Step 6: Document
        print("\n📝 STEP 6: DOCUMENTING SPRINT")
        print("-"*50)
        manager._document_sprint(sprint_plan, review)
        
        print("\n" + "="*70)
        print("✅ MVP WEEK 1 SPRINT CREATED!")
        print("="*70)
        
        # Show next actions
        print("\n🚀 NEXT ACTIONS:")
        print("1. Run tests to see failures:")
        print("   python -m pytest tests/")
        print("\n2. Start fixing the first issue:")
        print("   - Look for 500 errors in routes")
        print("   - Fix failing authentication tests")
        print("   - Ensure core user flow works")
        print("\n3. Track progress:")
        print("   python mvp_dashboard.py")
        print("\n4. Daily check-in:")
        print("   python mvp_dashboard.py check")
        
        return sprint_plan


if __name__ == "__main__":
    runner = AutoSprintRunner()
    sprint_plan = runner.run()