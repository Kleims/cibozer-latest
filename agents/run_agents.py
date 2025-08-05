"""
Run Agents - Main entry point for using the agent system with session management
This script demonstrates how to use agents with full context and history tracking
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add the agents directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_orchestrator import AgentOrchestrator
from session_manager import get_session_manager

class AgentRunner:
    """Main runner for agent-based development workflow"""
    
    def __init__(self, project_name: str = "Cibozer"):
        self.orchestrator = AgentOrchestrator(project_name)
        self.session_manager = get_session_manager(project_name)
    
    def run_single_agent(self, agent_role: str, task: str):
        """Run a single agent task"""
        print(f"\n{'='*60}")
        print(f"Running {agent_role} Agent")
        print(f"{'='*60}")
        
        # Start a session if not already active
        if not self.orchestrator.current_session_id:
            self.orchestrator.start_work_session(f"Single task: {task[:50]}...")
        
        # Deploy the agent
        agent_task = self.orchestrator.deploy_agent(agent_role, task)
        
        # Show what would be executed
        print(f"\nGenerated Task ID: {agent_task['task_id']}")
        print(f"Session: {agent_task['session_id']}")
        print("\n" + "="*60)
        
        return agent_task
    
    def run_feature_workflow(self, feature_name: str, requirements: str):
        """Run a complete feature development workflow"""
        print(f"\n{'='*60}")
        print(f"Starting Feature Development: {feature_name}")
        print(f"{'='*60}")
        
        # Start a new session for this feature
        session_id = self.orchestrator.start_work_session(
            f"Implement feature: {feature_name}",
            sprint=f"Feature-{feature_name.replace(' ', '-')}"
        )
        
        # Define the workflow steps
        workflow = [
            {
                "agent": "product-manager",
                "task": f"""
                Define detailed requirements for: {feature_name}
                
                Initial requirements: {requirements}
                
                Please provide:
                1. User stories
                2. Acceptance criteria
                3. Edge cases to consider
                4. Success metrics
                """
            },
            {
                "agent": "fullstack-developer",
                "task": f"""
                Implement the {feature_name} feature based on the requirements defined.
                
                Please:
                1. Review the existing codebase structure
                2. Implement the necessary database changes
                3. Create API endpoints
                4. Build the frontend components
                5. Write tests for the new functionality
                """
            },
            {
                "agent": "devops-sre",
                "task": f"""
                Prepare deployment for the {feature_name} feature.
                
                Please:
                1. Update CI/CD configuration if needed
                2. Add any new environment variables
                3. Set up monitoring for the new feature
                4. Create rollback plan
                """
            }
        ]
        
        # Execute the workflow
        results = self.orchestrator.collaborate_agents(workflow)
        
        # Update project context
        self.orchestrator.update_project_context({
            "active_features": [feature_name],
            "upcoming_tasks": [f"Test {feature_name}", f"Document {feature_name}"]
        })
        
        # End the session
        self.orchestrator.end_work_session(f"Feature {feature_name} implementation workflow completed")
        
        return results
    
    def run_bugfix_workflow(self, bug_description: str, severity: str = "medium"):
        """Run a bugfix workflow"""
        print(f"\n{'='*60}")
        print(f"Starting Bugfix Workflow")
        print(f"{'='*60}")
        print(f"Severity: {severity.upper()}")
        
        session_id = self.orchestrator.start_work_session(
            f"Fix bug: {bug_description[:50]}...",
            sprint="Bugfixes"
        )
        
        workflow = [
            {
                "agent": "fullstack-developer",
                "task": f"""
                Investigate and fix the following bug:
                {bug_description}
                
                Severity: {severity}
                
                Please:
                1. Identify the root cause
                2. Implement the fix
                3. Add tests to prevent regression
                4. Verify the fix doesn't break existing functionality
                """
            },
            {
                "agent": "devops-sre",
                "task": f"""
                Deploy the bugfix to staging for verification.
                
                Bug: {bug_description}
                Severity: {severity}
                
                Please:
                1. Deploy to staging environment
                2. Run integration tests
                3. Monitor for any new issues
                4. Prepare production hotfix if severity is high
                """
            }
        ]
        
        results = self.orchestrator.collaborate_agents(workflow)
        
        # Update context
        self.orchestrator.update_project_context({
            "known_issues": [f"FIXED: {bug_description}"]
        })
        
        self.orchestrator.end_work_session(f"Bugfix completed: {bug_description[:30]}...")
        
        return results
    
    def continue_previous_work(self):
        """Continue work from previous session with context"""
        print(f"\n{'='*60}")
        print(f"Loading Previous Session Context")
        print(f"{'='*60}")
        
        # Get project status
        status = self.orchestrator.get_project_status()
        
        print(f"\nProject Status:")
        print(f"  Total Sessions: {status['total_sessions']}")
        print(f"  Tasks Completed: {status['total_tasks_completed']}")
        print(f"  Current Sprint: {status['current_sprint']}")
        print(f"  Active Features: {status['active_features']}")
        print(f"  Known Issues: {status['known_issues']}")
        
        # Get standup report
        standup = self.orchestrator.get_standup_report()
        print(f"\nStandup Report:")
        print(standup)
        
        # Check for pending tasks
        context = self.session_manager.context
        if context.get("upcoming_tasks"):
            print(f"\nUpcoming Tasks:")
            for task in context["upcoming_tasks"][:3]:
                print(f"  - {task}")
            
            # Automatically start working on the first task
            if context["upcoming_tasks"]:
                first_task = context["upcoming_tasks"][0]
                print(f"\nStarting work on: {first_task}")
                
                self.orchestrator.start_work_session(f"Continue: {first_task}")
                
                # Determine which agent should handle this
                if "deploy" in first_task.lower() or "monitoring" in first_task.lower():
                    agent = "devops-sre"
                elif "requirement" in first_task.lower() or "user" in first_task.lower():
                    agent = "product-manager"
                else:
                    agent = "fullstack-developer"
                
                return self.run_single_agent(agent, first_task)
        
        return None
    
    def get_agent_command(self, agent_role: str, task: str) -> str:
        """Get the actual Claude Code command to run an agent"""
        agent_task = self.orchestrator.deploy_agent(agent_role, task)
        
        return f"""
