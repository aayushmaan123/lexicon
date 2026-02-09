# Phase 3 Architecture - Multi-PRD Orchestration & Advanced Execution

## Overview

Phase 3 extends the complete Phase 2 architecture (stateless agents, deterministic execution loops, RAG-based memory, PRD → execution pipeline) to enable advanced PRD-driven workflows, multi-PRD orchestration, feedback-based learning, and enhanced observability.

**Status**: Design Document  
**Dependencies**: Phase 1 (complete), Phase 2.1-2.4 (complete)  
**Version**: 1.0

---

## Core Objectives

Phase 3 introduces three major capabilities:

1. **Advanced PRD Handling**: Support for nested tasks, optional subtasks, cross-project dependencies, and enhanced validation
2. **Multi-PRD Orchestration**: Coordinate execution across multiple PRDs with conflict detection and dependency management
3. **Feedback & Learning**: Track outcomes in RAG memory, generate metrics, provide informational improvement suggestions

---

## Architectural Principles

### Backward Compatibility (Non-Negotiable)

- **Phase 1**: No changes to document analysis, contract review, legal research, or RAG pipeline
- **Phase 2.1**: Agents remain stateless; no modifications to Planner, Builder, Reviewer, Fixer
- **Phase 2.2**: RAG memory access control unchanged (agents READ-only, coordinator WRITE-only)
- **Phase 2.3**: Execution loop and self-healing mechanisms untouched
- **Phase 2.4**: PRD pipeline remains functional; Phase 3 extends, not replaces

### Determinism & Control

- **Coordinator Authority**: All execution flows through Coordinator.execute()
- **No Autonomous Planning**: PRDs define tasks; agents execute tasks
- **Deterministic Execution**: No dynamic agent creation or conditional branching outside PRD-defined tasks
- **Stateless Agents**: All execution state managed by Coordinator

### RAG Memory Integration

- **Context, Not Control**: RAG provides historical data for informational suggestions
- **Read-Only for Agents**: Agents query RAG for patterns; never write
- **Write-Only via Coordinator**: Only Coordinator stores execution outcomes
- **No Decision-Making**: RAG data informs suggestions but doesn't drive execution logic

---

## Component Architecture

### Phase 3.1: Advanced PRD Handler

```
lexicon/
└── pipeline/
    ├── advanced_prd_models.py      # Extended PRD models (nested tasks, subtasks)
    ├── advanced_prd_parser.py      # Multi-level PRD parsing
    ├── advanced_prd_validator.py   # Enhanced validation logic
    └── prd_decomposer.py           # Task decomposition with nesting
```

**Responsibilities**:
- Parse nested task structures (parent tasks with subtasks)
- Support optional vs. required subtasks
- Validate cross-project dependencies
- Handle priority levels and resource annotations
- Decompose complex PRDs into execution-ready task graphs

**Key Features**:
- Backward compatible with Phase 2.4 flat PRD structure
- Nested task representation: `parent_id` field in PRDRequirement
- Optional subtasks: `optional: bool` flag
- Cross-project links: `external_dependencies: List[str]`
- Priority levels: `priority: RequirementPriority` (HIGH, MEDIUM, LOW)

### Phase 3.2: Multi-PRD Orchestrator

```
lexicon/
└── orchestrator/
    ├── multi_prd_scheduler.py      # Cross-PRD task scheduling
    ├── conflict_detector.py        # Resource/output conflict detection
    ├── parallel_executor.py        # Parallel execution for independent tasks
    └── execution_aggregator.py     # Multi-PRD result aggregation
```

**Responsibilities**:
- Schedule tasks across multiple PRDs
- Detect resource conflicts (e.g., two tasks modifying the same file)
- Enable parallel execution for independent tasks
- Aggregate results and execution traces
- Maintain backward compatibility with single-PRD execution

**Key Features**:
- **Sequential Execution**: Default mode for dependent tasks
- **Parallel Execution**: Only for tasks with no dependencies or conflicts
- **Conflict Detection**: Analyze task outputs to prevent collisions
- **Execution Coordination**: Reuse Phase 2.3 execution loop per task
- **Result Aggregation**: Combine ExecutionTrace objects from multiple PRDs

### Phase 3.3: Feedback & Learning System

```
lexicon/
└── feedback/
    ├── outcome_tracker.py          # Track execution outcomes
    ├── metrics_collector.py        # Collect execution metrics
    ├── suggestion_generator.py     # Generate improvement suggestions
    └── rag_integration.py          # Write outcomes to RAG memory
```

**Responsibilities**:
- Track task success/failure rates
- Measure execution duration and retry frequency
- Store outcomes in RAG memory for pattern analysis
- Generate informational suggestions for PRD improvement
- Provide metrics dashboards (optional future API)

**Key Features**:
- **Outcome Tracking**: Success rate, failure patterns, fix effectiveness
- **Metrics Collection**: Execution time, agent performance, retry counts
- **RAG Storage**: Write execution summaries to RAG (coordinator-only)
- **Suggestion Generation**: Informational recommendations based on historical data
- **No Autonomous Changes**: Suggestions are advisory; humans decide

---

## Data Flow

### Phase 3.1: Advanced PRD Processing

