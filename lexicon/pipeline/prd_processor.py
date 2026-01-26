"""
PRD processor for converting PRD requirements into executable tasks.

This module transforms validated PRD requirements into PRDTask objects
that can be executed by the Coordinator.
"""

import uuid
from typing import Dict, List
from lexicon.pipeline.prd_models import PRD, PRDRequirement, PRDTask, TaskStatus


class PRDProcessor:
    """
    Processor for converting PRD requirements into executable tasks.
    
    This class performs deterministic transformation of requirements
    into tasks, handling dependency ordering and task description generation.
    """

    def __init__(self):
        """Initialize the PRD processor."""
        pass

    def process(self, prd: PRD) -> List[PRDTask]:
        """
        Process a PRD into a list of executable tasks.
        
        Tasks are ordered respecting dependencies (dependencies come first).
        
        Args:
            prd: Validated PRD to process
            
        Returns:
            List of PRDTask objects in dependency order
        """
        # Build dependency graph
        dep_graph = self._build_dependency_graph(prd.requirements)
        
        # Topological sort to get dependency order
        ordered_req_ids = self._topological_sort(dep_graph)
        
        # Create tasks in order
        tasks = []
        req_map = {req.id: req for req in prd.requirements}
        
        for req_id in ordered_req_ids:
            req = req_map[req_id]
            task = self._create_task_from_requirement(req, prd)
            tasks.append(task)
        
        return tasks

    def _build_dependency_graph(
        self, requirements: List[PRDRequirement]
    ) -> Dict[str, List[str]]:
        """
        Build a dependency graph from requirements.
        
        Returns:
            Dictionary mapping requirement ID to list of dependency IDs
        """
        graph = {}
        for req in requirements:
            graph[req.id] = req.dependencies.copy()
        return graph

    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Perform topological sort on dependency graph.
        
        Args:
            graph: Adjacency list of dependencies
            
        Returns:
            List of requirement IDs in dependency order
            
        Raises:
            ValueError: If circular dependency is detected
        """
        # Kahn's algorithm
        in_degree = {node: 0 for node in graph}
        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Start with nodes that have no dependencies
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # For each node that depends on current node
            for other_node in graph:
                if node in graph[other_node]:
                    in_degree[other_node] -= 1
                    if in_degree[other_node] == 0:
                        queue.append(other_node)
        
        if len(result) != len(graph):
            raise ValueError("Circular dependency detected in requirements")
        
        # Reverse to get dependencies-first order
        return list(reversed(result))

    def _create_task_from_requirement(
        self, requirement: PRDRequirement, prd: PRD
    ) -> PRDTask:
        """
        Create a PRDTask from a requirement.
        
        Args:
            requirement: Source requirement
            prd: Parent PRD for context
            
        Returns:
            PRDTask ready for execution
        """
        task_id = f"task-{requirement.id}-{uuid.uuid4().hex[:8]}"
        
        # Build task description for agents
        description = self._build_task_description(requirement, prd)
        
        # Build context dictionary
        context = {
            "requirement_id": requirement.id,
            "requirement_type": requirement.type.value,
            "requirement_priority": requirement.priority.value,
            "acceptance_criteria": requirement.acceptance_criteria,
            "dependencies": requirement.dependencies,
            "prd_title": prd.metadata.title,
            "prd_version": prd.metadata.version,
        }
        
        if requirement.estimated_effort:
            context["estimated_effort"] = requirement.estimated_effort
        
        if requirement.metadata:
            context["requirement_metadata"] = requirement.metadata
        
        return PRDTask(
            task_id=task_id,
            requirement_id=requirement.id,
            description=description,
            status=TaskStatus.PENDING,
            context=context,
        )

    def _build_task_description(
        self, requirement: PRDRequirement, prd: PRD
    ) -> str:
        """
        Build a detailed task description for agent execution.
        
        The description provides all context needed for agents to understand
        and execute the task.
        
        Args:
            requirement: Source requirement
            prd: Parent PRD
            
        Returns:
            Task description string
        """
        lines = [
            f"Requirement ID: {requirement.id}",
            f"Type: {requirement.type.value}",
            f"Priority: {requirement.priority.value}",
            "",
            "Description:",
            requirement.description,
        ]
        
        if requirement.acceptance_criteria:
            lines.append("")
            lines.append("Acceptance Criteria:")
            for i, criterion in enumerate(requirement.acceptance_criteria, 1):
                lines.append(f"{i}. {criterion}")
        
        if requirement.dependencies:
            lines.append("")
            lines.append(f"Dependencies: {', '.join(requirement.dependencies)}")
        
        if prd.constraints:
            lines.append("")
            lines.append("Constraints to consider:")
            for constraint in prd.constraints:
                lines.append(f"- {constraint}")
        
        return "\n".join(lines)
