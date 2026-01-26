"""Unit tests for ReviewerAgent."""

import pytest

from lexicon.agents.base import AgentErrorType
from lexicon.agents.reviewer import (
    FILE_TYPE_PYTHON_MODULE,
    FILE_TYPE_TEST,
    SYSTEM_LEVEL_CHECK,
    ReviewerAgent,
)


class TestReviewerAgent:
    """Test suite for ReviewerAgent."""

    def test_init_with_default_name(self):
        """Test initialization with default name."""
        agent = ReviewerAgent()

        assert agent.name == "reviewer"
        assert agent.config == {}

    def test_init_with_custom_name(self):
        """Test initialization with custom name."""
        agent = ReviewerAgent(name="custom_reviewer")

        assert agent.name == "custom_reviewer"

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"strictness": "high", "rules": ["pep8"]}
        agent = ReviewerAgent(config=config)

        assert agent.config == config

    def test_execute_with_valid_build_result(self):
        """Test execute with valid build result returns success."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b-123",
            "generated_files": [
                {
                    "path": "module.py",
                    "type": FILE_TYPE_PYTHON_MODULE,
                    "purpose": "Main module",
                }
            ],
        }

        result = agent.execute(build_result=build_result)

        assert result.success is True
        assert "review_id" in result.data
        assert "checks" in result.data
        assert result.error is None

    def test_execute_creates_review_report(self):
        """Test that execute creates a proper review report."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b-456",
            "generated_files": [
                {"path": "test.py", "type": FILE_TYPE_TEST, "purpose": "Tests"}
            ],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        assert "review_id" in review
        assert review["build_id"] == "b-456"
        assert "overall_status" in review
        assert "checks" in review
        assert isinstance(review["checks"], list)
        assert "can_proceed" in review
        assert "blocker_count" in review
        assert "warning_count" in review
        assert "created_at" in review

    def test_execute_with_standards(self):
        """Test execute with quality standards."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b1", "generated_files": []}
        standards = {"min_coverage": 80, "max_complexity": 10}

        result = agent.execute(build_result=build_result, standards=standards)

        assert result.success is True

    def test_execute_missing_build_result_returns_error(self):
        """Test that missing build_result returns validation error."""
        agent = ReviewerAgent()

        result = agent.execute()

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "build_result is required" in result.error.message
        assert result.error.recoverable is False

    @pytest.mark.parametrize(
        "invalid_build",
        [
            "string",
            123,
            True,
        ],
    )
    def test_execute_invalid_build_result_type_returns_error(self, invalid_build):
        """Test that invalid build_result types return validation error."""
        agent = ReviewerAgent()

        result = agent.execute(build_result=invalid_build)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "build_result must be a dictionary" in result.error.message

    def test_execute_all_checks_pass(self):
        """Test that all checks pass for valid files."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [
                {
                    "path": "module.py",
                    "type": FILE_TYPE_PYTHON_MODULE,
                    "purpose": "Module",
                },
                {"path": "test.py", "type": FILE_TYPE_TEST, "purpose": "Tests"},
            ],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        assert review["overall_status"] == "passed"
        assert review["can_proceed"] is True
        assert review["blocker_count"] == 0

    def test_execute_file_existence_check_fails_missing_path(self):
        """Test that file existence check fails for files without path."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [{"type": FILE_TYPE_PYTHON_MODULE, "purpose": "Test"}],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        assert review["overall_status"] == "failed"
        assert review["can_proceed"] is False
        assert review["blocker_count"] > 0

        # Find the file_existence check
        file_check = next(c for c in review["checks"] if c["name"] == "file_existence")
        assert file_check["status"] == "failed"
        assert len(file_check["issues"]) > 0

    def test_execute_test_coverage_check_warning(self):
        """Test that test coverage check warns for insufficient tests."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [
                {
                    "path": "module1.py",
                    "type": FILE_TYPE_PYTHON_MODULE,
                    "purpose": "M1",
                },
                {
                    "path": "module2.py",
                    "type": FILE_TYPE_PYTHON_MODULE,
                    "purpose": "M2",
                },
                {"path": "test.py", "type": FILE_TYPE_TEST, "purpose": "Tests"},
            ],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        # Should be warning status
        assert review["overall_status"] == "warning"
        assert review["warning_count"] > 0

        coverage_check = next(
            c for c in review["checks"] if c["name"] == "test_coverage"
        )
        assert coverage_check["status"] == "warning"

    def test_execute_file_structure_check_fails_missing_type(self):
        """Test that file structure check fails for files without type."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [{"path": "file.py", "purpose": "Test"}],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        assert review["overall_status"] == "failed"

        struct_check = next(
            c for c in review["checks"] if c["name"] == "file_structure"
        )
        assert struct_check["status"] == "failed"
        error_issues = [i for i in struct_check["issues"] if i["severity"] == "error"]
        assert len(error_issues) > 0

    def test_execute_file_structure_check_warns_missing_purpose(self):
        """Test that file structure check warns for files without purpose."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [{"path": "file.py", "type": FILE_TYPE_PYTHON_MODULE}],
        }

        result = agent.execute(build_result=build_result)

        review = result.data
        struct_check = next(
            c for c in review["checks"] if c["name"] == "file_structure"
        )
        assert struct_check["status"] == "warning"
        warning_issues = [
            i for i in struct_check["issues"] if i["severity"] == "warning"
        ]
        assert len(warning_issues) > 0

    def test_execute_metadata_contains_build_id(self):
        """Test that result metadata includes build_id."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b-999", "generated_files": []}

        result = agent.execute(build_result=build_result)

        assert result.metadata["build_id"] == "b-999"

    def test_execute_metadata_contains_check_count(self):
        """Test that result metadata includes check count."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b1", "generated_files": []}

        result = agent.execute(build_result=build_result)

        assert "check_count" in result.metadata
        assert result.metadata["check_count"] == len(result.data["checks"])

    def test_execute_metadata_contains_overall_status(self):
        """Test that result metadata includes overall status."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b1", "generated_files": []}

        result = agent.execute(build_result=build_result)

        assert "overall_status" in result.metadata
        assert result.metadata["overall_status"] == result.data["overall_status"]

    def test_stateless_multiple_calls_independent(self):
        """Test that agent is stateless - multiple calls don't affect each other."""
        agent = ReviewerAgent()
        build1 = {"build_id": "b1", "generated_files": []}
        build2 = {"build_id": "b2", "generated_files": []}

        result1 = agent.execute(build_result=build1)
        result2 = agent.execute(build_result=build2)

        assert result1.success is True
        assert result2.success is True
        assert result1.data["build_id"] == "b1"
        assert result2.data["build_id"] == "b2"
        assert result1.data["review_id"] != result2.data["review_id"]

    def test_execute_same_input_produces_consistent_structure(self):
        """Test that same input produces consistent output structure."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [
                {"path": "f.py", "type": FILE_TYPE_PYTHON_MODULE, "purpose": "P"}
            ],
        }

        result1 = agent.execute(build_result=build_result)
        result2 = agent.execute(build_result=build_result)

        # Structure should be the same
        assert result1.success == result2.success
        assert result1.data["build_id"] == result2.data["build_id"]
        assert len(result1.data["checks"]) == len(result2.data["checks"])

    def test_execute_empty_generated_files(self):
        """Test execute with empty generated_files list."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b1", "generated_files": []}

        result = agent.execute(build_result=build_result)

        assert result.success is True
        review = result.data
        # Should still run checks
        assert len(review["checks"]) > 0

    def test_execute_checks_list_has_required_structure(self):
        """Test that checks list items have required structure."""
        agent = ReviewerAgent()
        build_result = {"build_id": "b1", "generated_files": []}

        result = agent.execute(build_result=build_result)

        for check in result.data["checks"]:
            assert "name" in check
            assert "status" in check
            assert "issues" in check
            assert isinstance(check["issues"], list)

    def test_execute_issue_structure_for_errors(self):
        """Test that issues have required structure."""
        agent = ReviewerAgent()
        build_result = {
            "build_id": "b1",
            "generated_files": [{"type": FILE_TYPE_PYTHON_MODULE}],  # Missing path
        }

        result = agent.execute(build_result=build_result)

        file_check = next(c for c in result.data["checks"] if c["name"] == "file_existence")
        if file_check["issues"]:
            issue = file_check["issues"][0]
            assert "file" in issue
            assert "severity" in issue
            assert "message" in issue

    def test_execute_recoverable_on_execution_error(self):
        """Test that execution errors are marked as recoverable."""
        agent = ReviewerAgent()
        # Simulate an error by passing invalid structure
        build_result = {"build_id": "b1", "generated_files": None}

        result = agent.execute(build_result=build_result)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.EXECUTION_ERROR
        assert result.error.recoverable is True

    def test_get_info_returns_reviewer_details(self):
        """Test that get_info returns correct agent information."""
        config = {"param": "value"}
        agent = ReviewerAgent(name="test_reviewer", config=config)

        info = agent.get_info()

        assert info["name"] == "test_reviewer"
        assert info["type"] == "ReviewerAgent"
        assert info["config"] == config
        assert "initialized_at" in info

    def test_system_level_check_constant(self):
        """Test that SYSTEM_LEVEL_CHECK constant is defined."""
        assert SYSTEM_LEVEL_CHECK == "system"

    def test_file_type_constants(self):
        """Test that file type constants are defined."""
        assert FILE_TYPE_PYTHON_MODULE == "python_module"
        assert FILE_TYPE_TEST == "test"
