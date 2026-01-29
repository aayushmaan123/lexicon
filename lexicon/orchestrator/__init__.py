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

# Phase 3.2.1: Multi-PRD Intake
from lexicon.orchestrator.multi_prd_intake import (
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
    "MultiPRDInput",
    "MultiPRDIntake",
    "MultiPRDMetadata",
    "NormalizedPRDCollection",
]
