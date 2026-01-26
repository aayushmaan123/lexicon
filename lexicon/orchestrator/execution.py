"""
Execution loop implementation for Phase 2.3.

This module implements the deterministic execution loop with state machine,
retry logic, and self-healing mechanisms as defined in PHASE_2_EXECUTION_FLOW.md.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionState(Enum):
    """Execution states as defined in PHASE_2_EXECUTION_FLOW.md."""
    
    START = "start"
    PLANNING = "planning"
    PLAN_FAILED = "plan_failed"
    BUILDING = "building"
    BUILD_FAILED = "build_failed"
    VALIDATING = "validating"
    VALIDATION_FAILED = "validation_failed"
    FIXING = "fixing"
    FIX_FAILED = "fix_failed"
    RETRY_VALIDATION = "retry_validation"
    VALIDATED = "validated"
    MEMORY_UPDATE = "memory_update"
    COMPLETED = "completed"
    ESCALATE = "escalate"


@dataclass
class StateTransition:
    """Records a state transition with timestamp and reason."""
    
    from_state: ExecutionState
    to_state: ExecutionState
    timestamp: str
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """
    Complete execution trace including all state transitions and outputs.
    
    This provides observability into the execution process.
    """
    
    execution_id: str
    task_description: str
    started_at: str
    state_transitions: List[StateTransition] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None
    final_state: Optional[ExecutionState] = None
    
    def add_transition(
        self,
        from_state: ExecutionState,
        to_state: ExecutionState,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a state transition."""
        transition = StateTransition(
            from_state=from_state,
            to_state=to_state,
            timestamp=datetime.now(UTC).isoformat(),
            reason=reason,
            metadata=metadata or {}
        )
        self.state_transitions.append(transition)
    
    def add_agent_output(self, agent_type: str, output: Any) -> None:
        """Record agent output."""
        if agent_type not in self.agent_outputs:
            self.agent_outputs[agent_type] = []
        self.agent_outputs[agent_type].append({
            "timestamp": datetime.now(UTC).isoformat(),
            "output": output
        })
    
    def set_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Record error details."""
        self.error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            "timestamp": datetime.now(UTC).isoformat()
        }
    
    def complete(self, final_state: ExecutionState) -> None:
        """Mark execution as complete."""
        self.completed_at = datetime.now(UTC).isoformat()
        self.final_state = final_state
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "task_description": self.task_description,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "final_state": self.final_state.value if self.final_state else None,
            "state_transitions": [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "timestamp": t.timestamp,
                    "reason": t.reason,
                    "metadata": t.metadata
                }
                for t in self.state_transitions
            ],
            "agent_outputs": self.agent_outputs,
            "error_details": self.error_details
        }


@dataclass
class ExecutionResult:
    """
    Final result of an execution.
    
    Attributes:
        success: Whether execution succeeded
        execution_id: Unique execution identifier
        final_state: Final state reached
        trace: Complete execution trace
        artifacts: Generated artifacts (if successful)
        error_message: Error description (if failed)
    """
    
    success: bool
    execution_id: str
    final_state: ExecutionState
    trace: ExecutionTrace
    artifacts: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "execution_id": self.execution_id,
            "final_state": self.final_state.value,
            "trace": self.trace.to_dict(),
            "artifacts": self.artifacts,
            "error_message": self.error_message
        }


@dataclass
class RetryConfig:
    """
    Configuration for retry logic.
    
    Attributes:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for exponential backoff (default: 1.5)
        initial_delay: Initial delay in seconds (default: 1.0)
    """
    
    max_attempts: int = 3
    backoff_factor: float = 1.5
    initial_delay: float = 1.0
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        return self.initial_delay * (self.backoff_factor ** attempt)
