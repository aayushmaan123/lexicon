"""
PRD validator for checking PRD structural and semantic correctness.

This module validates PRDs without LLM interpretation, focusing on:
- Structural integrity (all required fields present)
- Dependency consistency (no circular dependencies)
- Content quality (non-empty descriptions, valid formats)
"""

from typing import List, Set
from lexicon.pipeline.prd_models import PRD, PRDRequirement, PRDValidationResult


class PRDValidator:
    """
    Validator for Product Requirements Documents.
    
    Performs deterministic validation checks on PRDs to ensure they are
    well-formed and internally consistent.
    """

    def __init__(self):
        """Initialize the PRD validator."""
        pass

    def validate(self, prd: PRD) -> PRDValidationResult:
        """
        Validate a PRD for structural and semantic correctness.
        
        Args:
            prd: PRD to validate
            
        Returns:
            Validation result with errors and warnings
        """
        result = PRDValidationResult(is_valid=True)
        
        # Validate metadata
        self._validate_metadata(prd, result)
        
        # Validate overview
        self._validate_overview(prd, result)
        
        # Validate requirements
        self._validate_requirements(prd, result)
        
        # Validate dependencies
        self._validate_dependencies(prd, result)
        
        # Validate acceptance criteria
        self._validate_acceptance_criteria(prd, result)
        
        # Validate success criteria
        self._validate_success_criteria(prd, result)
        
        return result

    def _validate_metadata(self, prd: PRD, result: PRDValidationResult):
        """Validate PRD metadata."""
        if not prd.metadata.title or len(prd.metadata.title) < 5:
            result.add_error("PRD title must be at least 5 characters")
        
        if not prd.metadata.version:
            result.add_error("PRD must have a version")
        
        if not prd.metadata.author:
            result.add_error("PRD must have an author")

    def _validate_overview(self, prd: PRD, result: PRDValidationResult):
        """Validate PRD overview."""
        if not prd.overview or len(prd.overview) < 20:
            result.add_error("PRD overview must be at least 20 characters")
        
        if len(prd.overview) > 5000:
            result.add_warning("PRD overview is very long (>5000 chars)")

    def _validate_requirements(self, prd: PRD, result: PRDValidationResult):
        """Validate individual requirements."""
        if not prd.requirements:
            result.add_error("PRD must have at least one requirement")
            return
        
        if len(prd.requirements) > 100:
            result.add_warning(
                f"PRD has {len(prd.requirements)} requirements - consider breaking into smaller PRDs"
            )
        
        # Check for duplicate IDs
        req_ids = [req.id for req in prd.requirements]
        if len(req_ids) != len(set(req_ids)):
            result.add_error("Duplicate requirement IDs found")
        
        # Validate each requirement
        for req in prd.requirements:
            if not req.description or len(req.description) < 10:
                result.add_error(
                    f"Requirement {req.id} description must be at least 10 characters"
                )
            
            if req.estimated_effort and req.estimated_effort > 1000:
                result.add_warning(
                    f"Requirement {req.id} has very high effort estimate (>1000h)"
                )

    def _validate_dependencies(self, prd: PRD, result: PRDValidationResult):
        """Validate requirement dependencies for cycles and validity."""
        req_id_set = {req.id for req in prd.requirements}
        
        # Check that all dependencies exist
        for req in prd.requirements:
            for dep_id in req.dependencies:
                if dep_id not in req_id_set:
                    result.add_error(
                        f"Requirement {req.id} depends on unknown requirement {dep_id}"
                    )
        
        # Check for circular dependencies
        cycles = self._find_circular_dependencies(prd.requirements)
        if cycles:
            for cycle in cycles:
                result.add_error(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )

    def _find_circular_dependencies(
        self, requirements: List[PRDRequirement]
    ) -> List[List[str]]:
        """
        Find circular dependencies using DFS.
        
        Returns:
            List of cycles (each cycle is a list of requirement IDs)
        """
        # Build adjacency list
        graph = {req.id: req.dependencies for req in requirements}
        
        cycles = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        for req_id in graph:
            if req_id not in visited:
                dfs(req_id, [])
        
        return cycles

    def _validate_acceptance_criteria(self, prd: PRD, result: PRDValidationResult):
        """Validate acceptance criteria for requirements."""
        for req in prd.requirements:
            if not req.acceptance_criteria:
                result.add_warning(
                    f"Requirement {req.id} has no acceptance criteria"
                )
            
            if len(req.acceptance_criteria) > 20:
                result.add_warning(
                    f"Requirement {req.id} has many acceptance criteria (>20)"
                )

    def _validate_success_criteria(self, prd: PRD, result: PRDValidationResult):
        """Validate overall success criteria."""
        if not prd.success_criteria:
            result.add_warning("PRD has no overall success criteria")
        
        if len(prd.success_criteria) > 20:
            result.add_warning("PRD has many success criteria (>20)")
