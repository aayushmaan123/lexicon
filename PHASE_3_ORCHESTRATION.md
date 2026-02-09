# Phase 3.2: Multi-PRD Orchestration

## Overview

Phase 3.2 enables coordinated execution across multiple PRDs with intelligent scheduling, conflict detection, and support for both sequential and parallel task execution. This allows managing complex multi-project workflows while maintaining determinism and full auditability.

**Status**: Design Document  
**Dependencies**: Phase 2.3 (Execution Loop), Phase 2.4 (PRD Pipeline), Phase 3.1 (Advanced PRD Handling)  
**Version**: 1.0

---

## Objectives

1. Schedule tasks across multiple PRDs with dependency awareness
2. Detect and prevent resource/output conflicts
3. Enable parallel execution for independent tasks
4. Maintain sequential execution for dependent tasks
5. Aggregate execution results across all PRDs
6. Preserve full backward compatibility with single-PRD execution

---

## Architecture

### Components

```
lexicon/
└── orchestrator/
    ├── multi_prd_scheduler.py      # Cross-PRD scheduling
    ├── conflict_detector.py        # Resource/output conflict analysis
    ├── parallel_executor.py        # Parallel task execution
    └── execution_aggregator.py     # Result aggregation
```

---

## Multi-PRD Scheduler

### Core Logic

```python
from typing import List, Dict, Set, Tuple
from lexicon.pipeline import PRD, PRDTask
from lexicon.orchestrator import Coordinator

class MultiPRDScheduler:
    """Schedule tasks across multiple PRDs."""
    
    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator
        self.conflict_detector = ConflictDetector()
    
    def schedule(self, prds: List[PRD]) -> TaskExecutionPlan:
        """Create execution plan for multiple PRDs."""
        # Step 1: Convert all PRDs to tasks
        all_tasks = []
        for prd in prds:
            tasks = self._prd_to_tasks(prd)
            all_tasks.extend(tasks)
        
        # Step 2: Build global dependency graph
        dependency_graph = self._build_global_graph(all_tasks)
        
        # Step 3: Detect conflicts
        conflicts = self.conflict_detector.detect_conflicts(all_tasks)
        
        # Step 4: Resolve conflicts (add implicit dependencies)
        resolved_graph = self._resolve_conflicts(dependency_graph, conflicts)
        
        # Step 5: Create execution waves (tasks that can run in parallel)
        execution_waves = self._create_execution_waves(resolved_graph)
        
        return TaskExecutionPlan(
            waves=execution_waves,
            total_tasks=len(all_tasks),
            conflicts_detected=len(conflicts),
            conflicts_resolved=conflicts
        )
    
    def _build_global_graph(self, tasks: List[PRDTask]) -> Dict[str, Set[str]]:
        """Build dependency graph across all tasks."""
        graph = {task.id: set(task.dependencies) for task in tasks}
        
        # Validate all dependencies exist
        all_ids = set(graph.keys())
        for task_id, deps in graph.items():
            missing = deps - all_ids
            if missing:
                raise ValueError(
                    f"Task {task_id} has missing dependencies: {missing}"
                )
        
        return graph
    
    def _create_execution_waves(
        self, 
        graph: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """Group tasks into waves (parallel execution within wave)."""
        waves = []
        remaining = set(graph.keys())
        completed = set()
        
        while remaining:
            # Find tasks with all dependencies satisfied
            ready = {
                task_id for task_id in remaining
                if graph[task_id].issubset(completed)
            }
            
            if not ready:
                raise ValueError("Circular dependency detected in global graph")
            
            waves.append(list(ready))
            completed.update(ready)
            remaining -= ready
        
        return waves
```

### Execution Plan

```python
from dataclasses import dataclass
from typing import List

@dataclass
class TaskExecutionPlan:
    """Execution plan for multi-PRD workflow."""
    waves: List[List[str]]  # Each wave = tasks that can run in parallel
    total_tasks: int
    conflicts_detected: int
    conflicts_resolved: List[TaskConflict]
    
    def get_wave_count(self) -> int:
        """Number of sequential waves."""
        return len(self.waves)
    
    def get_max_parallelism(self) -> int:
        """Maximum parallelism (largest wave size)."""
        return max(len(wave) for wave in self.waves) if self.waves else 0
```

---

## Conflict Detection

### Conflict Detector

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Set

class ConflictType(str, Enum):
    FILE_WRITE = "file_write"  # Multiple tasks write to same file
    RESOURCE_CONTENTION = "resource_contention"  # Limited resource
    OUTPUT_COLLISION = "output_collision"  # Same output artifact

