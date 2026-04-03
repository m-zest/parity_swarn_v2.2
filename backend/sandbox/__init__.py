"""
Parity Swarm - Docker Sandbox Module

Provides isolated Docker containers for each agent with a realistic
work environment (file system, database, internal APIs). Agents can
execute real system commands alongside social platform actions.

Usage:
    from sandbox.manager import SandboxManager
    from sandbox.actions import parse_agent_action, execute_system_action

    mgr = SandboxManager()
    mgr.create_sandbox("agent_0", "QA Engineer")
    
    # Agent executes a command
    result = mgr.execute_command("agent_0", "cat /workspace/src/payment_processor.py")
    
    # Get all action logs for monitoring
    action_log = mgr.get_action_log_text()
    
    # Clean up
    mgr.destroy_all()
"""

from sandbox.manager import SandboxManager
from sandbox.actions import parse_agent_action, execute_system_action

__all__ = ["SandboxManager", "parse_agent_action", "execute_system_action"]
