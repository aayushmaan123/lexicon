"""Unit tests for Agent base class, AgentResult, and AgentError."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from lexicon.agents.base import Agent, AgentError, AgentErrorType, AgentResult


class TestAgentError:
    """Test suite for AgentError dataclass."""

    def test_init_with_valid_data(self):
        """Test initialization with valid data."""
        error = AgentError(
            error_type=AgentErrorType.VALIDATION_ERROR,
            message="Invalid input",
            context={"field": "value"},
            recoverable=True,
            suggested_action="Fix the input",
            agent_name="test_agent",
        )

        assert error.error_type == AgentErrorType.VALIDATION_ERROR
        assert error.message == "Invalid input"
        assert error.context == {"field": "value"}
        assert error.recoverable is True
        assert error.suggested_action == "Fix the input"
        assert error.agent_name == "test_agent"

    def test_init_with_empty_context(self):
        """Test initialization with empty context dictionary."""
        error = AgentError(
            error_type=AgentErrorType.EXECUTION_ERROR,
            message="Failed",
            context={},
            recoverable=False,
            suggested_action="Retry",
            agent_name="agent",
        )

        assert error.context == {}

    @pytest.mark.parametrize(
        "error_type",
        [
            AgentErrorType.VALIDATION_ERROR,
            AgentErrorType.EXECUTION_ERROR,
            AgentErrorType.TIMEOUT_ERROR,
            AgentErrorType.RESOURCE_ERROR,
            AgentErrorType.ESCALATION_ERROR,
        ],
    )
    def test_all_error_types(self, error_type):
        """Test all error type variants."""
        error = AgentError(
            error_type=error_type,
            message="Test error",
            context={},
            recoverable=True,
            suggested_action="Retry",
            agent_name="agent",
        )

        assert error.error_type == error_type


class TestAgentResult:
    """Test suite for AgentResult dataclass."""

    def test_init_success_without_data(self):
        """Test successful result without data raises no error."""
        result = AgentResult(success=True, data={"key": "value"})

        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.error is None

    def test_init_success_with_data(self):
        """Test successful result with data."""
        data = {"output": "result"}
        metadata = {"duration": 1.5}

        result = AgentResult(
            success=True, data=data, metadata=metadata, duration_seconds=1.5
        )

        assert result.success is True
        assert result.data == data
        assert result.metadata == metadata
        assert result.duration_seconds == 1.5
        assert result.error is None

    def test_init_failure_with_error(self):
        """Test failed result with error."""
        error = AgentError(
            error_type=AgentErrorType.VALIDATION_ERROR,
            message="Validation failed",
            context={},
            recoverable=True,
            suggested_action="Fix input",
            agent_name="test",
        )

        result = AgentResult(success=False, error=error)

        assert result.success is False
        assert result.error == error
        assert result.data is None

    def test_init_failure_without_error_raises_error(self):
        """Test that failed result without error raises ValueError."""
        with pytest.raises(ValueError, match="Failed results must include an error"):
            AgentResult(success=False, error=None)

    def test_init_success_with_error_raises_error(self):
        """Test that successful result with error raises ValueError."""
        error = AgentError(
            error_type=AgentErrorType.VALIDATION_ERROR,
            message="Error",
            context={},
            recoverable=True,
            suggested_action="Action",
            agent_name="agent",
        )

        with pytest.raises(
            ValueError, match="Successful results should not include an error"
        ):
            AgentResult(success=True, error=error)

    def test_init_with_none_values(self):
        """Test initialization with None values for optional fields."""
        result = AgentResult(
            success=True,
            data={"key": "value"},
            metadata=None,
            duration_seconds=None,
        )

        assert result.metadata is None
        assert result.duration_seconds is None


class ConcreteAgent(Agent):
    """Concrete implementation of Agent for testing."""

    def execute(self, **kwargs):
        """Test implementation of execute method."""
        return self._create_success_result(data={"executed": True})


class TestAgent:
    """Test suite for Agent base class."""

    def test_init_with_name_only(self):
        """Test initialization with name only."""
        agent = ConcreteAgent(name="test_agent")

        assert agent.name == "test_agent"
        assert agent.config == {}
        assert agent._initialized_at is not None

    def test_init_with_name_and_config(self):
        """Test initialization with name and config."""
        config = {"param1": "value1", "param2": 42}
        agent = ConcreteAgent(name="configured_agent", config=config)

        assert agent.name == "configured_agent"
        assert agent.config == config

    def test_init_with_none_config(self):
        """Test initialization with None config defaults to empty dict."""
        agent = ConcreteAgent(name="agent", config=None)

        assert agent.config == {}

    def test_initialized_at_is_datetime(self):
        """Test that _initialized_at is a valid datetime."""
        agent = ConcreteAgent(name="agent")

        assert isinstance(agent._initialized_at, datetime)

    def test_get_info_returns_metadata(self):
        """Test get_info returns correct metadata."""
        config = {"key": "value"}
        agent = ConcreteAgent(name="info_agent", config=config)

        info = agent.get_info()

        assert info["name"] == "info_agent"
        assert info["type"] == "ConcreteAgent"
        assert "initialized_at" in info
        assert info["config"] == config

    def test_create_success_result_with_data_only(self):
        """Test _create_success_result with data only."""
        agent = ConcreteAgent(name="agent")
        data = {"result": "success"}

        result = agent._create_success_result(data=data)

        assert result.success is True
        assert result.data == data
        assert result.error is None
        assert result.metadata is None

    def test_create_success_result_with_data_and_metadata(self):
        """Test _create_success_result with data and metadata."""
        agent = ConcreteAgent(name="agent")
        data = {"result": "success"}
        metadata = {"info": "extra"}

        result = agent._create_success_result(data=data, metadata=metadata)

        assert result.success is True
        assert result.data == data
        assert result.metadata == metadata

    def test_create_error_result_minimal(self):
        """Test _create_error_result with minimal parameters."""
        agent = ConcreteAgent(name="error_agent")

        result = agent._create_error_result(
            error_type=AgentErrorType.EXECUTION_ERROR, message="Something went wrong"
        )

        assert result.success is False
        assert result.error is not None
        assert result.error.error_type == AgentErrorType.EXECUTION_ERROR
        assert result.error.message == "Something went wrong"
        assert result.error.context == {}
        assert result.error.recoverable is False
        assert result.error.suggested_action == "Review error and retry"
        assert result.error.agent_name == "error_agent"

    def test_create_error_result_with_all_parameters(self):
        """Test _create_error_result with all parameters."""
        agent = ConcreteAgent(name="detailed_agent")
        context = {"input": "bad_value"}

        result = agent._create_error_result(
            error_type=AgentErrorType.VALIDATION_ERROR,
            message="Invalid input provided",
            context=context,
            recoverable=True,
            suggested_action="Provide valid input",
        )

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert result.error.message == "Invalid input provided"
        assert result.error.context == context
        assert result.error.recoverable is True
        assert result.error.suggested_action == "Provide valid input"

    def test_execute_is_abstract(self):
        """Test that execute must be implemented by subclasses."""
        with pytest.raises(TypeError):
            Agent(name="abstract")  # Cannot instantiate abstract class

    def test_stateless_multiple_calls_same_result(self):
        """Test that agents are stateless - multiple calls with same input yield same result."""
        agent = ConcreteAgent(name="stateless_agent")

        result1 = agent.execute()
        result2 = agent.execute()

        assert result1.success == result2.success
        assert result1.data == result2.data

    def test_different_instances_independent(self):
        """Test that different agent instances are independent."""
        agent1 = ConcreteAgent(name="agent1", config={"value": 1})
        agent2 = ConcreteAgent(name="agent2", config={"value": 2})

        assert agent1.name != agent2.name
        assert agent1.config != agent2.config
        assert agent1._initialized_at != agent2._initialized_at