@dataclass
class TaskConflict:
    """Represents a conflict between tasks."""
    type: ConflictType
    task_ids: List[str]
    resource: str  # File path, API endpoint, etc.
    severity: str  # "error" or "warning"

class ConflictDetector:
    """Detect resource and output conflicts across tasks."""
    
    def detect_conflicts(self, tasks: List[PRDTask]) -> List[TaskConflict]:
        """Analyze tasks for potential conflicts."""
        conflicts = []
        
        # Check file write conflicts
        conflicts.extend(self._detect_file_conflicts(tasks))
        
        # Check resource contention
        conflicts.extend(self._detect_resource_conflicts(tasks))
        
        # Check output collisions
        conflicts.extend(self._detect_output_conflicts(tasks))
        
        return conflicts
    
    def _detect_file_conflicts(self, tasks: List[PRDTask]) -> List[TaskConflict]:
        """Detect tasks that write to the same file."""
        conflicts = []
        file_writers = {}  # file_path -> List[task_id]
        
        for task in tasks:
            # Extract file writes from task context
            files = task.context.get("output_files", [])
            for file_path in files:
                if file_path not in file_writers:
                    file_writers[file_path] = []
                file_writers[file_path].append(task.id)
        
        # Identify conflicts
        for file_path, writers in file_writers.items():
            if len(writers) > 1:
                conflicts.append(TaskConflict(
                    type=ConflictType.FILE_WRITE,
                    task_ids=writers,
                    resource=file_path,
                    severity="error"
                ))
        
        return conflicts
    
    def _detect_resource_conflicts(self, tasks: List[PRDTask]) -> List[TaskConflict]:
        """Detect resource contention (e.g., API rate limits)."""
        conflicts = []
        resource_users = {}  # resource_id -> List[task_id]
        
        for task in tasks:
            resources = task.context.get("resources", [])
            for resource in resources:
                # Check for rate-limited resources
                if resource.get("rate_limited", False):
                    resource_id = resource["id"]
                    if resource_id not in resource_users:
                        resource_users[resource_id] = []
                    resource_users[resource_id].append(task.id)
        
        # Flag resources with multiple concurrent users
        for resource_id, users in resource_users.items():
            if len(users) > 1:
                conflicts.append(TaskConflict(
                    type=ConflictType.RESOURCE_CONTENTION,
                    task_ids=users,
                    resource=resource_id,
                    severity="warning"  # May be acceptable
                ))
        
        return conflicts
    
    def _detect_output_conflicts(self, tasks: List[PRDTask]) -> List[TaskConflict]:
        """Detect tasks producing same output artifact."""
        conflicts = []
        output_producers = {}  # artifact_name -> List[task_id]
        
        for task in tasks:
            outputs = task.context.get("outputs", [])
            for output in outputs:
                if output not in output_producers:
                    output_producers[output] = []
                output_producers[output].append(task.id)
        
        for output, producers in output_producers.items():
            if len(producers) > 1:
                conflicts.append(TaskConflict(
                    type=ConflictType.OUTPUT_COLLISION,
                    task_ids=producers,
                    resource=output,
                    severity="error"
                ))
        
        return conflicts
```

---

## Parallel Execution

### Parallel Executor

```python
import asyncio
from typing import List, Dict
from lexicon.orchestrator import Coordinator, ExecutionResult

class ParallelExecutor:
    """Execute tasks in parallel where safe."""
    
    def __init__(self, coordinator: Coordinator, max_parallel: int = 3):
        self.coordinator = coordinator
        self.max_parallel = max_parallel
    
    async def execute_wave(
        self, 
        task_ids: List[str], 
        tasks: Dict[str, PRDTask]
    ) -> Dict[str, ExecutionResult]:
        """Execute a wave of tasks in parallel."""
        # Limit parallelism
        semaphore = asyncio.Semaphore(self.max_parallel)
        
        async def execute_task(task_id: str) -> Tuple[str, ExecutionResult]:
            async with semaphore:
                task = tasks[task_id]
                # Execute via existing coordinator
                result = await self._execute_async(task)
                return task_id, result
        
        # Execute all tasks in wave
        results = await asyncio.gather(*[
            execute_task(task_id) for task_id in task_ids
        ])
        
        return dict(results)
    
    async def _execute_async(self, task: PRDTask) -> ExecutionResult:
        """Async wrapper for coordinator.execute()."""
        # Run coordinator.execute() in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.coordinator.execute,
            task.description,
            task.context
        )
        return result
    
    def execute_wave_sync(
        self, 
        task_ids: List[str], 
        tasks: Dict[str, PRDTask]
    ) -> Dict[str, ExecutionResult]:
        """Synchronous fallback for wave execution."""
        results = {}
        for task_id in task_ids:
            task = tasks[task_id]
            result = self.coordinator.execute(task.description, task.context)
            results[task_id] = result
        return results
