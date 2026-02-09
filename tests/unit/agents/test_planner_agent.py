"""Unit tests for PlannerAgent."""

import pytest

from lexicon.agents.base import AgentErrorType
from lexicon.agents.planner import ExecutionPlan, PlannerAgent, Task


class TestTask:
    """Test suite for Task dataclass."""

    def test_init_with_valid_data(self):
        """Test initialization with valid data."""
        task = Task(
            id="task-1",
            description="Implement feature X",
            dependencies=["task-0"],
            estimated_duration="1h",
            risk_level="medium",
        )

        assert task.id == "task-1"
        assert task.description == "Implement feature X"
        assert task.dependencies == ["task-0"]
        assert task.estimated_duration == "1h"
        assert task.risk_level == "medium"

    def test_init_with_empty_dependencies(self):
        """Test initialization with empty dependencies list."""
        task = Task(
            id="task-1",
            description="Initial task",
            dependencies=[],
            estimated_duration="30m",
            risk_level="low",
        )

        assert task.dependencies == []


class TestExecutionPlan:
    """Test suite for ExecutionPlan dataclass."""

    def test_init_with_valid_data(self):
        """Test initialization with valid plan data."""
        subtasks = [
            Task(
                id="task-1",
                description="Step 1",
                dependencies=[],
                estimated_duration="30m",
                risk_level="low",
            )
        ]

        plan = ExecutionPlan(
            plan_id="plan-123",
            task="Original task",
            subtasks=subtasks,
            total_estimated_duration="30m",
            overall_risk="low",
            created_at="2024-01-01T00:00:00Z",
        )

        assert plan.plan_id == "plan-123"
        assert plan.task == "Original task"
        assert len(plan.subtasks) == 1
        assert plan.total_estimated_duration == "30m"
        assert plan.overall_risk == "low"
        assert plan.created_at == "2024-01-01T00:00:00Z"


class TestPlannerAgent:
    """Test suite for PlannerAgent."""

    def test_init_with_default_name(self):
        """Test initialization with default name."""
        agent = PlannerAgent()

        assert agent.name == "planner"
        assert agent.config == {}

    def test_init_with_custom_name(self):
        """Test initialization with custom name."""
        agent = PlannerAgent(name="custom_planner")

        assert agent.name == "custom_planner"

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"max_subtasks": 10, "detail_level": "high"}
        agent = PlannerAgent(config=config)

        assert agent.config == config

    def test_execute_with_valid_task_description(self):
        """Test execute with valid task description returns success."""
        agent = PlannerAgent()

        result = agent.execute(task_description="Implement user authentication")

        assert result.success is True
        assert "plan" in result.data
        assert result.error is None

    def test_execute_creates_execution_plan(self):
        """Test that execute creates a proper ExecutionPlan."""
        agent = PlannerAgent()

        result = agent.execute(task_description="Build REST API")

        plan_data = result.data["plan"]
        assert "plan_id" in plan_data
        assert plan_data["task"] == "Build REST API"
        assert "subtasks" in plan_data
        assert isinstance(plan_data["subtasks"], list)
        assert "total_estimated_duration" in plan_data
        assert "overall_risk" in plan_data
        assert "created_at" in plan_data

    def test_execute_with_context(self):
        """Test execute with additional context."""
        agent = PlannerAgent()
        context = {"language": "python", "framework": "django"}

        result = agent.execute(
            task_description="Create API endpoint", context=context
        )

        assert result.success is True
        assert result.metadata["has_context"] is True

    def test_execute_without_context(self):
        """Test execute without context still works."""
        agent = PlannerAgent()

        result = agent.execute(task_description="Write documentation")

        assert result.success is True
        assert result.metadata["has_context"] is False

    def test_execute_missing_task_description_returns_error(self):
        """Test that missing task_description returns validation error."""
        agent = PlannerAgent()

        result = agent.execute()

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "task_description is required" in result.error.message
        assert result.error.recoverable is False

    def test_execute_empty_task_description_returns_error(self):
        """Test that empty task_description returns validation error."""
        agent = PlannerAgent()

        result = agent.execute(task_description="")

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "task_description" in result.error.message

    def test_execute_whitespace_task_description_returns_error(self):
        """Test that whitespace-only task_description returns validation error."""
        agent = PlannerAgent()

        result = agent.execute(task_description="   \n\t  ")

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR

    @pytest.mark.parametrize(
        "invalid_task",
        [
            None,
            123,
            [],
            {},
            True,
        ],
    )
    def test_execute_invalid_task_description_type_returns_error(self, invalid_task):
        """Test that invalid task_description types return validation error."""
        agent = PlannerAgent()

        result = agent.execute(task_description=invalid_task)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR

    @pytest.mark.parametrize(
        "invalid_context",
        [
            "string",
            123,
            True,
        ],
    )
    def test_execute_invalid_context_type_returns_error(self, invalid_context):
        """Test that invalid context types return validation error."""
        agent = PlannerAgent()

        result = agent.execute(
            task_description="Valid task", context=invalid_context
        )

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "context must be a dictionary" in result.error.message

    def test_execute_metadata_contains_subtask_count(self):
        """Test that result metadata includes subtask count."""
        agent = PlannerAgent()

        result = agent.execute(task_description="Test task")

        assert "subtask_count" in result.metadata
        assert isinstance(result.metadata["subtask_count"], int)
        assert result.metadata["subtask_count"] > 0

    def test_execute_metadata_contains_task_description(self):
        """Test that result metadata includes original task description."""
        agent = PlannerAgent()
        task_desc = "Build feature"

        result = agent.execute(task_description=task_desc)

        assert result.metadata["task_description"] == task_desc

    def test_stateless_multiple_calls_independent(self):
        """Test that agent is stateless - multiple calls don't affect each other."""
        agent = PlannerAgent()

        result1 = agent.execute(task_description="Task 1")
        result2 = agent.execute(task_description="Task 2")

        assert result1.success is True
        assert result2.success is True
        assert result1.data["plan"]["task"] == "Task 1"
        assert result2.data["plan"]["task"] == "Task 2"
        # Different plan IDs prove independence
        assert result1.data["plan"]["plan_id"] != result2.data["plan"]["plan_id"]

    def test_execute_same_input_produces_consistent_structure(self):
        """Test that same input produces consistent output structure."""
        agent = PlannerAgent()
        task_desc = "Consistent task"

        result1 = agent.execute(task_description=task_desc)
        result2 = agent.execute(task_description=task_desc)

        # Structure should be the same
        assert result1.success == result2.success
        assert result1.data["plan"]["task"] == result2.data["plan"]["task"]
        assert len(result1.data["plan"]["subtasks"]) == len(
            result2.data["plan"]["subtasks"]
        )

    def test_subtasks_have_valid_structure(self):
        """Test that generated subtasks have valid structure."""
        agent = PlannerAgent()

        result = agent.execute(task_description="Test")

        subtasks = result.data["plan"]["subtasks"]
        assert len(subtasks) > 0

        for subtask in subtasks:
            assert "id" in subtask
            assert "description" in subtask
            assert "dependencies" in subtask
            assert "estimated_duration" in subtask
            assert "risk_level" in subtask

    def test_get_info_returns_planner_details(self):
        """Test that get_info returns correct agent information."""
        config = {"param": "value"}
        agent = PlannerAgent(name="test_planner", config=config)

        info = agent.get_info()

        assert info["name"] == "test_planner"
        assert info["type"] == "PlannerAgent"
        assert info["config"] == config
        assert "initialized_at" in info
