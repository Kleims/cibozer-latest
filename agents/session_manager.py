"""
Agent Session Manager - Tracks work history and maintains context across sessions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib

class AgentSessionManager:
    """Manages agent sessions with persistent history and context"""
    
    def __init__(self, project_name: str = "Cibozer", session_dir: str = ".agent_sessions"):
        self.project_name = project_name
        self.session_dir = session_dir
        self.session_file = os.path.join(session_dir, f"{project_name.lower()}_sessions.json")
        self.context_file = os.path.join(session_dir, f"{project_name.lower()}_context.json")
        self.current_session_id = None
        
        # Create session directory if it doesn't exist
        os.makedirs(session_dir, exist_ok=True)
        
        # Load existing sessions
        self.sessions = self._load_sessions()
        self.context = self._load_context()
    
    def _load_sessions(self) -> Dict:
        """Load existing session history"""
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {
            "project": self.project_name,
            "created_at": datetime.now().isoformat(),
            "sessions": [],
            "total_tasks_completed": 0,
            "agents_work_history": {
                "fullstack-developer": [],
                "product-manager": [],
                "devops-sre": []
            }
        }
    
    def _load_context(self) -> Dict:
        """Load project context and current state"""
        if os.path.exists(self.context_file):
            with open(self.context_file, 'r') as f:
                return json.load(f)
        return {
            "current_sprint": None,
            "active_features": [],
            "completed_features": [],
            "technical_debt": [],
            "deployment_status": "development",
            "last_deployment": None,
            "database_schema_version": "1.0.0",
            "api_version": "1.0.0",
            "known_issues": [],
            "upcoming_tasks": []
        }
    
    def _save_sessions(self):
        """Save sessions to disk"""
        with open(self.session_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def _save_context(self):
        """Save context to disk"""
        with open(self.context_file, 'w') as f:
            json.dump(self.context, f, indent=2)
    
    def start_session(self, description: str, sprint: Optional[str] = None) -> str:
        """Start a new work session"""
        session_id = hashlib.md5(f"{datetime.now().isoformat()}{description}".encode()).hexdigest()[:8]
        
        session = {
            "id": session_id,
            "description": description,
            "sprint": sprint or self.context.get("current_sprint"),
            "started_at": datetime.now().isoformat(),
            "ended_at": None,
            "tasks": [],
            "agents_involved": [],
            "status": "active"
        }
        
        self.sessions["sessions"].append(session)
        self.current_session_id = session_id
        
        if sprint:
            self.context["current_sprint"] = sprint
        
        self._save_sessions()
        self._save_context()
        
        return session_id
    
    def end_session(self, summary: str = None):
        """End the current session"""
        if not self.current_session_id:
            return
        
        for session in self.sessions["sessions"]:
            if session["id"] == self.current_session_id:
                session["ended_at"] = datetime.now().isoformat()
                session["status"] = "completed"
                if summary:
                    session["summary"] = summary
                break
        
        self.current_session_id = None
        self._save_sessions()
    
    def record_agent_task(self, agent_role: str, task: Dict[str, Any]) -> str:
        """Record a task performed by an agent"""
        task_id = hashlib.md5(f"{datetime.now().isoformat()}{agent_role}{task.get('description', '')}".encode()).hexdigest()[:8]
        
        task_record = {
            "id": task_id,
            "agent": agent_role,
            "session_id": self.current_session_id,
            "timestamp": datetime.now().isoformat(),
            "description": task.get("description"),
            "status": task.get("status", "pending"),
            "input": task.get("input"),
            "output": task.get("output"),
            "files_modified": task.get("files_modified", []),
            "tests_run": task.get("tests_run", []),
            "errors": task.get("errors", [])
        }
        
        # Add to current session
        if self.current_session_id:
            for session in self.sessions["sessions"]:
                if session["id"] == self.current_session_id:
                    session["tasks"].append(task_record)
                    if agent_role not in session["agents_involved"]:
                        session["agents_involved"].append(agent_role)
                    break
        
        # Add to agent's work history
        if agent_role in self.sessions["agents_work_history"]:
            self.sessions["agents_work_history"][agent_role].append(task_record)
        
        # Update total tasks
        if task.get("status") == "completed":
            self.sessions["total_tasks_completed"] += 1
        
        self._save_sessions()
        return task_id
    
    def update_context(self, updates: Dict[str, Any]):
        """Update project context"""
        for key, value in updates.items():
            if key in self.context:
                if isinstance(self.context[key], list):
                    if isinstance(value, list):
                        self.context[key].extend(value)
                    else:
                        self.context[key].append(value)
                else:
                    self.context[key] = value
        
        self._save_context()
    
    def get_agent_context(self, agent_role: str) -> Dict[str, Any]:
        """Get relevant context for a specific agent"""
        base_context = {
            "project": self.project_name,
            "current_sprint": self.context.get("current_sprint"),
            "deployment_status": self.context.get("deployment_status"),
            "recent_work": self._get_recent_agent_work(agent_role, limit=5)
        }
        
        # Add role-specific context
        if agent_role == "fullstack-developer":
            base_context.update({
                "active_features": self.context.get("active_features", []),
                "technical_debt": self.context.get("technical_debt", []),
                "database_schema_version": self.context.get("database_schema_version"),
                "api_version": self.context.get("api_version"),
                "known_issues": self.context.get("known_issues", [])
            })
        elif agent_role == "product-manager":
            base_context.update({
                "completed_features": self.context.get("completed_features", []),
                "upcoming_tasks": self.context.get("upcoming_tasks", []),
                "active_features": self.context.get("active_features", [])
            })
        elif agent_role == "devops-sre":
            base_context.update({
                "deployment_status": self.context.get("deployment_status"),
                "last_deployment": self.context.get("last_deployment"),
                "known_issues": self.context.get("known_issues", [])
            })
        
        return base_context
    
    def _get_recent_agent_work(self, agent_role: str, limit: int = 5) -> List[Dict]:
        """Get recent work history for an agent"""
        agent_history = self.sessions["agents_work_history"].get(agent_role, [])
        return agent_history[-limit:] if agent_history else []
    
    def get_session_summary(self, session_id: str = None) -> Dict:
        """Get summary of a session"""
        if not session_id:
            session_id = self.current_session_id
        
        for session in self.sessions["sessions"]:
            if session["id"] == session_id:
                return session
        
        return None
    
    def get_project_status(self) -> Dict:
        """Get overall project status"""
        return {
            "project": self.project_name,
            "total_sessions": len(self.sessions["sessions"]),
            "total_tasks_completed": self.sessions["total_tasks_completed"],
            "current_sprint": self.context.get("current_sprint"),
            "deployment_status": self.context.get("deployment_status"),
            "active_features": len(self.context.get("active_features", [])),
            "completed_features": len(self.context.get("completed_features", [])),
            "technical_debt_items": len(self.context.get("technical_debt", [])),
            "known_issues": len(self.context.get("known_issues", []))
        }
    
    def generate_standup_report(self) -> str:
        """Generate a daily standup report"""
        # Get today's sessions
        today = datetime.now().date().isoformat()
        today_sessions = [s for s in self.sessions["sessions"] 
                         if s["started_at"].startswith(today)]
        
        report = f"""
## Daily Standup Report - {today}
### Project: {self.project_name}

#### What was accomplished:
"""
        for session in today_sessions:
            report += f"- Session: {session['description']}\n"
            for task in session.get('tasks', []):
                if task['status'] == 'completed':
                    report += f"  - [{task['agent']}] {task['description']}\n"
        
        report += f"""
#### Current Status:
- Sprint: {self.context.get('current_sprint', 'Not set')}
- Deployment: {self.context.get('deployment_status')}
- Active Features: {len(self.context.get('active_features', []))}
- Known Issues: {len(self.context.get('known_issues', []))}

#### Next Steps:
"""
        for task in self.context.get('upcoming_tasks', [])[:3]:
            report += f"- {task}\n"
        
        return report


# Singleton instance
_session_manager = None

def get_session_manager(project_name: str = "Cibozer") -> AgentSessionManager:
    """Get or create the session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = AgentSessionManager(project_name)
    return _session_manager