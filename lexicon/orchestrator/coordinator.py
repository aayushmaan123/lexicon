"""
Coordinator implementation for Phase 2.

The Coordinator orchestrates agent interactions and manages execution state.
Phase 2.3 adds the full execution loop with state machine and self-healing.
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from lexicon.agents import (
    Agent,
    AgentError,
    BuilderAgent,
    FixerAgent,
    PlannerAgent,
    ReviewerAgent,
)
from lexicon.orchestrator.execution import (
    ExecutionResult,
    ExecutionState,
    ExecutionTrace,
    RetryConfig,
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """
    Execution context managed by the Coordinator.

    This stores all state for an execution run.
    Agents are stateless; state lives here.

    Attributes:
        id: Unique execution identifier
        task: Original task description
        created_at: When execution started
        state: Current execution state
        metadata: Additional context
        plan: Execution plan from Planner (if planning succeeded)
        build_result: Build result from Builder (if building succeeded)
        review_report: Review report from Reviewer (if validation ran)
        fix_result: Fix result from Fixer (if fixing attempted)
        fix_attempts: Number of fix attempts made
    """

    id: str
    task: str
    created_at: str
    state: ExecutionState = ExecutionState.START
    metadata: Dict[str, Any] = field(default_factory=dict)
    plan: Optional[Any] = None
    build_result: Optional[Any] = None
    review_report: Optional[Any] = None
    fix_result: Optional[Any] = None
    fix_attempts: int = 0


class Coordinator:
    """
    Coordinator: Orchestrates agent interactions and manages execution flow.

    Responsibilities:
    - Agent lifecycle management
    - Task routing and sequencing
    - State transitions
    - Failure detection and recovery
    - Execution loop orchestration (Phase 2.3)

    Phase 2.3 adds deterministic execution loop with state machine and self-healing.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Coordinator.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agents: Dict[str, Agent] = {}
        self._initialized_at = datetime.now(UTC)
        self.retry_config = RetryConfig(
            max_attempts=self.config.get("max_retry_attempts", 3),
            backoff_factor=self.config.get("retry_backoff_factor", 1.5),
            initial_delay=self.config.get("initial_retry_delay", 1.0)
        )

    def register_agent(self, agent_type: str, agent: Agent) -> None:
        """
        Register an agent with the coordinator.

        Args:
            agent_type: Type identifier ("planner", "builder", "reviewer", "fixer")
            agent: Agent instance to register
        """
        if agent_type in self.agents:
            raise ValueError(f"Agent type '{agent_type}' already registered")
        
        self.agents[agent_type] = agent

    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """
        Get a registered agent by type.

        Args:
            agent_type: Type identifier

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(agent_type)

    def create_execution_context(self, task: str) -> ExecutionContext:
        """
        Create a new execution context for a task.

        Args:
            task: Task description

        Returns:
            ExecutionContext with unique ID
        """
        return ExecutionContext(
            id=str(uuid4()),
            task=task,
            created_at=datetime.now(UTC).isoformat(),
            state=ExecutionState.START,
            metadata={},
        )

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the coordinator and registered agents.

        Returns:
            Dictionary with coordinator metadata
        """
        return {
            "initialized_at": self._initialized_at.isoformat(),
            "registered_agents": list(self.agents.keys()),
            "agent_details": {
                agent_type: agent.get_info()
                for agent_type, agent in self.agents.items()
            },
            "config": self.config,
        }
    
    def execute(self, task: str, context_metadata: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a task using the multi-agent workflow.
        
        This implements the deterministic execution loop as defined in
        PHASE_2_EXECUTION_FLOW.md with sequential agent invocation and
        retry logic.
        
        Flow: START → PLANNING → BUILDING → VALIDATING → (FIXING if needed) → COMPLETED
        
        Args:
            task: Task description
            context_metadata: Optional additional context
            
        Returns:
            ExecutionResult with success status, trace, and artifacts
        """
        # Create execution context and trace
        ctx = self.create_execution_context(task)
        if context_metadata:
            ctx.metadata.update(context_metadata)
        
        trace = ExecutionTrace(
            execution_id=ctx.id,
            task_description=task,
            started_at=ctx.created_at
        )
        
        logger.info(f"Starting execution {ctx.id} for task: {task[:100]}...")
        
        try:
            # Execute sequential workflow
            self._planning_phase(ctx, trace)
            if ctx.state == ExecutionState.PLAN_FAILED:
                return self._create_failure_result(ctx, trace, "Planning failed")
            
            self._building_phase(ctx, trace)
            if ctx.state == ExecutionState.BUILD_FAILED:
                return self._create_failure_result(ctx, trace, "Building failed")
            
            self._validation_phase(ctx, trace)
            if ctx.state == ExecutionState.VALIDATION_FAILED:
                # Attempt fixing
                self._fixing_phase(ctx, trace)
                if ctx.state == ExecutionState.FIX_FAILED:
                    return self._create_failure_result(ctx, trace, "Fixing failed after max attempts")
            
            # If we reach here, validation passed (either initially or after fixing)
            if ctx.state == ExecutionState.VALIDATED:
                return self._create_success_result(ctx, trace)
            else:
                # Unexpected state
                return self._create_failure_result(ctx, trace, f"Unexpected state: {ctx.state}")
                
        except Exception as e:
            logger.error(f"Execution {ctx.id} failed with exception: {e}")
            trace.set_error(e, {"state": ctx.state.value})
            ctx.state = ExecutionState.ESCALATE
            return self._create_failure_result(ctx, trace, f"Execution exception: {str(e)}")
    
    def _planning_phase(self, ctx: ExecutionContext, trace: ExecutionTrace) -> None:
        """
        Planning phase: Analyze task and create execution plan.
        
        Updates ctx.state to PLANNING → PLAN_FAILED or continues to next phase.
        """
        prev_state = ctx.state
        ctx.state = ExecutionState.PLANNING
        trace.add_transition(prev_state, ctx.state, "Starting planning phase")
        
        logger.info(f"[{ctx.id}] Planning phase started")
        
        try:
            planner = self.agents.get("planner")
            if not planner:
                raise ValueError("Planner agent not registered")
            
            result = planner.execute(task_description=ctx.task)
            
            if not result.success:
                ctx.state = ExecutionState.PLAN_FAILED
                trace.add_transition(ExecutionState.PLANNING, ctx.state, 
                                   f"Planning failed: {result.error}")
                logger.warning(f"[{ctx.id}] Planning failed: {result.error}")
                return
            
            ctx.plan = result.data
            trace.add_agent_output("planner", result.data)
            logger.info(f"[{ctx.id}] Planning completed successfully")
            
        except Exception as e:
            ctx.state = ExecutionState.PLAN_FAILED
            trace.add_transition(ExecutionState.PLANNING, ctx.state, 
                               f"Planning exception: {str(e)}")
            trace.set_error(e, {"phase": "planning"})
            logger.error(f"[{ctx.id}] Planning exception: {e}")
    
    def _building_phase(self, ctx: ExecutionContext, trace: ExecutionTrace) -> None:
        """
        Building phase: Generate code and artifacts.
        
        Updates ctx.state to BUILDING → BUILD_FAILED or continues to next phase.
        """
        prev_state = ctx.state
        ctx.state = ExecutionState.BUILDING
        trace.add_transition(prev_state, ctx.state, "Starting building phase")
        
        logger.info(f"[{ctx.id}] Building phase started")
        
        try:
            builder = self.agents.get("builder")
            if not builder:
                raise ValueError("Builder agent not registered")
            
            # Pass task and plan to builder
            result = builder.execute(task=ctx.task, plan=ctx.plan)
            
            if not result.success:
                ctx.state = ExecutionState.BUILD_FAILED
                trace.add_transition(ExecutionState.BUILDING, ctx.state,
                                   f"Building failed: {result.error}")
                logger.warning(f"[{ctx.id}] Building failed: {result.error}")
                return
            
            ctx.build_result = result.data
            trace.add_agent_output("builder", result.data)
            logger.info(f"[{ctx.id}] Building completed successfully")
            
        except Exception as e:
            ctx.state = ExecutionState.BUILD_FAILED
            trace.add_transition(ExecutionState.BUILDING, ctx.state,
                               f"Building exception: {str(e)}")
            trace.set_error(e, {"phase": "building"})
            logger.error(f"[{ctx.id}] Building exception: {e}")
    
    def _validation_phase(self, ctx: ExecutionContext, trace: ExecutionTrace) -> None:
        """
        Validation phase: Run quality checks.
        
        Updates ctx.state to VALIDATING → VALIDATED or VALIDATION_FAILED.
        """
        prev_state = ctx.state
        ctx.state = ExecutionState.VALIDATING
        trace.add_transition(prev_state, ctx.state, "Starting validation phase")
        
        logger.info(f"[{ctx.id}] Validation phase started")
        
        try:
            reviewer = self.agents.get("reviewer")
            if not reviewer:
                raise ValueError("Reviewer agent not registered")
            
            # Pass build result to reviewer
            result = reviewer.execute(build_result=ctx.build_result)
            
            ctx.review_report = result.data
            trace.add_agent_output("reviewer", result.data)
            
            # Check if validation passed
            if result.success and result.data.get("overall_status") == "passed":
                ctx.state = ExecutionState.VALIDATED
                trace.add_transition(ExecutionState.VALIDATING, ctx.state,
                                   "All validations passed")
                logger.info(f"[{ctx.id}] Validation passed")
            else:
                ctx.state = ExecutionState.VALIDATION_FAILED
                trace.add_transition(ExecutionState.VALIDATING, ctx.state,
                                   "Validation checks failed")
                logger.warning(f"[{ctx.id}] Validation failed")
            
        except Exception as e:
            ctx.state = ExecutionState.VALIDATION_FAILED
            trace.add_transition(ExecutionState.VALIDATING, ctx.state,
                               f"Validation exception: {str(e)}")
            trace.set_error(e, {"phase": "validation"})
            logger.error(f"[{ctx.id}] Validation exception: {e}")
    
    def _fixing_phase(self, ctx: ExecutionContext, trace: ExecutionTrace) -> None:
        """
        Fixing phase: Attempt automated remediation with retry logic.
        
        Retries up to max_attempts times. Each iteration:
        1. Apply fix
        2. Re-run validation
        3. If passed → VALIDATED, else retry
        
        Updates ctx.state to FIXING → VALIDATED or FIX_FAILED.
        """
        logger.info(f"[{ctx.id}] Fixing phase started (max attempts: {self.retry_config.max_attempts})")
        
        fixer = self.agents.get("fixer")
        if not fixer:
            ctx.state = ExecutionState.FIX_FAILED
            trace.add_transition(ExecutionState.VALIDATION_FAILED, ctx.state,
                               "Fixer agent not registered")
            return
        
        reviewer = self.agents.get("reviewer")
        if not reviewer:
            ctx.state = ExecutionState.FIX_FAILED
            trace.add_transition(ExecutionState.VALIDATION_FAILED, ctx.state,
                               "Reviewer agent not registered")
            return
        
        while ctx.fix_attempts < self.retry_config.max_attempts:
            ctx.fix_attempts += 1
            prev_state = ctx.state
            ctx.state = ExecutionState.FIXING
            trace.add_transition(prev_state, ctx.state,
                               f"Fix attempt {ctx.fix_attempts}/{self.retry_config.max_attempts}")
            
            logger.info(f"[{ctx.id}] Fix attempt {ctx.fix_attempts}")
            
            try:
                # Attempt fix
                fix_result = fixer.execute(
                    review_report=ctx.review_report,
                    build_result=ctx.build_result
                )
                trace.add_agent_output("fixer", fix_result.data)
                
                if not fix_result.success:
                    logger.warning(f"[{ctx.id}] Fix attempt {ctx.fix_attempts} failed: {fix_result.error}")
                    continue
                
                ctx.fix_result = fix_result.data
                
                # Re-run validation
                ctx.state = ExecutionState.RETRY_VALIDATION
                trace.add_transition(ExecutionState.FIXING, ctx.state,
                                   f"Re-validating after fix attempt {ctx.fix_attempts}")
                
                revalidation = reviewer.execute(
                    build_result=fix_result.data.get("updated_build", ctx.build_result)
                )
                ctx.review_report = revalidation.data
                trace.add_agent_output("reviewer", revalidation.data)
                
                # Check if fixed
                if revalidation.success and revalidation.data.get("overall_status") == "passed":
                    ctx.state = ExecutionState.VALIDATED
                    ctx.build_result = fix_result.data.get("updated_build", ctx.build_result)
                    trace.add_transition(ExecutionState.RETRY_VALIDATION, ctx.state,
                                       f"Validation passed after fix attempt {ctx.fix_attempts}")
                    logger.info(f"[{ctx.id}] Fixed successfully on attempt {ctx.fix_attempts}")
                    return
                else:
                    logger.warning(f"[{ctx.id}] Validation still failing after fix attempt {ctx.fix_attempts}")
                
            except Exception as e:
                logger.error(f"[{ctx.id}] Fix attempt {ctx.fix_attempts} exception: {e}")
                trace.set_error(e, {"phase": "fixing", "attempt": ctx.fix_attempts})
        
        # Exhausted attempts
        ctx.state = ExecutionState.FIX_FAILED
        trace.add_transition(ExecutionState.FIXING, ctx.state,
                           f"Exhausted all {self.retry_config.max_attempts} fix attempts")
        logger.error(f"[{ctx.id}] Fixing failed after {self.retry_config.max_attempts} attempts")
    
    def _create_success_result(self, ctx: ExecutionContext, trace: ExecutionTrace) -> ExecutionResult:
        """Create successful execution result."""
        ctx.state = ExecutionState.COMPLETED
        trace.add_transition(ExecutionState.VALIDATED, ctx.state, "Execution completed successfully")
        trace.complete(ctx.state)
        
        logger.info(f"[{ctx.id}] Execution completed successfully")
        
        return ExecutionResult(
            success=True,
            execution_id=ctx.id,
            final_state=ctx.state,
            trace=trace,
            artifacts={
                "plan": ctx.plan,
                "build_result": ctx.build_result,
                "review_report": ctx.review_report,
                "fix_applied": ctx.fix_result is not None,
                "fix_attempts": ctx.fix_attempts
            }
        )
    
    def _create_failure_result(
        self,
        ctx: ExecutionContext,
        trace: ExecutionTrace,
        error_message: str
    ) -> ExecutionResult:
        """Create failed execution result."""
        ctx.state = ExecutionState.ESCALATE
        trace.complete(ctx.state)
        
        logger.error(f"[{ctx.id}] Execution failed: {error_message}")
        
        return ExecutionResult(
            success=False,
            execution_id=ctx.id,
            final_state=ctx.state,
            trace=trace,
            error_message=error_message
        )
