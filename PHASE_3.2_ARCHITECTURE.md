# Phase 3.2: Multi-PRD Orchestration - Architecture Design

## Document Status

**Status**: Design Document (Pending Approval)  
**Phase**: 3.2 - Multi-PRD Orchestration  
**Dependencies**: Phase 2.3 (Execution Loop), Phase 2.4 (PRD Pipeline), Phase 3.1 (Advanced PRD Handling)  
**Version**: 1.0  
**Last Updated**: 2026-01-28

---

## Executive Summary

Phase 3.2 introduces **Multi-PRD Orchestration**, enabling the system to safely coordinate execution of multiple PRDs (both Phase 2.4 flat and Phase 3.1 nested) while maintaining determinism, backward compatibility, and coordinator authority.

**Critical Constraint**: Phase 3.2 is **orchestration-only**. It produces validated execution plans but does NOT execute tasks. Execution remains with the Phase 2.3 Coordinator.

---

## Objectives

### Primary Goals

1. **Multi-PRD Intake**: Accept and normalize multiple PRDs (flat + nested)
2. **Cross-PRD Dependency Resolution**: Validate dependencies across PRD boundaries
3. **Conflict Detection**: Detect and report conflicts (fail fast, no auto-resolution)
4. **Global Execution Plan**: Merge PRDs into single deterministic execution DAG
5. **Coordinator Compatibility**: Output compatible with existing Phase 2.3 Coordinator

### Non-Goals (Explicit)

❌ **NOT** a new execution engine  
❌ **NOT** agent logic or inference  
❌ **NOT** autonomous conflict resolution  
❌ **NOT** modifying Phase 3.1 or earlier phases  
❌ **NOT** LLM-based reasoning  

---

## Architecture Overview

### Component Structure

```
lexicon/
└── orchestrator/
    ├── multi_prd_intake.py         # PRD normalization
    ├── cross_prd_resolver.py       # Cross-PRD dependency validation
    ├── conflict_detector.py        # Conflict detection engine
    └── global_plan_builder.py      # Global DAG construction
```

**Design Principle**: All components are **stateless** and **deterministic**.

---

## Component Specifications

### 1. Multi-PRD Intake (`multi_prd_intake.py`)

**Responsibility**: Accept and normalize multiple PRDs into a common format.

**Input Schema**:
```python
class MultiPRDInput:
    """Input container for multiple PRDs."""
    prds: List[Union[PRD, AdvancedPRD]]  # Mixed types allowed
    metadata: MultiPRDMetadata
```

**Output Schema**:
```python
class NormalizedPRDCollection:
    """Normalized collection of decomposed tasks."""
    tasks: List[DecomposedTask]           # All tasks from all PRDs
    prd_sources: Dict[str, str]           # task_id -> prd_id mapping
    task_count_by_prd: Dict[str, int]     # Statistics
```

**Process**:
1. Accept list of PRDs (Phase 2.4 or Phase 3.1)
2. For each PRD:
   - If `PRD` (Phase 2.4): Convert to tasks using `PRDProcessor`
   - If `AdvancedPRD` (Phase 3.1): Decompose using `PRDDecomposer`
3. Assign unique PRD identifiers
4. Track task-to-PRD mapping
5. Return normalized collection

**Backward Compatibility**:
- Single PRD input still works (list of 1)
- Phase 2.4 PRDs processed identically to before
- Phase 3.1 decomposition unchanged

---

### 2. Cross-PRD Resolver (`cross_prd_resolver.py`)

**Responsibility**: Validate dependencies across PRD boundaries.

**Input**: `NormalizedPRDCollection`

**Output**:
```python
class CrossPRDValidationResult:
    """Result of cross-PRD dependency validation."""
    is_valid: bool
    errors: List[CrossPRDError]
    warnings: List[CrossPRDWarning]
    global_dependency_graph: Dict[str, Set[str]]
```

**Validation Rules**:

1. **Existence Check**: All dependencies must reference existing tasks
2. **Circular Dependency Detection**: DFS across all PRDs (O(V+E))
3. **Cross-PRD Reference Validation**: Dependencies can span PRDs (explicit only)
4. **ID Collision Detection**: Task IDs must be unique across all PRDs

**Algorithm - Circular Dependency Detection**:
```python
def detect_cross_prd_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """
    Detect cycles using DFS across global dependency graph.
    
    Returns list of cycles (each cycle is a list of task IDs).
    """
    visited = set()
    rec_stack = set()
    cycles = []
    
    def dfs(node: str, path: List[str]):
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path.copy())
            elif neighbor in rec_stack:
                # Cycle detected
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
        
        rec_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles
```

