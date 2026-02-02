
"""
Multi-PRD Conflict Detector for Phase 3.2.3.

This module detects conflicts across multiple PRDs, including:
- Resource overlaps within the same execution wave.
- Output path collisions across all tasks.

Constraints:
- Fail-fast on first critical conflict.
- Deterministic behavior (stable ordering).
- No task execution or scheduling logic.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from collections import deque

from lexicon.pipeline.advanced_prd_models import DecomposedTask, ResourceType
from lexicon.orchestrator.cross_prd_resolver import ResolvedDependencyGraph

# Exceptions
class ResourceConflictError(Exception):
    """Raised when multiple tasks in the same wave use the same exclusive resource."""
    pass

class OutputConflictError(Exception):
    """Raised when multiple tasks attempt to write to the same output path."""
    pass

# Data Structures
@dataclass(frozen=True)
class ResourceConflict:
    """Represents a conflict between tasks over a shared resource."""
    task_ids: List[str]
    resource: str

@dataclass(frozen=True)
class OutputConflict:
    """Represents a conflict between tasks over the same output path."""
    task_ids: List[str]
    output_path: str

@dataclass(frozen=True)
class ConflictReport:
    """Immutable report containing all detected conflicts."""
    resource_conflicts: List[ResourceConflict] = field(default_factory=list)
    output_conflicts: List[OutputConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        """Check if any conflicts were detected."""
        return len(self.resource_conflicts) > 0 or len(self.output_conflicts) > 0

class ConflictDetector:
    """
    Detector for Multi-PRD conflicts in Phase 3.2.3.
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

    def _generate_preliminary_waves(self) -> List[List[DecomposedTask]]:
        """
        Generate preliminary waves using Kahn's algorithm for dependency-aware grouping.
        This is for analysis only; final waves are built by GlobalPlanBuilder.
        
        Returns:
            List of waves, each containing a list of tasks.
        """
        # Calculate in-degrees
        in_degree = {tid: 0 for tid in self.tasks_by_id}
        for tid, deps in self.graph.adjacency_list.items():
            for dep in deps:
                # In-degree is number of tasks depending on this task
                # Wait, Kahn's usually uses in-degree as number of dependencies remaining.
                # In our adjacency_list, adjacency_list[tid] = {dependencies}
                pass
        
        # Recalculate correctly: in_degree[task] = number of dependencies it HAS.
        in_degree = {tid: len(deps) for tid, deps in self.graph.adjacency_list.items()}
        
        # Build inverse adjacency for easy lookup of dependents
        dependents = {tid: set() for tid in self.tasks_by_id}
        for tid, deps in self.graph.adjacency_list.items():
            for dep in deps:
                dependents[dep].add(tid)
        
        waves = []
        # Start with tasks that have 0 dependencies
        queue = deque(sorted([tid for tid, degree in in_degree.items() if degree == 0]))
        
        while queue:
            current_wave_ids = []
            wave_size = len(queue)
            
            for _ in range(wave_size):
                tid = queue.popleft()
                current_wave_ids.append(tid)
                
            # Sort IDs for determinism
            current_wave_ids.sort()
            
            wave_tasks = [self.tasks_by_id[tid] for tid in current_wave_ids]
            waves.append(wave_tasks)
            
            # Find next wave candidates
            next_candidates = []
            for tid in current_wave_ids:
                for dependent_tid in sorted(dependents[tid]):
                    in_degree[dependent_tid] -= 1
                    if in_degree[dependent_tid] == 0:
                        next_candidates.append(dependent_tid)
            
            queue.extend(sorted(next_candidates))
            
        return waves

    def detect_resource_conflicts(self) -> ConflictReport:
        """
        Detect resource overlaps within each execution wave.
        Only "exclusive" resources like DATABASE or FILE_WRITE cause conflicts.
        
        Returns:
            ConflictReport with resource conflicts found.
        """
        waves = self._generate_preliminary_waves()
        conflicts = []
        
        # Resources that cannot be shared in parallel
        EXCLUSIVE_RESOURCES = {
            ResourceType.DATABASE,
            ResourceType.FILE_WRITE,
            ResourceType.COMPUTE, # Assuming compute resources are exclusive per task for now
            "database", # String fallbacks
            "file_write"
        }
        
        for wave in waves:
            resource_usage: Dict[str, List[str]] = {}
            for task in wave:
                for resource in task.resources:
                    if resource in EXCLUSIVE_RESOURCES:
                        if resource not in resource_usage:
                            resource_usage[resource] = []
                        resource_usage[resource].append(task.task_id)
            
            # Check for overlaps
            for resource, tids in sorted(resource_usage.items()):
                if len(tids) > 1:
                    conflicts.append(ResourceConflict(task_ids=sorted(tids), resource=str(resource)))
                    
        return ConflictReport(resource_conflicts=conflicts)

    def detect_output_conflicts(self) -> ConflictReport:
        """
        Detect global output path collisions across all tasks.
        
        Returns:
            ConflictReport with output conflicts found.
        """
        output_usage: Dict[str, List[str]] = {}
        for tid, task in sorted(self.tasks_by_id.items()):
            # Check metadata for output_path (standard in Phase 3 models)
            output_path = task.metadata.get("output_path")
            if output_path:
                if output_path not in output_usage:
                    output_usage[output_path] = []
                output_usage[output_path].append(tid)
        
        conflicts = []
        for path, tids in sorted(output_usage.items()):
            if len(tids) > 1:
                conflicts.append(OutputConflict(task_ids=sorted(tids), output_path=path))
                
        return ConflictReport(output_conflicts=conflicts)

    def detect(self) -> ConflictReport:
        """
        Run all conflict detection checks.
        Fail-fast: raises exception on first critical conflict.
        
        Returns:
            ConflictReport if multiple non-critical conflicts are collected (future use),
            but currently raises on first found.
        """
        # Global output conflicts first (easiest to check)
        output_report = self.detect_output_conflicts()
        if output_report.output_conflicts:
            conflict = output_report.output_conflicts[0]
            tids_str = ", ".join([f"{tid} ({self.prd_sources[tid]})" for tid in conflict.task_ids])
            raise OutputConflictError(
                f"Output path conflict detected for '{conflict.output_path}'. "
                f"Tasks: {tids_str}"
            )
            
        # Resource conflicts within waves
        resource_report = self.detect_resource_conflicts()
        if resource_report.resource_conflicts:
            conflict = resource_report.resource_conflicts[0]
            tids_str = ", ".join([f"{tid} ({self.prd_sources[tid]})" for tid in conflict.task_ids])
            raise ResourceConflictError(
                f"Resource conflict detected for '{conflict.resource}'. "
                f"Tasks: {tids_str}"
            )
            
        return ConflictReport()
