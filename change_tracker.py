#!/usr/bin/env python3
"""
Comprehensive Change Tracking System for Cibozer
Tracks all changes, metrics, and progress over time
"""

import json
import datetime
import subprocess
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class ChangeEvent:
    """Represents a single change event"""
    timestamp: str
    category: str  # "code", "config", "metrics", "task", "test"
    action: str    # "added", "modified", "deleted", "completed"
    description: str
    details: Dict[str, Any]
    author: str = "system"
    commit_hash: Optional[str] = None

class ChangeTracker:
    """Main change tracking system"""
    
    def __init__(self):
        self.db_path = Path("change_history.db")
        self.changelog_path = Path("CHANGELOG.md")
        self.metrics_history_path = Path("metrics_history.json")
        self.setup_database()
        
    def setup_database(self):
        """Initialize the change tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Changes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                description TEXT NOT NULL,
                details TEXT,
                author TEXT,
                commit_hash TEXT,
                file_path TEXT,
                old_hash TEXT,
                new_hash TEXT
            )
        ''')
        
        # Metrics snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                category TEXT,
                phase INTEGER,
                iteration INTEGER
            )
        ''')
        
        # Task progress table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                phase INTEGER,
                task_id TEXT,
                task_name TEXT,
                status TEXT,
                duration_seconds INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate hash of a file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def get_git_info(self) -> Dict[str, str]:
        """Get current git information"""
        info = {}
        try:
            # Get current commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['commit_hash'] = result.stdout.strip()[:7]
            
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                info['branch'] = result.stdout.strip()
            
            # Get uncommitted changes count
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                changes = result.stdout.strip().split('\n') if result.stdout.strip() else []
                info['uncommitted_changes'] = len(changes)
        except:
            pass
        
        return info
    
    def track_change(self, category: str, action: str, description: str, 
                    details: Optional[Dict] = None, file_path: Optional[str] = None):
        """Track a single change event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        git_info = self.get_git_info()
        
        # Get file hashes if file_path provided
        old_hash = None
        new_hash = None
        if file_path:
            new_hash = self.get_file_hash(file_path)
        
        cursor.execute('''
            INSERT INTO changes 
            (category, action, description, details, author, commit_hash, file_path, old_hash, new_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            category,
            action,
            description,
            json.dumps(details or {}),
            "launch_automation",
            git_info.get('commit_hash'),
            file_path,
            old_hash,
            new_hash
        ))
        
        conn.commit()
        conn.close()
        
        # Also append to changelog
        self.update_changelog(category, action, description)
    
    def track_metrics_snapshot(self, metrics: Dict[str, Dict[str, Any]], phase: int, iteration: int):
        """Save a snapshot of all current metrics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        
        # Save each metric
        for category, category_metrics in metrics.items():
            if isinstance(category_metrics, dict):
                for metric_name, value in category_metrics.items():
                    if value is not None:
                        cursor.execute('''
                            INSERT INTO metrics_snapshots
                            (metric_name, metric_value, category, phase, iteration)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (metric_name, float(value) if value else 0, category, phase, iteration))
        
        conn.commit()
        conn.close()
        
        # Also save to JSON for easy access
        history = []
        if self.metrics_history_path.exists():
            with open(self.metrics_history_path, 'r') as f:
                history = json.load(f)
        
        history.append({
            'timestamp': timestamp,
            'phase': phase,
            'iteration': iteration,
            'metrics': metrics,
            'git_info': self.get_git_info()
        })
        
        with open(self.metrics_history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def track_task_completion(self, phase: int, task_id: str, task_name: str, 
                            status: str, duration_seconds: float):
        """Track task completion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO task_progress
            (phase, task_id, task_name, status, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        ''', (phase, task_id, task_name, status, int(duration_seconds)))
        
        conn.commit()
        conn.close()
        
        self.track_change(
            "task",
            "completed" if status == "success" else "failed",
            f"Task '{task_name}' {status}",
            {"phase": phase, "task_id": task_id, "duration": duration_seconds}
        )
    
    def update_changelog(self, category: str, action: str, description: str):
        """Update the CHANGELOG.md file"""
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        # Read existing changelog
        if self.changelog_path.exists():
            with open(self.changelog_path, 'r') as f:
                content = f.read()
        else:
            content = "# Cibozer Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        
        # Find today's section or create it
        section_header = f"## [{today}]"
        if section_header not in content:
            # Add new date section
            new_section = f"\n{section_header}\n\n### Added\n\n### Changed\n\n### Fixed\n\n### Removed\n\n"
            # Insert after the title and description
            lines = content.split('\n')
            insert_pos = 3  # After title and description
            lines.insert(insert_pos, new_section)
            content = '\n'.join(lines)
        
        # Determine which subsection to update
        subsection_map = {
            'added': '### Added',
            'created': '### Added',
            'modified': '### Changed',
            'updated': '### Changed',
            'fixed': '### Fixed',
            'deleted': '### Removed',
            'removed': '### Removed'
        }
        
        subsection = subsection_map.get(action, '### Changed')
        
        # Add the change entry
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line == section_header:
                # Find the right subsection
                for j in range(i, len(lines)):
                    if lines[j] == subsection:
                        # Insert the change after the subsection header
                        lines.insert(j + 1, f"- [{category.upper()}] {description}")
                        break
                break
        
        content = '\n'.join(lines)
        
        # Write back
        with open(self.changelog_path, 'w') as f:
            f.write(content)
    
    def get_metrics_history(self, metric_name: str, days: int = 7) -> List[Dict]:
        """Get historical data for a specific metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute('''
            SELECT timestamp, metric_value, phase, iteration
            FROM metrics_snapshots
            WHERE metric_name = ? AND timestamp >= ?
            ORDER BY timestamp
        ''', (metric_name, since.isoformat()))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'value': row[1],
                'phase': row[2],
                'iteration': row[3]
            })
        
        conn.close()
        return results
    
    def get_recent_changes(self, limit: int = 20) -> List[Dict]:
        """Get recent changes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, category, action, description, details, commit_hash
            FROM changes
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'timestamp': row[0],
                'category': row[1],
                'action': row[2],
                'description': row[3],
                'details': json.loads(row[4]) if row[4] else {},
                'commit_hash': row[5]
            })
        
        conn.close()
        return results
    
    def generate_progress_report(self) -> str:
        """Generate a comprehensive progress report"""
        report = []
        report.append("="*60)
        report.append("CIBOZER PROGRESS REPORT")
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*60)
        
        # Git information
        git_info = self.get_git_info()
        if git_info:
            report.append("\nGit Status:")
            report.append(f"  Branch: {git_info.get('branch', 'unknown')}")
            report.append(f"  Commit: {git_info.get('commit_hash', 'unknown')}")
            report.append(f"  Uncommitted Changes: {git_info.get('uncommitted_changes', 0)}")
        
        # Recent changes
        report.append("\nRecent Changes (Last 10):")
        changes = self.get_recent_changes(10)
        for change in changes:
            time = datetime.datetime.fromisoformat(change['timestamp']).strftime('%m-%d %H:%M')
            report.append(f"  [{time}] {change['category'].upper()}: {change['description']}")
        
        # Task progress
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT phase, COUNT(*) as total, 
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as completed
            FROM task_progress
            GROUP BY phase
            ORDER BY phase
        ''')
        
        report.append("\nTask Progress by Phase:")
        for row in cursor.fetchall():
            phase, total, completed = row
            percentage = (completed / total * 100) if total > 0 else 0
            report.append(f"  Phase {phase}: {completed}/{total} tasks ({percentage:.1f}%)")
        
        # Metrics trends
        report.append("\nKey Metrics Trends:")
        key_metrics = ['test_coverage', 'total_users', 'mrr']
        
        for metric in key_metrics:
            history = self.get_metrics_history(metric, days=30)
            if history:
                latest = history[-1]['value']
                first = history[0]['value']
                if first and latest:
                    change = ((latest - first) / first * 100) if first != 0 else 0
                    trend = "UP" if change > 0 else "DOWN" if change < 0 else "SAME"
                    report.append(f"  {metric}: {latest:.1f} ({trend} {abs(change):.1f}%)")
        
        conn.close()
        
        report.append("\n" + "="*60)
        return "\n".join(report)


# Integration with launch_automation.py
class EnhancedLaunchAutomation:
    """Enhanced version of launch automation with change tracking"""
    
    def __init__(self, base_automation):
        self.base = base_automation
        self.tracker = ChangeTracker()
        self.iteration_count = self.load_iteration_count()
    
    def load_iteration_count(self) -> int:
        """Load the current iteration count"""
        iteration_file = Path('.iteration')
        if iteration_file.exists():
            with open(iteration_file, 'r') as f:
                return int(f.read().strip())
        return 0
    
    def save_iteration_count(self):
        """Save the current iteration count"""
        with open('.iteration', 'w') as f:
            f.write(str(self.iteration_count))
    
    def run_task_with_tracking(self, task: Dict, force: bool = False) -> bool:
        """Run a task with full change tracking"""
        start_time = datetime.datetime.now()
        
        # Track task start
        self.tracker.track_change(
            "task",
            "started",
            f"Starting task: {task['name']}",
            {"phase": self.base.progress['current_phase'], "task_id": task['id']}
        )
        
        # Run the actual task using the original method
        task_id = task["id"]
        
        # Check if already completed
        if task_id in self.base.progress["completed_tasks"] and not force:
            self.base.log(f"Task '{task['name']}' already completed, skipping")
            return True
        
        self.base.log(f"Starting task: {task['name']}")
        
        # Run the task command
        success, output = self.base.run_command(task["command"])
        if not success:
            return False
        
        # Validate the task
        if self.base.validate_task(task):
            self.base.log(f"Task '{task['name']}' completed successfully")
            if task_id not in self.base.progress["completed_tasks"]:
                self.base.progress["completed_tasks"].append(task_id)
            self.base.save_progress()
            task_success = True
        else:
            self.base.log(f"Task '{task['name']}' validation failed", "ERROR")
            task_success = False
        
        # Calculate duration
        duration = (datetime.datetime.now() - start_time).total_seconds()
        
        # Track task completion
        self.tracker.track_task_completion(
            self.base.progress['current_phase'],
            task['id'],
            task['name'],
            'success' if task_success else 'failed',
            duration
        )
        
        return task_success
    
    def run_with_tracking(self, target_phase: Optional[int] = None, force: bool = False):
        """Run automation with comprehensive tracking"""
        self.iteration_count += 1
        self.save_iteration_count()
        
        # Track iteration start
        self.tracker.track_change(
            "iteration",
            "started",
            f"Started iteration #{self.iteration_count}",
            {"phase": self.base.progress['current_phase']}
        )
        
        # Take metrics snapshot before
        self.base.update_metrics()
        self.tracker.track_metrics_snapshot(
            self.base.metrics,
            self.base.progress['current_phase'],
            self.iteration_count
        )
        
        # Override run_task method to use tracking version
        original_run_task = self.base.run_task
        self.base.run_task = lambda task, force=False: self.run_task_with_tracking(task, force)
        
        # Run the base automation
        self.base.run(target_phase, force)
        
        # Restore original method
        self.base.run_task = original_run_task
        
        # Take metrics snapshot after
        self.base.update_metrics()
        self.tracker.track_metrics_snapshot(
            self.base.metrics,
            self.base.progress['current_phase'],
            self.iteration_count
        )
        
        # Generate and display progress report
        try:
            print("\n" + self.tracker.generate_progress_report())
        except UnicodeEncodeError:
            # Fallback for Windows encoding issues
            report = self.tracker.generate_progress_report()
            print("\n" + report.encode('ascii', 'replace').decode('ascii'))
        
        # Update METRICS.md with new data
        self.update_metrics_file()
    
    def update_metrics_file(self):
        """Update METRICS.md with new iteration data"""
        metrics_file = Path("METRICS.md")
        
        # Read existing content
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Find the insertion point (at the top of iterations)
        lines = content.split('\n')
        insert_pos = None
        for i, line in enumerate(lines):
            if line.startswith('## Iteration #'):
                insert_pos = i
                break
        
        if insert_pos is None:
            insert_pos = len(lines)
        
        # Create new iteration entry
        new_entry = f"""## Iteration #{self.iteration_count} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Mode: ENHANCED | Health: {self.calculate_health_score()}/100
