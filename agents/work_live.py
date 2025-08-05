#!/usr/bin/env python
"""
LIVE AUTONOMOUS AGENT - Actually executes tasks with full verbosity
This version shows real agent thinking by printing prompts that can be executed
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_analyzer_agent import ProjectAnalyzerAgent
from session_manager import get_session_manager


class LiveAutonomousAgent:
    """Live agent that shows its full thinking process"""
    
    def __init__(self):
        self.analyzer = ProjectAnalyzerAgent()
        self.session_manager = get_session_manager("Cibozer")
        
    def get_next_task(self):
        """Get the next task to work on"""
        context = self.session_manager.context
        
        # Check for pending work
        if context.get("upcoming_tasks"):
            task = context["upcoming_tasks"][0]
            context["upcoming_tasks"] = context["upcoming_tasks"][1:]
            self.session_manager._save_context()
            return task, "pending"
        
        # Analyze project for new tasks
        task = self.analyzer.get_next_task()
        return task, "new"
    
    def create_agent_prompt(self, task):
        """Create detailed prompt for the task"""
        task_lower = task.lower()
        
        # Determine agent type and create specialized prompt
        if any(word in task_lower for word in ["fix", "bug", "error", "broken", "issue"]):
            agent_type = "Bug Fixer"
            prompt = f"""You are debugging an issue in the Cibozer application.

TASK: {task}

APPROACH:
1. First, investigate the issue thoroughly:
   - Search for related error messages or TODOs
   - Check relevant files and configurations
   - Understand the root cause

2. Show your thinking:
   - Explain what you found
   - Describe your solution approach
   - Consider edge cases

3. Implement the fix:
   - Make necessary code changes
   - Ensure the fix is comprehensive
   - Add any missing error handling

4. Verify the fix:
   - Test that it works
   - Check for side effects
   - Ensure no regressions

5. Document what you did:
   - Summarize the problem and solution
   - Note any follow-up tasks needed

Be thorough and explain each step."""

        elif any(word in task_lower for word in ["test", "testing", "coverage"]):
            agent_type = "Test Engineer"
            prompt = f"""You are improving test coverage for the Cibozer application.

TASK: {task}

APPROACH:
1. Analyze current test coverage:
   - Check what's already tested
   - Identify gaps

2. Plan your testing strategy:
   - Decide what needs testing
   - Choose appropriate test types

3. Implement tests:
   - Write comprehensive test cases
   - Cover edge cases
   - Ensure good assertions

4. Run and verify:
   - Execute the tests
   - Fix any failures
   - Check coverage improvement

Show your reasoning at each step."""

        elif any(word in task_lower for word in ["security", "vulnerability", "auth"]):
            agent_type = "Security Engineer"
            prompt = f"""You are addressing a security concern in the Cibozer application.

TASK: {task}

SECURITY CHECKLIST:
1. Analyze the security issue:
   - Identify the vulnerability type
   - Assess the risk level
   - Check for similar issues

2. Implement security fix:
   - Apply security best practices
   - Use appropriate security controls
   - Ensure comprehensive protection

3. Verify the fix:
   - Test that it blocks attacks
   - Ensure functionality preserved
   - Check for bypass methods

4. Document security changes:
   - Explain what was vulnerable
   - Describe the fix
   - Note any configuration needed

Be thorough about security implications."""

        elif any(word in task_lower for word in ["implement", "add", "create", "feature"]):
            agent_type = "Feature Developer"
            prompt = f"""You are implementing a new feature for the Cibozer application.

TASK: {task}

DEVELOPMENT PROCESS:
1. Understand requirements:
   - Analyze what needs to be built
   - Check existing similar features
   - Plan the implementation

2. Design the solution:
   - Explain your approach
   - Consider architecture
   - Plan for scalability

3. Implement the feature:
   - Write clean, maintainable code
   - Follow existing patterns
   - Add proper error handling

4. Test the feature:
   - Verify it works as expected
   - Test edge cases
   - Ensure no breaks

5. Document the feature:
   - Explain how to use it
   - Note any limitations
   - Suggest improvements

