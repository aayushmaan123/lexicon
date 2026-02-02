
"""
Phase 3.2.5 Scheduler for Multi-PRD Orchestration.

This module orchestrates the execution of waves from a GlobalExecutionPlan.
It ensures deterministic ordering and fail-fast behavior.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, UTC

from lexicon.pipeline.advanced_prd_models import DecomposedTask
from lexicon.orchestrator.global_plan_builder import GlobalExecutionPlan, ExecutionWave

# Configure logging
logger = logging.getLogger(__name__)

class ExecutionError(Exception):
    """Raised when a task or wave execution fails critically."""
    pass

class Scheduler:
    """
    Orchestrates the execution of a GlobalExecutionPlan.
    """

    def __init__(self, plan: GlobalExecutionPlan):
        """
        Initialize the scheduler with an execution plan.
        
        Args:
            plan: The global execution plan to execute.
        """
        self.plan = plan
        self.task_results: Dict[str, Any] = {}
        self.wave_results: Dict[int, Any] = {}

    def execute(self, task_executor: Callable[[DecomposedTask], Any]) -> Dict[str, Any]:
        """
        Execute the plan wave by wave.
        
        Args:
            task_executor: A function that takes a DecomposedTask and returns its result.
            
        Returns:
            A dictionary of task_id to execution result.
            
        Raises:
            ExecutionError: If any task execution fails.
        """
        logger.info(f"Starting execution of plan {self.plan.orchestration_id}")
        logger.info(f"Total waves: {len(self.plan.waves)}, Total tasks: {self.plan.total_tasks}")

        for wave in self.plan.waves:
            logger.info(f"--- Starting Wave {wave.wave_number} ({len(wave.tasks)} tasks) ---")
            
            # Tasks in a wave are pre-sorted lexicographically for determinism by GlobalPlanBuilder.
            for task in wave.tasks:
                logger.info(f"Executing task: {task.task_id} (PRD requirement: {task.requirement_id})")
                
                try:
                    result = task_executor(task)
                    self.task_results[task.task_id] = result
                    logger.info(f"Task {task.task_id} completed successfully.")
                except Exception as e:
                    logger.error(f"Critical failure in task {task.task_id}: {str(e)}")
                    raise ExecutionError(f"Task {task.task_id} failed: {str(e)}") from e
            
            logger.info(f"--- Wave {wave.wave_number} completed. ---")

        logger.info(f"Plan {self.plan.orchestration_id} execution finished.")
        return self.task_results
