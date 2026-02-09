"""
Advanced PRD data models for Phase 3.1: Nested task hierarchies and enhanced features.

This module extends Phase 2.4 PRD models with support for:
- Nested task hierarchies (parent/subtask relationships)
- Optional vs. required subtasks
- Cross-project dependencies
- Enhanced resource and metadata tracking

All extensions are purely additive and maintain 100% backward compatibility with Phase 2.4.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional

from .prd_models import (
    PRDMetadata,
    RequirementType,
    RequirementPriority,
    TaskStatus,
)


class ResourceType(str, Enum):
    """Types of resources that a task might need."""
    
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    DATABASE = "database"
    NETWORK = "network"
    COMPUTE = "compute"
    MEMORY = "memory"


@dataclass
class AdvancedPRDRequirement:
    """
    Enhanced PRD requirement with support for nested hierarchies and advanced features.
    
    This extends Phase 2.4 PRDRequirement with Phase 3.1 capabilities while
    maintaining full backward compatibility.
    
    Core fields (from Phase 2.4):
        id: Unique identifier for the requirement
        description: Detailed description
        dependencies: IDs of requirements this depends on (explicit only)
        type: Type of requirement (feature, bugfix, etc.)
    
    Phase 3.1 extensions (all optional, purely additive):
        parent_id: Parent requirement ID (informational only, does NOT imply dependency)
        optional: Whether this subtask is optional (default False = required)
        priority: Priority level for scheduling hints
        estimated_hours: Effort estimate (informational only)
        external_dependencies: Cross-project dependencies (strings, not enforced)
        resources: Resource types this task needs (for conflict detection)
        acceptance_criteria: Success criteria for this requirement
        tags: Categorization tags
        assignee: Optional assignee (informational only)
    
    CRITICAL CONSTRAINTS:
    - parent_id does NOT create implicit dependencies
    - Execution order determined ONLY by dependencies field
    - All Phase 3.1 fields are optional and backward compatible
    """
    
    # Core Phase 2.4 fields (required)
    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    type: str = "feature"  # Compatible with RequirementType enum
    
    # Phase 3.1 extensions (all optional)
    parent_id: Optional[str] = None  # Informational only, NOT a dependency
    optional: bool = False  # False = required, True = optional
    priority: RequirementPriority = RequirementPriority.MEDIUM
    estimated_hours: Optional[float] = None  # Informational only
    external_dependencies: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)  # ResourceType values
    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    assignee: Optional[str] = None  # Informational only
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate requirement fields."""
        if not self.id or not self.id.strip():
            raise ValueError("Requirement ID cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Requirement description cannot be empty")
        if self.estimated_hours is not None and self.estimated_hours < 0:
            raise ValueError("Estimated effort cannot be negative")
        
        # Validate that parent_id is not in dependencies
        # (parent_id is informational only, dependencies are for execution order)
        if self.parent_id and self.parent_id in self.dependencies:
            raise ValueError(
                f"Requirement {self.id}: parent_id must not appear in dependencies. "
                "Use dependencies for execution order, parent_id for hierarchy only."
            )
    
    def is_root(self) -> bool:
        """Check if this is a root-level requirement (no parent)."""
        return self.parent_id is None
    
    def is_required(self) -> bool:
        """Check if this requirement is required (not optional)."""
        return not self.optional
    
    def get_resource_types(self) -> List[ResourceType]:
        """Convert resource strings to ResourceType enums."""
        result = []
        for res in self.resources:
            try:
                result.append(ResourceType(res))
            except ValueError:
                # Invalid resource type, skip
                pass
        return result