Show your thinking throughout."""

        elif any(word in task_lower for word in ["optimize", "performance", "speed"]):
            agent_type = "Performance Engineer"
            prompt = f"""You are optimizing performance in the Cibozer application.

TASK: {task}

OPTIMIZATION PROCESS:
1. Profile current state:
   - Identify bottlenecks
   - Measure baseline performance
   - Find inefficiencies

2. Plan optimizations:
   - Explain your strategy
   - Prioritize improvements
   - Consider trade-offs

3. Implement optimizations:
   - Apply performance fixes
   - Optimize algorithms/queries
   - Add caching if needed

4. Measure improvements:
   - Compare before/after
   - Verify functionality preserved
   - Document gains

Show metrics and reasoning."""

        else:
            agent_type = "General Developer"
            prompt = f"""You are working on the Cibozer application.

TASK: {task}

GENERAL APPROACH:
1. Understand the task:
   - Analyze what needs to be done
   - Check related code/files
   - Plan your approach

2. Execute the task:
   - Show your thinking
   - Implement step by step
   - Handle edge cases

3. Verify your work:
   - Test the changes
   - Check for issues
   - Ensure quality

4. Document what you did:
   - Summarize the work
   - Note any findings
   - Suggest next steps

Be thorough and clear."""

        return agent_type, prompt
    
    def save_upcoming_tasks(self):
        """Save upcoming tasks for next run"""
        # Get more tasks for the queue
        all_tasks = self.analyzer.analyze_project()
        all_tasks = self.analyzer.prioritize_tasks(all_tasks)
        
        if all_tasks:
            upcoming = [t["task"] for t in all_tasks[:5]]
            self.session_manager.update_context({
                "upcoming_tasks": upcoming
            })
            return len(upcoming)
        return 0
    
    def run(self):
        """Run the autonomous agent"""
        print("\n" + "="*70)
        print("LIVE AUTONOMOUS AGENT SYSTEM")
        print("="*70)
        print("This version shows complete agent thinking and actions\n")
        
        # Get next task
        task, source = self.get_next_task()
        
        if not task:
            print("PROJECT IS IN EXCELLENT SHAPE!")
            print("\nNo issues found in:")
            print("  - Code quality")
            print("  - Security")
            print("  - Tests")
            print("  - Performance")
            print("  - Documentation")
            return None
        
        # Display task info
        if source == "pending":
            print(f"[QUEUE] Resuming from queue: {task}")
        else:
            print(f"[NEW] Found new task: {task}")
        
        # Create agent prompt
        agent_type, prompt = self.create_agent_prompt(task)
        
        print(f"\n[AGENT TYPE] {agent_type}")
        print("-"*70)
        
        # Save upcoming tasks
        num_queued = self.save_upcoming_tasks()
        if num_queued:
            print(f"\n[QUEUED] {num_queued} more tasks saved for later")
        
        return {
            "task": task,
            "agent_type": agent_type,
            "prompt": prompt
        }


def display_prompt_for_execution(result):
    """Display the prompt in a format ready for Task tool execution"""
    print("\n" + "="*70)
    print("READY TO EXECUTE WITH TASK TOOL")
    print("="*70)
    
    print("\nCopy this to execute the agent:\n")
    print("-"*70)
    print(f'Task(')
    print(f'    description="{result["agent_type"]}: {result["task"][:40]}...",')
    print(f'    prompt="""')
    print(result["prompt"])
    print('    """,')
    print('    subagent_type="general-purpose"')
    print(')')
    print("-"*70)


if __name__ == "__main__":
    agent = LiveAutonomousAgent()
    result = agent.run()
    
    if result:
        # Show what the agent will do
        print("\n[AGENT PROMPT PREVIEW]")
        print("="*70)
        print(result["prompt"])
        print("="*70)
        
        # Ask if user wants to see execution format
        print("\n[INFO] To see the agent's full thinking process,")
        print("       I'll execute it with the Task tool now...")
        
        # Optional: Uncomment to show copy-paste format
        # display_prompt_for_execution(result)