```

---

## Execution Aggregator

### Result Aggregation

```python
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class MultiPRDResult:
    """Aggregated results from multi-PRD execution."""
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    skipped_tasks: int
    execution_time_seconds: float
    task_results: Dict[str, ExecutionResult]
    execution_traces: List[ExecutionTrace]
    
    @property
    def success_rate(self) -> float:
        """Percentage of successful tasks."""
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100

class ExecutionAggregator:
    """Aggregate results from multi-PRD execution."""
    
    def aggregate(
        self, 
        task_results: Dict[str, ExecutionResult]
    ) -> MultiPRDResult:
        """Combine results from all tasks."""
        successful = sum(1 for r in task_results.values() if r.success)
        failed = sum(1 for r in task_results.values() if not r.success)
        
        traces = [r.trace for r in task_results.values()]
        total_time = sum(r.execution_time for r in task_results.values())
        
        return MultiPRDResult(
            total_tasks=len(task_results),
            successful_tasks=successful,
            failed_tasks=failed,
            skipped_tasks=0,  # Phase 3.2 doesn't skip tasks
            execution_time_seconds=total_time,
            task_results=task_results,
            execution_traces=traces
        )
```

---

## Usage Example

```python
from lexicon.orchestrator import MultiPRDScheduler, ParallelExecutor, ExecutionAggregator
from lexicon.pipeline import PRDPipeline

# Initialize components
coordinator = Coordinator()
scheduler = MultiPRDScheduler(coordinator)
executor = ParallelExecutor(coordinator, max_parallel=3)
aggregator = ExecutionAggregator()

# Load multiple PRDs
prd1 = load_prd("project_a.json")
prd2 = load_prd("project_b.json")
prd3 = load_prd("project_c.json")

# Create execution plan
plan = scheduler.schedule([prd1, prd2, prd3])

print(f"Total tasks: {plan.total_tasks}")
print(f"Execution waves: {plan.get_wave_count()}")
print(f"Max parallelism: {plan.get_max_parallelism()}")
print(f"Conflicts detected: {plan.conflicts_detected}")

# Execute plan
all_results = {}
for wave_idx, wave_task_ids in enumerate(plan.waves):
    print(f"Executing wave {wave_idx + 1}/{len(plan.waves)}...")
    wave_results = executor.execute_wave_sync(wave_task_ids, tasks)
    all_results.update(wave_results)

# Aggregate results
final_result = aggregator.aggregate(all_results)
print(f"Success rate: {final_result.success_rate:.1f}%")
```

---

## Testing Strategy

### Unit Tests
- Task scheduling across multiple PRDs
- Conflict detection (file, resource, output)
- Wave creation with dependencies
- Parallel execution simulation

### Integration Tests
- End-to-end multi-PRD workflow
- Conflict resolution
- Parallel vs. sequential execution comparison
- Result aggregation

### Performance Tests
- 10 PRDs with 100 tasks total
- Measure scheduling overhead
- Validate parallelism speedup

---

## Backward Compatibility

- Single-PRD execution unchanged (use Phase 2.4 directly)
- Multi-PRD is opt-in feature
- All Phase 2.3 execution loop features preserved

---

## Performance Targets

- **Scheduling**: < 2 seconds for 50 tasks across 5 PRDs
- **Conflict Detection**: < 1 second for 50 tasks
- **Parallel Speedup**: 2-3x for fully independent tasks
- **Memory Overhead**: < 100 MB for 100 tasks

---

## Out of Scope

- **Real-Time Updates**: Batch execution only
- **Dynamic Replanning**: Execution plan fixed after scheduling
- **Distributed Execution**: Local parallel execution only
- **Priority Preemption**: Tasks execute in wave order

---

## Success Criteria

- ✅ Schedule 5+ PRDs with 50+ total tasks
- ✅ Detect and resolve all file/resource conflicts
- ✅ Execute independent tasks in parallel
- ✅ Aggregate results correctly
- ✅ 100% backward compatible with Phase 2.3/2.4

---

## Summary

Phase 3.2 enables multi-PRD workflows with intelligent scheduling, conflict detection, and parallel execution while maintaining full backward compatibility and determinism.
