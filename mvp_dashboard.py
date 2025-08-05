#!/usr/bin/env python3
"""
MVP Dashboard - Track progress toward 10 real users in 30 days
"""

import json
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class MVPDashboard:
    """Dashboard for tracking MVP progress"""
    
    def __init__(self):
        self.sprint_dir = Path.cwd() / '.sprint'
        self.mvp_tracker_file = self.sprint_dir / 'mvp_tracker.json'
        self.mvp_tracker = self._load_mvp_tracker()
        
    def _load_mvp_tracker(self) -> Dict:
        """Load MVP tracker data"""
        if self.mvp_tracker_file.exists():
            with open(self.mvp_tracker_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("❌ No MVP tracker found. Run 'python new_sprint.py' first.")
            sys.exit(1)
    
    def show_dashboard(self):
        """Display the MVP dashboard"""
        print("\n" + "="*80)
        print("🎯 MVP DASHBOARD - 10 Real Users in 30 Days")
        print("="*80)
        
        # Calculate days remaining
        start_date = datetime.fromisoformat(self.mvp_tracker['mvp_goal']['start_date'])
        end_date = datetime.fromisoformat(self.mvp_tracker['mvp_goal']['end_date'])
        today = datetime.now()
        days_elapsed = (today - start_date).days
        days_remaining = (end_date - today).days
        
        print(f"\n📅 Timeline: Day {days_elapsed}/30 ({days_remaining} days remaining)")
        
        # Progress bar
        progress = min(days_elapsed / 30, 1.0)
        bar_length = 50
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"Progress: [{bar}] {progress*100:.0f}%")
        
        # Current week status
        current_week = self.mvp_tracker['mvp_goal']['current_week']
        week_data = self.mvp_tracker['weekly_goals'].get(f'week{current_week}', {})
        print(f"\n📌 Current Focus: Week {current_week} - {week_data.get('name', 'Unknown')}")
        print(f"Status: {week_data.get('status', 'pending').upper()}")
        
        # Show weekly progress
        print("\n📊 Weekly Progress:")
        for week_num in range(1, 5):
            week_key = f'week{week_num}'
            week = self.mvp_tracker['weekly_goals'].get(week_key, {})
            status_icon = {
                'completed': '✅',
                'in_progress': '🔄',
                'pending': '⏳'
            }.get(week.get('status', 'pending'), '❓')
            
            print(f"  Week {week_num}: {status_icon} {week.get('name', 'Unknown')}")
            
            # Show success metrics for current/completed weeks
            if week.get('status') in ['completed', 'in_progress']:
                metrics = week.get('success_metrics', {})
                true_count = sum(1 for v in metrics.values() if v)
                total_count = len(metrics)
                print(f"         Metrics: {true_count}/{total_count} achieved")
        
        # Core requirements checklist
        print("\n✅ Core Requirements (Must Work):")
        for i, req in enumerate(self.mvp_tracker['core_requirements']['must_work'], 1):
            # Check if requirement is met (simplified check)
            check = "☐" if i > current_week else "☑"
            print(f"  {check} {req}")
        
        # Current metrics
        metrics = self.mvp_tracker['current_metrics']
        print("\n📈 Current Metrics:")
        print(f"  👥 Real Users: {metrics['real_users']}/10")
        print(f"  📝 Meal Plans Created: {metrics['meal_plans_created']}")
        print(f"  🔄 Returning Users: {metrics['returning_users']}")
        print(f"  ⏱️ Uptime Hours: {metrics['uptime_hours']}")
        
        # Success criteria for current week
        print(f"\n🎯 Week {current_week} Success Criteria:")
        for req in week_data.get('requirements', [])[:3]:
            print(f"  • {req}")
        if len(week_data.get('requirements', [])) > 3:
            print(f"  ... and {len(week_data['requirements']) - 3} more")
        
        # Daily checklist
        print("\n📋 Today's Checklist:")
        checklist = self.mvp_tracker['daily_checklist']
        print(f"  ☐ Is the site up? {checklist.get('site_up', 'Not checked')}")
        print(f"  ☐ New signups today? {checklist.get('new_signups', 0)}")
        print(f"  ☐ Bugs reported? {len(checklist.get('bugs_reported', []))}")
        print(f"  ☐ Top problem? {checklist.get('top_problem', 'Not identified')}")
        print(f"  ☐ Quick fix? {checklist.get('quick_fix', 'Not identified')}")
        
        # Next action
        print("\n🚀 Next Action:")
        if current_week == 1:
            print("  → Run tests: python -m pytest tests/")
            print("  → Fix the first failing test")
        elif current_week == 2:
            print("  → Add loading indicators to async operations")
            print("  → Test with a non-technical person")
        elif current_week == 3:
            print("  → Set up Sentry monitoring")
            print("  → Test with 5 friends/family")
        elif current_week == 4:
            print("  → Create landing page")
            print("  → Post in relevant community")
        
        # Show recent progress log
        if self.mvp_tracker.get('progress_log'):
            print("\n📜 Recent Activity:")
            for entry in self.mvp_tracker['progress_log'][-3:]:
                date = datetime.fromisoformat(entry['date']).strftime("%m/%d")
                print(f"  {date}: {entry['sprint']} ({entry['completion_rate']}% complete)")
        
        print("\n" + "="*80)
        print("💪 Remember: The goal isn't perfection. It's 10 real users using a thing that works.")
        print("="*80)
    
    def update_metrics(self, **kwargs):
        """Update MVP metrics"""
        metrics = self.mvp_tracker['current_metrics']
        
        for key, value in kwargs.items():
            if key in metrics:
                if isinstance(metrics[key], int):
                    metrics[key] += value
                else:
                    metrics[key] = value
        
        # Save updated tracker
        with open(self.mvp_tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.mvp_tracker, f, indent=2)
        
        print(f"✅ Metrics updated: {kwargs}")
    
    def check_daily(self):
        """Interactive daily checklist"""
        print("\n📋 Daily MVP Check")
        print("-" * 40)
        
        checklist = self.mvp_tracker['daily_checklist']
        
        # Check site status
        site_up = input("Is the site up and running? (y/n): ").lower() == 'y'
        checklist['site_up'] = site_up
        
        # Check signups
        signups = input("How many new signups today? (0 if none): ")
        try:
            checklist['new_signups'] = int(signups)
        except:
            checklist['new_signups'] = 0
        
        # Check bugs
        bugs = input("Any bugs reported? (describe or press enter): ").strip()
        if bugs:
            checklist['bugs_reported'].append({
                'date': datetime.now().isoformat(),
                'description': bugs
            })
        
        # Identify top problem
        problem = input("What's the #1 problem right now? ").strip()
        if problem:
            checklist['top_problem'] = problem
        
        # Identify quick fix
        fix = input("What can you fix in 2 hours? ").strip()
        if fix:
            checklist['quick_fix'] = fix
        
        # Save updated tracker
        with open(self.mvp_tracker_file, 'w', encoding='utf-8') as f:
            json.dump(self.mvp_tracker, f, indent=2)
        
        print("\n✅ Daily check complete!")
        
        # Show summary
        if checklist['new_signups'] > 0:
            self.mvp_tracker['current_metrics']['total_users'] += checklist['new_signups']
            print(f"🎉 {checklist['new_signups']} new users! Total: {self.mvp_tracker['current_metrics']['total_users']}")
        
        if checklist['top_problem']:
            print(f"⚠️ Focus on: {checklist['top_problem']}")
        
        if checklist['quick_fix']:
            print(f"💡 Quick win: {checklist['quick_fix']}")


def main():
    """Main entry point"""
    dashboard = MVPDashboard()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'check':
            dashboard.check_daily()
        elif command == 'update':
            # Example: python mvp_dashboard.py update real_users=1
            if len(sys.argv) > 2:
                updates = {}
                for arg in sys.argv[2:]:
                    if '=' in arg:
                        key, value = arg.split('=')
                        try:
                            updates[key] = int(value)
                        except:
                            updates[key] = value
                dashboard.update_metrics(**updates)
            else:
                print("Usage: python mvp_dashboard.py update key=value")
        else:
            print(f"Unknown command: {command}")
            print("Usage: python mvp_dashboard.py [check|update]")
    else:
        # Default: show dashboard
        dashboard.show_dashboard()


if __name__ == "__main__":
    main()