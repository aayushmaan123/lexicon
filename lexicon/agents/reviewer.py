"""
Reviewer Agent implementation.

The Reviewer Agent validates generated code against quality standards.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lexicon.agents.base import Agent, AgentErrorType, AgentResult

# File type constants
FILE_TYPE_PYTHON_MODULE = "python_module"
FILE_TYPE_TEST = "test"

# System-level check identifier (not a file path)
SYSTEM_LEVEL_CHECK = "system"


class ReviewerAgent(Agent):
    """
    Reviewer Agent: Validates generated code against quality standards.

    Responsibilities:
    - Run linting and formatting checks
    - Execute type checking
    - Verify test coverage
    - Check for security vulnerabilities
    - Validate against architecture patterns
    - Ensure backward compatibility
    - Check documentation completeness

    NOT Responsible For:
    - Fixing issues (delegates to Fixer)
    - Making subjective design decisions
    - Generating new code
    """

    def __init__(self, name: str = "reviewer", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Reviewer Agent.

        Args:
            name: Agent identifier
            config: Optional configuration
        """
        super().__init__(name, config)

    def execute(self, **kwargs) -> AgentResult:
        """
        Review build artifacts against quality standards.

        Args:
            build_result (Dict): Build artifacts from BuilderAgent
            standards (Optional[Dict]): Quality standards to enforce

        Returns:
            AgentResult with review_report containing checks list
        """
        build_result = kwargs.get("build_result")
        standards = kwargs.get("standards", {})

        # Validate inputs
        if not build_result:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="build_result is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid build_result parameter",
            )

        if not isinstance(build_result, dict):
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="build_result must be a dictionary",
                context={"build_result_type": type(build_result).__name__},
                recoverable=False,
                suggested_action="Ensure build_result is properly formatted",
            )

        try:
            # Perform validation
            # NOTE: In Phase 2.1, this performs basic checks
            # In Phase 2.2+, this will run actual linters, type checkers, etc.
            review_report = self._validate_artifacts(build_result, standards)

            return self._create_success_result(
                data=review_report,
                metadata={
                    "build_id": build_result.get("build_id", "unknown"),
                    "check_count": len(review_report.get("checks", [])),
                    "overall_status": review_report.get("overall_status"),
                },
            )

        except Exception as e:
            return self._create_error_result(
                error_type=AgentErrorType.EXECUTION_ERROR,
                message=f"Failed to review artifacts: {str(e)}",
                context={"build_result": build_result, "error": str(e)},
                recoverable=True,
                suggested_action="Review build artifacts and retry",
            )

    def _validate_artifacts(
        self, build_result: Dict[str, Any], standards: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate build artifacts against quality standards.

        This is a simplified implementation for Phase 2.1.
        In later phases, this will run actual validation tools.

        Args:
            build_result: Build artifacts to validate
            standards: Quality standards

        Returns:
            Review report with pass/fail status
        """
        review_id = str(uuid4())
        build_id = build_result.get("build_id", "unknown")
        generated_files = build_result.get("generated_files", [])

        # Run basic validation checks
        checks = []

        # Check 1: Files exist
        file_check = self._check_files_exist(generated_files)
        checks.append(file_check)

        # Check 2: Test coverage (check if test files are present)
        coverage_check = self._check_test_coverage(generated_files)
        checks.append(coverage_check)

        # Check 3: File structure (basic validation)
        structure_check = self._check_file_structure(generated_files)
        checks.append(structure_check)

        # Determine overall status
        failed_checks = [c for c in checks if c["status"] == "failed"]
        warning_checks = [c for c in checks if c["status"] == "warning"]

        overall_status = "passed"
        can_proceed = True

        if failed_checks:
            overall_status = "failed"
            can_proceed = False
        elif warning_checks:
            overall_status = "warning"

        return {
            "review_id": review_id,
            "build_id": build_id,
            "overall_status": overall_status,
            "checks": checks,
            "can_proceed": can_proceed,
            "blocker_count": len(failed_checks),
            "warning_count": len(warning_checks),
            "created_at": datetime.now(UTC).isoformat(),
        }

    def _check_files_exist(self, generated_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if generated files are properly defined."""
        issues = []

        for file_info in generated_files:
            if not file_info.get("path"):
                issues.append({
                    "file": "unknown",
                    "severity": "error",
                    "message": "File path is missing",
                })

        status = "failed" if issues else "passed"

        return {
            "name": "file_existence",
            "status": status,
            "issues": issues,
        }

    def _check_test_coverage(self, generated_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check if test files are present for source files."""
        issues = []

        source_files = [f for f in generated_files if f.get("type") == FILE_TYPE_PYTHON_MODULE]
        test_files = [f for f in generated_files if f.get("type") == FILE_TYPE_TEST]

        # Simple heuristic: should have at least one test file per source file
        if source_files and len(test_files) < len(source_files):
            issues.append({
                "file": SYSTEM_LEVEL_CHECK,
                "severity": "warning",
                "message": f"Test coverage may be incomplete: {len(test_files)} test files for {len(source_files)} source files",
            })

        status = "warning" if issues else "passed"

        return {
            "name": "test_coverage",
            "status": status,
            "issues": issues,
        }

    def _check_file_structure(self, generated_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate basic file structure."""
        issues = []

        for file_info in generated_files:
            # Check that files have required fields
            if not file_info.get("type"):
                issues.append({
                    "file": file_info.get("path", "unknown"),
                    "severity": "error",
                    "message": "File type is missing",
                })

            if not file_info.get("purpose"):
                issues.append({
                    "file": file_info.get("path", "unknown"),
                    "severity": "warning",
                    "message": "File purpose is not documented",
                })

        # Count errors vs warnings
        error_issues = [i for i in issues if i.get("severity") == "error"]
        status = "failed" if error_issues else ("warning" if issues else "passed")

        return {
            "name": "file_structure",
            "status": status,
            "issues": issues,
        }
