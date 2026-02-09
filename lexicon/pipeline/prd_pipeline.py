"""
PRD Pipeline - end-to-end orchestration for PRD → Task → Execution.

This module provides the complete pipeline from PRD ingestion to
execution via the Coordinator.
"""

import logging
from typing import Any, Dict, List, Optional
from lexicon.orchestrator.coordinator import Coordinator
from lexicon.orchestrator.execution import ExecutionResult
from lexicon.pipeline.prd_models import PRD, PRDTask, TaskStatus
from lexicon.pipeline.prd_parser import PRDParser
from lexicon.pipeline.prd_processor import PRDProcessor
from lexicon.pipeline.prd_validator import PRDValidator

logger = logging.getLogger(__name__)


class PRDPipeline:
    """
    End-to-end pipeline for PRD processing and execution.
    
    The pipeline orchestrates:
    1. PRD parsing (from dict/JSON/Markdown)
    2. PRD validation
    3. Task generation from requirements
    4. Sequential task execution via Coordinator
    5. Result aggregation
    
    The pipeline is deterministic and does not make autonomous decisions.
    All execution flows through the existing Phase 2.3 Coordinator.
    """

    def __init__(self, coordinator: Coordinator):
        """
        Initialize the PRD pipeline.
        
        Args:
            coordinator: Phase 2.3 Coordinator for task execution
        """
        self.coordinator = coordinator
        self.parser = PRDParser()
        self.validator = PRDValidator()
        self.processor = PRDProcessor()
        
        logger.info("PRD Pipeline initialized")

    def execute_from_dict(
        self, prd_dict: Dict[str, Any], validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a PRD from a Python dictionary.
        
        Args:
            prd_dict: Dictionary containing PRD data
            validate: Whether to validate PRD before execution
            
        Returns:
            Dictionary with execution results
            
        Raises:
            ValueError: If PRD is invalid
        """
        logger.info("Parsing PRD from dictionary")
        prd = self.parser.parse_from_dict(prd_dict)
        return self.execute(prd, validate=validate)

    def execute_from_json(
        self, prd_json: str, validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a PRD from a JSON string.
        
        Args:
            prd_json: JSON string containing PRD data
            validate: Whether to validate PRD before execution
            
        Returns:
            Dictionary with execution results
            
        Raises:
            ValueError: If PRD is invalid
        """
        logger.info("Parsing PRD from JSON")
        prd = self.parser.parse_from_json(prd_json)
        return self.execute(prd, validate=validate)

    def execute_from_markdown(
        self, prd_markdown: str, validate: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a PRD from a Markdown document.
        
        Args:
            prd_markdown: Markdown text containing PRD
            validate: Whether to validate PRD before execution
            
        Returns:
            Dictionary with execution results
            
        Raises:
            ValueError: If PRD is invalid
        """
        logger.info("Parsing PRD from Markdown")
        prd = self.parser.parse_from_markdown(prd_markdown)
        return self.execute(prd, validate=validate)

    def execute(self, prd: PRD, validate: bool = True) -> Dict[str, Any]:
        """
        Execute a PRD through the complete pipeline.
        
        Steps:
        1. Validate PRD (if requested)
        2. Convert requirements to tasks
        3. Execute tasks sequentially via Coordinator
        4. Aggregate results
        
        Args:
            prd: PRD object to execute
            validate: Whether to validate PRD before execution
            
        Returns:
            Dictionary with execution results:
            {
                "prd_title": str,
                "prd_version": str,
                "total_requirements": int,
                "total_tasks": int,
                "completed_tasks": int,
                "failed_tasks": int,
                "task_results": List[Dict],
                "validation_result": Optional[Dict],
                "success": bool
            }
            
        Raises:
            ValueError: If PRD validation fails
        """
        logger.info(
            f"Executing PRD: {prd.metadata.title} v{prd.metadata.version}"
        )
        
        # Step 1: Validation
        validation_result = None
        if validate:
            logger.info("Validating PRD")
            validation_result = self.validator.validate(prd)
            
            if not validation_result.is_valid:
                error_msg = "; ".join(validation_result.errors)
                logger.error(f"PRD validation failed: {error_msg}")
                raise ValueError(f"PRD validation failed: {error_msg}")
            
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"PRD validation warning: {warning}")
        
        # Step 2: Process requirements into tasks
        logger.info(f"Processing {len(prd.requirements)} requirements into tasks")
        tasks = self.processor.process(prd)
        logger.info(f"Generated {len(tasks)} tasks in dependency order")
        
        # Step 3: Execute tasks sequentially
        task_results = []
        completed_count = 0
        failed_count = 0
        
        for task in tasks:
            logger.info(f"Executing task {task.task_id} (req: {task.requirement_id})")
            
            task.mark_in_progress()
            
            try:
                # Execute via Coordinator (Phase 2.3)
                execution_result = self.coordinator.execute(
                    task_description=task.description,
                    context=task.context
                )
                
                # Update task status based on execution result
                if execution_result.success:
                    task.mark_completed()
                    completed_count += 1
                    logger.info(f"Task {task.task_id} completed successfully")
                else:
                    task.mark_failed()
                    failed_count += 1
                    logger.error(
                        f"Task {task.task_id} failed: {execution_result.final_state}"
                    )
                
                # Record result
                task_results.append({
                    "task_id": task.task_id,
                    "requirement_id": task.requirement_id,
                    "status": task.status.value,
                    "execution_id": execution_result.execution_id,
                    "success": execution_result.success,
                    "final_state": execution_result.final_state.value,
                    "error": execution_result.error,
                })
                
            except Exception as e:
                task.mark_failed()
                failed_count += 1
                logger.error(f"Task {task.task_id} raised exception: {e}")
                
                task_results.append({
                    "task_id": task.task_id,
                    "requirement_id": task.requirement_id,
                    "status": task.status.value,
                    "success": False,
                    "error": str(e),
                })
        
        # Step 4: Aggregate results
        result = {
            "prd_title": prd.metadata.title,
            "prd_version": prd.metadata.version,
            "prd_author": prd.metadata.author,
            "total_requirements": len(prd.requirements),
            "total_tasks": len(tasks),
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "task_results": task_results,
            "success": failed_count == 0,
        }
        
        if validation_result:
            result["validation_result"] = {
                "is_valid": validation_result.is_valid,
                "errors": validation_result.errors,
                "warnings": validation_result.warnings,
            }
        
        logger.info(
            f"PRD execution complete: {completed_count}/{len(tasks)} tasks succeeded"
        )
        
        return result
