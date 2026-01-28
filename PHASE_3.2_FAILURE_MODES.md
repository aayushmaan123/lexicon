# Phase 3.2: Multi-PRD Orchestration - Failure Modes

## Document Status

**Status**: Design Document (Pending Approval)  
**Phase**: 3.2 - Multi-PRD Orchestration  
**Version**: 1.0  
**Last Updated**: 2026-01-28

---

## Overview

This document catalogs all possible failure modes in Phase 3.2 Multi-PRD Orchestration, defining detection methods, error responses, and recovery strategies. Every failure mode results in **immediate failure** with clear error messages - no silent failures, no auto-resolution.

**Core Principle**: Fail fast, fail loud, fail informatively.

---

## Failure Mode Categories

| Category | Detection Phase | Action | Severity |
|----------|----------------|--------|----------|
| Input Validation | Intake | Reject immediately | CRITICAL |
| Dependency Errors | Resolution | Fail with details | CRITICAL |
| Conflict Detection | Detection | Report all conflicts | CRITICAL |
| Resource Exhaustion | Building | Fail with limits | ERROR |
| System Errors | Any | Escalate | CRITICAL |

---

## 1. Input Validation Failures

### 1.1 Empty PRD List

**Condition**: `len(prds) == 0`

**Detection**: Intake initialization

**Error**:
```python
class EmptyPRDListError(ValueError):
    """No PRDs provided for orchestration."""
    
    def __init__(self):
        super().__init__(
            "At least one PRD required for orchestration. "
            "Received empty list."
        )
```

**Example**:
```python
orchestrator.orchestrate([])
# Raises: EmptyPRDListError
```

**Recovery**: User must provide at least one PRD.

---

### 1.2 Invalid PRD Type

**Condition**: PRD is neither `PRD` nor `AdvancedPRD`

**Detection**: Intake type checking

**Error**:
```python
class InvalidPRDTypeError(TypeError):
    """Invalid PRD type in input list."""
    
    def __init__(self, prd_index: int, actual_type: type):
        super().__init__(
            f"PRD at index {prd_index} has invalid type: {actual_type}. "
            f"Expected: PRD or AdvancedPRD."
        )
```

**Example**:
```python
orchestrator.orchestrate([prd1, "not a PRD", prd3])
# Raises: InvalidPRDTypeError(prd_index=1, actual_type=str)
```

**Recovery**: Replace invalid item with valid PRD object.

---

### 1.3 Malformed PRD Structure

**Condition**: PRD fails internal validation (missing required fields)

**Detection**: Phase 2.4 or 3.1 validation

**Error**:
```python
class MalformedPRDError(ValueError):
    """PRD structure is invalid."""
    
    def __init__(self, prd_index: int, validation_errors: List[str]):
        super().__init__(
            f"PRD at index {prd_index} failed validation:\n" +
            "\n".join(f"  - {err}" for err in validation_errors)
        )
```

**Example**:
```python
prd = PRD(metadata=None, requirements=[])  # Missing metadata
orchestrator.orchestrate([prd])
# Raises: MalformedPRDError(prd_index=0, validation_errors=["metadata is required"])
```

**Recovery**: Fix PRD structure to meet schema requirements.

---

## 2. Task ID Conflicts

### 2.1 Duplicate Task IDs Across PRDs

**Condition**: Same task ID appears in multiple PRDs

**Detection**: Resolution phase (task ID uniqueness check)

**Error**:
```python
class DuplicateTaskIDError(ValueError):
    """Duplicate task IDs detected across PRDs."""
    
    def __init__(self, duplicates: Dict[str, List[str]]):
        """
        Args:
            duplicates: {task_id: [prd_id1, prd_id2, ...]}
        """
        msg_parts = ["Duplicate task IDs detected:"]
        for task_id, prd_ids in duplicates.items():
            msg_parts.append(
                f"  - Task '{task_id}' appears in PRDs: {', '.join(prd_ids)}"
            )
        super().__init__("\n".join(msg_parts))
```

**Example**:
```python
prd1 = PRD(requirements=[PRDRequirement(id="task-1", ...)])
prd2 = AdvancedPRD(requirements=[AdvancedPRDRequirement(id="task-1", ...)])

orchestrator.orchestrate([prd1, prd2])
# Raises: DuplicateTaskIDError({"task-1": ["prd-000", "prd-001"]})
```

**Recovery**: Rename tasks to ensure unique IDs across all PRDs.

