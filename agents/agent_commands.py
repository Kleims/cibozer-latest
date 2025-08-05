#!/usr/bin/env python
"""
Claude Code Slash Commands for Agent System
Run these with /run in Claude Code
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_orchestrator import AgentOrchestrator
from run_agents import AgentRunner

def status():
    """Check project status - /run python agents/agent_commands.py status"""
    orchestrator = AgentOrchestrator("Cibozer")
    status = orchestrator.get_project_status()
    print("\nPROJECT STATUS")
    print("="*40)
    for key, value in status.items():
        print(f"{key}: {value}")
    print("\nSTANDUP REPORT")
    print("="*40)
    print(orchestrator.get_standup_report())

def continue_work():
    """Continue from last session - /run python agents/agent_commands.py continue"""
    runner = AgentRunner("Cibozer")
    runner.continue_previous_work()

def dev(task):
    """Deploy developer agent - /run python agents/agent_commands.py dev 'task description'"""
    orchestrator = AgentOrchestrator("Cibozer")
    orchestrator.start_work_session(f"Dev task: {task[:30]}")
    agent_task = orchestrator.deploy_agent("fullstack-developer", task)
    print(f"\nAgent ready. Task ID: {agent_task['task_id']}")
    print("\nNow run the Task tool with the generated prompt")

def pm(task):
    """Deploy product manager - /run python agents/agent_commands.py pm 'task description'"""
    orchestrator = AgentOrchestrator("Cibozer")
    orchestrator.start_work_session(f"PM task: {task[:30]}")
    agent_task = orchestrator.deploy_agent("product-manager", task)
    print(f"\nAgent ready. Task ID: {agent_task['task_id']}")
    print("\nNow run the Task tool with the generated prompt")

def ops(task):
    """Deploy DevOps agent - /run python agents/agent_commands.py ops 'task description'"""
    orchestrator = AgentOrchestrator("Cibozer")
    orchestrator.start_work_session(f"Ops task: {task[:30]}")
    agent_task = orchestrator.deploy_agent("devops-sre", task)
    print(f"\nAgent ready. Task ID: {agent_task['task_id']}")
    print("\nNow run the Task tool with the generated prompt")

def feature(name, requirements):
    """Start feature workflow - /run python agents/agent_commands.py feature 'name' 'requirements'"""
    runner = AgentRunner("Cibozer")
    runner.run_feature_workflow(name, requirements)

def fix(bug_description, severity="medium"):
    """Fix a bug - /run python agents/agent_commands.py fix 'bug description' 'severity'"""
    runner = AgentRunner("Cibozer")
    runner.run_bugfix_workflow(bug_description, severity)

def help():
    """Show available commands"""
    print("\nAGENT SYSTEM COMMANDS")
    print("="*50)
    print("\nBasic Commands:")
    print('  /run python agents/agent_commands.py status')
    print('      - Check project status and standup')
    print('\n  /run python agents/agent_commands.py continue')
    print('      - Continue from last session')
    print('\nDeploy Single Agent:')
    print('  /run python agents/agent_commands.py dev "implement user auth"')
    print('      - Deploy fullstack developer')
    print('\n  /run python agents/agent_commands.py pm "define checkout flow"')
    print('      - Deploy product manager')
    print('\n  /run python agents/agent_commands.py ops "setup CI/CD pipeline"')
    print('      - Deploy DevOps/SRE')
    print('\nWorkflows:')
    print('  /run python agents/agent_commands.py feature "Cart" "shopping cart with checkout"')
    print('      - Run complete feature workflow')
    print('\n  /run python agents/agent_commands.py fix "login fails" "high"')
    print('      - Run bugfix workflow')

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        status()
    elif command == "continue":
        continue_work()
    elif command == "dev" and len(sys.argv) > 2:
        dev(" ".join(sys.argv[2:]))
    elif command == "pm" and len(sys.argv) > 2:
        pm(" ".join(sys.argv[2:]))
    elif command == "ops" and len(sys.argv) > 2:
        ops(" ".join(sys.argv[2:]))
    elif command == "feature" and len(sys.argv) > 3:
        feature(sys.argv[2], " ".join(sys.argv[3:]))
    elif command == "fix" and len(sys.argv) > 2:
        severity = sys.argv[3] if len(sys.argv) > 3 else "medium"
        fix(sys.argv[2], severity)
    elif command == "help":
        help()
    else:
        print(f"Unknown command: {command}")
        help()