"""
Base agent interface and common types for Phase 2 agents.

All agents must inherit from the Agent base class and follow stateless design principles.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, Optional


class AgentErrorType(str, Enum):
    """Types of errors that can occur during agent execution."""

    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    ESCALATION_ERROR = "escalation_error"


@dataclass
class AgentError:
    """
    Structured error response from an agent.

    Attributes:
        error_type: Category of error
        message: Human-readable error description
        context: Additional error context
        recoverable: Whether the error can be automatically recovered
        suggested_action: Recommended next step
        agent_name: Name of the agent that produced the error
    """

    error_type: AgentErrorType
    message: str
    context: Dict[str, Any]
    recoverable: bool
    suggested_action: str
    agent_name: str


@dataclass
class AgentResult:
    """
    Base result class for all agent operations.

    Attributes:
        success: Whether the operation succeeded
        data: Result data (agent-specific)
        error: Error information if success is False
        metadata: Additional metadata about execution
        duration_seconds: How long the operation took
    """

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[AgentError] = None
    metadata: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[float] = None

    def __post_init__(self):
        """Validate result consistency."""
        if not self.success and self.error is None:
            raise ValueError("Failed results must include an error")
        if self.success and self.error is not None:
            raise ValueError("Successful results should not include an error")


class Agent(ABC):
    """
    Abstract base class for all Phase 2 agents.

    All agents must be stateless - they receive inputs, perform operations,
    and return outputs without maintaining internal state between calls.

    State management is the responsibility of the Coordinator.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.

        Args:
            name: Unique identifier for this agent instance
            config: Optional configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self._initialized_at = datetime.now(UTC)

    @abstractmethod
    def execute(self, **kwargs) -> AgentResult:
        """
        Execute the agent's primary function.

        This method must be implemented by all concrete agents.
        It should be idempotent - calling with the same inputs produces
        the same outputs.

        Args:
            **kwargs: Agent-specific input parameters

        Returns:
            AgentResult with success status and data or error
        """
        pass

    def _create_success_result(
        self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Helper to create a successful result.

        Args:
            data: Result data
            metadata: Optional metadata

        Returns:
            AgentResult with success=True
        """
        return AgentResult(success=True, data=data, metadata=metadata)

    def _create_error_result(
        self,
        error_type: AgentErrorType,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        suggested_action: str = "Review error and retry",
    ) -> AgentResult:
        """
        Helper to create an error result.

        Args:
            error_type: Type of error
            message: Error description
            context: Additional context
            recoverable: Whether error can be auto-fixed
            suggested_action: Recommendation for next step

        Returns:
            AgentResult with success=False and error details
        """
        error = AgentError(
            error_type=error_type,
            message=message,
            context=context or {},
            recoverable=recoverable,
            suggested_action=suggested_action,
            agent_name=self.name,
        )
        return AgentResult(success=False, error=error)

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.

        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "initialized_at": self._initialized_at.isoformat(),
            "config": self.config,
        }
