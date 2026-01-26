"""
Fixer Agent implementation.

The Fixer Agent automatically resolves validation failures and runtime errors.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lexicon.agents.base import Agent, AgentErrorType, AgentResult

# Keywords for identifying fixable issues
FIXABLE_KEYWORDS = ["missing", "incomplete", "not documented"]

# Keywords for identifying issues requiring escalation
ESCALATION_KEYWORDS = ["incompatible", "conflict", "critical", "security"]


class FixerAgent(Agent):
    """
    Fixer Agent: Automatically resolves validation failures.

    Responsibilities:
    - Analyze validation failures
    - Query memory for similar past failures
    - Apply minimal corrective changes
    - Re-run validations to confirm fix
    - Document fix patterns for memory
    - Escalate complex issues that can't be auto-fixed

    NOT Responsible For:
    - Making major architectural changes
    - Bypassing validation checks
    - Rewriting large sections of code
    - Making subjective improvements
    """

    def __init__(self, name: str = "fixer", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Fixer Agent.

        Args:
            name: Agent identifier
            config: Optional configuration
        """
        super().__init__(name, config)

    def execute(self, **kwargs) -> AgentResult:
        """
        Attempt to fix validation failures automatically.

        Args:
            review_report (Dict): Review report from ReviewerAgent
            build_result (Dict): Original build result
            max_attempts (int): Maximum fix attempts (default: 3)

        Returns:
            AgentResult with fixes_applied list or escalation notice
        """
        review_report = kwargs.get("review_report")
        build_result = kwargs.get("build_result")
        max_attempts = kwargs.get("max_attempts", 3)

        # Validate inputs
        if not review_report:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="review_report is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid review_report parameter",
            )

        if not build_result:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="build_result is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid build_result parameter",
            )

        if not isinstance(review_report, dict):
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="review_report must be a dictionary",
                context={"review_report_type": type(review_report).__name__},
                recoverable=False,
                suggested_action="Ensure review_report is properly formatted",
            )

        if not isinstance(max_attempts, int) or max_attempts < 1:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="max_attempts must be a positive integer",
                context={"max_attempts": max_attempts},
                recoverable=False,
                suggested_action="Provide a valid max_attempts value",
            )

        try:
            # Attempt to fix issues
            # NOTE: In Phase 2.1, this determines if issues are fixable
            # In Phase 2.2+, this will apply actual fixes using LLM
            fix_result = self._apply_fixes(review_report, build_result, max_attempts)

            return self._create_success_result(
                data=fix_result,
                metadata={
                    "review_id": review_report.get("review_id", "unknown"),
                    "fixes_count": len(fix_result.get("fixes_applied", [])),
                    "attempts": fix_result.get("attempts", 0),
                    "escalated": fix_result.get("escalated", False),
                },
            )

        except Exception as e:
            return self._create_error_result(
                error_type=AgentErrorType.EXECUTION_ERROR,
                message=f"Failed to apply fixes: {str(e)}",
                context={"review_report": review_report, "error": str(e)},
                recoverable=True,
                suggested_action="Review failure details and retry",
            )

    def _apply_fixes(
        self,
        review_report: Dict[str, Any],
        build_result: Dict[str, Any],
        max_attempts: int,
    ) -> Dict[str, Any]:
        """
        Apply fixes to validation failures.

        This is a simplified implementation for Phase 2.1.
        In later phases, this will use LLM to apply actual fixes.

        Args:
            review_report: Review report with issues
            build_result: Original build result
            max_attempts: Maximum fix attempts

        Returns:
            Fix result with applied fixes or escalation
        """
        fix_id = str(uuid4())
        review_id = review_report.get("review_id", "unknown")
        checks = review_report.get("checks", [])

        # Collect all issues that need fixing
        all_issues = []
        for check in checks:
            if check.get("status") in ["failed", "warning"]:
                issues = check.get("issues", [])
                for issue in issues:
                    all_issues.append({
                        "check_name": check.get("name"),
                        "issue": issue,
                    })

        # Categorize issues by severity
        error_issues = [
            i for i in all_issues if i["issue"].get("severity") == "error"
        ]
        warning_issues = [
            i for i in all_issues if i["issue"].get("severity") == "warning"
        ]

        # Determine if issues are fixable
        # In Phase 2.1, we use simple heuristics
        fixable_issues = self._identify_fixable_issues(error_issues, warning_issues)
        escalated_issues = self._identify_escalated_issues(error_issues, warning_issues)

        fixes_applied = []
        # NOTE: In Phase 2.1, we use a single attempt for simplicity.
        # In Phase 2.2+, this will iterate up to max_attempts with actual fixes.
        attempts = 1

        # For fixable issues, document the fixes that would be applied
        for issue_info in fixable_issues:
            fix = {
                "issue_id": str(uuid4()),
                "check": issue_info["check_name"],
                "file": issue_info["issue"].get("file", "unknown"),
                "message": issue_info["issue"].get("message", ""),
                "change": "Placeholder fix for Phase 2.1",
                "severity": issue_info["issue"].get("severity", "unknown"),
            }
            fixes_applied.append(fix)

        # Determine overall status
        escalated = len(escalated_issues) > 0
        status = "escalated" if escalated else "success"

        return {
            "fix_id": fix_id,
            "review_id": review_id,
            "status": status,
            "fixes_applied": fixes_applied,
            "escalated_issues": escalated_issues,
            "attempts": attempts,
            "max_attempts": max_attempts,
            "escalated": escalated,
            "created_at": datetime.now(UTC).isoformat(),
        }

    def _identify_fixable_issues(
        self, error_issues: List[Dict[str, Any]], warning_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify issues that can be automatically fixed.

        For Phase 2.1, we use simple heuristics.
        """
        fixable = []

        # Warnings are generally fixable
        fixable.extend(warning_issues)

        # Some errors are fixable (e.g., missing fields)
        for issue_info in error_issues:
            issue = issue_info["issue"]
            message = issue.get("message", "").lower()

            # Simple heuristic: missing/incomplete items are often fixable
            if any(keyword in message for keyword in FIXABLE_KEYWORDS):
                fixable.append(issue_info)

        return fixable

    def _identify_escalated_issues(
        self, error_issues: List[Dict[str, Any]], warning_issues: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify issues that require escalation.

        For Phase 2.1, we use simple heuristics.
        """
        escalated = []

        # Issues that aren't easily fixable
        for issue_info in error_issues:
            issue = issue_info["issue"]
            message = issue.get("message", "").lower()

            # Complex errors require escalation
            if any(keyword in message for keyword in ESCALATION_KEYWORDS):
                escalated.append({
                    "check": issue_info["check_name"],
                    "issue": issue,
                    "reason": "Complex issue requiring manual intervention",
                })

        return escalated