```
Advanced PRD (nested tasks, optional subtasks)
    ↓
Advanced Parser → Validate structure & dependencies
    ↓
Decomposer → Flatten to execution-ready task graph
    ↓
Phase 2.4 PRDProcessor → Topological sort
    ↓
Phase 2.3 Coordinator → Execute
```

### Phase 3.2: Multi-PRD Execution

```
Multiple PRDs
    ↓
Multi-PRD Scheduler → Merge task graphs
    ↓
Conflict Detector → Identify resource/output conflicts
    ↓
Parallel Executor → Execute independent tasks in parallel
    ↓
Sequential Executor → Execute dependent tasks sequentially
    ↓
Aggregator → Combine results
```

### Phase 3.3: Feedback Loop

```
Execution Result
    ↓
Outcome Tracker → Record success/failure
    ↓
Metrics Collector → Calculate statistics
    ↓
RAG Integration → Store in memory (coordinator-only)
    ↓
Suggestion Generator → Query RAG for patterns
    ↓
Informational Suggestions (advisory only)
```

---

## Technology Stack

- **Python 3.11+**: Maintain existing version
- **Pydantic**: Extended models for nested PRDs
- **AsyncIO**: Parallel task execution (optional, with sync fallback)
- **NetworkX**: Task graph analysis for conflict detection
- **Existing Dependencies**: No new external dependencies for core functionality

---

## Testing Strategy

### Unit Tests
- Advanced PRD parsing and validation
- Conflict detection algorithms
- Metrics calculation
- Suggestion generation logic

### Integration Tests
- Multi-PRD scheduling
- Parallel vs. sequential execution
- RAG memory integration
- End-to-end feedback loop

### E2E Tests
- Complete multi-PRD workflow
- Nested task execution
- Feedback-driven iteration

**Target**: 80%+ code coverage across all Phase 3 modules

---

## Performance Targets

- **Advanced PRD Parsing**: < 5 seconds for PRDs with 100+ tasks
- **Conflict Detection**: < 2 seconds for 50 tasks across 5 PRDs
- **Parallel Execution**: 2-3x speedup for fully independent tasks
- **Metrics Collection**: < 1 second overhead per task
- **Suggestion Generation**: < 5 seconds for historical analysis

---

## Security & Compliance

- **No Secrets in RAG**: Maintain Phase 2.2 constraints
- **Audit Trail**: All multi-PRD executions fully logged
- **Deterministic Replay**: Execution traces enable exact reproduction
- **No Autonomous Actions**: All suggestions require human approval

---

## Backward Compatibility Validation

### Phase 2.4 PRD Compatibility
- All Phase 2.4 PRDs execute unchanged
- Flat PRD structure remains fully supported
- No breaking changes to PRD models

### Phase 2.3 Execution Loop
- Single-task execution path unchanged
- ExecutionTrace format remains compatible
- Retry and self-healing logic untouched

### Phase 2.2 RAG Memory
- Access control unchanged (READ for agents, WRITE for coordinator)
- Storage scope unchanged (no secrets, no execution state)
- Existing retrieval patterns work unchanged

---

## Migration Path

Phase 3 is **purely additive**. Existing Phase 1-2 functionality continues working without modification:

1. **Phase 2.4 Users**: Can continue using flat PRDs indefinitely
2. **Advanced Features**: Opt-in to nested PRDs via new models
3. **Multi-PRD**: Opt-in to multi-PRD orchestration via new scheduler
4. **Feedback**: Opt-in to outcome tracking via configuration flag

---

## Out of Scope (Explicitly)

- **LLM-Based PRD Generation**: PRDs remain human-authored
- **Autonomous PRD Modification**: Suggestions are advisory; no auto-edits
- **Real-Time Execution**: Batch execution only (no streaming updates)
- **Cloud Infrastructure**: Local execution only
- **Multi-Tenancy**: Single-user/project execution
- **Authentication/Authorization**: No user management

---

## Phase 3 Success Criteria

### Phase 3.1
- ✅ Nested PRDs parsed and validated correctly
- ✅ Cross-project dependencies supported
- ✅ Backward compatible with Phase 2.4 flat PRDs
- ✅ 100% test passing rate

### Phase 3.2
- ✅ Multi-PRD scheduling without conflicts
- ✅ Parallel execution for independent tasks
- ✅ Sequential execution for dependent tasks
- ✅ Full execution trace aggregation

### Phase 3.3
- ✅ Execution outcomes stored in RAG
- ✅ Metrics tracked and reportable
- ✅ Suggestions generated from historical data
- ✅ No autonomous changes (advisory only)

---

## Future Extensibility (Phase 4+)

Phase 3 architecture supports future enhancements:

- **Real-Time Monitoring**: WebSocket-based execution updates
- **Advanced Analytics**: ML-based pattern recognition
- **Multi-Tenant Support**: User isolation and permissions
- **Cloud Deployment**: Distributed task execution
- **API Enhancements**: GraphQL interface for complex queries

---

## Summary

Phase 3 maintains strict backward compatibility while enabling:
- Advanced PRD handling with nested tasks and cross-project dependencies
- Multi-PRD orchestration with conflict detection and parallel execution
- Feedback-based learning with RAG integration for informational suggestions

All features are opt-in, deterministic, and fully auditable.