**Error Types**:
- `MISSING_DEPENDENCY`: Referenced task does not exist
- `CIRCULAR_DEPENDENCY`: Cycle detected in global graph
- `DUPLICATE_TASK_ID`: Same task ID in multiple PRDs
- `INVALID_CROSS_PRD_REFERENCE`: Malformed cross-PRD dependency

---

### 3. Conflict Detector (`conflict_detector.py`)

**Responsibility**: Detect resource and output conflicts. **DOES NOT RESOLVE**.

**Input**: `NormalizedPRDCollection` + `CrossPRDValidationResult`

**Output**:
```python
class ConflictReport:
    """Report of all detected conflicts."""
    has_conflicts: bool
    resource_conflicts: List[ResourceConflict]
    output_conflicts: List[OutputConflict]
    constraint_conflicts: List[ConstraintConflict]
```

**Conflict Types**:

1. **Resource Conflicts**:
   - Same resource (FILE_WRITE, DATABASE, etc.) used by tasks in same execution wave
   - Detection: Group tasks by wave, check resource overlap
   
   ```python
   class ResourceConflict:
       task_a: str
       task_b: str
       resource: ResourceType
       wave: int  # Execution wave number where conflict occurs
   ```

2. **Output Conflicts**:
   - Multiple tasks declare same output file/artifact
   - Detection: Build output map, detect duplicates
   
   ```python
   class OutputConflict:
       task_a: str
       task_b: str
       output_path: str
   ```

3. **Constraint Conflicts**:
   - Incompatible execution constraints (future: timeouts, priorities)
   - Detection: Constraint compatibility matrix
   
   ```python
   class ConstraintConflict:
       task_a: str
       task_b: str
       constraint_type: str
       reason: str
   ```

**Detection Rules**:

| Conflict Type | Detection Method | Action |
|--------------|------------------|--------|
| Resource overlap in same wave | Set intersection per wave | FAIL |
| Duplicate output paths | Dictionary key collision | FAIL |
| Duplicate task IDs | Set membership | FAIL |
| Circular dependencies | DFS cycle detection | FAIL |

**Important**: Conflicts cause **immediate failure**. No automatic resolution.

---

### 4. Global Plan Builder (`global_plan_builder.py`)

**Responsibility**: Construct global execution plan from validated tasks.

**Input**: Validated `NormalizedPRDCollection`

**Output**:
```python
class GlobalExecutionPlan:
    """Complete execution plan for all PRDs."""
    execution_waves: List[ExecutionWave]
    total_tasks: int
    total_prds: int
    is_deterministic: bool  # Always True
    parallel_capacity: int  # Max tasks in any wave
```

**Execution Wave**:
```python
class ExecutionWave:
    """Tasks that can execute in parallel."""
    wave_number: int
    tasks: List[DecomposedTask]
    depends_on_waves: List[int]  # Previous waves
    estimated_duration: Optional[float]
```

**Algorithm - Wave Generation**:
```python
def build_execution_waves(
    tasks: List[DecomposedTask],
    dependency_graph: Dict[str, Set[str]]
) -> List[ExecutionWave]:
    """
    Build execution waves using Kahn's algorithm (topological sort).
    
    Tasks in the same wave have no dependencies on each other.
    """
    # Calculate in-degree for each task
    in_degree = {task.id: 0 for task in tasks}
    for deps in dependency_graph.values():
        for dep in deps:
            in_degree[dep] += 1
    
    waves = []
    queue = deque([t for t in tasks if in_degree[t.id] == 0])
    
    while queue:
        # Current wave: all tasks with in-degree 0
        current_wave = []
        wave_size = len(queue)
        
        for _ in range(wave_size):
            task = queue.popleft()
            current_wave.append(task)
            
            # Reduce in-degree for dependents
            for dependent in get_dependents(task.id, dependency_graph):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(get_task(dependent, tasks))
        
        waves.append(ExecutionWave(
            wave_number=len(waves),
            tasks=current_wave,
            depends_on_waves=list(range(len(waves)))
        ))
    
    return waves
```

**Determinism Guarantee**:
- Same inputs → same waves (stable sort by task ID within wave)
- No randomness, no inference
- Reproducible across runs

---

## Data Model Specifications

### Multi-PRD Input

```python
from dataclasses import dataclass
from typing import List, Union, Optional
from datetime import datetime

@dataclass
class MultiPRDMetadata:
    """Metadata for multi-PRD execution."""
    execution_id: str
    requested_by: Optional[str] = None
    requested_at: datetime = datetime.now(UTC)
    tags: List[str] = None

@dataclass
class MultiPRDInput:
    """Container for multiple PRDs."""
    prds: List[Union[PRD, AdvancedPRD]]
    metadata: MultiPRDMetadata
    
    def __post_init__(self):
        if not self.prds:
            raise ValueError("At least one PRD required")
        
        # Assign unique PRD IDs if not present
        for i, prd in enumerate(self.prds):
            if not hasattr(prd.metadata, 'prd_id'):
                prd.metadata.prd_id = f"prd-{i:03d}"
```

