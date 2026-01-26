"""
Planner Agent implementation.

The Planner Agent decomposes complex tasks into structured execution plans.
"""

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lexicon.agents.base import Agent, AgentErrorType, AgentResult


@dataclass
class Task:
    """
    A single atomic task in an execution plan.

    Attributes:
        id: Unique task identifier
        description: What the task accomplishes
        dependencies: IDs of tasks that must complete first
        estimated_duration: Time estimate (e.g., "30m", "2h")
        risk_level: Assessment of task complexity/risk
    """

    id: str
    description: str
    dependencies: List[str]
    estimated_duration: str
    risk_level: str  # "low", "medium", "high"


@dataclass
class ExecutionPlan:
    """
    Complete execution plan produced by the Planner.

    Attributes:
        plan_id: Unique plan identifier
        task: Original task description
        subtasks: List of atomic tasks
        total_estimated_duration: Combined time estimate
        overall_risk: Risk assessment for entire plan
        created_at: When the plan was created
    """

    plan_id: str
    task: str
    subtasks: List[Task]
    total_estimated_duration: str
    overall_risk: str
    created_at: str


class PlannerAgent(Agent):
    """
    Planner Agent: Decomposes complex tasks into structured execution plans.

    Responsibilities:
    - Parse and understand task requirements
    - Break down into atomic subtasks
    - Identify dependencies between tasks
    - Estimate complexity and duration
    - Flag potential risks or blockers

    NOT Responsible For:
    - Writing code or generating artifacts
    - Making architectural decisions
    - Executing tasks
    - Validating outputs
    """

    def __init__(self, name: str = "planner", config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Planner Agent.

        Args:
            name: Agent identifier
            config: Optional configuration
        """
        super().__init__(name, config)

    def execute(self, **kwargs) -> AgentResult:
        """
        Create an execution plan from a task description.

        Args:
            task_description (str): High-level task to decompose
            context (Optional[Dict]): Additional project context
            memory_hints (Optional[List[Dict]]): Hints from memory (Phase 2.2)

        Returns:
            AgentResult with ExecutionPlan or error
        """
        task_description = kwargs.get("task_description")
        context = kwargs.get("context", {})
        
        # Validate inputs
        if not task_description:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="task_description is required",
                context={"kwargs": kwargs},
                recoverable=False,
                suggested_action="Provide a valid task_description parameter",
            )

        if not isinstance(task_description, str) or len(task_description.strip()) == 0:
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="task_description must be a non-empty string",
                context={"task_description": task_description},
                recoverable=False,
                suggested_action="Provide a descriptive task",
            )
        
        if context and not isinstance(context, dict):
            return self._create_error_result(
                error_type=AgentErrorType.VALIDATION_ERROR,
                message="context must be a dictionary",
                context={"context_type": type(context).__name__},
                recoverable=False,
                suggested_action="Provide context as a dictionary",
            )

        try:
            # Create execution plan
            # NOTE: In Phase 2.1, this is a simple decomposition
            # In Phase 2.2+, this will query memory for patterns
            plan = self._decompose_task(task_description, context)

            return self._create_success_result(
                data={"plan": asdict(plan)},
                metadata={
                    "task_description": task_description,
                    "subtask_count": len(plan.subtasks),
                    "has_context": bool(context),
                },
            )

        except Exception as e:
            return self._create_error_result(
                error_type=AgentErrorType.EXECUTION_ERROR,
                message=f"Failed to create execution plan: {str(e)}",
                context={"task_description": task_description, "error": str(e)},
                recoverable=False,
                suggested_action="Review task description and retry",
            )

    def _decompose_task(
        self, task_description: str, context: Dict[str, Any]
    ) -> ExecutionPlan:
        """
        Decompose a task into subtasks.

        This is a simplified implementation for Phase 2.1.
        In later phases, this will use LLM and memory to create better plans.

        Args:
            task_description: Task to decompose
            context: Additional context

        Returns:
            ExecutionPlan with subtasks
        """
        plan_id = str(uuid4())
        
        # Simple heuristic decomposition
        # In Phase 2.2+, this will be replaced with LLM-based planning
        # Phase 2.1: Always creates a single task as a placeholder
        num_subtasks = 1
        subtasks = [
            Task(
                id=f"task-{i+1}",
                description=f"Step {i+1}: {task_description}",
                dependencies=[f"task-{i}"] if i > 0 else [],
                estimated_duration="30m",
                risk_level="low",
            )
            for i in range(num_subtasks)
        ]

        return ExecutionPlan(
            plan_id=plan_id,
            task=task_description,
            subtasks=subtasks,
            total_estimated_duration="30m",
            overall_risk="low",
            created_at=datetime.now(UTC).isoformat(),
        )
