"""
PRD decomposer for Phase 3.1: Flatten nested structures into executable DAG.

This module handles decomposition of nested PRD hierarchies into a flat
dependency-ordered task list ready for execution by the Phase 2.3 Coordinator.

Key responsibilities:
- Flatten nested parent-child relationships
- Preserve explicit dependencies
- Generate execution-ready task list
- Maintain optional/required status
- Topological sort for execution order

All decomposition is deterministic and based only on explicit dependencies.
"""

from collections import deque
from typing import Dict, List, Set, Tuple

from .advanced_prd_models import (
    AdvancedPRD,
    AdvancedPRDRequirement,
    DecomposedTask,
    ResourceType,
)


class PRDDecomposer:
    """
    Decomposer for flattening nested PRD structures into executable task DAGs.
    
    The decomposer:
    1. Extracts all requirements (nested and flat)
    2. Preserves explicit dependencies only
    3. Performs topological sort for execution order
    4. Creates DecomposedTask objects ready for execution
    
    CRITICAL: parent_id is informational only and does NOT create dependencies.
    Execution order is determined ONLY by the dependencies field.
    """
    
    @staticmethod
    def decompose(prd: AdvancedPRD) -> List[DecomposedTask]:
        """
        Decompose an AdvancedPRD into a flat list of executable tasks.
        
        Args:
            prd: The AdvancedPRD to decompose
            
        Returns:
            List of DecomposedTask objects in dependency order (topologically sorted)
            
        Raises:
            ValueError: If PRD contains cycles or invalid dependencies
        """
        # Step 1: Create tasks from all requirements
        tasks = PRDDecomposer._create_tasks_from_requirements(prd)
        
        # Step 2: Topologically sort tasks by dependencies
        sorted_tasks = PRDDecomposer._topological_sort(tasks, prd)
        
        return sorted_tasks
    
    @staticmethod
    def _create_tasks_from_requirements(
        prd: AdvancedPRD
    ) -> Dict[str, DecomposedTask]:
        """
        Create DecomposedTask objects from all requirements.
        
        Args:
            prd: The AdvancedPRD
            
        Returns:
            Dictionary mapping task_id to DecomposedTask
        """
        tasks = {}
        
        for req in prd.requirements:
            # Create task description with hierarchy context if nested
            description = PRDDecomposer._create_task_description(req, prd)
            
            # Convert resource strings to ResourceType enums
            resources = req.get_resource_types()
            
            # Build context
            context = {
                "requirement_id": req.id,
                "type": req.type,
                "parent_id": req.parent_id,  # Informational only
                "acceptance_criteria": req.acceptance_criteria,
                "tags": req.tags,
                "assignee": req.assignee,
                "external_dependencies": req.external_dependencies,
            }
            
            # Build metadata
            metadata = {
                "estimated_hours": req.estimated_hours,
                **req.metadata,
            }
            
            # Create task
            task = DecomposedTask(
                task_id=req.id,  # Use requirement ID as task ID
                requirement_id=req.id,
                description=description,
                dependencies=req.dependencies.copy(),  # Explicit dependencies only
                is_optional=req.optional,
                priority=req.priority,
                resources=resources,
                context=context,
                metadata=metadata,
            )
            
            tasks[task.task_id] = task
        
        return tasks
    
    @staticmethod
    def _create_task_description(
        req: AdvancedPRDRequirement,
        prd: AdvancedPRD
    ) -> str:
        """
        Create enriched task description with hierarchy context.
        
        Args:
            req: The requirement
            prd: The parent PRD
            
        Returns:
            Enhanced description string
        """
        description_parts = [req.description]
        
        # Add parent context if this is a subtask
        if req.parent_id:
            parent = prd.get_requirement(req.parent_id)
            if parent:
                # Build ancestor chain
                ancestors = []
                current = parent
                while current:
                    ancestors.append(current.id)
                    if current.parent_id:
                        current = prd.get_requirement(current.parent_id)
                    else:
                        break
                
                # Add context
                if len(ancestors) == 1:
                    description_parts.append(
                        f"\n[Subtask of: {ancestors[0]}]"
                    )
                else:
                    description_parts.append(
                        f"\n[Subtask hierarchy: {' > '.join(reversed(ancestors))} > {req.id}]"
                    )
        
        # Add acceptance criteria if present
        if req.acceptance_criteria:
            description_parts.append("\n\nAcceptance Criteria:")
            for i, criterion in enumerate(req.acceptance_criteria, 1):
                description_parts.append(f"{i}. {criterion}")
        
        # Add external dependencies if present
        if req.external_dependencies:
            description_parts.append(
                f"\n\nExternal Dependencies: {', '.join(req.external_dependencies)}"
            )
        
        return "\n".join(description_parts)
    
    @staticmethod
    def _topological_sort(
        tasks: Dict[str, DecomposedTask],
        prd: AdvancedPRD
    ) -> List[DecomposedTask]:
        """
        Topologically sort tasks by dependencies using Kahn's algorithm.
        
        Args:
            tasks: Dictionary of tasks
            prd: The parent PRD (for validation)
            
        Returns:
            List of tasks in dependency order
            
        Raises:
            ValueError: If circular dependencies detected
        """
        # Build in-degree map
        in_degree = {task_id: 0 for task_id in tasks}
        
        # Count incoming edges
        for task in tasks.values():
            for dep_id in task.dependencies:
                if dep_id in in_degree:
                    in_degree[dep_id] += 0  # Dependency goes from dep to task
                else:
                    raise ValueError(
                        f"Task {task.task_id} depends on unknown task {dep_id}"
                    )
        
        # Actually count dependencies properly
        in_degree = {task_id: 0 for task_id in tasks}
        for task in tasks.values():
            in_degree[task.task_id] = len(task.dependencies)
        
        # Queue for tasks with no dependencies
        queue = deque([
            task_id for task_id, degree in in_degree.items() if degree == 0
        ])
        
        sorted_tasks = []
        
        while queue:
            # Get task with no remaining dependencies
            current_id = queue.popleft()
            current_task = tasks[current_id]
            sorted_tasks.append(current_task)
            
            # Find tasks that depend on current task
            for task in tasks.values():
                if current_id in task.dependencies:
                    in_degree[task.task_id] -= 1
                    if in_degree[task.task_id] == 0:
                        queue.append(task.task_id)
        
        # Check if all tasks were sorted (no cycles)
        if len(sorted_tasks) != len(tasks):
            remaining = set(tasks.keys()) - {t.task_id for t in sorted_tasks}
            raise ValueError(
                f"Circular dependencies detected. Could not sort tasks: {remaining}"
            )
        
        return sorted_tasks
    
    @staticmethod
    def decompose_with_filter(
        prd: AdvancedPRD,
        include_optional: bool = True
    ) -> List[DecomposedTask]:
        """
        Decompose PRD with optional filtering.
        
        Args:
            prd: The AdvancedPRD to decompose
            include_optional: Whether to include optional tasks
            
        Returns:
            List of DecomposedTask objects in dependency order
        """
        all_tasks = PRDDecomposer.decompose(prd)
        
        if include_optional:
            return all_tasks
        
        # Filter out optional tasks
        required_tasks = [task for task in all_tasks if not task.is_optional]
        
        # Need to also remove dependencies on optional tasks
        optional_ids = {task.task_id for task in all_tasks if task.is_optional}
        
        for task in required_tasks:
            task.dependencies = [
                dep for dep in task.dependencies if dep not in optional_ids
            ]
        
        return required_tasks
    
    @staticmethod
    def get_execution_waves(tasks: List[DecomposedTask]) -> List[List[DecomposedTask]]:
        """
        Group tasks into execution waves for potential parallel execution.
        
        A wave is a set of tasks that have no dependencies on each other
        and all their dependencies are in previous waves.
        
        Args:
            tasks: List of tasks in dependency order
            
        Returns:
            List of waves, where each wave is a list of tasks that can
            execute in parallel
        """
        waves = []
        completed = set()
        task_dict = {task.task_id: task for task in tasks}
        
        while len(completed) < len(tasks):
            # Find tasks whose dependencies are all completed
            current_wave = []
            
            for task in tasks:
                if task.task_id in completed:
                    continue
                
                # Check if all dependencies are completed
                deps_completed = all(
                    dep in completed for dep in task.dependencies
                )
                
                if deps_completed:
                    current_wave.append(task)
            
            if not current_wave:
                # Should not happen if tasks are properly sorted
                remaining = [t.task_id for t in tasks if t.task_id not in completed]
                raise ValueError(
                    f"Cannot create execution waves. Remaining tasks: {remaining}"
                )
            
            waves.append(current_wave)
            completed.update(task.task_id for task in current_wave)
        
        return waves
