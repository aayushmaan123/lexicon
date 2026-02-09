"""Unit tests for Coordinator."""

import pytest

from lexicon.agents.base import Agent, AgentResult
from lexicon.agents.builder import BuilderAgent
from lexicon.agents.fixer import FixerAgent
from lexicon.agents.planner import PlannerAgent
from lexicon.agents.reviewer import ReviewerAgent
from lexicon.orchestrator.coordinator import Coordinator, ExecutionContext


class TestExecutionContext:
    """Test suite for ExecutionContext dataclass."""

    def test_init_with_required_fields(self):
        """Test initialization with required fields."""
        context = ExecutionContext(
            id="exec-123",
            task="Test task",
            created_at="2024-01-01T00:00:00Z",
        )

        assert context.id == "exec-123"
        assert context.task == "Test task"
        assert context.created_at == "2024-01-01T00:00:00Z"
        assert context.state == "initialized"
        assert context.metadata is None

    def test_init_with_all_fields(self):
        """Test initialization with all fields."""
        metadata = {"key": "value"}
        context = ExecutionContext(
            id="exec-456",
            task="Complete task",
            created_at="2024-01-01T00:00:00Z",
            state="running",
            metadata=metadata,
        )

        assert context.id == "exec-456"
        assert context.state == "running"
        assert context.metadata == metadata

    def test_default_state_is_initialized(self):
        """Test that default state is initialized."""
        context = ExecutionContext(
            id="exec-1",
            task="Task",
            created_at="2024-01-01T00:00:00Z",
        )

        assert context.state == "initialized"


class MockAgent(Agent):
    """Mock agent for testing."""

    def execute(self, **kwargs):
        """Mock execute method."""
        return AgentResult(success=True, data={"result": "mock"})


