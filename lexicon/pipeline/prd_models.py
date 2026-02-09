"""
PRD data models using Pydantic for type safety and validation.

These models define the structure of Product Requirements Documents (PRDs)
and their transformation into executable tasks.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional


class RequirementType(str, Enum):
    """Type of requirement in a PRD."""

    FEATURE = "feature"
    BUGFIX = "bugfix"
    ENHANCEMENT = "enhancement"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


class RequirementPriority(str, Enum):
    """Priority level for requirements."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, Enum):
    """Status of a PRD-derived task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PRDMetadata:
    """
    Metadata for a PRD.
    
    Attributes:
        title: PRD title
        version: PRD version string
        author: PRD author
        created_at: Creation timestamp
        updated_at: Last update timestamp
        tags: Optional tags for categorization
    """

    title: str
    version: str
    author: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate metadata fields."""
        if not self.title or not self.title.strip():
            raise ValueError("PRD title cannot be empty")
        if not self.version or not self.version.strip():
            raise ValueError("PRD version cannot be empty")
        if not self.author or not self.author.strip():
            raise ValueError("PRD author cannot be empty")


@dataclass
class PRDRequirement:
    """
    A single requirement from a PRD.
    
    Attributes:
        id: Unique identifier for the requirement
        type: Type of requirement (feature, bugfix, etc.)
        priority: Priority level
        description: Detailed description
        acceptance_criteria: List of acceptance criteria
        dependencies: IDs of requirements this depends on
        estimated_effort: Optional effort estimate in hours
        metadata: Additional metadata
    """

    id: str
    type: RequirementType
    priority: RequirementPriority
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate requirement fields."""
        if not self.id or not self.id.strip():
            raise ValueError("Requirement ID cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Requirement description cannot be empty")
        if self.estimated_effort is not None and self.estimated_effort < 0:
            raise ValueError("Estimated effort cannot be negative")


@dataclass
class PRD:
    """
    Product Requirements Document.
    
    A PRD is a structured input document that defines what needs to be built.
    It does NOT contain execution logic or control flow.
    
    Attributes:
        metadata: PRD metadata
        overview: High-level overview/summary
        requirements: List of requirements
        constraints: List of constraints or limitations
        out_of_scope: Explicitly out-of-scope items
        success_criteria: Overall success criteria
    """

    metadata: PRDMetadata
    overview: str
    requirements: List[PRDRequirement]
    constraints: List[str] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate PRD structure."""
        if not self.overview or not self.overview.strip():
            raise ValueError("PRD overview cannot be empty")
        if not self.requirements:
            raise ValueError("PRD must have at least one requirement")
        
        # Check for duplicate requirement IDs
        req_ids = [req.id for req in self.requirements]
        if len(req_ids) != len(set(req_ids)):
            raise ValueError("Duplicate requirement IDs found")
        
        # Validate dependency references
        req_id_set = set(req_ids)
        for req in self.requirements:
            for dep_id in req.dependencies:
                if dep_id not in req_id_set:
                    raise ValueError(
                        f"Requirement {req.id} depends on unknown requirement {dep_id}"
                    )

    def get_requirement(self, req_id: str) -> Optional[PRDRequirement]:
        """Get a requirement by ID."""
        for req in self.requirements:
            if req.id == req_id:
                return req
        return None

    def get_requirements_by_priority(
        self, priority: RequirementPriority
    ) -> List[PRDRequirement]:
        """Get all requirements with a specific priority."""
        return [req for req in self.requirements if req.priority == priority]

    def get_requirements_by_type(
        self, req_type: RequirementType
    ) -> List[PRDRequirement]:
        """Get all requirements of a specific type."""
        return [req for req in self.requirements if req.type == req_type]


@dataclass
class PRDTask:
    """
    A task derived from a PRD requirement.
    
    Tasks are the executable units that are sent to the Coordinator.
    They are created from PRD requirements but do not store PRD state.
    
    Attributes:
        task_id: Unique task identifier
        requirement_id: Source requirement ID
        description: Task description for agents
        status: Current task status
        context: Additional context for execution
        created_at: Creation timestamp
        completed_at: Completion timestamp
    """

    task_id: str
    requirement_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate task fields."""
        if not self.task_id or not self.task_id.strip():
            raise ValueError("Task ID cannot be empty")
        if not self.requirement_id or not self.requirement_id.strip():
            raise ValueError("Requirement ID cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Task description cannot be empty")

    def mark_completed(self):
        """Mark the task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def mark_failed(self):
        """Mark the task as failed."""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now(UTC)

    def mark_in_progress(self):
        """Mark the task as in progress."""
        self.status = TaskStatus.IN_PROGRESS


@dataclass
class PRDValidationResult:
    """
    Result of PRD validation.
    
    Attributes:
        is_valid: Whether the PRD is valid
        errors: List of validation errors
        warnings: List of validation warnings
        validated_at: Validation timestamp
    """

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_error(self, error: str):
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        """Add a validation warning."""
        self.warnings.append(warning)