@dataclass
class AdvancedPRD:
    """
    Enhanced PRD with support for nested task hierarchies.
    
    This extends Phase 2.4 PRD with Phase 3.1 nested task support while
    maintaining 100% backward compatibility.
    
    Core fields (from Phase 2.4):
        metadata: PRD metadata
        overview: High-level overview/summary
        requirements: List of requirements
        constraints: List of constraints
        out_of_scope: Out-of-scope items
        success_criteria: Overall success criteria
    
    Phase 3.1 note:
        requirements field now contains AdvancedPRDRequirement objects
        which support nested hierarchies via parent_id
    """
    
    metadata: PRDMetadata
    overview: str
    requirements: List[AdvancedPRDRequirement]
    constraints: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate AdvancedPRD structure."""
        if not self.overview or not self.overview.strip():
            raise ValueError("PRD overview cannot be empty")
        if not self.requirements:
            raise ValueError("PRD must have at least one requirement")
        
        # Check for duplicate requirement IDs
        req_ids = [req.id for req in self.requirements]
        if len(req_ids) != len(set(req_ids)):
            raise ValueError("Duplicate requirement IDs found")
        
        req_id_set = set(req_ids)
        
        # Validate dependency references
        for req in self.requirements:
            for dep_id in req.dependencies:
                if dep_id not in req_id_set:
                    raise ValueError(
                        f"Requirement {req.id} depends on unknown requirement {dep_id}"
                    )
        
        # Validate parent_id references (parent must exist)
        for req in self.requirements:
            if req.parent_id and req.parent_id not in req_id_set:
                raise ValueError(
                    f"Requirement {req.id} has unknown parent {req.parent_id}"
                )
    
    def get_requirement(self, req_id: str) -> Optional[AdvancedPRDRequirement]:
        """Get a requirement by ID."""
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None
    
    def get_root_requirements(self) -> List[AdvancedPRDRequirement]:
        """Get all root-level requirements (no parent)."""
        return [req for req in self.requirements if req.is_root()]
    
    def get_children(self, parent_id: str) -> List[AdvancedPRDRequirement]:
        """Get all direct children of a requirement."""
        return [req for req in self.requirements if req.parent_id == parent_id]
    
    def get_subtree(self, req_id: str) -> List[AdvancedPRDRequirement]:
        """
        Get a requirement and all its descendants (recursive).
        
        Returns list in depth-first order: [node, child1, grandchild1, child2, ...]
        """
        result = []
        req = self.get_requirement(req_id)
        if not req:
            return result
        
        result.append(req)
        children = self.get_children(req_id)
        for child in children:
            result.extend(self.get_subtree(child.id))
        
        return result
    
    def get_required_requirements(self) -> List[AdvancedPRDRequirement]:
        """Get all required (non-optional) requirements."""
        return [req for req in self.requirements if req.is_required()]
    
    def get_optional_requirements(self) -> List[AdvancedPRDRequirement]:
        """Get all optional requirements."""
        return [req for req in self.requirements if req.optional]
    
    def get_requirements_by_priority(
        self, priority: RequirementPriority
    ) -> List[AdvancedPRDRequirement]:
        """Get all requirements with a specific priority."""
        return [req for req in self.requirements if req.priority == priority]
    
    def has_nested_structure(self) -> bool:
        """Check if this PRD uses nested task hierarchies."""
        return any(req.parent_id is not None for req in self.requirements)
    
    def get_max_depth(self) -> int:
        """
        Get the maximum nesting depth of the requirement tree.
        
        Returns 0 for flat PRD, 1 for one level of nesting, etc.
        """
        if not self.has_nested_structure():
            return 0
        
        def _get_depth(req_id: str, visited: set) -> int:
            if req_id in visited:
                # Cycle detected, return depth so far
                return 0
            visited.add(req_id)
            
            children = self.get_children(req_id)
            if not children:
                return 0
            
            max_child_depth = 0
            for child in children:
                child_depth = _get_depth(child.id, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)
            
            return 1 + max_child_depth
        
        max_depth = 0
        for root in self.get_root_requirements():
            depth = _get_depth(root.id, set())
            max_depth = max(max_depth, depth)
        
        return max_depth


@dataclass
class DecomposedTask:
    """
    A task after decomposition from potentially nested structure.
    
    This is the flattened representation of AdvancedPRDRequirement
    that is ready for execution by the Phase 2.3 Coordinator.
    
    Attributes:
        task_id: Unique task identifier
        requirement_id: Source requirement ID
        description: Task description for agents
        dependencies: Flattened dependency list (execution order)
        is_optional: Whether this task is optional
        priority: Priority for scheduling hints
        resources: Resource types needed (for conflict detection)
        context: Additional context for execution
        metadata: Additional metadata
    """
    
    task_id: str
    requirement_id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    is_optional: bool = False
    priority: RequirementPriority = RequirementPriority.MEDIUM
    resources: List[ResourceType] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate task fields."""
        if not self.task_id or not self.task_id.strip():
            raise ValueError("Task ID cannot be empty")
        if not self.requirement_id or not self.requirement_id.strip():
            raise ValueError("Requirement ID cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Task description cannot be empty")
