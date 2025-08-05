"""
Self-Directed Agent System - Figures out what to do on its own
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict
from project_analyzer_agent import ProjectAnalyzerAgent
from autonomous_agent import AutonomousAgentSystem
from session_manager import get_session_manager
from datetime import datetime

class SelfDirectedSystem:
    """Completely autonomous system that decides what to work on"""
    
    def __init__(self, project_name: str = "Cibozer"):
        self.project_name = project_name
        self.analyzer = ProjectAnalyzerAgent()
        self.autonomous = AutonomousAgentSystem(project_name)
        self.session_manager = get_session_manager(project_name)
        
    def run(self) -> Dict:
        """Run completely autonomously - figure out what needs doing and do it"""
        
        print("\n" + "="*60)
        print("SELF-DIRECTED AGENT SYSTEM ACTIVATED")
        print("="*60)
        print("I'll figure out what needs to be done...\n")
        
        # First, check if there's pending work from last session
        context = self.session_manager.context
        if context.get("upcoming_tasks"):
            print("Found pending work from last session:")
            task = context["upcoming_tasks"][0]
            print(f"  - {task}")
            
            # Remove from pending and execute
            context["upcoming_tasks"] = context["upcoming_tasks"][1:]
            self.session_manager._save_context()
            
            return self.autonomous.execute(task)
        
        # No pending work, analyze the project to find what needs doing
        print("No pending work. Analyzing project to find tasks...\n")
        
        next_task = self.analyzer.get_next_task()
        
        if next_task:
            print("\n" + "-"*60)
            print("DECISION: I will work on this task")
            print("-"*60)
            
            # Execute the task
            result = self.autonomous.execute(next_task)
            
            # If successful, analyze again to find next task
            if result["status"] == "completed":
                print("\nTask completed successfully!")
                print("Analyzing for next task...")
                
                # Get all tasks and add to upcoming
                all_tasks = self.analyzer.analyze_project()
                all_tasks = self.analyzer.prioritize_tasks(all_tasks)
                
                # Add top 5 to upcoming tasks
                upcoming = [t["task"] for t in all_tasks[1:6]]  # Skip the one we just did
                self.session_manager.update_context({
                    "upcoming_tasks": upcoming
                })
                
                print(f"Added {len(upcoming)} tasks to queue for next time")
            
            return result
        else:
            print("\nPROJECT IS IN GOOD SHAPE!")
            print("No critical issues found.")
            print("\nI checked for:")
            print("  - TODO/FIXME comments")
            print("  - Failing tests")
            print("  - Security issues")
            print("  - Missing documentation")
            print("  - Code quality issues")
            print("  - Performance problems")
            print("  - Missing features")
            print("  - Deployment issues")
            
            print("\nEverything looks good!")
            
            return {
                "status": "complete",
                "message": "No tasks found - project is in good shape!"
            }
    
    def continuous_run(self, max_tasks: int = 5):
        """Run continuously, doing multiple tasks in sequence"""
        
        print("\n" + "="*60)
        print("CONTINUOUS AUTONOMOUS MODE")
        print(f"Will complete up to {max_tasks} tasks")
        print("="*60)
        
        completed = 0
        
        for i in range(max_tasks):
            print(f"\n[Task {i+1}/{max_tasks}]")
            result = self.run()
            
            if result["status"] == "complete":
                print("\nAll tasks completed!")
                break
            elif result["status"] == "completed":
                completed += 1
            elif result["status"] == "escalated":
                print("\nEscalation needed - stopping here")
                break
        
        print(f"\n" + "="*60)
        print(f"SESSION COMPLETE")
        print(f"Tasks Completed: {completed}/{max_tasks}")
        print("="*60)
        
        return completed


def work():
    """The ultimate zero-input function - just call it and it works"""
    system = SelfDirectedSystem("Cibozer")
    return system.run()


def work_all_day():
    """Work continuously on multiple tasks"""
    system = SelfDirectedSystem("Cibozer")
    return system.continuous_run(max_tasks=10)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        # Work on multiple tasks
        work_all_day()
    else:
        # Work on one task
        work()