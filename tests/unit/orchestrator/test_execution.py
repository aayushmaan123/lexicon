"""
Unit tests for execution loop data structures (Phase 2.3).
"""

import pytest
from datetime import UTC, datetime

from lexicon.orchestrator.execution import (
    ExecutionState,
    ExecutionTrace,
    ExecutionResult,
    StateTransition,
    RetryConfig,
)


class TestExecutionState:
    """Test ExecutionState enum."""
    
    def test_all_states_defined(self):
        """Test that all required states are defined."""
        required_states = [
            "start", "planning", "plan_failed", "building", "build_failed",
            "validating", "validation_failed", "fixing", "fix_failed",
            "retry_validation", "validated", "memory_update", "completed", "escalate"
        ]
        
        actual_states = [state.value for state in ExecutionState]
        
        for required in required_states:
            assert required in actual_states


class TestStateTransition:
    """Test StateTransition dataclass."""
    
    def test_create_transition(self):
        """Test creating a state transition."""
        transition = StateTransition(
            from_state=ExecutionState.START,
            to_state=ExecutionState.PLANNING,
            timestamp="2024-01-01T00:00:00Z",
            reason="Test transition"
        )
        
        assert transition.from_state == ExecutionState.START
        assert transition.to_state == ExecutionState.PLANNING
        assert transition.reason == "Test transition"
    
    def test_transition_with_metadata(self):
        """Test transition with metadata."""
        transition = StateTransition(
            from_state=ExecutionState.VALIDATING,
            to_state=ExecutionState.FIXING,
            timestamp="2024-01-01T00:00:00Z",
            metadata={"attempt": 1, "error_count": 3}
        )
        
        assert transition.metadata["attempt"] == 1
        assert transition.metadata["error_count"] == 3


class TestExecutionTrace:
    """Test ExecutionTrace class."""
    
    def test_create_trace(self):
        """Test creating an execution trace."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test task",
            started_at="2024-01-01T00:00:00Z"
        )
        
        assert trace.execution_id == "test-123"
        assert trace.task_description == "Test task"
        assert len(trace.state_transitions) == 0
        assert len(trace.agent_outputs) == 0
        assert trace.error_details is None
    
    def test_add_transition(self):
        """Test adding state transitions."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        trace.add_transition(
            ExecutionState.START,
            ExecutionState.PLANNING,
            reason="Starting planning"
        )
        
        assert len(trace.state_transitions) == 1
        assert trace.state_transitions[0].from_state == ExecutionState.START
        assert trace.state_transitions[0].to_state == ExecutionState.PLANNING
    
    def test_add_agent_output(self):
        """Test recording agent outputs."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        trace.add_agent_output("planner", {"plan": "test plan"})
        trace.add_agent_output("planner", {"plan": "updated plan"})
        
        assert "planner" in trace.agent_outputs
        assert len(trace.agent_outputs["planner"]) == 2
    
    def test_set_error(self):
        """Test recording error details."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        error = ValueError("Test error")
        trace.set_error(error, {"context": "testing"})
        
        assert trace.error_details is not None
        assert trace.error_details["error_type"] == "ValueError"
        assert trace.error_details["error_message"] == "Test error"
        assert trace.error_details["context"]["context"] == "testing"
    
    def test_complete(self):
        """Test marking execution as complete."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        trace.complete(ExecutionState.COMPLETED)
        
        assert trace.completed_at is not None
        assert trace.final_state == ExecutionState.COMPLETED
    
    def test_to_dict(self):
        """Test converting trace to dictionary."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        trace.add_transition(ExecutionState.START, ExecutionState.PLANNING)
        trace.add_agent_output("planner", {"test": "data"})
        trace.complete(ExecutionState.COMPLETED)
        
        result = trace.to_dict()
        
        assert result["execution_id"] == "test-123"
        assert result["final_state"] == "completed"
        assert len(result["state_transitions"]) == 1
        assert "planner" in result["agent_outputs"]


class TestExecutionResult:
    """Test ExecutionResult class."""
    
    def test_create_success_result(self):
        """Test creating a successful result."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        result = ExecutionResult(
            success=True,
            execution_id="test-123",
            final_state=ExecutionState.COMPLETED,
            trace=trace,
            artifacts={"files": ["test.py"]}
        )
        
        assert result.success is True
        assert result.execution_id == "test-123"
        assert result.final_state == ExecutionState.COMPLETED
        assert result.artifacts["files"] == ["test.py"]
        assert result.error_message is None
    
    def test_create_failure_result(self):
        """Test creating a failed result."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        result = ExecutionResult(
            success=False,
            execution_id="test-123",
            final_state=ExecutionState.ESCALATE,
            trace=trace,
            error_message="Test failure"
        )
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
        assert result.error_message == "Test failure"
        assert result.artifacts is None
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        trace = ExecutionTrace(
            execution_id="test-123",
            task_description="Test",
            started_at="2024-01-01T00:00:00Z"
        )
        
        result = ExecutionResult(
            success=True,
            execution_id="test-123",
            final_state=ExecutionState.COMPLETED,
            trace=trace,
            artifacts={"test": "data"}
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["execution_id"] == "test-123"
        assert result_dict["final_state"] == "completed"
        assert "trace" in result_dict


class TestRetryConfig:
    """Test RetryConfig class."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.backoff_factor == 1.5
        assert config.initial_delay == 1.0
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            backoff_factor=2.0,
            initial_delay=0.5
        )
        
        assert config.max_attempts == 5
        assert config.backoff_factor == 2.0
        assert config.initial_delay == 0.5
    
    def test_get_delay(self):
        """Test calculating delay with exponential backoff."""
        config = RetryConfig(
            max_attempts=3,
            backoff_factor=2.0,
            initial_delay=1.0
        )
        
        assert config.get_delay(0) == 1.0  # 1.0 * 2^0
        assert config.get_delay(1) == 2.0  # 1.0 * 2^1
        assert config.get_delay(2) == 4.0  # 1.0 * 2^2
    
    def test_get_delay_with_custom_values(self):
        """Test delay calculation with custom values."""
        config = RetryConfig(
            initial_delay=0.5,
            backoff_factor=1.5
        )
        
        assert config.get_delay(0) == 0.5
        assert config.get_delay(1) == 0.75  # 0.5 * 1.5^1
        assert config.get_delay(2) == 1.125  # 0.5 * 1.5^2
