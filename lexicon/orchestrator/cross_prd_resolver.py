
"""
Cross-PRD Dependency Resolver for Phase 3.2.2.

This module is responsible for:
- Resolving dependencies within and across multiple PRDs
- Validating dependency existence
- Detecting circular dependencies (DFS)
- Detecting self-dependencies
- Maintaining provenance tracking (PRD IDs)
- Ensuring deterministic graph construction

Constraints:
- Analysis-only (no execution, scheduling, or conflicts)
- Fail-fast on any validation error
- Stateless and deterministic
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
import logging

from lexicon.pipeline.advanced_prd_models import DecomposedTask
from lexicon.orchestrator.multi_prd_intake import NormalizedPRDCollection

# Error Classes
class CrossPRDError(ValueError):
    """Base class for Cross-PRD validation errors."""
    pass

class MissingDependencyError(CrossPRDError):
    """Raised when a task references a dependency that does not exist."""
    def __init__(self, missing_deps: Dict[str, List[str]], task_to_prd: Dict[str, str]):
        """
        Args:
            missing_deps: {task_id: [missing_dep_ids]}
            task_to_prd: {task_id: prd_id} used to enrich error message
        """
        msg_parts = ["Missing dependencies detected:"]
        for task_id, deps in sorted(missing_deps.items()):
            prd_id = task_to_prd.get(task_id, "unknown")
            msg_parts.append(
                f"  - Task '{task_id}' (PRD: {prd_id}) depends on non-existent: {', '.join(sorted(deps))}"
            )
        super().__init__("\n".join(msg_parts))

class CircularDependencyError(CrossPRDError):
    """Raised when circular dependencies are detected in the global graph."""
    def __init__(self, cycles: List[List[str]], task_to_prd: Dict[str, str]):
        """
        Args:
            cycles: List of cycles, each cycle is a list of task IDs forming a loop
            task_to_prd: {task_id: prd_id} used to enrich error message
        """
        msg_parts = ["Circular dependencies detected:"]
        for i, cycle in enumerate(cycles, 1):
            cycle_desc = []
            for tid in cycle:
                pid = task_to_prd.get(tid, "unknown")
                cycle_desc.append(f"{tid} ({pid})")
            msg_parts.append(f"  {i}. {' -> '.join(cycle_desc)}")
        super().__init__("\n".join(msg_parts))

class SelfDependencyError(CrossPRDError):
    """Raised when a task depends on itself."""
    def __init__(self, task_ids: List[str], task_to_prd: Dict[str, str]):
        msg_parts = ["Self-dependencies detected:"]
        for tid in sorted(task_ids):
            pid = task_to_prd.get(tid, "unknown")
            msg_parts.append(f"  - Task '{tid}' (PRD: {pid}) depends on itself")
        super().__init__("\n".join(msg_parts))

@dataclass(frozen=True)
class DependencyEdge:
    """
    Provenance-tracked dependency edge.
    
    Attributes:
        source_task_id: The dependent task
        target_task_id: The task being depended on
        source_prd_id: PRD ID of the source task
        target_prd_id: PRD ID of the target task
    """
    source_task_id: str
    target_task_id: str
    source_prd_id: str
    target_prd_id: str

@dataclass(frozen=True)
class ResolvedDependencyGraph:
    """
    Immutable representation of the resolved cross-PRD dependency graph.
    
    Attributes:
        tasks: Dictionary of all tasks {task_id: DecomposedTask}
        edges: List of all validated dependency edges
        adjacency_list: Global graph {task_id: Set[dependency_task_ids]}
        prd_sources: Provenance mapping {task_id: prd_id}
        orchestration_id: ID of the orchestration run
    """
    tasks: Dict[str, DecomposedTask]
    edges: List[DependencyEdge]
    adjacency_list: Dict[str, Set[str]]
    prd_sources: Dict[str, str]
    orchestration_id: str

class CrossPRDResolver:
    """
    Resolver for Phase 3.2.2: Cross-PRD Dependency Validation.
    """
    
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def resolve(self, normalized: NormalizedPRDCollection) -> ResolvedDependencyGraph:
        """
        Resolve and validate dependencies across all tasks in the collection.
        
        Args:
            normalized: The output of Multi-PRD Intake (Phase 3.2.1)
            
        Returns:
            ResolvedDependencyGraph if valid
            
        Raises:
            MissingDependencyError: If any task references a non-existent task
            CircularDependencyError: If any cycles are detected
            SelfDependencyError: If any task depends on itself
        """
        all_tasks = {t.task_id: t for t in normalized.tasks}
        task_id_list = sorted(all_tasks.keys())  # Deterministic order
        
        adjacency_list: Dict[str, Set[str]] = {tid: set() for tid in task_id_list}
        edges: List[DependencyEdge] = []
        
        missing_deps = {}
        self_deps = []
        
        # Step 1: Basic validation and adjacency construction
        for tid in task_id_list:
            task = all_tasks[tid]
            source_prd_id = normalized.prd_sources[tid]
            
            for dep_id in sorted(task.dependencies):  # Deterministic sorting of dependencies
                # Check Self-Dependency
                if dep_id == tid:
                    self_deps.append(tid)
                    continue
                
                # Check Existence
                if dep_id not in all_tasks:
                    if tid not in missing_deps:
                        missing_deps[tid] = []
                    missing_deps[tid].append(dep_id)
                    continue
                
                # Create adjacency
                adjacency_list[tid].add(dep_id)
                
                # Create edge with provenance
                target_prd_id = normalized.prd_sources[dep_id]
                edges.append(DependencyEdge(
                    source_task_id=tid,
                    target_task_id=dep_id,
                    source_prd_id=source_prd_id,
                    target_prd_id=target_prd_id
                ))
        
        # Fail-fast if any basic errors found
        if self_deps:
            raise SelfDependencyError(self_deps, normalized.prd_sources)
        
        if missing_deps:
            raise MissingDependencyError(missing_deps, normalized.prd_sources)
            
        # Step 2: Cycle Detection (DFS)
        cycles = self._detect_cycles(adjacency_list, task_id_list)
        if cycles:
            raise CircularDependencyError(cycles, normalized.prd_sources)
            
        # Step 3: Construct Immutable Result
        return ResolvedDependencyGraph(
            tasks=all_tasks,
            edges=edges,
            adjacency_list=adjacency_list,
            prd_sources=normalized.prd_sources,
            orchestration_id=normalized.orchestration_metadata.orchestration_id
        )

    def _detect_cycles(self, adjacency_list: Dict[str, Set[str]], nodes: List[str]) -> List[List[str]]:
        """
        DFS-based cycle detection on the adjacency list.
        
        Returns a list of cycles found. Each cycle is a list of node IDs forming a loop.
        """
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            # Use deterministic iteration order for neighbors
            for neighbor in sorted(adjacency_list.get(node, set())):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Cycle detected
                    try:
                        idx = path.index(neighbor)
                        cycles.append(path[idx:] + [neighbor])
                    except ValueError:
                        # Should not happen if neighbor is in rec_stack
                        pass
            
            rec_stack.remove(node)
            
        # Iterate nodes in deterministic order
        for node in nodes:
            if node not in visited:
                dfs(node, [])
                
        return cycles
