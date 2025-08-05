#!/usr/bin/env python
"""
VERBOSE AUTONOMOUS AGENT - Shows all thinking and actions
This version uses the actual Task tool to show real agent thinking
"""

import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from project_analyzer_agent import ProjectAnalyzerAgent
from session_manager import get_session_manager


def analyze_and_work():
    """Analyze project and execute tasks with full verbosity"""
    
    print("\n" + "="*60)
    print("VERBOSE AUTONOMOUS AGENT SYSTEM")
    print("Shows all thinking and actions in real-time")
    print("="*60)
    
    # Initialize components
    analyzer = ProjectAnalyzerAgent()
    session_manager = get_session_manager("Cibozer")
    
    # Check for pending work
    context = session_manager.context
    if context.get("upcoming_tasks"):
        print("\nFound pending work from last session:")
        for task in context["upcoming_tasks"][:3]:
            print(f"  - {task}")
        task_to_do = context["upcoming_tasks"][0]
        
        # Remove from pending
        context["upcoming_tasks"] = context["upcoming_tasks"][1:]
        session_manager._save_context()
    else:
        print("\nNo pending work. Analyzing project to find tasks...")
        print("\nScanning for:")
        print("  ✓ TODO/FIXME comments in code")
        print("  ✓ Failing tests")
        print("  ✓ Security vulnerabilities")
        print("  ✓ Performance issues")
        print("  ✓ Missing documentation")
        print("  ✓ Code quality problems")
        
        task_to_do = analyzer.get_next_task()
        
        if not task_to_do:
            print("\n" + "="*60)
            print("PROJECT IS IN EXCELLENT SHAPE!")
            print("No critical issues found.")
            print("="*60)
            return
    
    print("\n" + "-"*60)
    print("TASK SELECTED:")
    print(f"  {task_to_do}")
    print("-"*60)
    
    # Determine task type
    task_lower = task_to_do.lower()
    
    # Create the actual prompt for the Task tool
    if any(word in task_lower for word in ["fix", "bug", "error", "implement", "code", "test"]):
        agent_type = "Development Task"
        prompt = f"""
You are a fullstack developer agent. Your task is:

{task_to_do}

Please:
1. First, analyze the issue thoroughly
2. Show your thinking process step by step
3. Implement the fix or feature
4. Test your changes
5. Provide a summary of what was done

Use all available tools (Read, Edit, Bash, Grep, etc.) to complete this task.
Be thorough and show your work at each step.
"""
    elif any(word in task_lower for word in ["deploy", "setup", "config", "environment"]):
        agent_type = "DevOps Task"
        prompt = f"""
You are a DevOps/SRE agent. Your task is:

{task_to_do}

Please:
1. Analyze the current deployment/configuration
2. Show your thinking about what needs to be done
3. Implement the necessary changes
4. Verify the changes work correctly
5. Document what was changed

Use all available tools to complete this task.
Show your reasoning at each step.
"""
    else:
        agent_type = "General Task"
        prompt = f"""
You are an autonomous agent. Your task is:

{task_to_do}

Please:
1. Analyze what needs to be done
2. Show your thinking and planning
3. Execute the necessary steps
4. Verify your work
5. Summarize what was accomplished

Be thorough and explain your reasoning.
"""
    
    print(f"\nAgent Type: {agent_type}")
    print("\nDEPLOYING AGENT WITH FULL VERBOSITY...")
    print("(You will now see the agent's complete thinking process)")
    print("\n" + "="*60)
    
    # Return the configuration for manual execution
    return {
        "task": task_to_do,
        "agent_type": agent_type,
        "prompt": prompt,
        "instruction": "\nTo execute this agent task, use the Task tool with the prompt above."
    }


if __name__ == "__main__":
    result = analyze_and_work()
    
    if result:
        print("\n" + "="*60)
        print("AGENT CONFIGURATION READY")
        print("="*60)
        print(f"\nTask: {result['task']}")
        print(f"Type: {result['agent_type']}")
        print("\nPrompt for Task tool:")
        print("-"*40)
        print(result['prompt'])
        print("-"*40)
        print(result['instruction'])