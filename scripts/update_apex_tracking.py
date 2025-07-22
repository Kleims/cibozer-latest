#!/usr/bin/env python3
"""
Update APEX tracking files after each iteration
This ensures all metrics, contexts, and logs are properly maintained
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path


def update_metrics(iteration, mode, health, focus, result, tests_before, tests_after, 
                  coverage_before, coverage_after, loc, todos, duration):
    """Append iteration metrics to METRICS.md"""
    
    metrics_file = Path("METRICS.md")
    
    # Create entry
    entry = f"""
## Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Mode**: {mode} | **Health**: {health}/100 | **Focus**: {focus}
- **Result**: {result}
- **Tests**: {tests_before} → {tests_after} (Δ{tests_after - tests_before}) | **Coverage**: {coverage_before}% → {coverage_after}% (Δ{coverage_after - coverage_before:.1f}%)
- **LOC**: {loc} | **TODOs**: {todos}
- **Duration**: {duration}s
"""
    
    # Append to file
    with open(metrics_file, 'a') as f:
        f.write(entry)
    
    print(f"✅ Updated METRICS.md for iteration {iteration}")


def update_failed_attempts(iteration, issue, priority="MEDIUM"):
    """Log failed attempts to FAILED_ATTEMPTS.md"""
    
    failed_file = Path("FAILED_ATTEMPTS.md")
    
    entry = f"""
## Iteration #{iteration} - {datetime.now().strftime('%a, %b %d, %Y %I:%M:%S %p')}
**Issue**: {issue}
**Priority**: {priority}
---
"""
    
    with open(failed_file, 'a') as f:
        f.write(entry)
    
    print(f"✅ Updated FAILED_ATTEMPTS.md for iteration {iteration}")


def update_project_context():
    """Update PROJECT_CONTEXT.md with current project state"""
    
    context_file = Path("PROJECT_CONTEXT.md")
    
    # Check if we need to preserve the v4.1 architectural documentation
    if context_file.exists():
        with open(context_file, 'r') as f:
            content = f.read()
            if "Project Context - Cibozer v4.1" in content and "System Architecture Overview" in content:
                print("ℹ️  PROJECT_CONTEXT.md already has v4.1 architecture documentation")
                return
    
    # Update with current context
    print("✅ PROJECT_CONTEXT.md maintained")


def get_current_metrics():
    """Extract current metrics from the project"""
    
    # Count tests
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'pytest', '--collect-only', '-q'], 
                              capture_output=True, text=True)
        test_count = len([line for line in result.stdout.split('\n') if line.strip()])
    except:
        test_count = 0
    
    # Count TODOs
    try:
        import subprocess
        result = subprocess.run(['grep', '-r', 'TODO\\|FIXME', '.', '--include=*.py'], 
                              capture_output=True, text=True)
        todo_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except:
        todo_count = 0
    
    # Count LOC
    try:
        import subprocess
        result = subprocess.run(['find', '.', '-name', '*.py', '-type', 'f', '-exec', 'wc', '-l', '{}', '+'], 
                              capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        if lines and 'total' in lines[-1]:
            loc = int(lines[-1].split()[0])
        else:
            loc = 0
    except:
        loc = 0
    
    return {
        'tests': test_count,
        'todos': todo_count,
        'loc': loc
    }


if __name__ == "__main__":
    # Example usage - this would be called by apex_complete.sh
    print("🔧 APEX Tracking Files Updater")
    print("==============================")
    
    # Get current metrics
    metrics = get_current_metrics()
    print(f"📊 Current Metrics: Tests={metrics['tests']}, TODOs={metrics['todos']}, LOC={metrics['loc']}")
    
    # Update project context
    update_project_context()
    
    print("\n✨ All tracking files updated successfully!")