**Prevention**: Use prefixed IDs (e.g., `api-task-1`, `ui-task-1`).

---

### 2.2 Empty Task ID

**Condition**: Task has empty or whitespace-only ID

**Detection**: Intake normalization

**Error**:
```python
class EmptyTaskIDError(ValueError):
    """Task has empty or invalid ID."""
    
    def __init__(self, prd_index: int, task_index: int):
        super().__init__(
            f"Task at PRD[{prd_index}].requirements[{task_index}] "
            f"has empty or invalid ID"
        )
```

**Example**:
```python
prd = PRD(requirements=[PRDRequirement(id="", description="Task")])
# Raises: EmptyTaskIDError(prd_index=0, task_index=0)
```

**Recovery**: Assign valid task IDs.

---

## 3. Dependency Resolution Failures

### 3.1 Missing Dependency Reference

**Condition**: Task depends on non-existent task

**Detection**: Resolution phase (dependency existence check)

**Error**:
```python
class MissingDependencyError(ValueError):
    """Tasks reference dependencies that don't exist."""
    
    def __init__(self, missing_deps: Dict[str, List[str]]):
        """
        Args:
            missing_deps: {task_id: [missing_dep_id1, missing_dep_id2, ...]}
        """
        msg_parts = ["Missing dependencies detected:"]
        for task_id, deps in missing_deps.items():
            msg_parts.append(
                f"  - Task '{task_id}' depends on non-existent: {', '.join(deps)}"
            )
        msg_parts.append("\nAll dependencies must reference existing tasks.")
        super().__init__("\n".join(msg_parts))
```

**Example**:
```python
prd = PRD(requirements=[
    PRDRequirement(id="task-1", dependencies=["nonexistent-task"])
])
# Raises: MissingDependencyError({"task-1": ["nonexistent-task"]})
```

**Recovery**: 
1. Add missing task to one of the PRDs, OR
2. Remove invalid dependency reference

---

### 3.2 Circular Dependencies Across PRDs

**Condition**: Dependency cycle spans multiple PRDs

**Detection**: Resolution phase (DFS cycle detection)

**Error**:
```python
class CircularDependencyError(ValueError):
    """Circular dependencies detected in global graph."""
    
    def __init__(self, cycles: List[List[str]]):
        """
        Args:
            cycles: List of cycles, each cycle is list of task IDs forming loop
        """
        msg_parts = ["Circular dependencies detected:"]
        for i, cycle in enumerate(cycles, 1):
            cycle_str = " → ".join(cycle)
            msg_parts.append(f"  {i}. {cycle_str}")
        msg_parts.append("\nRemove circular dependencies to proceed.")
        super().__init__("\n".join(msg_parts))
```

**Example**:
```python
# PRD 1
prd1 = PRD(requirements=[
    PRDRequirement(id="a", dependencies=["c"])  # Depends on PRD 2
])

# PRD 2
prd2 = PRD(requirements=[
    PRDRequirement(id="b", dependencies=["a"]),  # Depends on PRD 1
    PRDRequirement(id="c", dependencies=["b"])
])

orchestrator.orchestrate([prd1, prd2])
# Raises: CircularDependencyError([["a", "c", "b", "a"]])
```

**Recovery**: Break the cycle by removing one dependency.

**Detection Algorithm**:
```python
def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    """DFS-based cycle detection."""
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
                # Cycle found
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
        
        rec_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node, [])
    
    return cycles
```

---

### 3.3 Self-Dependency

**Condition**: Task depends on itself

**Detection**: Resolution phase (early check before graph construction)

**Error**:
```python
class SelfDependencyError(ValueError):
    """Task depends on itself."""
    
    def __init__(self, task_ids: List[str]):
        super().__init__(
            f"Tasks with self-dependencies: {', '.join(task_ids)}. "
            f"Tasks cannot depend on themselves."
        )
```

**Example**:
```python
prd = PRD(requirements=[
    PRDRequirement(id="task-1", dependencies=["task-1"])
])
# Raises: SelfDependencyError(["task-1"])
```

**Recovery**: Remove self-reference from dependencies.

---

## 4. Resource Conflicts

### 4.1 Resource Conflict in Same Execution Wave

**Condition**: Multiple tasks in same wave use same exclusive resource

**Detection**: Conflict detection phase

