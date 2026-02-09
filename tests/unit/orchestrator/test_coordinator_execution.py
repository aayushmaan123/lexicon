"""
Integration tests for Coordinator execution loop (Phase 2.3).

Tests the complete execution workflow with state machine and self-healing.
"""

import pytest

from lexicon.agents import PlannerAgent, BuilderAgent, ReviewerAgent, FixerAgent
from lexicon.orchestrator import Coordinator, ExecutionState


class TestCoordinatorExecutionLoop:
    """Test the full execution loop workflow."""
    
    def test_successful_execution_without_fixing(self):
        """Test successful execution that passes validation on first try."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Create a simple function")
        
        assert result.success is True
        assert result.final_state == ExecutionState.COMPLETED
        assert result.artifacts is not None
        assert result.artifacts["fix_applied"] is False
        assert result.artifacts["fix_attempts"] == 0
        
        # Check state transitions
        trace_dict = result.trace.to_dict()
        states_visited = [t["to"] for t in trace_dict["state_transitions"]]
        
        assert "planning" in states_visited
        assert "building" in states_visited
        assert "validating" in states_visited
        assert "validated" in states_visited
        assert "completed" in states_visited
    
    def test_execution_with_fixing(self):
        """Test execution that requires fixing."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        
        # Create a reviewer that fails initially
        class FailOnceReviewer(ReviewerAgent):
            def __init__(self):
                super().__init__()
                self.call_count = 0
            
            def execute(self, inputs):
                self.call_count += 1
                if self.call_count == 1:
                    # First call: fail validation
                    return type('obj', (object,), {
                        'success': True,
                        'data': {
                            'overall_status': 'failed',
                            'issues': [{'severity': 'error', 'message': 'Test failure'}]
                        },
                        'error': None
                    })()
                else:
                    # Subsequent calls: pass
                    return super().execute(inputs)
        
        coordinator.register_agent("reviewer", FailOnceReviewer())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Create a function with validation issues")
        
        assert result.success is True
        assert result.final_state == ExecutionState.COMPLETED
        assert result.artifacts["fix_applied"] is True
        assert result.artifacts["fix_attempts"] > 0
        
        # Check fixing was attempted
        trace_dict = result.trace.to_dict()
        states_visited = [t["to"] for t in trace_dict["state_transitions"]]
        
        assert "fixing" in states_visited
        assert "retry_validation" in states_visited
    
    def test_execution_fails_planning(self):
        """Test execution that fails during planning."""
        coordinator = Coordinator()
        
        # Create a planner that always fails
        class FailingPlanner(PlannerAgent):
            def execute(self, inputs):
                return type('obj', (object,), {
                    'success': False,
                    'data': None,
                    'error': 'Planning failed'
                })()
        
        coordinator.register_agent("planner", FailingPlanner())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Invalid task")
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
        assert "Planning failed" in result.error_message
    
    def test_execution_fails_building(self):
        """Test execution that fails during building."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        
        # Create a builder that always fails
        class FailingBuilder(BuilderAgent):
            def execute(self, inputs):
                return type('obj', (object,), {
                    'success': False,
                    'data': None,
                    'error': 'Building failed'
                })()
        
        coordinator.register_agent("builder", FailingBuilder())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Task that breaks builder")
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
        assert "Building failed" in result.error_message
    
    def test_execution_fails_after_max_fix_attempts(self):
        """Test execution that exhausts fix attempts."""
        coordinator = Coordinator(config={"max_retry_attempts": 2})
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        
        # Create a reviewer that always fails
        class AlwaysFailReviewer(ReviewerAgent):
            def execute(self, inputs):
                return type('obj', (object,), {
                    'success': True,
                    'data': {
                        'overall_status': 'failed',
                        'issues': [{'severity': 'error', 'message': 'Unfixable error'}]
                    },
                    'error': None
                })()
        
        coordinator.register_agent("reviewer", AlwaysFailReviewer())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Task with unfixable issues")
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
        assert "after max attempts" in result.error_message.lower() or "exhausted" in result.error_message.lower()
    
    def test_execution_without_required_agents(self):
        """Test execution fails gracefully when agents are missing."""
        coordinator = Coordinator()
        # Only register planner, missing others
        coordinator.register_agent("planner", PlannerAgent())
        
        result = coordinator.execute("Task")
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
    
    def test_execution_trace_completeness(self):
        """Test that execution trace captures all relevant information."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Test task for tracing")
        
        trace = result.trace
        trace_dict = trace.to_dict()
        
        # Check trace structure
        assert trace.execution_id == result.execution_id
        assert trace.task_description == "Test task for tracing"
        assert trace.started_at is not None
        assert trace.completed_at is not None
        assert trace.final_state is not None
        
        # Check transitions were recorded
        assert len(trace.state_transitions) > 0
        
        # Check agent outputs were recorded
        assert len(trace.agent_outputs) > 0
    
    def test_execution_with_context_metadata(self):
        """Test execution with additional context metadata."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        metadata = {"priority": "high", "project": "test"}
        result = coordinator.execute("Task", context_metadata=metadata)
        
        assert result.success is True
        # Metadata should be preserved in context
        # (implementation-specific check)
    
    def test_retry_config_applied(self):
        """Test that custom retry configuration is used."""
        coordinator = Coordinator(config={
            "max_retry_attempts": 5,
            "retry_backoff_factor": 2.0,
            "initial_retry_delay": 0.1
        })
        
        assert coordinator.retry_config.max_attempts == 5
        assert coordinator.retry_config.backoff_factor == 2.0
        assert coordinator.retry_config.initial_delay == 0.1


class TestCoordinatorStateTransitions:
    """Test state machine transitions."""
    
    def test_valid_happy_path_transitions(self):
        """Test valid state transitions in happy path."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Simple task")
        
        trace_dict = result.trace.to_dict()
        transitions = trace_dict["state_transitions"]
        
        # Verify sequential progression
        expected_sequence = [
            ("start", "planning"),
            ("planning", "building"),
            ("building", "validating"),
            ("validating", "validated"),
            ("validated", "completed")
        ]
        
        actual_sequence = [(t["from"], t["to"]) for t in transitions]
        
        for expected_trans in expected_sequence:
            assert expected_trans in actual_sequence
    
    def test_failure_path_transitions(self):
        """Test state transitions when failures occur."""
        coordinator = Coordinator()
        
        # Failing planner
        class FailingPlanner(PlannerAgent):
            def execute(self, inputs):
                return type('obj', (object,), {
                    'success': False,
                    'data': None,
                    'error': 'Test failure'
                })()
        
        coordinator.register_agent("planner", FailingPlanner())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Failing task")
        
        trace_dict = result.trace.to_dict()
        states_visited = [t["to"] for t in trace_dict["state_transitions"]]
        
        assert "plan_failed" in states_visited or "planning" in states_visited