### Global Execution Plan

```python
@dataclass
class ExecutionWave:
    """Tasks that can run in parallel."""
    wave_number: int
    tasks: List[DecomposedTask]
    depends_on_waves: List[int]
    estimated_duration: Optional[float] = None

@dataclass
class GlobalExecutionPlan:
    """Complete execution plan across all PRDs."""
    execution_waves: List[ExecutionWave]
    total_tasks: int
    total_prds: int
    metadata: MultiPRDMetadata
    
    # Statistics
    parallel_capacity: int  # Max tasks in single wave
    critical_path_length: int  # Number of waves (sequential depth)
    
    # Validation
    is_deterministic: bool = True
    conflicts_detected: int = 0
    
    def get_parallelizable_tasks(self) -> int:
        """Count tasks that can run in parallel."""
        return sum(len(w.tasks) for w in self.execution_waves if len(w.tasks) > 1)
```

### Conflict Reports

```python
@dataclass
class ResourceConflict:
    """Resource usage conflict between tasks."""
    task_a_id: str
    task_b_id: str
    resource: ResourceType
    wave_number: int
    severity: str = "ERROR"

@dataclass
class OutputConflict:
    """Output path collision."""
    task_a_id: str
    task_b_id: str
    output_path: str
    severity: str = "ERROR"

@dataclass
class ConflictReport:
    """Comprehensive conflict report."""
    has_conflicts: bool
    resource_conflicts: List[ResourceConflict]
    output_conflicts: List[OutputConflict]
    constraint_conflicts: List[ConstraintConflict]
    
    @property
    def total_conflicts(self) -> int:
        return (
            len(self.resource_conflicts) +
            len(self.output_conflicts) +
            len(self.constraint_conflicts)
        )
```

---

## Interface Specifications

### Public API

```python
class MultiPRDOrchestrator:
    """
    Main orchestration interface for Phase 3.2.
    
    Coordinates multiple PRDs into a single execution plan.
    Does NOT execute - only produces validated plans.
    """
    
    def __init__(self):
        self.intake = MultiPRDIntake()
        self.resolver = CrossPRDResolver()
        self.detector = ConflictDetector()
        self.builder = GlobalPlanBuilder()
    
    def orchestrate(
        self, 
        prds: List[Union[PRD, AdvancedPRD]],
        metadata: Optional[MultiPRDMetadata] = None
    ) -> GlobalExecutionPlan:
        """
        Orchestrate multiple PRDs into execution plan.
        
        Args:
            prds: List of PRDs (mixed Phase 2.4 and 3.1)
            metadata: Optional execution metadata
            
        Returns:
            GlobalExecutionPlan ready for Coordinator
            
        Raises:
            ConflictError: If unresolvable conflicts detected
            ValidationError: If cross-PRD validation fails
        """
        # Step 1: Normalize all PRDs
        normalized = self.intake.normalize(prds, metadata)
        
        # Step 2: Validate cross-PRD dependencies
        validation = self.resolver.validate(normalized)
        if not validation.is_valid:
            raise ValidationError(validation.errors)
        
        # Step 3: Detect conflicts
        conflicts = self.detector.detect(normalized, validation)
        if conflicts.has_conflicts:
            raise ConflictError(conflicts)
        
        # Step 4: Build global execution plan
        plan = self.builder.build(normalized, validation)
        
        return plan
```

---

## Backward Compatibility

### Phase 2.4 Compatibility

**Guarantee**: Single PRD execution works identically.

```python
# Phase 2.4 usage (unchanged)
from lexicon.pipeline import PRDPipeline, PRD

prd = PRD(...)
pipeline = PRDPipeline(coordinator)
result = pipeline.execute_prd(prd)  # Still works

# Phase 3.2 usage (new, opt-in)
from lexicon.orchestrator import MultiPRDOrchestrator

orchestrator = MultiPRDOrchestrator()
plan = orchestrator.orchestrate([prd])  # Single PRD as list
# Execute plan with coordinator (separate step)
```

**Test Coverage**:
- All Phase 2.4 tests must pass unchanged
- Single PRD through Phase 3.2 must produce identical plan to Phase 2.4

### Phase 3.1 Compatibility

**Guarantee**: Advanced PRD decomposition unchanged.

