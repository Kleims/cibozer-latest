#!/usr/bin/env python3
"""
Sprint History Manager - Tracks sprint progress across sessions
Maintains continuity and learns from past sprints
"""

import json
import subprocess
import sys
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class SprintHistoryManager:
    """Manages sprint history and progress tracking"""
    
    def __init__(self):
        self.root = Path.cwd()
        self.sprint_dir = self.root / '.sprint'
        self.history_file = self.sprint_dir / 'sprint_history.json'
        self.sprint_dir.mkdir(exist_ok=True)
        
        # Load or initialize history
        self.history = self._load_history()
        
    def _load_history(self) -> Dict:
        """Load sprint history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'sprints': [],
            'total_sprints': 0,
            'start_date': datetime.now().isoformat(),
            'achievements': [],
            'recurring_issues': []
        }
    
    def _save_history(self):
        """Save sprint history to file"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2)
    
    def log_sprint_completion(self, sprint_data: Dict):
        """Log completed sprint to history"""
        sprint_record = {
            'number': sprint_data['number'],
            'name': sprint_data['name'],
            'started': sprint_data['started'],
            'completed': datetime.now().isoformat(),
            'goal': sprint_data['goal'],
            'tasks_completed': sprint_data.get('completed', []),
            'tasks_remaining': sprint_data.get('tasks', []),
            'metrics': sprint_data.get('metrics', {}),
            'improvements': []
        }
        
        # Analyze improvements
        if self.history['sprints']:
            last_sprint = self.history['sprints'][-1]
            last_metrics = last_sprint.get('metrics', {})
            current_metrics = sprint_record['metrics']
            
            if current_metrics.get('tests_passing', 0) > last_metrics.get('tests_passing', 0):
                improvement = f"Tests improved: {last_metrics.get('tests_passing', 0)} → {current_metrics.get('tests_passing', 0)}"
                sprint_record['improvements'].append(improvement)
            
            if current_metrics.get('critical_issues', 999) < last_metrics.get('critical_issues', 999):
                improvement = f"Critical issues reduced: {last_metrics.get('critical_issues', 999)} → {current_metrics.get('critical_issues', 0)}"
                sprint_record['improvements'].append(improvement)
        
        # Add to history
        self.history['sprints'].append(sprint_record)
        self.history['total_sprints'] += 1
        
        # Identify recurring issues
        self._identify_recurring_issues()
        
        # Save history
        self._save_history()
        
        # Archive current sprint file
        self._archive_sprint_file(sprint_data['number'])
        
        print(f"✅ Sprint {sprint_data['number']} logged to history")
        
    def _archive_sprint_file(self, sprint_number: int):
        """Archive current sprint file"""
        current_file = self.sprint_dir / 'current_sprint.json'
        archive_file = self.sprint_dir / f'sprint_{sprint_number:03d}.json'
        
        if current_file.exists():
            shutil.copy2(current_file, archive_file)
            print(f"Sprint file archived as {archive_file.name}")
    
    def _identify_recurring_issues(self):
        """Identify patterns in recurring issues"""
        if len(self.history['sprints']) < 2:
            return
        
        # Look for patterns in uncompleted tasks
        task_frequencies = {}
        for sprint in self.history['sprints'][-3:]:  # Last 3 sprints
            for task in sprint.get('tasks_remaining', []):
                key = self._normalize_task(task)
                task_frequencies[key] = task_frequencies.get(key, 0) + 1
        
        # Update recurring issues
        self.history['recurring_issues'] = [
            task for task, freq in task_frequencies.items() if freq >= 2
        ]
    
    def _normalize_task(self, task: str) -> str:
        """Normalize task description for comparison"""
        # Remove numbers and normalize common phrases
        import re
        task = re.sub(r'\d+', 'N', task.lower())
        task = re.sub(r'\s+', ' ', task).strip()
        return task
    
    def get_sprint_summary(self, last_n: int = 3) -> str:
        """Get summary of last N sprints"""
        if not self.history['sprints']:
            return "No sprint history available"
        
        summary = []
        summary.append("\n" + "="*60)
        summary.append(f"📊 SPRINT HISTORY (Last {last_n} sprints)")
        summary.append("="*60)
        
        for sprint in self.history['sprints'][-last_n:]:
            summary.append(f"\n🏃 Sprint {sprint['number']}: {sprint['name']}")
            summary.append(f"   Period: {sprint['started'][:10]} to {sprint['completed'][:10]}")
            summary.append(f"   Goal: {sprint['goal']}")
            
            metrics = sprint.get('metrics', {})
            if metrics:
                summary.append(f"   Tests: {metrics.get('tests_passing', 0)}/{metrics.get('tests_total', 0)} passing")
                summary.append(f"   Critical Issues: {metrics.get('critical_issues', 'Unknown')}")
            
            if sprint['improvements']:
                summary.append("   ✅ Improvements:")
                for imp in sprint['improvements']:
                    summary.append(f"      - {imp}")
            
            completed = len(sprint.get('tasks_completed', []))
            remaining = len(sprint.get('tasks_remaining', []))
            summary.append(f"   Tasks: {completed} completed, {remaining} remaining")
        
        if self.history['recurring_issues']:
            summary.append("\n⚠️ Recurring Issues:")
            for issue in self.history['recurring_issues'][:3]:
                summary.append(f"   - {issue}")
        
        # Overall progress
        if len(self.history['sprints']) >= 2:
            first_metrics = self.history['sprints'][0].get('metrics', {})
            last_metrics = self.history['sprints'][-1].get('metrics', {})
            
            summary.append("\n📈 Overall Progress:")
            tests_delta = last_metrics.get('tests_passing', 0) - first_metrics.get('tests_passing', 0)
            summary.append(f"   Tests: {first_metrics.get('tests_passing', 0)} → {last_metrics.get('tests_passing', 0)} ({'+' if tests_delta >= 0 else ''}{tests_delta})")
            
            issues_delta = last_metrics.get('critical_issues', 0) - first_metrics.get('critical_issues', 999)
            summary.append(f"   Critical Issues: {first_metrics.get('critical_issues', 'Unknown')} → {last_metrics.get('critical_issues', 0)} ({'+' if issues_delta >= 0 else ''}{issues_delta})")
        
        return '\n'.join(summary)
    
    def suggest_next_sprint_focus(self) -> List[str]:
        """Suggest focus areas for next sprint based on history"""
        suggestions = []
        
        if not self.history['sprints']:
            return ["Complete initial assessment", "Fix critical issues", "Establish baseline metrics"]
        
        last_sprint = self.history['sprints'][-1]
        metrics = last_sprint.get('metrics', {})
        
        # Based on test coverage
        coverage = metrics.get('coverage', 0)
        if coverage < 70:
            suggestions.append(f"Improve test coverage (currently {coverage}%)")
        elif coverage < 90:
            suggestions.append(f"Push test coverage to 90%+ (currently {coverage}%)")
        
        # Based on critical issues
        critical = metrics.get('critical_issues', 0)
        if critical > 0:
            suggestions.append(f"Eliminate remaining {critical} critical issues")
        
        # Based on recurring issues
        if self.history['recurring_issues']:
            suggestions.append(f"Address recurring issue: {self.history['recurring_issues'][0]}")
        
        # Based on uncompleted tasks
        if last_sprint.get('tasks_remaining'):
            suggestions.append(f"Complete {len(last_sprint['tasks_remaining'])} remaining tasks from last sprint")
        
        return suggestions[:3] if suggestions else ["Continue incremental improvements"]
    
    def create_sprint_report(self, sprint_data: Dict) -> str:
        """Create a detailed sprint report for commit message"""
        report = []
        report.append(f"Sprint {sprint_data['number']}: {sprint_data['name']} Completion Report")
        report.append("="*60)
        report.append(f"Started: {sprint_data['started'][:10]}")
        report.append(f"Completed: {datetime.now().isoformat()[:10]}")
        report.append(f"Goal: {sprint_data['goal']}")
        report.append("")
        
        metrics = sprint_data.get('metrics', {})
        if metrics:
            report.append("Metrics:")
            report.append(f"  - Tests: {metrics.get('tests_passing', 0)}/{metrics.get('tests_total', 0)} passing ({metrics.get('coverage', 0)}%)")
            report.append(f"  - Critical Issues: {metrics.get('critical_issues', 'Unknown')}")
        
        if sprint_data.get('completed'):
            report.append("")
            report.append("Completed Tasks:")
            for task in sprint_data['completed'][:10]:
                report.append(f"  ✅ {task}")
        
        if sprint_data.get('tasks'):
            report.append("")
            report.append("Remaining Tasks:")
            for task in sprint_data['tasks'][:5]:
                report.append(f"  ⏳ {task}")
        
        report.append("")
        report.append("Next Sprint Suggestions:")
        for suggestion in self.suggest_next_sprint_focus():
            report.append(f"  - {suggestion}")
        
        return '\n'.join(report)


