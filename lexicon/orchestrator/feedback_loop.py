
"""
Phase 3.3 Feedback Loop for Multi-PRD Orchestration.

This module captures execution results and provides structured feedback
to PRD models.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC

class TaskExecutionStatus(str, Enum):
    """Execution status of a task."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

@dataclass(frozen=True)
class TaskExecutionRecord:
    """Immutable record of a single task execution."""
    task_id: str
    prd_id: str
    wave_number: int
    status: TaskExecutionStatus
    result: Any = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

@dataclass(frozen=True)
class ExecutionReport:
    """Immutable final report of a plan execution."""
    orchestration_id: str
    records: List[TaskExecutionRecord]
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    skipped_tasks: int
    started_at: datetime
    completed_at: datetime

class FeedbackCollector:
    """
    Aggregates execution results and generates reports.
    """

    def __init__(self, orchestration_id: str):
        """
        Initialize the collector for an orchestration session.
        
        Args:
            orchestration_id: Unique ID for the orchestration run.
        """
        self.orchestration_id = orchestration_id
        self.records: List[TaskExecutionRecord] = []
        self.started_at = datetime.now(UTC)

    def add_record(self, record: TaskExecutionRecord):
        """Add an execution record to the collection."""
        self.records.append(record)

    def generate_report(self) -> ExecutionReport:
        """
        Generate the final execution report.
        
        Returns:
            An immutable ExecutionReport.
        """
        completed_at = datetime.now(UTC)
        
        success = len([r for r in self.records if r.status == TaskExecutionStatus.SUCCESS])
        failed = len([r for r in self.records if r.status == TaskExecutionStatus.FAILED])
        skipped = len([r for r in self.records if r.status == TaskExecutionStatus.SKIPPED])
        
        return ExecutionReport(
            orchestration_id=self.orchestration_id,
            records=self.records,
            total_tasks=len(self.records),
            successful_tasks=success,
            failed_tasks=failed,
            skipped_tasks=skipped,
            started_at=self.started_at,
            completed_at=completed_at
        )

    def get_prd_metrics(self, prd_id: str) -> Dict[str, Any]:
        """
        Get execution metrics for a specific PRD.
        
        Args:
            prd_id: The PRD identifier.
            
        Returns:
            A dictionary of metrics.
        """
        prd_records = [r for r in self.records if r.prd_id == prd_id]
        if not prd_records:
            return {}
            
        success = len([r for r in prd_records if r.status == TaskExecutionStatus.SUCCESS])
        return {
            "total_tasks": len(prd_records),
            "successful_tasks": success,
            "failed_tasks": len([r for r in prd_records if r.status == TaskExecutionStatus.FAILED]),
            "skipped_tasks": len([r for r in prd_records if r.status == TaskExecutionStatus.SKIPPED]),
            "success_rate": success / len(prd_records) if prd_records else 0
        }