- Phase: {self.base.progress['current_phase']}
- Completed Tasks: {len(self.base.progress['completed_tasks'])}
- Test Coverage: {self.base.metrics.get('technical', {}).get('test_coverage', 'N/A')}%
- Changes: See CHANGELOG.md for details
"""
        
        # Insert the new entry
        lines.insert(insert_pos, new_entry)
        
        # Write back
        with open(metrics_file, 'w') as f:
            f.write('\n'.join(lines))
    
    def calculate_health_score(self) -> int:
        """Calculate overall project health score"""
        score = 0
        factors = 0
        
        # Test coverage
        coverage = self.base.metrics.get('technical', {}).get('test_coverage', 0)
        if coverage:
            score += min(coverage, 100)
            factors += 1
        
        # Task completion
        from launch_automation import PHASES
        total_tasks = sum(len(PHASES[p]['tasks']) for p in PHASES)
        completed = len(self.base.progress['completed_tasks'])
        if total_tasks > 0:
            completion_rate = (completed / total_tasks) * 100
            score += completion_rate
            factors += 1
        
        # No critical bugs (assumed for now)
        score += 100
        factors += 1
        
        return int(score / factors) if factors > 0 else 0


if __name__ == "__main__":
    # Example usage
    tracker = ChangeTracker()
    print(tracker.generate_progress_report())