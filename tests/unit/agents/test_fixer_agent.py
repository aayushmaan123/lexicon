"""Unit tests for FixerAgent."""

import pytest

from lexicon.agents.base import AgentErrorType
from lexicon.agents.fixer import (
    ESCALATION_KEYWORDS,
    FIXABLE_KEYWORDS,
    FixerAgent,
)


class TestFixerAgent:
    """Test suite for FixerAgent."""

    def test_init_with_default_name(self):
        """Test initialization with default name."""
        agent = FixerAgent()

        assert agent.name == "fixer"
        assert agent.config == {}

    def test_init_with_custom_name(self):
        """Test initialization with custom name."""
        agent = FixerAgent(name="custom_fixer")

        assert agent.name == "custom_fixer"

    def test_init_with_config(self):
        """Test initialization with configuration."""
        config = {"auto_fix": True, "max_iterations": 5}
        agent = FixerAgent(config=config)

        assert agent.config == config

    def test_execute_with_valid_inputs(self):
        """Test execute with valid review report and build result returns success."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r-123",
            "checks": [{"name": "test", "status": "passed", "issues": []}],
        }
        build_result = {"build_id": "b-123", "generated_files": []}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.success is True
        assert "fix_id" in result.data
        assert "fixes_applied" in result.data
        assert result.error is None

    def test_execute_creates_fix_result(self):
        """Test that execute creates a proper fix result."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r-456",
            "checks": [{"name": "check1", "status": "passed", "issues": []}],
        }
        build_result = {"build_id": "b-456"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        fix_data = result.data
        assert "fix_id" in fix_data
        assert fix_data["review_id"] == "r-456"
        assert "status" in fix_data
        assert "fixes_applied" in fix_data
        assert isinstance(fix_data["fixes_applied"], list)
        assert "escalated_issues" in fix_data
        assert "attempts" in fix_data
        assert "max_attempts" in fix_data
        assert "escalated" in fix_data
        assert "created_at" in fix_data

    def test_execute_with_max_attempts(self):
        """Test execute with custom max_attempts parameter."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report,
            build_result=build_result,
            max_attempts=5,
        )

        assert result.success is True
        assert result.data["max_attempts"] == 5

    def test_execute_default_max_attempts(self):
        """Test execute uses default max_attempts of 3."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.data["max_attempts"] == 3

    def test_execute_missing_review_report_returns_error(self):
        """Test that missing review_report returns validation error."""
        agent = FixerAgent()
        build_result = {"build_id": "b1"}

        result = agent.execute(build_result=build_result)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "review_report is required" in result.error.message
        assert result.error.recoverable is False

    def test_execute_missing_build_result_returns_error(self):
        """Test that missing build_result returns validation error."""
        agent = FixerAgent()
        review_report = {"review_id": "r1"}

        result = agent.execute(review_report=review_report)

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "build_result is required" in result.error.message

    @pytest.mark.parametrize(
        "invalid_review",
        [
            "string",
            123,
            True,
        ],
    )
    def test_execute_invalid_review_report_type_returns_error(self, invalid_review):
        """Test that invalid review_report types return validation error."""
        agent = FixerAgent()
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=invalid_review, build_result=build_result
        )

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "review_report must be a dictionary" in result.error.message

    @pytest.mark.parametrize(
        "invalid_attempts",
        [
            0,
            -1,
            "string",
            [],
            {},
            None,
        ],
    )
    def test_execute_invalid_max_attempts_returns_error(self, invalid_attempts):
        """Test that invalid max_attempts values return validation error."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report,
            build_result=build_result,
            max_attempts=invalid_attempts,
        )

        assert result.success is False
        assert result.error.error_type == AgentErrorType.VALIDATION_ERROR
        assert "max_attempts must be a positive integer" in result.error.message

    def test_execute_no_issues_success_status(self):
        """Test that no issues results in success status."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [{"name": "check1", "status": "passed", "issues": []}],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.data["status"] == "success"
        assert result.data["escalated"] is False
        assert len(result.data["fixes_applied"]) == 0
        assert len(result.data["escalated_issues"]) == 0

    def test_execute_fixable_warning_issues(self):
        """Test that warning issues are identified as fixable."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "check1",
                    "status": "warning",
                    "issues": [
                        {
                            "file": "test.py",
                            "severity": "warning",
                            "message": "Missing documentation",
                        }
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.data["status"] == "success"
        assert len(result.data["fixes_applied"]) > 0
        assert result.data["escalated"] is False

    def test_execute_fixable_error_with_keywords(self):
        """Test that errors with fixable keywords are identified as fixable."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "check1",
                    "status": "failed",
                    "issues": [
                        {
                            "file": "test.py",
                            "severity": "error",
                            "message": "Field is missing",
                        }
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert len(result.data["fixes_applied"]) > 0

    def test_execute_escalation_with_keywords(self):
        """Test that errors with escalation keywords are escalated."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "security_check",
                    "status": "failed",
                    "issues": [
                        {
                            "file": "test.py",
                            "severity": "error",
                            "message": "Critical security vulnerability detected",
                        }
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.data["escalated"] is True
        assert result.data["status"] == "escalated"
        assert len(result.data["escalated_issues"]) > 0

    def test_execute_fixes_have_required_structure(self):
        """Test that applied fixes have required structure."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "check1",
                    "status": "warning",
                    "issues": [
                        {
                            "file": "file.py",
                            "severity": "warning",
                            "message": "Issue",
                        }
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        for fix in result.data["fixes_applied"]:
            assert "issue_id" in fix
            assert "check" in fix
            assert "file" in fix
            assert "message" in fix
            assert "change" in fix
            assert "severity" in fix

    def test_execute_metadata_contains_review_id(self):
        """Test that result metadata includes review_id."""
        agent = FixerAgent()
        review_report = {"review_id": "r-999", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.metadata["review_id"] == "r-999"

    def test_execute_metadata_contains_fixes_count(self):
        """Test that result metadata includes fixes count."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert "fixes_count" in result.metadata
        assert result.metadata["fixes_count"] == len(result.data["fixes_applied"])

    def test_execute_metadata_contains_attempts(self):
        """Test that result metadata includes attempts."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert "attempts" in result.metadata
        assert result.metadata["attempts"] == result.data["attempts"]

    def test_execute_metadata_contains_escalated(self):
        """Test that result metadata includes escalated flag."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert "escalated" in result.metadata
        assert result.metadata["escalated"] == result.data["escalated"]

    def test_stateless_multiple_calls_independent(self):
        """Test that agent is stateless - multiple calls don't affect each other."""
        agent = FixerAgent()
        review1 = {"review_id": "r1", "checks": []}
        review2 = {"review_id": "r2", "checks": []}
        build1 = {"build_id": "b1"}
        build2 = {"build_id": "b2"}

        result1 = agent.execute(review_report=review1, build_result=build1)
        result2 = agent.execute(review_report=review2, build_result=build2)

        assert result1.success is True
        assert result2.success is True
        assert result1.data["review_id"] == "r1"
        assert result2.data["review_id"] == "r2"
        assert result1.data["fix_id"] != result2.data["fix_id"]

    def test_execute_same_input_produces_consistent_structure(self):
        """Test that same input produces consistent output structure."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": []}
        build_result = {"build_id": "b1"}

        result1 = agent.execute(
            review_report=review_report, build_result=build_result
        )
        result2 = agent.execute(
            review_report=review_report, build_result=build_result
        )

        # Structure should be the same
        assert result1.success == result2.success
        assert result1.data["review_id"] == result2.data["review_id"]
        assert result1.data["status"] == result2.data["status"]

    def test_execute_blocker_count_affects_status(self):
        """Test that blocker count affects escalation status."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "check1",
                    "status": "failed",
                    "issues": [
                        {
                            "file": "test.py",
                            "severity": "error",
                            "message": "Incompatible version",
                        }
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        # "incompatible" is an escalation keyword
        assert result.data["escalated"] is True

    def test_execute_recoverable_on_execution_error(self):
        """Test that execution errors are marked as recoverable."""
        agent = FixerAgent()
        review_report = {"review_id": "r1", "checks": None}  # Will cause error
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        assert result.success is False
        assert result.error.error_type == AgentErrorType.EXECUTION_ERROR
        assert result.error.recoverable is True

    def test_get_info_returns_fixer_details(self):
        """Test that get_info returns correct agent information."""
        config = {"param": "value"}
        agent = FixerAgent(name="test_fixer", config=config)

        info = agent.get_info()

        assert info["name"] == "test_fixer"
        assert info["type"] == "FixerAgent"
        assert info["config"] == config
        assert "initialized_at" in info

    def test_fixable_keywords_constant(self):
        """Test that FIXABLE_KEYWORDS constant is defined."""
        assert isinstance(FIXABLE_KEYWORDS, list)
        assert "missing" in FIXABLE_KEYWORDS
        assert "incomplete" in FIXABLE_KEYWORDS

    def test_escalation_keywords_constant(self):
        """Test that ESCALATION_KEYWORDS constant is defined."""
        assert isinstance(ESCALATION_KEYWORDS, list)
        assert "critical" in ESCALATION_KEYWORDS
        assert "security" in ESCALATION_KEYWORDS

    def test_execute_mixed_issues_partial_escalation(self):
        """Test that mixed issues result in partial escalation."""
        agent = FixerAgent()
        review_report = {
            "review_id": "r1",
            "checks": [
                {
                    "name": "check1",
                    "status": "failed",
                    "issues": [
                        {
                            "file": "test1.py",
                            "severity": "warning",
                            "message": "Missing field",
                        },
                        {
                            "file": "test2.py",
                            "severity": "error",
                            "message": "Critical security issue",
                        },
                    ],
                }
            ],
        }
        build_result = {"build_id": "b1"}

        result = agent.execute(
            review_report=review_report, build_result=build_result
        )

        # Should have both fixes and escalations
        assert len(result.data["fixes_applied"]) > 0
        assert len(result.data["escalated_issues"]) > 0
        assert result.data["escalated"] is True
