"""
Coordinator implementation for Phase 2.

The Coordinator orchestrates agent interactions and manages execution state.
In Phase 2.1, this is a skeleton implementation. Full execution loop comes in Phase 2.3.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from lexicon.agents import (
    Agent,
    BuilderAgent,
    FixerAgent,
    PlannerAgent,
    ReviewerAgent,
)


@dataclass
class ExecutionContext:
    """
    Execution context managed by the Coordinator.

    This stores all state for an execution run.
    Agents are stateless; state lives here.

    Attributes:
        id: Unique execution identifier
        task: Original task description
        created_at: When execution started
        state: Current execution state
        metadata: Additional context
    """

    id: str
    task: str
    created_at: str
    state: str = "initialized"
    metadata: Optional[Dict[str, Any]] = None


class Coordinator:
    """
    Coordinator: Orchestrates agent interactions and manages execution flow.

    Responsibilities:
    - Agent lifecycle management
    - Task routing and sequencing
    - State transitions
    - Failure detection and recovery

    In Phase 2.1, this is a skeleton for agent registration.
    Full execution loop and state management comes in Phase 2.3.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Coordinator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agents: Dict[str, Agent] = {}
        self._initialized_at = datetime.now(UTC)

    def register_agent(self, agent_type: str, agent: Agent) -> None:
        """
        Register an agent with the coordinator.

        Args:
            agent_type: Type identifier ("planner", "builder", "reviewer", "fixer")
            agent: Agent instance to register
        """
        if agent_type in self.agents:
            raise ValueError(f"Agent type '{agent_type}' already registered")
        
        self.agents[agent_type] = agent

    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """
        Get a registered agent by type.

        Args:
            agent_type: Type identifier

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_type)

    def create_execution_context(self, task: str) -> ExecutionContext:
        """
        Create a new execution context for a task.

        Args:
            task: Task description

        Returns:
            ExecutionContext with unique ID
        """
        return ExecutionContext(
            id=str(uuid4()),
            task=task,
            created_at=datetime.now(UTC).isoformat(),
            state="initialized",
            metadata={},
        )

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the coordinator and registered agents.

        Returns:
            Dictionary with coordinator metadata
        """
        return {
            "initialized_at": self._initialized_at.isoformat(),
            "registered_agents": list(self.agents.keys()),
            "agent_details": {
                agent_type: agent.get_info()
                for agent_type, agent in self.agents.items()
            },
            "config": self.config,
        }
