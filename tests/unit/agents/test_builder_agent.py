"""Unit tests for BuilderAgent."""

import pytest

from lexicon.agents.base import AgentErrorType
from lexicon.agents.builder import BuilderAgent


class TestBuilderAgent:
    """Test suite for BuilderAgent."""

    def test_init_with_default_name(self):
        """Test initialization with default name."""
        agent = BuilderAgent()

        assert agent.name == "builder"
        assert agent.config == {}

    def test_init_with_custom_name(self):
        """Test initialization with custom name."""
        agent = BuilderAgent(name="custom_builder")

        assert agent.name == "custom_builder"

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"code_style": "pep8", "test_framework": "pytest"}
        agent = BuilderAgent(config=config)

        assert agent.config == config

    def test_execute_with_valid_inputs(self):
        """Test execute with valid task and plan returns success."""
        agent = BuilderAgent()
        task = "Create user model"
        plan = {
            "plan_id": "plan-123",
            "subtasks": [
                {"id": "task-1", "description": "Define model fields"}
            ],
        }

        result = agent.execute(task=task, plan=plan)

        assert result.success is True
        assert "generated_files" in result.data
        assert "build_id" in result.data
        assert result.error is None

    def test_execute_creates_build_result(self):
        """Test that execute creates a proper build result."""
        agent = BuilderAgent()
        task = "Implement API"
        plan = {
            "plan_id": "plan-456",
            "subtasks": [{"id": "task-1", "description": "Create endpoint"}],
        }

        result = agent.execute(task=task, plan=plan)

        build_data = result.data
        assert "build_id" in build_data
        assert build_data["plan_id"] == "plan-456"
        assert build_data["task"] == task
        assert "generated_files" in build_data
        assert "modified_files" in build_data
        assert "status" in build_data
        assert "warnings" in build_data
        assert "created_at" in build_data

    def test_execute_with_context(self):
        """Test execute with additional context."""
        agent = BuilderAgent()
        context = {"language": "python", "framework": "flask"}
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Build API", plan=plan, context=context)

        assert result.success is True
        assert result.metadata["has_context"] is True

    def test_execute_without_context(self):
        """Test execute without context still works."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan)

        assert result.success is True
        assert result.metadata["has_context"] is False

    def test_execute_missing_task_returns_error(self):
        """Test that missing task returns validation error."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1"}

        result = agent.execute(plan=plan)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "task is required" in result.error.message
        assert result.error.recoverable is False

    def test_execute_missing_plan_returns_error(self):
        """Test that missing plan returns validation error."""
        agent = BuilderAgent()

        result = agent.execute(task="Test task")

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "plan is required" in result.error.message

    @pytest.mark.parametrize(
        "invalid_plan",
        [
            "string",
            123,
            True,
        ],
    )
    def test_execute_invalid_plan_type_returns_error(self, invalid_plan):
        """Test that invalid plan types return validation error."""
        agent = BuilderAgent()

        result = agent.execute(task="Task", plan=invalid_plan)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "plan must be a dictionary" in result.error.message

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
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan, context=invalid_context)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "context must be a dictionary" in result.error.message

    def test_execute_generates_files_for_subtasks(self):
        """Test that generated files correspond to subtasks."""
        agent = BuilderAgent()
        plan = {
            "plan_id": "p1",
            "subtasks": [
                {"id": "task-1", "description": "Module 1"},
                {"id": "task-2", "description": "Module 2"},
            ],
        }

        result = agent.execute(task="Task", plan=plan)

        # Should generate source + test file for each subtask
        files = result.data["generated_files"]
        assert len(files) == 4  # 2 subtasks * (1 source + 1 test)

    def test_execute_generated_files_have_required_fields(self):
        """Test that generated files have required structure."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": [{"id": "t1", "description": "Test"}]}

        result = agent.execute(task="Task", plan=plan)

        for file_info in result.data["generated_files"]:
            assert "path" in file_info
            assert "type" in file_info
            assert "lines" in file_info
            assert "purpose" in file_info
            assert "content" in file_info

    def test_execute_metadata_contains_file_count(self):
        """Test that result metadata includes file count."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": [{"id": "t1", "description": "T"}]}

        result = agent.execute(task="Task", plan=plan)

        assert "file_count" in result.metadata
        assert result.metadata["file_count"] == len(result.data["generated_files"])

    def test_execute_metadata_contains_task(self):
        """Test that result metadata includes task."""
        agent = BuilderAgent()
        task = "Build feature"
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task=task, plan=plan)

        assert result.metadata["task"] == task

    def test_stateless_multiple_calls_independent(self):
        """Test that agent is stateless - multiple calls don't affect each other."""
        agent = BuilderAgent()
        plan1 = {"plan_id": "p1", "subtasks": [{"id": "t1", "description": "T1"}]}
        plan2 = {"plan_id": "p2", "subtasks": [{"id": "t2", "description": "T2"}]}

        result1 = agent.execute(task="Task 1", plan=plan1)
        result2 = agent.execute(task="Task 2", plan=plan2)

        assert result1.success is True
        assert result2.success is True
        assert result1.data["task"] == "Task 1"
        assert result2.data["task"] == "Task 2"
        assert result1.data["build_id"] != result2.data["build_id"]

    def test_execute_same_input_produces_consistent_structure(self):
        """Test that same input produces consistent output structure."""
        agent = BuilderAgent()
        task = "Consistent task"
        plan = {"plan_id": "p1", "subtasks": []}

        result1 = agent.execute(task=task, plan=plan)
        result2 = agent.execute(task=task, plan=plan)

        # Structure should be the same
        assert result1.success == result2.success
        assert result1.data["task"] == result2.data["task"]
        assert result1.data["plan_id"] == result2.data["plan_id"]

    def test_execute_with_empty_subtasks(self):
        """Test execute with empty subtasks list."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan)

        assert result.success is True
        assert result.data["generated_files"] == []

    def test_execute_build_status_is_success(self):
        """Test that build result status is success."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan)

        assert result.data["status"] == "success"

    def test_execute_modified_files_is_empty(self):
        """Test that modified_files is empty in Phase 2.1."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan)

        assert result.data["modified_files"] == []

    def test_execute_warnings_is_empty(self):
        """Test that warnings list is empty in Phase 2.1."""
        agent = BuilderAgent()
        plan = {"plan_id": "p1", "subtasks": []}

        result = agent.execute(task="Task", plan=plan)

        assert result.data["warnings"] == []

    def test_get_info_returns_builder_details(self):
        """Test that get_info returns correct agent information."""
        config = {"param": "value"}
        agent = BuilderAgent(name="test_builder", config=config)

        info = agent.get_info()

        assert info["name"] == "test_builder"
        assert info["type"] == "BuilderAgent"
        assert info["config"] == config
        assert "initialized_at" in info

    def test_execute_recoverable_on_execution_error(self):
        """Test that execution errors are marked as recoverable."""
        agent = BuilderAgent()
        # Simulate an error by passing a plan that will cause an issue
        plan = {"plan_id": "p1", "subtasks": None}  # None will cause iteration error

        result = agent.execute(task="Task", plan=plan)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.EXECUTION_ERROR
        assert result.error.recoverable is True