**Error**:
```python
class ResourceConflictError(ValueError):
    """Resource conflicts detected in execution plan."""
    
    def __init__(self, conflicts: List[ResourceConflict]):
        msg_parts = ["Resource conflicts detected:"]
        for conflict in conflicts:
            msg_parts.append(
                f"  - Wave {conflict.wave_number}: "
                f"Tasks '{conflict.task_a_id}' and '{conflict.task_b_id}' "
                f"both use resource {conflict.resource.value}"
            )
        msg_parts.append(
            "\nConflicts must be resolved by adding dependencies "
            "to enforce sequential execution."
        )
        super().__init__("\n".join(msg_parts))
```

**Example**:
```python
# Both tasks write to database in same wave (parallel execution)
prd1 = AdvancedPRD(requirements=[
    AdvancedPRDRequirement(
        id="task-a",
        resources=[ResourceType.DATABASE, ResourceType.FILE_WRITE]
    ),
    AdvancedPRDRequirement(
        id="task-b",
        resources=[ResourceType.DATABASE]  # Conflict!
    )
])

orchestrator.orchestrate([prd1])
# Raises: ResourceConflictError([
#     ResourceConflict(
#         task_a_id="task-a",
#         task_b_id="task-b",
#         resource=ResourceType.DATABASE,
#         wave_number=0
#     )
# ])
```

**Recovery**:
1. Add dependency: `task-b.dependencies = ["task-a"]` (sequential execution)
2. Change resource type if conflict is incorrect
3. Split into separate PRDs if truly independent

**Note**: File reads (FILE_READ) are non-conflicting. Multiple tasks can read simultaneously.

---

### 4.2 Output Path Collision

**Condition**: Multiple tasks produce same output file/path

**Detection**: Conflict detection phase

**Error**:
```python
class OutputConflictError(ValueError):
    """Output path conflicts detected."""
    
    def __init__(self, conflicts: List[OutputConflict]):
        msg_parts = ["Output path conflicts detected:"]
        for conflict in conflicts:
            msg_parts.append(
                f"  - Tasks '{conflict.task_a_id}' and '{conflict.task_b_id}' "
                f"both write to: {conflict.output_path}"
            )
        msg_parts.append(
            "\nEnsure each task writes to unique output path, "
            "or add dependencies for sequential writes."
        )
        super().__init__("\n".join(msg_parts))
```

**Example**:
```python
prd = AdvancedPRD(requirements=[
    AdvancedPRDRequirement(id="task-a", output_path="/data/result.json"),
    AdvancedPRDRequirement(id="task-b", output_path="/data/result.json")
])
# Raises: OutputConflictError
```

**Recovery**:
1. Change output paths to be unique
2. Add dependency if sequential overwrite is intended
3. Use different output formats/names

---

## 5. Execution Plan Building Failures

### 5.1 Unsatisfiable Dependencies

**Condition**: Topological sort fails (tasks remain after all waves processed)

