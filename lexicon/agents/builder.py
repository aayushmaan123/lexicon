"""
Builder Agent implementation.

The Builder Agent generates code and artifacts based on approved execution plans.
"""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lexicon.agents.base import Agent, AgentErrorType, AgentResult


class BuilderAgent(Agent):
    """
    Builder Agent: Generates code, configuration, and artifacts.

    Responsibilities:
    - Generate syntactically correct code
    - Follow existing code patterns and style
    - Create corresponding test files
    - Update documentation
    - Respect project structure and conventions

    NOT Responsible For:
    - Testing the generated code
    - Reviewing code quality
    - Deploying artifacts
    - Making architectural choices (follows plan)
    """

    def __init__(self, name: str = "builder", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Builder Agent.

        Args:
            name: Agent identifier
            config: Optional configuration
        """
        super().__init__(name, config)

    def execute(self, **kwargs) -> AgentResult:
        """
        Generate artifacts based on task and plan.

        Args:
            task (str): Task description to implement
            plan (Dict): Execution plan with subtasks
            context (Optional[Dict]): Additional codebase context

        Returns:
            AgentResult with generated_files list or error
        """
        task = kwargs.get("task")
        plan = kwargs.get("plan")
        context = kwargs.get("context", {})

        # Validate inputs
        if not task:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="task is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid task parameter",
            )

        if not plan:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="plan is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid execution plan",
            )

        if not isinstance(plan, dict):
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="plan must be a dictionary",
                context={"plan_type": type(plan).__name__},
                recoverable=False,
                suggested_action="Ensure plan is properly formatted",
            )

        try:
            # Generate artifacts
            # NOTE: In Phase 2.1, this creates placeholder file structures
            # In Phase 2.2+, this will use LLM to generate actual code
            build_result = self._generate_artifacts(task, plan, context)

            return self._create_success_result(
                data=build_result,
                metadata={
                    "task": task,
                    "file_count": len(build_result.get("generated_files", [])),
                    "has_context": bool(context),
                },
            )

        except Exception as e:
            return self._create_error_result(
                error_type=AgentErrorType.EXECUTION_ERROR,
                message=f"Failed to generate artifacts: {str(e)}",
                context={"task": task, "error": str(e)},
                recoverable=True,
                suggested_action="Review task and plan, then retry",
            )

    def _generate_artifacts(
        self, task: str, plan: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate code and artifact placeholders.

        This is a simplified implementation for Phase 2.1.
        In later phases, this will use LLM to generate actual code.

        Args:
            task: Task to implement
            plan: Execution plan
            context: Additional context

        Returns:
            Build result with generated files
        """
        build_id = str(uuid4())
        plan_id = plan.get("plan_id", "unknown")
        subtasks = plan.get("subtasks", [])

        # Create placeholder files based on subtasks
        # In Phase 2.1, we just document what would be created
        generated_files = []

        for i, subtask in enumerate(subtasks):
            # Generate a source file placeholder
            generated_files.append({
                "path": f"generated/module_{i+1}.py",
                "type": "python_module",
                "lines": 50,
                "purpose": subtask.get("description", "Generated module"),
                "content": f"# Placeholder for: {subtask.get('description', 'N/A')}",
            })

            # Generate corresponding test file placeholder
            generated_files.append({
                "path": f"tests/test_module_{i+1}.py",
                "type": "test",
                "lines": 30,
                "purpose": f"Tests for module_{i+1}",
                "content": f"# Test placeholder for: {subtask.get('description', 'N/A')}",
            })

        return {
            "build_id": build_id,
            "plan_id": plan_id,
            "task": task,
            "generated_files": generated_files,
            "modified_files": [],
            "status": "success",
            "warnings": [],
            "created_at": datetime.now(UTC).isoformat(),
        }
