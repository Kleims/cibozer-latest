"""
Example script showing how to use the SaaS Team Agents with Claude Code
This demonstrates practical usage of each agent role
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from saas_team_agents import get_agent_prompt, list_agents

def example_fullstack_task():
    """Example: Using Full-Stack Developer agent for a coding task"""
    print("\n" + "="*50)
    print("FULL-STACK DEVELOPER AGENT EXAMPLE")
    print("="*50)
    
    task = """
    Current situation: The Cibozer app needs a new feature for users to favorite meal plans.
    
    Requirements:
    1. Add a 'favorites' table to store user's favorite meal plans
    2. Create API endpoints for adding/removing/listing favorites
    3. Add UI buttons to meal plan cards for favoriting
    4. Show a favorites section on the user dashboard
    
    Please implement this feature following the existing codebase patterns.
    """
    
    # In Claude Code, you would use:
    # Task(
    #     description="Add favorites feature",
    #     prompt=get_agent_prompt("fullstack-developer") + task,
    #     subagent_type="general-purpose"
    # )
    
    print("Task for Full-Stack Developer Agent:")
    print(task)
    print("\nAgent would analyze the codebase and implement the complete feature")

def example_product_manager_task():
    """Example: Using Product Manager agent for requirements definition"""
    print("\n" + "="*50)
    print("PRODUCT MANAGER AGENT EXAMPLE")
    print("="*50)
    
    task = """
    Context: Users have requested a way to share their meal plans with family members.
    
    Please define:
    1. User stories for this feature
    2. Acceptance criteria
    3. MVP vs. full feature set
    4. Potential edge cases
    5. Success metrics
    """
    
    print("Task for Product Manager Agent:")
    print(task)
    print("\nAgent would provide detailed requirements and specifications")

def example_devops_task():
    """Example: Using DevOps/SRE agent for deployment setup"""
    print("\n" + "="*50)
    print("DEVOPS/SRE AGENT EXAMPLE")
    print("="*50)
    
    task = """
    Current situation: The Cibozer Flask app is ready for production deployment.
    
    Requirements:
    1. Set up CI/CD pipeline with GitHub Actions
    2. Configure deployment to Railway or Render
    3. Set up monitoring and error tracking
    4. Implement automated backups for the database
    5. Configure SSL and security headers
    
    Please create the necessary configuration files and deployment scripts.
    """
    
    print("Task for DevOps/SRE Agent:")
    print(task)
    print("\nAgent would create deployment configurations and automation scripts")

def collaborative_example():
    """Example: How agents work together on a feature"""
    print("\n" + "="*50)
    print("COLLABORATIVE WORKFLOW EXAMPLE")
    print("="*50)
    
    print("""
    Feature Request: "Add subscription management to Cibozer"
    
    Workflow:
    1. Product Manager Agent:
       - Defines subscription tiers (Free, Pro, Enterprise)
       - Creates user stories and acceptance criteria
       - Specifies billing requirements
    
    2. Full-Stack Developer Agent:
       - Implements subscription models and database schema
       - Creates billing integration with Stripe
       - Builds subscription management UI
    
    3. DevOps/SRE Agent:
       - Sets up Stripe webhooks infrastructure
       - Configures monitoring for payment failures
       - Implements PCI compliance requirements
    
    Each agent handles their domain expertise while collaborating on the overall feature.
    """)

def main():
    print("SaaS TEAM AGENTS - USAGE EXAMPLES")
    print("="*50)
    print("\nAvailable Agents:")
    list_agents()
    
    # Show individual examples
    example_product_manager_task()
    example_fullstack_task()
    example_devops_task()
    
    # Show collaborative example
    collaborative_example()
    
    print("\n" + "="*50)
    print("TO USE IN CLAUDE CODE:")
    print("="*50)
    print("""
    Use the Task tool with:
    - subagent_type: "general-purpose"
    - prompt: get_agent_prompt("[role-name]") + your specific task
    - description: Brief description of what you want done
    
    The agents will use Claude Code's tools to:
    - Read and analyze existing code
    - Make changes to files
    - Run tests and commands
    - Create new implementations
    """)

if __name__ == "__main__":
    main()