**Detection**: Building phase (Kahn's algorithm residue check)

**Error**:
```python
class UnsatisfiableDependenciesError(ValueError):
    """Unable to satisfy all dependencies."""
    
    def __init__(self, remaining_tasks: List[str]):
        super().__init__(
            f"Unable to create valid execution plan. "
            f"Tasks with unsatisfiable dependencies: {', '.join(remaining_tasks)}. "
            f"This typically indicates a circular dependency."
        )
```

**Example**:
```python
# Should be caught earlier, but defense in depth
prd = PRD(requirements=[
    PRDRequirement(id="a", dependencies=["b"]),
    PRDRequirement(id="b", dependencies=["a"])
])
# Raises: UnsatisfiableDependenciesError(["a", "b"])
```

**Recovery**: Fix circular dependency (should be caught in resolution phase).

---

### 5.2 Excessive Nesting Depth

**Condition**: Execution plan has too many sequential waves

**Detection**: Building phase (wave count check)

**Error**:
```python
class ExcessiveNestingError(ValueError):
    """Execution plan exceeds maximum nesting depth."""
    
    def __init__(self, wave_count: int, max_waves: int = 100):
        super().__init__(
            f"Execution plan has {wave_count} waves, "
            f"exceeding maximum of {max_waves}. "
            f"Simplify dependency graph or split into smaller PRDs."
        )
```

**Example**:
```python
# 101 tasks in linear chain
requirements = [
    PRDRequirement(id=f"task-{i}", dependencies=[f"task-{i-1}"] if i > 0 else [])
    for i in range(101)
]
prd = PRD(requirements=requirements)
# Raises: ExcessiveNestingError(wave_count=101, max_waves=100)
```

**Recovery**: 
1. Reduce sequential dependencies
2. Parallelize where possible
3. Split into multiple execution batches

---

### 5.3 Excessive Parallelism

**Condition**: Single wave has too many parallel tasks

**Detection**: Building phase (wave size check)

**Error**:
```python
class ExcessiveParallelismError(ValueError):
    """Execution wave exceeds maximum parallel task count."""
    
    def __init__(self, wave_number: int, task_count: int, max_parallel: int = 50):
        super().__init__(
            f"Wave {wave_number} contains {task_count} parallel tasks, "
            f"exceeding maximum of {max_parallel}. "
            f"Add dependencies to limit parallelism."
        )
```

**Example**:
```python
# 60 independent tasks (all in wave 0)
requirements = [
    PRDRequirement(id=f"task-{i}", dependencies=[])
    for i in range(60)
]
prd = PRD(requirements=requirements)
# Raises: ExcessiveParallelismError(wave_number=0, task_count=60, max_parallel=50)
```

**Recovery**: Add dependencies to create sequential groups.

---

## 6. System-Level Failures

### 6.1 Memory Exhaustion

**Condition**: Too many tasks to hold in memory

**Detection**: Any phase (memory monitoring)

**Error**:
```python
class MemoryExhaustionError(MemoryError):
    """Insufficient memory for orchestration."""
    
    def __init__(self, task_count: int):
        super().__init__(
            f"Unable to orchestrate {task_count} tasks: insufficient memory. "
            f"Consider splitting into smaller batches."
        )
```

**Recovery**: 
1. Reduce number of PRDs
2. Simplify PRD structures
3. Process in batches

---

### 6.2 Timeout

**Condition**: Orchestration takes too long

**Detection**: Timeout wrapper (if enabled)

**Error**:
```python
class OrchestrationTimeoutError(TimeoutError):
    """Orchestration exceeded time limit."""
    
    def __init__(self, timeout_seconds: int):
        super().__init__(
            f"Orchestration exceeded {timeout_seconds}s timeout. "
            f"Simplify PRDs or increase timeout limit."
        )
```

**Recovery**:
1. Optimize PRD structure
2. Increase timeout
3. Process fewer PRDs per batch

---

## 7. Phase-Specific Constraint Violations

### 7.1 Phase 3.1 Constraint: parent_id in dependencies

**Condition**: AdvancedPRD has parent_id appearing in dependencies

**Detection**: Phase 3.1 validation (before orchestration)

**Error**:
```python
class ParentIDInDependenciesError(ValueError):
    """parent_id cannot appear in dependencies."""
    
    def __init__(self, task_id: str, parent_id: str):
        super().__init__(
            f"Task '{task_id}' has parent_id '{parent_id}' in dependencies. "
            f"parent_id is informational only; use dependencies for execution order."
        )
```

**Example**:
```python
prd = AdvancedPRD(requirements=[
    AdvancedPRDRequirement(id="parent", parent_id=None),
    AdvancedPRDRequirement(
        id="child",
        parent_id="parent",
        dependencies=["parent"]  # VIOLATION
    )
])
# Raises: ParentIDInDependenciesError
```

**Recovery**: Remove parent_id from dependencies list.

---

## Error Response Format

All errors include:

```python
{
    "error_type": "ResourceConflictError",
    "message": "Resource conflicts detected: ...",
    "details": {
        "conflicts": [
            {
                "task_a": "api-task-1",
                "task_b": "ui-task-2",
                "resource": "DATABASE",
                "wave": 2
            }
        ]
    },
    "recovery_suggestions": [
        "Add dependency: ui-task-2 depends on api-task-1",
        "Change resource type if conflict is incorrect"
    ],
    "timestamp": "2026-01-28T18:00:00Z"
}
```

---

## Failure Mode Detection Summary

| Failure Mode | Detection Method | Complexity | Action |
|--------------|------------------|------------|--------|
| Empty PRD list | Length check | O(1) | Reject |
| Invalid type | isinstance() | O(N) | Reject |
| Duplicate IDs | Set membership | O(N) | Reject |
| Missing deps | Set difference | O(E) | Reject |
| Circular deps | DFS | O(V+E) | Reject |
| Resource conflict | Set intersection per wave | O(W×T²) | Reject |
| Output conflict | Dictionary collision | O(N) | Reject |
| Memory exhaustion | Size check | O(1) | Reject |

Where: N=tasks, E=edges, V=vertices, W=waves, T=tasks per wave

---

## Testing Strategy for Failure Modes

### Unit Tests

Each failure mode must have:

1. **Trigger Test**: Verify error is raised
2. **Message Test**: Verify error message is informative
3. **Recovery Test**: Verify suggested fix resolves error

Example:
```python
def test_duplicate_task_id_error():
    """Verify duplicate task ID detection."""
    prd1 = PRD(requirements=[PRDRequirement(id="task-1", ...)])
    prd2 = PRD(requirements=[PRDRequirement(id="task-1", ...)])
    
    with pytest.raises(DuplicateTaskIDError) as exc_info:
        orchestrator.orchestrate([prd1, prd2])
    
    assert "task-1" in str(exc_info.value)
    assert "prd-000" in str(exc_info.value)
    assert "prd-001" in str(exc_info.value)

def test_duplicate_task_id_recovery():
    """Verify fixing duplicate IDs resolves error."""
    prd1 = PRD(requirements=[PRDRequirement(id="task-1", ...)])
    prd2 = PRD(requirements=[PRDRequirement(id="task-2", ...)])  # Fixed
    
    plan = orchestrator.orchestrate([prd1, prd2])  # Should succeed
    assert plan.total_tasks == 2
```

---

## Failure Mode Prevention

### Design-Time Prevention

1. **Type Safety**: Use Pydantic models with strict validation
2. **Early Validation**: Catch errors at PRD creation, not orchestration
3. **Clear Contracts**: Document what's allowed/forbidden

### Runtime Prevention

1. **Input Validation**: Check all inputs before processing
2. **Defensive Programming**: Validate at each phase boundary
3. **Fail Fast**: Don't process invalid data

### User Prevention

1. **PRD Templates**: Provide validated templates
2. **ID Prefixing**: Recommend unique prefixes per PRD (e.g., `api-`, `ui-`)
3. **Validation Tools**: Provide pre-orchestration validation

---

## Backward Compatibility Failure Analysis

### Phase 2.4 Failures

**New Failure Modes**: None  
**Changed Behavior**: None  
**Risk**: Zero

Single PRD orchestration cannot trigger multi-PRD specific errors (duplicate IDs across PRDs, cross-PRD cycles).

### Phase 3.1 Failures

**New Failure Modes**: None  
**Changed Behavior**: None  
**Risk**: Zero

Advanced PRD decomposition happens before orchestration. All Phase 3.1 constraints still enforced.

---

## Appendix: Complete Failure Mode Catalog

| ID | Failure Mode | Severity | Recovery Time |
|----|--------------|----------|---------------|
| F-01 | Empty PRD list | CRITICAL | Immediate |
| F-02 | Invalid PRD type | CRITICAL | Immediate |
| F-03 | Malformed PRD | CRITICAL | Minutes |
| F-04 | Duplicate task IDs | CRITICAL | Minutes |
| F-05 | Empty task ID | CRITICAL | Immediate |
| F-06 | Missing dependency | CRITICAL | Minutes |
| F-07 | Circular dependency | CRITICAL | Hours* |
| F-08 | Self-dependency | CRITICAL | Immediate |
| F-09 | Resource conflict | CRITICAL | Minutes |
| F-10 | Output conflict | CRITICAL | Minutes |
| F-11 | Unsatisfiable deps | CRITICAL | Hours* |
| F-12 | Excessive nesting | ERROR | Hours* |
| F-13 | Excessive parallelism | ERROR | Minutes |
| F-14 | Memory exhaustion | CRITICAL | Hours** |
| F-15 | Timeout | ERROR | Variable |
| F-16 | parent_id in deps | CRITICAL | Immediate |

\* Requires dependency graph restructuring  
\*\* May require architectural changes

---

## Monitoring & Alerting

### Metrics to Track

1. **Error Rate**: Percentage of orchestrations that fail
2. **Error Type Distribution**: Which errors are most common
3. **Recovery Time**: Time from error to successful orchestration
4. **Conflict Frequency**: How often conflicts detected

### Alert Thresholds

- Error rate > 10%: Investigate PRD quality
- Same error type > 50%: User education needed
- Recovery time > 1 hour: Process improvement needed

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-28  
**Status**: Pending Approval
