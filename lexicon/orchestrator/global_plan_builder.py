
"""
Global Plan Builder for Phase 3.2.4.

This module constructs the final, deterministic execution plan from 
multiple PRDs using topological sorting (Kahn's algorithm).

Constraints:
- Dependency-ordered and deterministic.
- No execution or conflict resolution logic.
- Stable sorting by task ID within waves.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from collections import deque

from lexicon.pipeline.advanced_prd_models import DecomposedTask
from lexicon.orchestrator.cross_prd_resolver import ResolvedDependencyGraph

# Data Structures
@dataclass(frozen=True)
class ExecutionWave:
    """A group of tasks that can be executed in parallel."""
    tasks: List[DecomposedTask]
    wave_number: int

@dataclass(frozen=True)
class GlobalExecutionPlan:
    """The complete execution plan across all orchestrated PRDs."""
    waves: List[ExecutionWave]
    total_tasks: int
    total_prds: int
    orchestration_id: str

class GlobalPlanBuilder:
    """
    Builder for generating the Global Execution Plan in Phase 3.2.4.
    """

    def __init__(self, resolved_graph: ResolvedDependencyGraph):
        """
        Initialize with a validated dependency graph.
        
        Args:
            resolved_graph: Output from CrossPRDResolver
        """
        self.graph = resolved_graph
        self.tasks_by_id = resolved_graph.tasks
        self.prd_sources = resolved_graph.prd_sources

    def build_execution_waves(self) -> List[ExecutionWave]:
        """
        Construct execution waves using Kahn's algorithm.
        Tasks in each wave have all dependencies satisfied by prior waves.
        
        Returns:
            List of ExecutionWave objects in order.
        """
        # Calculate initial in-degrees (number of dependencies for each task)
        in_degree = {tid: len(deps) for tid, deps in self.graph.adjacency_list.items()}
        
        # Build inverse adjacency (task_id -> set of tasks that depend on it)
        dependents = {tid: set() for tid in self.tasks_by_id}
        for tid, deps in self.graph.adjacency_list.items():
            for dep in deps:
                dependents[dep].add(tid)
        
        waves = []
        # Queue starts with tasks that have no dependencies
        # Sort for determinism
        queue = deque(sorted([tid for tid, degree in in_degree.items() if degree == 0]))
        
        wave_count = 0
        while queue:
            current_wave_ids = []
            wave_size = len(queue)
            
            # Extract all current candidates for this wave
            for _ in range(wave_size):
                tid = queue.popleft()
                current_wave_ids.append(tid)
            
            # Sort IDs within the wave for determinism
            current_wave_ids.sort()
            
            # Create the ExecutionWave object
            wave_tasks = [self.tasks_by_id[tid] for tid in current_wave_ids]
            waves.append(ExecutionWave(tasks=wave_tasks, wave_number=wave_count))
            wave_count += 1
            
            # Propagate: reduce in-degree of dependents
            next_candidates = []
            for tid in current_wave_ids:
                for dep_tid in dependents[tid]:
                    in_degree[dep_tid] -= 1
                    if in_degree[dep_tid] == 0:
                        next_candidates.append(dep_tid)
            
            # Add new candidates to queue, maintaining lexicographical order
            queue.extend(sorted(next_candidates))
            
        return waves

    def generate_global_plan(self) -> GlobalExecutionPlan:
        """
        Generate the complete GlobalExecutionPlan.
        
        Returns:
            A GlobalExecutionPlan ready for the Coordinator.
        """
        waves = self.build_execution_waves()
        
        return GlobalExecutionPlan(
            waves=waves,
            total_tasks=len(self.tasks_by_id),
            total_prds=len(set(self.prd_sources.values())),
            orchestration_id=self.graph.orchestration_id
        )

    def validate_plan(self) -> None:
        """
        Validate the generated plan for sanity (defense-in-depth).
        Ensures all tasks are assigned to a wave and no cycles remain.
        
        Raises:
            ValueError: If the plan is incomplete.
        """
        waves = self.build_execution_waves()
        assigned_task_count = sum(len(wave.tasks) for wave in waves)
        
        if assigned_task_count != len(self.tasks_by_id):
            missing = len(self.tasks_by_id) - assigned_task_count
            raise ValueError(
                f"Plan validation failed: {missing} tasks were not assigned to any wave. "
                "This indicates an unexpected cycle or dependency issue."
            )