```python
# Phase 3.1 usage (unchanged)
from lexicon.pipeline import PRDDecomposer, AdvancedPRD

advanced_prd = AdvancedPRD(...)
decomposer = PRDDecomposer()
tasks = decomposer.decompose(advanced_prd)  # Still works

# Phase 3.2 usage (new)
orchestrator = MultiPRDOrchestrator()
plan = orchestrator.orchestrate([advanced_prd])  # Uses decomposer internally
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| PRD normalization | < 100ms per PRD | 5 PRDs in < 500ms |
| Cycle detection | O(V+E) | 100 tasks < 50ms |
| Conflict detection | < 200ms total | 100 tasks across 5 PRDs |
| Wave generation | O(V log V) | 100 tasks < 100ms |
| **Total orchestration** | **< 1s** | **5 PRDs, 100 tasks** |

**Scalability**:
- Up to 10 PRDs
- Up to 500 tasks total
- Up to 10 execution waves

---

## Security & Compliance

### Input Validation

- All PRD IDs sanitized (no special characters)
- Task IDs validated for uniqueness
- Dependency references validated
- Resource types from controlled enum

### Audit Trail

Every orchestration produces:
1. Input PRD fingerprints
2. Normalization log
3. Validation results
4. Conflict reports (if any)
5. Final execution plan

All deterministic and reproducible.

---

## Testing Strategy

### Unit Tests

1. **Multi-PRD Intake**:
   - Mixed PRD types (Phase 2.4 + 3.1)
   - Empty PRD list (should fail)
   - Duplicate PRD IDs (should assign unique)

2. **Cross-PRD Resolver**:
   - Valid cross-PRD dependencies
   - Missing cross-PRD references
   - Circular dependencies across PRDs
   - Duplicate task IDs

3. **Conflict Detector**:
   - Resource conflicts in same wave
   - Output path collisions
   - No conflicts (should pass)

4. **Global Plan Builder**:
   - Deterministic wave generation
   - Parallel capacity calculation
   - Empty task list handling

### Integration Tests

1. **End-to-End Orchestration**:
   - 3 flat PRDs → single plan
   - 2 nested PRDs → single plan
   - Mixed flat + nested → single plan

2. **Backward Compatibility**:
   - Single Phase 2.4 PRD → identical to Phase 2.4 output
   - Single Phase 3.1 PRD → uses decomposer correctly

3. **Failure Scenarios**:
   - Conflict detection → immediate failure
   - Circular dependency → clear error message
   - Missing dependency → validation failure

---

## Migration Path

### Adopting Phase 3.2

**For existing Phase 2.4 users**:
```python
# Before (Phase 2.4)
pipeline = PRDPipeline(coordinator)
result = pipeline.execute_prd(prd)

# After (Phase 3.2, optional)
orchestrator = MultiPRDOrchestrator()
plan = orchestrator.orchestrate([prd])
# Execute via coordinator (manual step)
```

**For existing Phase 3.1 users**:
```python
# Before (Phase 3.1)
decomposer = PRDDecomposer()
tasks = decomposer.decompose(prd)

# After (Phase 3.2, for multi-PRD)
orchestrator = MultiPRDOrchestrator()
plan = orchestrator.orchestrate([prd1, prd2])
```

**No breaking changes**: All existing code continues to work.

---

## Out of Scope (Explicit)

### NOT in Phase 3.2

1. **Execution**: Phase 3.2 produces plans, does NOT execute
2. **Conflict Resolution**: Detects only, user must resolve
3. **Agent Logic**: No LLM calls, no inference
4. **Dynamic Replanning**: Plans are static once created
5. **Parallel Execution Implementation**: Only plans for it
6. **Real-time Updates**: Plans are immutable
7. **Distributed Coordination**: Single-machine only

These may be addressed in Phase 4 or beyond.

---

## Success Criteria

Phase 3.2 is complete when:

✅ All 4 components implemented and tested  
✅ Multi-PRD orchestration works for 2+ PRDs  
✅ Conflict detection catches all defined conflict types  
✅ Global execution plan is deterministic  
✅ Phase 2.4 single-PRD tests pass unchanged  
✅ Phase 3.1 decomposition tests pass unchanged  
✅ Documentation complete (architecture, data flow, failure modes)  
✅ Performance targets met (< 1s for 5 PRDs, 100 tasks)  

---

## Approval Checklist

Before implementation begins:

- [ ] Architecture reviewed and approved
- [ ] Data models finalized
- [ ] Interface contracts agreed
- [ ] Failure modes documented
- [ ] Backward compatibility verified at design level
- [ ] Performance targets validated
- [ ] Test strategy approved

**Next Step**: Create `PHASE_3.2_DATA_FLOW.md` and `PHASE_3.2_FAILURE_MODES.md`.

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-28  
**Status**: Pending Approval