class TestCoordinatorAgentOutputs:
    """Test agent output recording in trace."""
    
    def test_all_agent_outputs_recorded(self):
        """Test that outputs from all agents are recorded."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Test task")
        
        agent_outputs = result.trace.agent_outputs
        
        # At minimum, we should have outputs from planner, builder, reviewer
        assert "planner" in agent_outputs
        assert "builder" in agent_outputs
        assert "reviewer" in agent_outputs
    
    def test_agent_outputs_have_timestamps(self):
        """Test that agent outputs include timestamps."""
        coordinator = Coordinator()
        coordinator.register_agent("planner", PlannerAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Test task")
        
        for agent_type, outputs in result.trace.agent_outputs.items():
            for output in outputs:
                assert "timestamp" in output
                assert "output" in output


class TestCoordinatorErrorHandling:
    """Test error handling and escalation."""
    
    def test_exception_during_execution_escalates(self):
        """Test that exceptions during execution are properly escalated."""
        coordinator = Coordinator()
        
        # Agent that raises exception
        class ExceptionAgent(PlannerAgent):
            def execute(self, inputs):
                raise RuntimeError("Unexpected error")
        
        coordinator.register_agent("planner", ExceptionAgent())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Task that causes exception")
        
        assert result.success is False
        assert result.final_state == ExecutionState.ESCALATE
        assert result.error_message is not None
    
    def test_error_details_recorded_in_trace(self):
        """Test that error details are recorded in trace."""
        coordinator = Coordinator()
        
        class FailingPlanner(PlannerAgent):
            def execute(self, inputs):
                raise ValueError("Test error")
        
        coordinator.register_agent("planner", FailingPlanner())
        coordinator.register_agent("builder", BuilderAgent())
        coordinator.register_agent("reviewer", ReviewerAgent())
        coordinator.register_agent("fixer", FixerAgent())
        
        result = coordinator.execute("Error task")
        
        # Error should be recorded in trace
        assert result.trace.error_details is not None
        assert "Test error" in result.trace.error_details["error_message"]
