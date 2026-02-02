"""
Lexicon Phase 2 Orchestrator.

The orchestrator manages agent interactions and execution flow.
Phase 2.3 adds execution loop with state machine and self-healing.
Phase 3.2.1 adds multi-PRD intake for orchestrating multiple PRDs.
"""

from lexicon.orchestrator.coordinator import Coordinator, ExecutionContext
from lexicon.orchestrator.execution import (
    ExecutionResult,
    ExecutionState,
    ExecutionTrace,
    RetryConfig,
    StateTransition,
)

# Phase 3.2.2: Cross-PRD Resolver
from lexicon.orchestrator.cross_prd_resolver import (
    CircularDependencyError,
    CrossPRDResolver,
    DependencyEdge,
    MissingDependencyError,
    ResolvedDependencyGraph,
    SelfDependencyError,
)

# Phase 3.2.3: Conflict Detector
from lexicon.orchestrator.conflict_detector import (
    ConflictDetector,
    ConflictReport,
    OutputConflict,
    OutputConflictError,
    ResourceConflict,
    ResourceConflictError,
)

# Phase 3.2.4: Global Plan Builder
from lexicon.orchestrator.global_plan_builder import (
    ExecutionWave,
    GlobalExecutionPlan,
    GlobalPlanBuilder,
)

# Phase 3.2.5: Scheduler
from lexicon.orchestrator.scheduler import ExecutionError, Scheduler

# Phase 3.3: Feedback Loop
from lexicon.orchestrator.feedback_loop import (
    ExecutionReport,
    FeedbackCollector,
    TaskExecutionRecord,
    TaskExecutionStatus,
)

# Phase 3.2.1: Multi-PRD Intake
from lexicon.orchestrator.multi_prd_intake import (
    DuplicateTaskIDError,
    MultiPRDInput,
    MultiPRDIntake,
    MultiPRDMetadata,
    NormalizedPRDCollection,
)

__all__ = [
    # Phase 2.3 exports
    "Coordinator",
    "ExecutionContext",
    "ExecutionResult",
    "ExecutionState",
    "ExecutionTrace",
    "RetryConfig",
    "StateTransition",
    # Phase 3.2.1 exports
    "DuplicateTaskIDError",
    "MultiPRDInput",
    "MultiPRDIntake",
    "MultiPRDMetadata",
    "NormalizedPRDCollection",
    # Phase 3.2.2 exports
    "CircularDependencyError",
    "CrossPRDResolver",
    "DependencyEdge",
    "MissingDependencyError",
    "ResolvedDependencyGraph",
    "SelfDependencyError",
    # Phase 3.2.3 exports
    "ConflictDetector",
    "ConflictReport",
    "OutputConflict",
    "OutputConflictError",
    "ResourceConflict",
    "ResourceConflictError",
    # Phase 3.2.4 exports
    "ExecutionWave",
    "GlobalExecutionPlan",
    "GlobalPlanBuilder",
    # Phase 3.2.5 exports
    "ExecutionError",
    "Scheduler",
    # Phase 3.3 exports
    "ExecutionReport",
    "FeedbackCollector",
    "TaskExecutionRecord",
    "TaskExecutionStatus",
]
