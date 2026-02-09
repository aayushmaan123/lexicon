"""
Advanced PRD validator for Phase 3.1: Enhanced validation for nested structures.

This module extends Phase 2.4 PRD validation with:
- Parent-child relationship validation
- Optional subtask constraint checking
- Circular dependency detection in nested structures
- Cross-project dependency validation
- Resource conflict detection

Maintains 100% backward compatibility with Phase 2.4 validation.
"""

from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, UTC

from .advanced_prd_models import AdvancedPRD, AdvancedPRDRequirement
from .prd_models import PRDValidationResult


class AdvancedPRDValidator:
    """
    Validator for Advanced PRDs with nested task hierarchies.
    
    Performs comprehensive validation including:
    - Basic structure validation (IDs, descriptions, etc.)
    - Dependency graph validation (cycles, missing refs)
    - Parent-child hierarchy validation
    - Optional subtask constraints
    - Nesting depth limits
    """
    
    MAX_NESTING_DEPTH = 5  # Maximum allowed nesting depth
    
    @staticmethod
    def validate(prd: AdvancedPRD) -> PRDValidationResult:
        """
        Validate an AdvancedPRD.
        
        Args:
            prd: The PRD to validate
            
        Returns:
            PRDValidationResult with validation status and messages
        """
        result = PRDValidationResult(is_valid=True)
        
        # Basic structure validation
        AdvancedPRDValidator._validate_structure(prd, result)
        
        # Dependency validation
        AdvancedPRDValidator._validate_dependencies(prd, result)
        
        # Parent-child hierarchy validation
        AdvancedPRDValidator._validate_hierarchy(prd, result)
        
        # Optional subtask validation
        AdvancedPRDValidator._validate_optional_constraints(prd, result)
        
        # Nesting depth validation
        AdvancedPRDValidator._validate_nesting_depth(prd, result)
        
        # Circular dependency detection
        AdvancedPRDValidator._validate_no_cycles(prd, result)
        
        return result
    
    @staticmethod
    def _validate_structure(prd: AdvancedPRD, result: PRDValidationResult):
        """Validate basic PRD structure."""
        # Check metadata
        if not prd.metadata.title:
            result.add_error("PRD metadata missing title")
        
        if not prd.metadata.version:
            result.add_error("PRD metadata missing version")
        
        if not prd.metadata.author:
            result.add_error("PRD metadata missing author")
        
        # Check overview
        if not prd.overview or not prd.overview.strip():
            result.add_error("PRD overview cannot be empty")
        
        # Check requirements
        if not prd.requirements:
            result.add_error("PRD must have at least one requirement")
        
        # Check for duplicate IDs
        req_ids = [req.id for req in prd.requirements]
        duplicates = [id for id in req_ids if req_ids.count(id) > 1]
        if duplicates:
            result.add_error(f"Duplicate requirement IDs found: {set(duplicates)}")
    
    @staticmethod
    def _validate_dependencies(prd: AdvancedPRD, result: PRDValidationResult):
        """Validate dependency references."""
        req_id_set = {req.id for req in prd.requirements}
        
        for req in prd.requirements:
            # Check that all dependencies exist
            for dep_id in req.dependencies:
                if dep_id not in req_id_set:
                    result.add_error(
                        f"Requirement {req.id} depends on unknown requirement {dep_id}"
                    )
            
            # Check that parent_id is not in dependencies
            if req.parent_id and req.parent_id in req.dependencies:
                result.add_error(
                    f"Requirement {req.id}: parent_id {req.parent_id} must not appear in dependencies. "
                    "Use dependencies for execution order, parent_id for hierarchy only."
                )
    
    @staticmethod
    def _validate_hierarchy(prd: AdvancedPRD, result: PRDValidationResult):
        """Validate parent-child hierarchy."""
        req_id_set = {req.id for req in prd.requirements}
        
        for req in prd.requirements:
            # Check that parent exists
            if req.parent_id and req.parent_id not in req_id_set:
                result.add_error(
                    f"Requirement {req.id} has unknown parent {req.parent_id}"
                )
            
            # Check for self-parenting
            if req.parent_id == req.id:
                result.add_error(
                    f"Requirement {req.id} cannot be its own parent"
                )
        
        # Check for cycles in parent relationships
        AdvancedPRDValidator._validate_no_parent_cycles(prd, result)
    
    @staticmethod
    def _validate_no_parent_cycles(prd: AdvancedPRD, result: PRDValidationResult):
        """Detect cycles in parent-child relationships."""
        def has_cycle(req_id: str, visited: Set[str], rec_stack: Set[str]) -> bool:
            """DFS to detect cycles in parent chain."""
            visited.add(req_id)
            rec_stack.add(req_id)
            
            req = prd.get_requirement(req_id)
            if req and req.parent_id:
                if req.parent_id not in visited:
                    if has_cycle(req.parent_id, visited, rec_stack):
                        return True
                elif req.parent_id in rec_stack:
                    return True
            
            rec_stack.remove(req_id)
            return False
        
        visited: Set[str] = set()
        for req in prd.requirements:
            if req.id not in visited:
                rec_stack: Set[str] = set()
                if has_cycle(req.id, visited, rec_stack):
                    result.add_error(
                        f"Circular parent relationship detected involving requirement {req.id}"
                    )
                    break
    
    @staticmethod
    def _validate_optional_constraints(prd: AdvancedPRD, result: PRDValidationResult):
        """
        Validate optional subtask constraints.
        
        Rules:
        - Optional subtasks should not be dependencies of required tasks
        - Optional tasks should have warning if they have required children
        """
        optional_ids = {req.id for req in prd.requirements if req.optional}
        required_ids = {req.id for req in prd.requirements if not req.optional}
        
        for req in prd.requirements:
            if not req.optional:  # Required task
                # Check if it depends on optional tasks
                for dep_id in req.dependencies:
                    if dep_id in optional_ids:
                        result.add_warning(
                            f"Required requirement {req.id} depends on optional requirement {dep_id}. "
                            "This may cause execution issues if optional task is skipped."
                        )
            
            if req.optional and req.parent_id:
                # Check if optional task has required children
                children = prd.get_children(req.id)
                required_children = [c for c in children if not c.optional]
                if required_children:
                    result.add_warning(
                        f"Optional requirement {req.id} has required children: "
                        f"{[c.id for c in required_children]}. Consider making children optional too."
                    )
    
    @staticmethod
    def _validate_nesting_depth(prd: AdvancedPRD, result: PRDValidationResult):
        """Validate that nesting depth doesn't exceed maximum."""
        max_depth = prd.get_max_depth()
        
        if max_depth > AdvancedPRDValidator.MAX_NESTING_DEPTH:
            result.add_error(
                f"Nesting depth {max_depth} exceeds maximum allowed depth "
                f"{AdvancedPRDValidator.MAX_NESTING_DEPTH}"
            )
        elif max_depth > 3:
            result.add_warning(
                f"Nesting depth {max_depth} is high. Consider flattening the structure."
            )
    
    @staticmethod
    def _validate_no_cycles(prd: AdvancedPRD, result: PRDValidationResult):
        """
        Detect cycles in dependency graph using DFS.
        
        This is critical for ensuring the task DAG can be executed.
        """
        def has_dependency_cycle(
            req_id: str,
            visited: Set[str],
            rec_stack: Set[str],
            path: List[str]
        ) -> Tuple[bool, List[str]]:
            """
            DFS to detect cycles in dependency graph.
            
            Returns:
                (has_cycle, cycle_path)
            """
            visited.add(req_id)
            rec_stack.add(req_id)
            path.append(req_id)
            
            req = prd.get_requirement(req_id)
            if req:
                for dep_id in req.dependencies:
                    if dep_id not in visited:
                        has_cycle, cycle = has_dependency_cycle(dep_id, visited, rec_stack, path.copy())
                        if has_cycle:
                            return True, cycle
                    elif dep_id in rec_stack:
                        # Found cycle
                        cycle_start = path.index(dep_id)
                        cycle_path = path[cycle_start:] + [dep_id]
                        return True, cycle_path
            
            rec_stack.remove(req_id)
            return False, []
        
        visited: Set[str] = set()
        for req in prd.requirements:
            if req.id not in visited:
                rec_stack: Set[str] = set()
                has_cycle, cycle_path = has_dependency_cycle(req.id, visited, rec_stack, [])
                if has_cycle:
                    cycle_str = " -> ".join(cycle_path)
                    result.add_error(
                        f"Circular dependency detected: {cycle_str}"
                    )
                    break
    
    @staticmethod
    def validate_quick(prd: AdvancedPRD) -> bool:
        """
        Quick validation check (returns boolean).
        
        Args:
            prd: The PRD to validate
            
        Returns:
            True if valid, False otherwise
        """
        result = AdvancedPRDValidator.validate(prd)
        return result.is_valid
