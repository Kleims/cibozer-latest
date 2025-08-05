"""
Autonomous Agent System - Just tell it what you want, it handles everything
"""

import re
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from agent_orchestrator import AgentOrchestrator
from session_manager import get_session_manager

class AutonomousAgentSystem:
    """Fully autonomous agent that determines what needs to be done"""
    
    def __init__(self, project_name: str = "Cibozer"):
        self.orchestrator = AgentOrchestrator(project_name)
        self.session_manager = get_session_manager(project_name)
        
        # Keywords to determine agent assignment
        self.agent_keywords = {
            "fullstack-developer": [
                "fix", "bug", "error", "implement", "code", "function", "api", 
                "endpoint", "database", "schema", "frontend", "backend", "test",
                "refactor", "optimize", "performance", "security", "validation",
                "form", "component", "integration", "migrate", "update code"
            ],
            "product-manager": [
                "requirement", "feature", "user story", "design", "plan", "define",
                "specification", "criteria", "workflow", "user experience", "ux",
                "priority", "roadmap", "mvp", "scope", "analyze", "research"
            ],
            "devops-sre": [
                "deploy", "deployment", "ci/cd", "pipeline", "docker", "kubernetes",
                "monitoring", "logging", "infrastructure", "ssl", "certificate",
                "backup", "restore", "scale", "environment", "production", "staging",
                "server", "cloud", "aws", "configuration", "nginx", "setup"
            ]
        }
        
        # Task patterns that require multiple agents
        self.workflow_patterns = {
            "new_feature": ["feature", "add", "create new", "implement new", "build"],
            "bugfix": ["fix", "bug", "broken", "not working", "error", "issue"],
            "deployment": ["deploy", "release", "publish", "go live"],
            "optimization": ["optimize", "improve", "enhance", "speed up"],
        }
        
    def analyze_task(self, task: str) -> Tuple[str, List[str]]:
        """Analyze task and determine workflow type and agents needed"""
        task_lower = task.lower()
        
        # Check for workflow patterns first
        for workflow_type, patterns in self.workflow_patterns.items():
            if any(pattern in task_lower for pattern in patterns):
                if workflow_type == "new_feature":
                    # New features need all three agents
                    return "feature_workflow", ["product-manager", "fullstack-developer", "devops-sre"]
                elif workflow_type == "bugfix":
                    # Bugs need developer and potentially ops
                    if "production" in task_lower or "deploy" in task_lower:
                        return "bugfix_workflow", ["fullstack-developer", "devops-sre"]
                    return "single_task", ["fullstack-developer"]
                elif workflow_type == "deployment":
                    return "deployment_workflow", ["devops-sre", "fullstack-developer"]
                elif workflow_type == "optimization":
                    return "optimization_workflow", ["fullstack-developer", "devops-sre"]
        
        # If no workflow pattern, determine single agent
        agent_scores = {}
        for agent, keywords in self.agent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in task_lower)
            if score > 0:
                agent_scores[agent] = score
        
        if agent_scores:
            best_agent = max(agent_scores, key=agent_scores.get)
            return "single_task", [best_agent]
        
        # Default to product manager for unclear requirements
        return "single_task", ["product-manager"]
    
    def execute(self, task: str, auto_approve: bool = True) -> Dict[str, Any]:
        """Execute the task autonomously"""
        print("\nAUTONOMOUS AGENT SYSTEM")
        print("="*50)
        print(f"Task: {task}")
        print("-"*50)
        
        # Analyze what needs to be done
        workflow_type, agents_needed = self.analyze_task(task)
        
        print(f"\nAnalysis Complete:")
        print(f"  Workflow Type: {workflow_type}")
        print(f"  Agents Required: {', '.join(agents_needed)}")
        
        # Start session
        session_id = self.orchestrator.start_work_session(
            goal=task,
            sprint=f"Auto-{datetime.now().strftime('%Y%m%d')}"
        )
        
        results = []
        
        try:
            if workflow_type == "feature_workflow":
                results = self._run_feature_workflow(task, agents_needed)
            elif workflow_type == "bugfix_workflow":
                results = self._run_bugfix_workflow(task, agents_needed)
            elif workflow_type == "deployment_workflow":
                results = self._run_deployment_workflow(task, agents_needed)
            elif workflow_type == "optimization_workflow":
                results = self._run_optimization_workflow(task, agents_needed)
            else:  # single_task
                results = self._run_single_task(task, agents_needed[0])
            
            # Update context based on what was done
            self._update_project_context(task, workflow_type, results)
            
            # End session
            self.orchestrator.end_work_session(f"Completed: {task[:50]}")
            
            print("\n" + "="*50)
            print("TASK COMPLETED SUCCESSFULLY")
            
            return {
                "status": "completed",
                "workflow_type": workflow_type,
                "agents_used": agents_needed,
                "results": results,
                "session_id": session_id
            }
            
        except Exception as e:
            print("\n" + "!"*50)
            print("ESCALATION REQUIRED")
            print(f"Error: {str(e)}")
            print("\nThe agents need your help with this task.")
            print("Please provide more context or handle manually.")
            
            return {
                "status": "escalated",
                "error": str(e),
                "workflow_type": workflow_type,
                "agents_attempted": agents_needed,
                "session_id": session_id
            }
    
    def _run_feature_workflow(self, task: str, agents: List[str]) -> List[Dict]:
        """Run a complete feature workflow"""
        print("\nRunning Feature Development Workflow...")
        
        workflow_steps = []
        
        # Step 1: Product Manager defines requirements
        if "product-manager" in agents:
            workflow_steps.append({
                "agent": "product-manager",
                "task": f"""
                Define detailed requirements for: {task}
                
                Provide:
                1. User stories
                2. Acceptance criteria  
                3. Technical requirements
                4. Edge cases
                5. Success metrics
                """
            })
        
        # Step 2: Developer implements
        if "fullstack-developer" in agents:
            workflow_steps.append({
                "agent": "fullstack-developer",
                "task": f"""
                Implement the following: {task}
                
                Based on the requirements:
                1. Review existing code structure
                2. Implement necessary changes
                3. Add tests
                4. Ensure code quality
                """
            })
        
        # Step 3: DevOps prepares deployment
        if "devops-sre" in agents:
            workflow_steps.append({
                "agent": "devops-sre",
                "task": f"""
                Prepare deployment for: {task}
                
                1. Update CI/CD if needed
                2. Configure environments
                3. Set up monitoring
                4. Create rollback plan
                """
            })
        
        return self.orchestrator.collaborate_agents(workflow_steps)
    
    def _run_bugfix_workflow(self, task: str, agents: List[str]) -> List[Dict]:
        """Run bugfix workflow"""
        print("\nRunning Bugfix Workflow...")
        
        workflow_steps = []
        
        # Developer fixes the bug
        workflow_steps.append({
            "agent": "fullstack-developer",
            "task": f"""
            Fix the following issue: {task}
            
            1. Identify root cause
            2. Implement fix
            3. Add tests to prevent regression
            4. Verify fix doesn't break existing functionality
            """
        })
        
        # If production deployment needed
        if "devops-sre" in agents:
            workflow_steps.append({
                "agent": "devops-sre",
                "task": f"""
                Deploy bugfix to production: {task}
                
                1. Deploy to staging first
                2. Run integration tests
                3. Monitor for issues
                4. Deploy to production if stable
                """
            })
        
        return self.orchestrator.collaborate_agents(workflow_steps)
    
    def _run_deployment_workflow(self, task: str, agents: List[str]) -> List[Dict]:
        """Run deployment workflow"""
        print("\nRunning Deployment Workflow...")
        
        workflow_steps = []
        
        # Check code readiness
        if "fullstack-developer" in agents:
            workflow_steps.append({
                "agent": "fullstack-developer",
                "task": f"""
                Verify code is ready for: {task}
                
                1. Run all tests
                2. Fix any failing tests
                3. Update version numbers
                4. Ensure no debug code remains
                """
            })
        
        # Deploy
        workflow_steps.append({
            "agent": "devops-sre",
            "task": f"""
            Execute deployment: {task}
            
            1. Create deployment plan
            2. Backup current state
            3. Deploy to target environment
            4. Verify deployment success
            5. Monitor for issues
            """
        })
        
        return self.orchestrator.collaborate_agents(workflow_steps)
    
    def _run_optimization_workflow(self, task: str, agents: List[str]) -> List[Dict]:
        """Run optimization workflow"""
        print("\nRunning Optimization Workflow...")
        
        workflow_steps = []
        
        # Developer optimizes code
        workflow_steps.append({
            "agent": "fullstack-developer",
            "task": f"""
            Optimize: {task}
            
            1. Profile current performance
            2. Identify bottlenecks
            3. Implement optimizations
            4. Measure improvements
            5. Ensure functionality preserved
            """
        })
        
        # DevOps optimizes infrastructure
        if "devops-sre" in agents:
            workflow_steps.append({
                "agent": "devops-sre",
                "task": f"""
                Infrastructure optimization for: {task}
                
                1. Review resource usage
                2. Optimize configurations
                3. Implement caching if needed
                4. Set up performance monitoring
                """
            })
        
        return self.orchestrator.collaborate_agents(workflow_steps)
    
    def _run_single_task(self, task: str, agent: str) -> List[Dict]:
        """Run single agent task"""
        print(f"\nDeploying {agent} for single task...")
        
        agent_task = self.orchestrator.deploy_agent(agent, task)
        
        return [{
            "agent": agent,
            "task_id": agent_task["task_id"],
            "status": "deployed"
        }]
    
    def _update_project_context(self, task: str, workflow_type: str, results: List[Dict]):
        """Update project context based on completed work"""
        updates = {}
        
        if workflow_type == "feature_workflow":
            updates["active_features"] = [task[:50]]
        elif workflow_type == "bugfix_workflow":
            updates["known_issues"] = [f"FIXED: {task[:50]}"]
        elif workflow_type == "deployment_workflow":
            updates["last_deployment"] = datetime.now().isoformat()
            updates["deployment_status"] = "deployed"
        
        if updates:
            self.orchestrator.update_project_context(updates)
    
    def check_and_continue(self) -> Optional[Dict]:
        """Check for pending work and continue autonomously"""
        print("\nChecking for pending work...")
        
        context = self.session_manager.context
        
        # Check upcoming tasks
        if context.get("upcoming_tasks"):
            next_task = context["upcoming_tasks"][0]
            print(f"Found pending task: {next_task}")
            
            # Remove from upcoming and execute
            context["upcoming_tasks"] = context["upcoming_tasks"][1:]
            self.session_manager._save_context()
            
            return self.execute(next_task)
        
        # Check for known issues
        if context.get("known_issues"):
            for issue in context["known_issues"]:
                if not issue.startswith("FIXED:"):
                    print(f"Found unresolved issue: {issue}")
                    return self.execute(f"Fix issue: {issue}")
        
        print("No pending work found.")
        return None


# Single entry point function
def do(task: str = None):
    """The ONLY function you need - just tell it what you want"""
    system = AutonomousAgentSystem("Cibozer")
    
    if task:
        return system.execute(task)
    else:
        # No task given, check for pending work
        return system.check_and_continue()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Task provided
        task = " ".join(sys.argv[1:])
        do(task)
    else:
        # No task, check for pending work
        do()