def main():
    """Main entry point for sprint history management"""
    import sys
    
    manager = SprintHistoryManager()
    
    if len(sys.argv) < 2:
        print("Usage: python sprint_history_manager.py [command]")
        print("Commands:")
        print("  summary     - Show summary of last 3 sprints")
        print("  log         - Log current sprint to history")
        print("  suggest     - Get suggestions for next sprint")
        print("  report      - Generate sprint report for commit")
        return
    
    command = sys.argv[1].lower()
    
    if command == "summary":
        print(manager.get_sprint_summary())
    
    elif command == "log":
        # Load current sprint data
        current_sprint_file = Path.cwd() / '.sprint' / 'current_sprint.json'
        if current_sprint_file.exists():
            with open(current_sprint_file, 'r') as f:
                sprint_data = json.load(f)
            manager.log_sprint_completion(sprint_data)
        else:
            print("❌ No current sprint data found")
    
    elif command == "suggest":
        suggestions = manager.suggest_next_sprint_focus()
        print("\n🎯 Suggested focus for next sprint:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    
    elif command == "report":
        current_sprint_file = Path.cwd() / '.sprint' / 'current_sprint.json'
        if current_sprint_file.exists():
            with open(current_sprint_file, 'r') as f:
                sprint_data = json.load(f)
            print(manager.create_sprint_report(sprint_data))
        else:
            print("❌ No current sprint data found")
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()