# Copy and run this in Claude Code:

from agents.agent_orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator("Cibozer")
orchestrator.start_work_session("{task[:30]}...")

# Deploy the agent
agent_task = orchestrator.deploy_agent(
    agent_role="{agent_role}",
    task_description=\"\"\"{task}\"\"\"
)

# Then use the Task tool:
Task(
    description="{agent_role}: {task[:50]}",
    prompt=agent_task["prompt"],
    subagent_type="general-purpose"
)
"""


def main():
    """Main entry point with example workflows"""
    runner = AgentRunner("Cibozer")
    
    print("AGENT SYSTEM WITH SESSION MANAGEMENT")
    print("="*60)
    
    # Check if we should continue previous work
    print("\n1. Checking for previous session context...")
    previous_task = runner.continue_previous_work()
    
    if not previous_task:
        # Example: Run a new feature workflow
        print("\n2. Example: New Feature Workflow")
        runner.run_feature_workflow(
            feature_name="Social Sharing",
            requirements="Users should be able to share their meal plans on social media with a nice preview image"
        )
    
    # Example: Run a bugfix
    print("\n3. Example: Bugfix Workflow")
    runner.run_bugfix_workflow(
        bug_description="Login form doesn't show error messages when credentials are incorrect",
        severity="high"
    )
    
    # Example: Single agent task
    print("\n4. Example: Single Agent Task")
    runner.run_single_agent(
        agent_role="fullstack-developer",
        task="Add input validation to the meal preference form to ensure portion sizes are positive numbers"
    )
    
    # Show how to get the actual command
    print("\n5. Getting Claude Code Command")
    command = runner.get_agent_command(
        "product-manager",
        "Define requirements for a meal plan templates feature"
    )
    print(command)


if __name__ == "__main__":
    main()