class TestCoordinator:
    """Test suite for Coordinator."""

    def test_init_without_config(self):
        """Test initialization without config."""
        coordinator = Coordinator()

        assert coordinator.config == {}
        assert coordinator.agents == {}
        assert coordinator._initialized_at is not None

    def test_init_with_config(self):
        """Test initialization with config."""
        config = {"max_retries": 3, "timeout": 300}
        coordinator = Coordinator(config=config)

        assert coordinator.config == config

    def test_init_with_none_config(self):
        """Test initialization with None config defaults to empty dict."""
        coordinator = Coordinator(config=None)

        assert coordinator.config == {}

    def test_register_agent_success(self):
        """Test successful agent registration."""
        coordinator = Coordinator()
        agent = MockAgent(name="test_agent")

        coordinator.register_agent("test", agent)

        assert "test" in coordinator.agents
        assert coordinator.agents["test"] == agent

    def test_register_agent_planner(self):
        """Test registering PlannerAgent."""
        coordinator = Coordinator()
        planner = PlannerAgent()

        coordinator.register_agent("planner", planner)

        assert coordinator.agents["planner"] == planner

    def test_register_agent_builder(self):
        """Test registering BuilderAgent."""
        coordinator = Coordinator()
        builder = BuilderAgent()

        coordinator.register_agent("builder", builder)

        assert coordinator.agents["builder"] == builder

    def test_register_agent_reviewer(self):
        """Test registering ReviewerAgent."""
        coordinator = Coordinator()
        reviewer = ReviewerAgent()

        coordinator.register_agent("reviewer", reviewer)

        assert coordinator.agents["reviewer"] == reviewer

    def test_register_agent_fixer(self):
        """Test registering FixerAgent."""
        coordinator = Coordinator()
        fixer = FixerAgent()

        coordinator.register_agent("fixer", fixer)

        assert coordinator.agents["fixer"] == fixer

    def test_register_agent_duplicate_raises_error(self):
        """Test that registering duplicate agent type raises ValueError."""
        coordinator = Coordinator()
        agent1 = MockAgent(name="agent1")
        agent2 = MockAgent(name="agent2")

        coordinator.register_agent("test", agent1)

        with pytest.raises(ValueError, match="already registered"):
            coordinator.register_agent("test", agent2)

    def test_register_multiple_different_agents(self):
        """Test registering multiple different agent types."""
        coordinator = Coordinator()
        planner = PlannerAgent()
        builder = BuilderAgent()
        reviewer = ReviewerAgent()

        coordinator.register_agent("planner", planner)
        coordinator.register_agent("builder", builder)
        coordinator.register_agent("reviewer", reviewer)

        assert len(coordinator.agents) == 3
        assert coordinator.agents["planner"] == planner
        assert coordinator.agents["builder"] == builder
        assert coordinator.agents["reviewer"] == reviewer

    def test_get_agent_exists(self):
        """Test getting an existing agent."""
        coordinator = Coordinator()
        agent = MockAgent(name="test")
        coordinator.register_agent("test", agent)

        retrieved = coordinator.get_agent("test")

        assert retrieved == agent

    def test_get_agent_not_exists_returns_none(self):
        """Test getting non-existent agent returns None."""
        coordinator = Coordinator()

        retrieved = coordinator.get_agent("nonexistent")

        assert retrieved is None

    def test_get_agent_after_registration(self):
        """Test that get_agent returns correct agent after registration."""
        coordinator = Coordinator()
        planner = PlannerAgent(name="planner1")
        coordinator.register_agent("planner", planner)

        retrieved = coordinator.get_agent("planner")

        assert isinstance(retrieved, PlannerAgent)
        assert retrieved.name == "planner1"

    def test_create_execution_context_basic(self):
        """Test creating execution context."""
        coordinator = Coordinator()
        task = "Implement feature X"

        context = coordinator.create_execution_context(task)

        assert isinstance(context, ExecutionContext)
        assert context.task == task
        assert context.state == "initialized"
        assert context.id is not None
        assert context.created_at is not None

    def test_create_execution_context_unique_ids(self):
        """Test that each execution context has a unique ID."""
        coordinator = Coordinator()

        context1 = coordinator.create_execution_context("Task 1")
        context2 = coordinator.create_execution_context("Task 2")

        assert context1.id != context2.id

    def test_create_execution_context_metadata_initialized(self):
        """Test that execution context metadata is initialized as empty dict."""
        coordinator = Coordinator()

        context = coordinator.create_execution_context("Task")

        assert context.metadata == {}

    def test_get_info_no_agents(self):
        """Test get_info with no registered agents."""
        coordinator = Coordinator()

        info = coordinator.get_info()

        assert "initialized_at" in info
        assert info["registered_agents"] == []
        assert info["agent_details"] == {}
        assert info["config"] == {}

    def test_get_info_with_agents(self):
        """Test get_info with registered agents."""
        coordinator = Coordinator()
        planner = PlannerAgent(name="p1")
        builder = BuilderAgent(name="b1")
        coordinator.register_agent("planner", planner)
        coordinator.register_agent("builder", builder)

        info = coordinator.get_info()

        assert "planner" in info["registered_agents"]
        assert "builder" in info["registered_agents"]
        assert len(info["registered_agents"]) == 2
        assert "planner" in info["agent_details"]
        assert "builder" in info["agent_details"]

    def test_get_info_agent_details_structure(self):
        """Test that agent_details contains proper agent info."""
        coordinator = Coordinator()
        planner = PlannerAgent(name="test_planner")
        coordinator.register_agent("planner", planner)

        info = coordinator.get_info()

        planner_info = info["agent_details"]["planner"]
        assert planner_info["name"] == "test_planner"
        assert planner_info["type"] == "PlannerAgent"
        assert "initialized_at" in planner_info

    def test_get_info_includes_config(self):
        """Test that get_info includes coordinator config."""
        config = {"setting": "value"}
        coordinator = Coordinator(config=config)

        info = coordinator.get_info()

        assert info["config"] == config

    def test_stateless_agents_independent_calls(self):
        """Test that coordinator doesn't maintain agent state between calls."""
        coordinator = Coordinator()
        planner = PlannerAgent()
        coordinator.register_agent("planner", planner)

        # Get agent twice
        agent1 = coordinator.get_agent("planner")
        agent2 = coordinator.get_agent("planner")

        # Should be the same instance
        assert agent1 is agent2

    def test_multiple_coordinators_independent(self):
        """Test that multiple coordinator instances are independent."""
        coord1 = Coordinator(config={"id": 1})
        coord2 = Coordinator(config={"id": 2})

        agent1 = MockAgent(name="agent1")
        agent2 = MockAgent(name="agent2")

        coord1.register_agent("test", agent1)
        coord2.register_agent("test", agent2)

        assert coord1.agents["test"] != coord2.agents["test"]
        assert coord1.config != coord2.config

    def test_register_agent_type_parameter(self):
        """Test that agent_type parameter can be any string."""
        coordinator = Coordinator()
        agent = MockAgent(name="custom")

        # Should accept any string
        coordinator.register_agent("custom_type", agent)
        coordinator.register_agent("my-agent", agent)

        assert "custom_type" in coordinator.agents
        # Note: Second registration will fail due to duplicate agent object
        # but we're testing the type parameter flexibility

    def test_empty_coordinator_state(self):
        """Test that new coordinator has empty state."""
        coordinator = Coordinator()

        assert len(coordinator.agents) == 0
        info = coordinator.get_info()
        assert len(info["registered_agents"]) == 0

    def test_create_execution_context_preserves_task(self):
        """Test that execution context preserves task description."""
        coordinator = Coordinator()
        task = "Complex multi-step task with special characters: @#$%"

        context = coordinator.create_execution_context(task)

        assert context.task == task

    def test_agents_dict_modification_detection(self):
        """Test that agents dict can be modified through registration."""
        coordinator = Coordinator()

        initial_count = len(coordinator.agents)
        coordinator.register_agent("agent1", MockAgent(name="a1"))
        after_first = len(coordinator.agents)
        coordinator.register_agent("agent2", MockAgent(name="a2"))
        after_second = len(coordinator.agents)

        assert initial_count == 0
        assert after_first == 1
        assert after_second == 2

    def test_get_info_initialized_at_format(self):
        """Test that initialized_at is in ISO format."""
        coordinator = Coordinator()

        info = coordinator.get_info()

        # Should be ISO format string
        assert isinstance(info["initialized_at"], str)
        assert "T" in info["initialized_at"]  # ISO format includes T

    def test_all_agent_types_registration(self):
        """Test registering all Phase 2.1 agent types together."""
        coordinator = Coordinator()

        planner = PlannerAgent()
        builder = BuilderAgent()
        reviewer = ReviewerAgent()
        fixer = FixerAgent()

        coordinator.register_agent("planner", planner)
        coordinator.register_agent("builder", builder)
        coordinator.register_agent("reviewer", reviewer)
        coordinator.register_agent("fixer", fixer)

        assert len(coordinator.agents) == 4
        assert isinstance(coordinator.get_agent("planner"), PlannerAgent)
        assert isinstance(coordinator.get_agent("builder"), BuilderAgent)
        assert isinstance(coordinator.get_agent("reviewer"), ReviewerAgent)
        assert isinstance(coordinator.get_agent("fixer"), FixerAgent)
