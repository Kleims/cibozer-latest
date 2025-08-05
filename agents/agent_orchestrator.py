"""
Agent Orchestrator - Coordinates agents with context and history awareness
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from session_manager import get_session_manager
from saas_team_agents import get_agent_prompt, AGENTS

class AgentOrchestrator:
    """Orchestrates agent tasks with full context and history awareness"""
    
    def __init__(self, project_name: str = "Cibozer"):
        self.project_name = project_name
        self.session_manager = get_session_manager(project_name)
        self.current_session_id = None
    
    def start_work_session(self, goal: str, sprint: Optional[str] = None) -> str:
        """Start a new work session with a specific goal"""
        self.current_session_id = self.session_manager.start_session(goal, sprint)
        print(f"Started session: {self.current_session_id}")
        print(f"Goal: {goal}")
        if sprint:
            print(f"Sprint: {sprint}")
        return self.current_session_id
    
    def deploy_agent(self, agent_role: str, task_description: str, 
                    additional_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Deploy an agent with full context awareness"""
        
        if agent_role not in AGENTS:
            raise ValueError(f"Unknown agent role: {agent_role}")
        
        # Get agent's historical context
        agent_context = self.session_manager.get_agent_context(agent_role)
        
        # Build the full prompt with context
        context_prompt = self._build_context_prompt(agent_role, agent_context, additional_context)
        full_prompt = f"{get_agent_prompt(agent_role)}\n\n{context_prompt}\n\nCurrent Task:\n{task_description}"
        
        # Record the task start
        task_record = {
            "description": task_description,
            "status": "in_progress",
            "input": {
                "task": task_description,
                "context": agent_context
            }
        }
        
        task_id = self.session_manager.record_agent_task(agent_role, task_record)
        
        # This is where you would actually invoke the agent using Claude Code's Task tool
        # For now, we'll return the structured task that would be executed
        
        agent_task = {
            "task_id": task_id,
            "agent_role": agent_role,
            "prompt": full_prompt,
            "context": agent_context,
            "session_id": self.current_session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\nDeploying {agent_role} agent")
        print(f"Task ID: {task_id}")
        print(f"Task: {task_description[:100]}...")
        
        return agent_task
    
    def _build_context_prompt(self, agent_role: str, agent_context: Dict, 
                             additional_context: Optional[Dict]) -> str:
        """Build context-aware prompt for the agent"""
        
        prompt = "## Project Context\n"
        prompt += f"Project: {agent_context['project']}\n"
        
        if agent_context.get('current_sprint'):
            prompt += f"Current Sprint: {agent_context['current_sprint']}\n"
        
        prompt += f"Deployment Status: {agent_context['deployment_status']}\n\n"
        
        # Add recent work history
        if agent_context.get('recent_work'):
            prompt += "## Your Recent Work\n"
            for work in agent_context['recent_work']:
                prompt += f"- [{work['timestamp'][:10]}] {work['description']} (Status: {work['status']})\n"
            prompt += "\n"
        
        # Add role-specific context
        if agent_role == "fullstack-developer":
            if agent_context.get('active_features'):
                prompt += "## Active Features in Development\n"
                for feature in agent_context['active_features']:
                    prompt += f"- {feature}\n"
                prompt += "\n"
            
            if agent_context.get('technical_debt'):
                prompt += "## Technical Debt Items\n"
                for debt in agent_context['technical_debt']:
                    prompt += f"- {debt}\n"
                prompt += "\n"
            
            if agent_context.get('known_issues'):
                prompt += "## Known Issues to Consider\n"
                for issue in agent_context['known_issues']:
                    prompt += f"- {issue}\n"
                prompt += "\n"
        
        elif agent_role == "product-manager":
            if agent_context.get('completed_features'):
                prompt += "## Recently Completed Features\n"
                for feature in agent_context['completed_features'][-5:]:
                    prompt += f"- {feature}\n"
                prompt += "\n"
            
            if agent_context.get('upcoming_tasks'):
                prompt += "## Upcoming Prioritized Tasks\n"
                for task in agent_context['upcoming_tasks'][:5]:
                    prompt += f"- {task}\n"
                prompt += "\n"
        
        elif agent_role == "devops-sre":
            if agent_context.get('last_deployment'):
                prompt += f"## Last Deployment\n{agent_context['last_deployment']}\n\n"
        
        # Add any additional context provided
        if additional_context:
            prompt += "## Additional Context\n"
            for key, value in additional_context.items():
                prompt += f"{key}: {value}\n"
            prompt += "\n"
        
        return prompt
    
    def complete_task(self, task_id: str, results: Dict[str, Any]):
        """Mark a task as complete and record results"""
        task_update = {
            "status": "completed",
            "output": results.get("output"),
            "files_modified": results.get("files_modified", []),
            "tests_run": results.get("tests_run", []),
            "errors": results.get("errors", [])
        }
        
        # Update the task in history
        for agent_history in self.session_manager.sessions["agents_work_history"].values():
            for task in agent_history:
                if task["id"] == task_id:
                    task.update(task_update)
                    break
        
        self.session_manager._save_sessions()
        
        print(f"Task {task_id} completed")
    
    def update_project_context(self, updates: Dict[str, Any]):
        """Update the project context based on completed work"""
        self.session_manager.update_context(updates)
        print(f"Updated project context")
    
    def end_work_session(self, summary: Optional[str] = None):
        """End the current work session"""
        if self.current_session_id:
            self.session_manager.end_session(summary)
            print(f"Session {self.current_session_id} ended")
            if summary:
                print(f"Summary: {summary}")
            self.current_session_id = None
    
    def get_standup_report(self) -> str:
        """Get daily standup report"""
        return self.session_manager.generate_standup_report()
    
    def get_project_status(self) -> Dict:
        """Get current project status"""
        return self.session_manager.get_project_status()
    
    def collaborate_agents(self, workflow: List[Dict[str, Any]]) -> List[Dict]:
        """Execute a multi-agent workflow"""
        results = []
        
        print(f"\nStarting collaborative workflow with {len(workflow)} steps")
        
        for i, step in enumerate(workflow, 1):
            print(f"\nStep {i}/{len(workflow)}: {step['agent']} - {step['task'][:50]}...")
            
            # Deploy the agent with any outputs from previous steps
            previous_outputs = [r["output"] for r in results if r.get("output")]
            additional_context = {
                "workflow_step": f"{i}/{len(workflow)}",
                "previous_outputs": previous_outputs[-1] if previous_outputs else None
            }
            
            agent_task = self.deploy_agent(
                agent_role=step["agent"],
                task_description=step["task"],
                additional_context=additional_context
            )
            
            # In a real implementation, this would wait for the agent to complete
            # For now, we'll simulate the result
            result = {
                "step": i,
                "agent": step["agent"],
                "task_id": agent_task["task_id"],
                "status": "would_be_executed",
                "output": f"Output from {step['agent']} for: {step['task'][:50]}..."
            }
            
            results.append(result)
        
        print(f"\nWorkflow completed with {len(results)} steps")
        return results


def create_agent_task_prompt(orchestrator: AgentOrchestrator, agent_role: str, 
                            task: str) -> str:
    """Helper function to create the actual Task tool invocation"""
    agent_task = orchestrator.deploy_agent(agent_role, task)
    
    # This is what you would actually run in Claude Code:
    return f"""
# To execute this agent task in Claude Code, use:

Task(
    description="{agent_task['agent_role']}: {task[:50]}...",
    prompt=\"\"\"{agent_task['prompt']}\"\"\",
    subagent_type="general-purpose"
)
"""