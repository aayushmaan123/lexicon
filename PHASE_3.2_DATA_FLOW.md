# Phase 3.2: Multi-PRD Orchestration - Data Flow Design

## Document Status

**Status**: Design Document (Pending Approval)  
**Phase**: 3.2 - Multi-PRD Orchestration  
**Version**: 1.0  
**Last Updated**: 2026-01-28

---

## Overview

This document defines the complete data flow through Phase 3.2 Multi-PRD Orchestration, including all transformations, validations, and output schemas. Every step is deterministic and reproducible.

---

## High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Input: Multiple PRDs                           │
│              [PRD (Phase 2.4), AdvancedPRD (Phase 3.1)]         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Multi-PRD Intake (Normalization)                       │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ For each PRD:                                          │      │
│  │  - If PRD (Phase 2.4) → PRDProcessor → PRDTask list  │      │
│  │  - If AdvancedPRD (Phase 3.1) → PRDDecomposer →      │      │
│  │                                   DecomposedTask list  │      │
│  │  - Assign unique PRD identifier                        │      │
│  │  - Track task-to-PRD mapping                          │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│           Output: NormalizedPRDCollection                        │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ - tasks: List[DecomposedTask]                         │      │
│  │ - prd_sources: Dict[task_id -> prd_id]               │      │
│  │ - task_count_by_prd: Dict[prd_id -> count]           │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Cross-PRD Dependency Resolution                        │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Build global dependency graph                      │      │
│  │ 2. Validate all task IDs unique                       │      │
│  │ 3. Validate all dependencies exist                    │      │
│  │ 4. Detect circular dependencies (DFS)                 │      │
│  │ 5. Build adjacency list for wave generation           │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│         Output: CrossPRDValidationResult                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ - is_valid: bool                                       │      │
│  │ - errors: List[CrossPRDError]                         │      │
│  │ - warnings: List[CrossPRDWarning]                     │      │
│  │ - global_dependency_graph: Dict[str, Set[str]]        │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (if valid)
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Conflict Detection                                     │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Generate execution waves (preliminary)              │      │
│  │ 2. Check resource conflicts within waves              │      │
│  │ 3. Check output path collisions                       │      │
│  │ 4. Check constraint incompatibilities                 │      │
│  │ 5. Report ALL conflicts (fail fast)                   │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              Output: ConflictReport                              │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ - has_conflicts: bool                                  │      │
│  │ - resource_conflicts: List[ResourceConflict]          │      │
│  │ - output_conflicts: List[OutputConflict]              │      │
│  │ - constraint_conflicts: List[ConstraintConflict]      │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼ (if no conflicts)
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Global Execution Plan Building                         │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ 1. Topological sort (Kahn's algorithm)                │      │
│  │ 2. Group into execution waves                         │      │
│  │ 3. Calculate parallel capacity                        │      │
│  │ 4. Compute critical path length                       │      │
│  │ 5. Attach metadata and statistics                     │      │
│  └───────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│          Output: GlobalExecutionPlan                             │
│  ┌───────────────────────────────────────────────────────┐      │
│  │ - execution_waves: List[ExecutionWave]                │      │
│  │ - total_tasks: int                                     │      │
│  │ - total_prds: int                                      │      │
│  │ - parallel_capacity: int                               │      │
│  │ - critical_path_length: int                            │      │
│  │ - is_deterministic: bool (always True)                 │      │
│  └───────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
            Ready for Phase 2.3 Coordinator Execution
```

---

## Detailed Data Flow Steps

### Step 1: Multi-PRD Intake

**Input Schema**:
```python
{
    "prds": [
        {
            "type": "PRD",  # Phase 2.4
            "metadata": {
                "title": "Feature A",
                "version": "1.0"
            },
            "requirements": [
                {
                    "id": "feat-a-1",
                    "description": "Task 1",
                    "dependencies": []
                },
                {
                    "id": "feat-a-2",
                    "description": "Task 2",
                    "dependencies": ["feat-a-1"]
                }
            ]
        },
        {
            "type": "AdvancedPRD",  # Phase 3.1
            "metadata": {
                "title": "Feature B",
                "version": "1.0"
            },
            "requirements": [
                {
                    "id": "feat-b-1",
                    "description": "Parent task",
                    "parent_id": null,
                    "dependencies": ["feat-a-2"]  # Cross-PRD dependency
                },
                {
                    "id": "feat-b-1-sub",
                    "description": "Subtask",
                    "parent_id": "feat-b-1",
                    "dependencies": ["feat-b-1"]
                }
            ]
        }
    ],
    "metadata": {
        "execution_id": "exec-2026-01-28-001",
        "requested_by": "user@example.com"
    }
}
```

**Processing**:

1. **PRD Type Detection**:
   ```python
   for prd in input.prds:
       if isinstance(prd, PRD):
           # Phase 2.4 processing
           processor = PRDProcessor()
           tasks = processor.process(prd)
       elif isinstance(prd, AdvancedPRD):
           # Phase 3.1 processing
           decomposer = PRDDecomposer()
           tasks = decomposer.decompose(prd)
   ```

2. **Task ID Assignment**:
   - Each task gets unique ID (already in PRD)
   - PRD ID assigned: `prd-{index:03d}` or from metadata
   - Task-to-PRD mapping created

3. **Normalization**:
   ```python
   normalized_tasks = []
   prd_sources = {}
   
   for prd_idx, prd in enumerate(prds):
       prd_id = f"prd-{prd_idx:03d}"
       tasks = process_prd(prd)  # Phase-specific
       
       for task in tasks:
           normalized_tasks.append(task)
           prd_sources[task.id] = prd_id
   ```

**Output Schema**:
```python
{
    "tasks": [
        {
            "id": "feat-a-1",
            "description": "Task 1",
            "dependencies": [],
            "source_prd": "prd-000"
        },
        {
            "id": "feat-a-2",
            "description": "Task 2",
            "dependencies": ["feat-a-1"],
            "source_prd": "prd-000"
        },
        {
            "id": "feat-b-1",
            "description": "Parent task",
            "dependencies": ["feat-a-2"],
            "source_prd": "prd-001"
        },
        {
            "id": "feat-b-1-sub",
            "description": "Subtask",
            "dependencies": ["feat-b-1"],
            "source_prd": "prd-001"
        }
    ],
    "prd_sources": {
        "feat-a-1": "prd-000",
        "feat-a-2": "prd-000",
        "feat-b-1": "prd-001",
        "feat-b-1-sub": "prd-001"
    },
    "task_count_by_prd": {
        "prd-000": 2,
        "prd-001": 2
    }
}
```

---

### Step 2: Cross-PRD Dependency Resolution

**Input**: `NormalizedPRDCollection` from Step 1

**Processing**:

1. **Build Global Dependency Graph**:
   ```python
   dependency_graph = {}
   all_task_ids = set()
   
   for task in normalized.tasks:
       all_task_ids.add(task.id)
       dependency_graph[task.id] = set(task.dependencies)
   ```

2. **Validate Task ID Uniqueness**:
   ```python
   seen_ids = set()
   duplicates = []
   
   for task in normalized.tasks:
       if task.id in seen_ids:
           duplicates.append(task.id)
       seen_ids.add(task.id)
   
   if duplicates:
       raise DuplicateTaskIDError(duplicates)
   ```

3. **Validate Dependency Existence**:
   ```python
   missing_deps = {}
   
   for task_id, deps in dependency_graph.items():
       missing = deps - all_task_ids
       if missing:
           missing_deps[task_id] = list(missing)
   
   if missing_deps:
       raise MissingDependencyError(missing_deps)
   ```

4. **Circular Dependency Detection** (DFS):
   ```python
   def detect_cycles(graph):
       visited = set()
       rec_stack = set()
       cycles = []
       
       def dfs(node, path):
           visited.add(node)
           rec_stack.add(node)
           path.append(node)
           
           for neighbor in graph[node]:
               if neighbor not in visited:
                   dfs(neighbor, path.copy())
               elif neighbor in rec_stack:
                   cycle_start = path.index(neighbor)
                   cycles.append(path[cycle_start:] + [neighbor])
           
           rec_stack.remove(node)
       
       for node in graph:
           if node not in visited:
               dfs(node, [])
       
       return cycles
   ```

**Output Schema**:
```python
{
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "global_dependency_graph": {
        "feat-a-1": [],
        "feat-a-2": ["feat-a-1"],
        "feat-b-1": ["feat-a-2"],
        "feat-b-1-sub": ["feat-b-1"]
    }
}
```

**Example Error Output**:
```python
{
    "is_valid": false,
    "errors": [
        {
            "type": "CIRCULAR_DEPENDENCY",
            "cycle": ["task-a", "task-b", "task-c", "task-a"],
            "message": "Circular dependency detected across PRDs"
        }
    ],
    "warnings": [],
    "global_dependency_graph": null
}
```

---

### Step 3: Conflict Detection

**Input**: `NormalizedPRDCollection` + `CrossPRDValidationResult`

**Processing**:

1. **Generate Preliminary Execution Waves**:
   ```python
   waves = build_execution_waves(
       tasks=normalized.tasks,
       dependency_graph=validation.global_dependency_graph
   )
   ```

2. **Resource Conflict Detection**:
   ```python
   resource_conflicts = []
   
   for wave in waves:
       # Group tasks by resource
       resource_map = defaultdict(list)
       for task in wave.tasks:
           for resource in task.resources:
               resource_map[resource].append(task.id)
       
       # Find conflicts (multiple tasks using same resource)
       for resource, task_ids in resource_map.items():
           if len(task_ids) > 1:
               # Potential conflict (same resource in same wave)
               for i, task_a in enumerate(task_ids):
                   for task_b in task_ids[i+1:]:
                       resource_conflicts.append(
                           ResourceConflict(
                               task_a_id=task_a,
                               task_b_id=task_b,
                               resource=resource,
                               wave_number=wave.wave_number
                           )
                       )
   ```

3. **Output Path Conflict Detection**:
   ```python
   output_conflicts = []
   output_map = defaultdict(list)
   
   for task in normalized.tasks:
       if hasattr(task, 'output_path') and task.output_path:
           output_map[task.output_path].append(task.id)
   
   for output_path, task_ids in output_map.items():
       if len(task_ids) > 1:
           for i, task_a in enumerate(task_ids):
               for task_b in task_ids[i+1:]:
                   output_conflicts.append(
                       OutputConflict(
                           task_a_id=task_a,
                           task_b_id=task_b,
                           output_path=output_path
                       )
                   )
   ```

**Output Schema**:
```python
{
    "has_conflicts": true,
    "resource_conflicts": [
        {
            "task_a_id": "feat-a-2",
            "task_b_id": "feat-c-1",
            "resource": "DATABASE",
            "wave_number": 2,
            "severity": "ERROR"
        }
    ],
    "output_conflicts": [
        {
            "task_a_id": "feat-b-3",
            "task_b_id": "feat-d-1",
            "output_path": "/output/data.json",
            "severity": "ERROR"
        }
    ],
    "constraint_conflicts": []
}
```

---

### Step 4: Global Execution Plan Building

**Input**: Validated `NormalizedPRDCollection` (no conflicts)

**Processing**:

1. **Topological Sort with Wave Generation** (Kahn's Algorithm):
   ```python
   def build_execution_waves(tasks, dependency_graph):
       # Calculate in-degree
       in_degree = {task.id: 0 for task in tasks}
       for deps in dependency_graph.values():
           for dep in deps:
               if dep in in_degree:
                   in_degree[dep] += 1
       
       # Initialize queue with zero in-degree tasks
       queue = deque([t for t in tasks if in_degree[t.id] == 0])
       waves = []
       
       while queue:
           current_wave = []
           wave_size = len(queue)
           
           for _ in range(wave_size):
               task = queue.popleft()
               current_wave.append(task)
               
               # Update in-degree for dependents
               for dependent_id in get_dependents(task.id, dependency_graph):
                   in_degree[dependent_id] -= 1
                   if in_degree[dependent_id] == 0:
                       dependent_task = get_task_by_id(dependent_id, tasks)
                       queue.append(dependent_task)
           
           # Sort tasks within wave for determinism
           current_wave.sort(key=lambda t: t.id)
           
           waves.append(ExecutionWave(
               wave_number=len(waves),
               tasks=current_wave,
               depends_on_waves=list(range(len(waves)))
           ))
       
       return waves
   ```

2. **Calculate Statistics**:
   ```python
   parallel_capacity = max(len(wave.tasks) for wave in waves)
   critical_path_length = len(waves)
   ```

**Output Schema**:
```python
{
    "execution_waves": [
        {
            "wave_number": 0,
            "tasks": [
                {
                    "id": "feat-a-1",
                    "description": "Task 1",
                    "dependencies": []
                }
            ],
            "depends_on_waves": []
        },
        {
            "wave_number": 1,
            "tasks": [
                {
                    "id": "feat-a-2",
                    "description": "Task 2",
                    "dependencies": ["feat-a-1"]
                }
            ],
            "depends_on_waves": [0]
        },
        {
            "wave_number": 2,
            "tasks": [
                {
                    "id": "feat-b-1",
                    "description": "Parent task",
                    "dependencies": ["feat-a-2"]
                }
            ],
            "depends_on_waves": [0, 1]
        },
        {
            "wave_number": 3,
            "tasks": [
                {
                    "id": "feat-b-1-sub",
                    "description": "Subtask",
                    "dependencies": ["feat-b-1"]
                }
            ],
            "depends_on_waves": [0, 1, 2]
        }
    ],
    "total_tasks": 4,
    "total_prds": 2,
    "parallel_capacity": 1,
    "critical_path_length": 4,
    "is_deterministic": true,
    "conflicts_detected": 0
}
```

---

## Data Transformations Summary

| Stage | Input | Output | Key Transformation |
|-------|-------|--------|-------------------|
| Intake | List[Union[PRD, AdvancedPRD]] | NormalizedPRDCollection | Type-specific processing |
| Resolution | NormalizedPRDCollection | CrossPRDValidationResult | Graph construction + validation |
| Detection | Normalized + Validated | ConflictReport | Wave generation + conflict checks |
| Building | Validated (no conflicts) | GlobalExecutionPlan | Topological sort + statistics |

---

## Determinism Guarantees

### Sources of Determinism

1. **Input Processing**: Same PRDs → same tasks (Phase 2.4 and 3.1 are deterministic)
2. **Dependency Graph**: Same tasks → same graph (set operations are stable)
3. **Topological Sort**: Stable sort within waves (by task ID)
4. **Wave Generation**: Kahn's algorithm is deterministic with stable ordering

### Reproducibility Test

```python
def test_determinism():
    """Verify same inputs produce identical outputs."""
    prds = [prd1, prd2, prd3]
    
    plan1 = orchestrator.orchestrate(prds)
    plan2 = orchestrator.orchestrate(prds)
    
    assert plan1.execution_waves == plan2.execution_waves
    assert plan1.total_tasks == plan2.total_tasks
    assert plan1.parallel_capacity == plan2.parallel_capacity
```

---

## Error Propagation

```
Input Error → Intake fails → ValidationError
  └─> Example: Invalid PRD format

Normalization Success → Resolution Error → ValidationError
  └─> Example: Missing dependency reference

Resolution Success → Conflict Detected → ConflictError
  └─> Example: Resource conflict in wave

All Valid → Plan Built → GlobalExecutionPlan
  └─> Success case
```

**Error Handling Strategy**: Fail fast at first error, provide detailed context.

---

## Performance Characteristics

| Operation | Complexity | Example (100 tasks) |
|-----------|-----------|---------------------|
| PRD Normalization | O(N) | Linear in task count |
| Graph Construction | O(V + E) | ~200 operations |
| Cycle Detection | O(V + E) | ~200 operations |
| Conflict Detection | O(W × T²) | W=waves, T=tasks per wave |
| Topological Sort | O(V + E) | ~200 operations |
| **Total** | **O(V + E + W×T²)** | **< 1s for 5 PRDs** |

Where:
- V = number of tasks (vertices)
- E = number of dependencies (edges)
- W = number of waves
- T = max tasks per wave

---

## Data Flow Validation

### Invariants

1. **Task Count Preservation**: `len(input.prds.requirements) == len(output.tasks)`
2. **Dependency Closure**: All dependencies in output exist in task list
3. **Wave Ordering**: Wave N tasks only depend on waves < N
4. **Determinism**: `hash(input) == hash(output)` for same inputs

### Validation Checkpoints

- [ ] After intake: All PRDs converted to tasks
- [ ] After resolution: All dependencies valid
- [ ] After detection: No conflicts present
- [ ] After building: Wave ordering correct

---

## Backward Compatibility Data Flow

### Phase 2.4 Single PRD

```
PRD (Phase 2.4) 
  → MultiPRDOrchestrator.orchestrate([prd])
  → Intake: PRDProcessor (Phase 2.4)
  → Resolution: Single-PRD graph (trivial)
  → Detection: No cross-PRD conflicts possible
  → Building: Same waves as Phase 2.4 PRDProcessor
  → Output: GlobalExecutionPlan (compatible with Coordinator)
```

**Guarantee**: Waves identical to Phase 2.4 output.

### Phase 3.1 Single AdvancedPRD

```
AdvancedPRD (Phase 3.1)
  → MultiPRDOrchestrator.orchestrate([advanced_prd])
  → Intake: PRDDecomposer (Phase 3.1)
  → Resolution: Single-PRD graph
  → Detection: No cross-PRD conflicts
  → Building: Same waves as Phase 3.1 decomposer
  → Output: GlobalExecutionPlan
```

**Guarantee**: Waves identical to Phase 3.1 output.

---

## Appendix: Example Complete Flow

**Input**:
```python
prd1 = PRD(
    metadata=PRDMetadata(title="API", version="1.0"),
    requirements=[
        PRDRequirement(id="api-1", description="Create endpoint"),
        PRDRequirement(id="api-2", description="Add tests", dependencies=["api-1"])
    ]
)

prd2 = AdvancedPRD(
    metadata=PRDMetadata(title="UI", version="1.0"),
    requirements=[
        AdvancedPRDRequirement(
            id="ui-1", 
            description="Build UI", 
            dependencies=["api-2"],  # Cross-PRD
            resources=[ResourceType.NETWORK]
        )
    ]
)

orchestrator = MultiPRDOrchestrator()
plan = orchestrator.orchestrate([prd1, prd2])
```

**Output**:
```python
GlobalExecutionPlan(
    execution_waves=[
        ExecutionWave(wave_number=0, tasks=[api-1]),
        ExecutionWave(wave_number=1, tasks=[api-2]),
        ExecutionWave(wave_number=2, tasks=[ui-1])
    ],
    total_tasks=3,
    total_prds=2,
    parallel_capacity=1,
    critical_path_length=3,
    is_deterministic=True
)
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-28  
**Status**: Pending Approval
