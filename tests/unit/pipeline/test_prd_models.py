"""
Tests for PRD data models.

Validates the Pydantic/dataclass models used for PRDs and tasks.
"""

import pytest
from datetime import datetime, UTC
from lexicon.pipeline.prd_models import (
    PRD,
    PRDMetadata,
    PRDRequirement,
    PRDTask,
    PRDValidationResult,
    RequirementPriority,
    RequirementType,
    TaskStatus,
)


class TestRequirementType:
    """Tests for RequirementType enum."""

    def test_all_types_defined(self):
        """Test that all expected requirement types are defined."""
        assert RequirementType.FEATURE == "feature"
        assert RequirementType.BUGFIX == "bugfix"
        assert RequirementType.ENHANCEMENT == "enhancement"
        assert RequirementType.DOCUMENTATION == "documentation"
        assert RequirementType.TESTING == "testing"
        assert RequirementType.INFRASTRUCTURE == "infrastructure"


class TestRequirementPriority:
    """Tests for RequirementPriority enum."""

    def test_all_priorities_defined(self):
        """Test that all expected priorities are defined."""
        assert RequirementPriority.CRITICAL == "critical"
        assert RequirementPriority.HIGH == "high"
        assert RequirementPriority.MEDIUM == "medium"
        assert RequirementPriority.LOW == "low"


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_all_statuses_defined(self):
        """Test that all expected task statuses are defined."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.SKIPPED == "skipped"


class TestPRDMetadata:
    """Tests for PRDMetadata dataclass."""

    def test_create_valid_metadata(self):
        """Test creating valid PRD metadata."""
        metadata = PRDMetadata(
            title="Test PRD",
            version="1.0.0",
            author="Test Author",
            tags=["test", "demo"],
        )
        
        assert metadata.title == "Test PRD"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "demo"]
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="title cannot be empty"):
            PRDMetadata(title="", version="1.0.0", author="Author")

    def test_empty_version_raises_error(self):
        """Test that empty version raises ValueError."""
        with pytest.raises(ValueError, match="version cannot be empty"):
            PRDMetadata(title="Title", version="", author="Author")

    def test_empty_author_raises_error(self):
        """Test that empty author raises ValueError."""
        with pytest.raises(ValueError, match="author cannot be empty"):
            PRDMetadata(title="Title", version="1.0.0", author="")


class TestPRDRequirement:
    """Tests for PRDRequirement dataclass."""

    def test_create_valid_requirement(self):
        """Test creating a valid requirement."""
        req = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Test requirement",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            dependencies=["REQ-000"],
            estimated_effort=8.5,
        )
        
        assert req.id == "REQ-001"
        assert req.type == RequirementType.FEATURE
        assert req.priority == RequirementPriority.HIGH
        assert req.description == "Test requirement"
        assert len(req.acceptance_criteria) == 2
        assert len(req.dependencies) == 1
        assert req.estimated_effort == 8.5

    def test_empty_id_raises_error(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="ID cannot be empty"):
            PRDRequirement(
                id="",
                type=RequirementType.FEATURE,
                priority=RequirementPriority.HIGH,
                description="Test",
            )

    def test_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            PRDRequirement(
                id="REQ-001",
                type=RequirementType.FEATURE,
                priority=RequirementPriority.HIGH,
                description="",
            )

    def test_negative_effort_raises_error(self):
        """Test that negative estimated effort raises ValueError."""
        with pytest.raises(ValueError, match="cannot be negative"):
            PRDRequirement(
                id="REQ-001",
                type=RequirementType.FEATURE,
                priority=RequirementPriority.HIGH,
                description="Test",
                estimated_effort=-5.0,
            )


class TestPRD:
    """Tests for PRD dataclass."""

    def test_create_valid_prd(self):
        """Test creating a valid PRD."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req1 = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Requirement 1",
        )
        req2 = PRDRequirement(
            id="REQ-002",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.MEDIUM,
            description="Requirement 2",
            dependencies=["REQ-001"],
        )
        
        prd = PRD(
            metadata=metadata,
            overview="Test overview",
            requirements=[req1, req2],
            constraints=["Constraint 1"],
            out_of_scope=["Out of scope 1"],
            success_criteria=["Success 1"],
        )
        
        assert prd.metadata.title == "Test PRD"
        assert len(prd.requirements) == 2
        assert len(prd.constraints) == 1
        assert len(prd.out_of_scope) == 1
        assert len(prd.success_criteria) == 1

    def test_empty_overview_raises_error(self):
        """Test that empty overview raises ValueError."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Test",
        )
        
        with pytest.raises(ValueError, match="overview cannot be empty"):
            PRD(metadata=metadata, overview="", requirements=[req])

    def test_no_requirements_raises_error(self):
        """Test that PRD with no requirements raises ValueError."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        
        with pytest.raises(ValueError, match="at least one requirement"):
            PRD(metadata=metadata, overview="Overview", requirements=[])

    def test_duplicate_requirement_ids_raises_error(self):
        """Test that duplicate requirement IDs raise ValueError."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req1 = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Req 1",
        )
        req2 = PRDRequirement(
            id="REQ-001",  # Duplicate ID
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Req 2",
        )
        
        with pytest.raises(ValueError, match="Duplicate requirement IDs"):
            PRD(metadata=metadata, overview="Overview", requirements=[req1, req2])

    def test_invalid_dependency_raises_error(self):
        """Test that invalid dependency reference raises ValueError."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Test",
            dependencies=["REQ-999"],  # Non-existent dependency
        )
        
        with pytest.raises(ValueError, match="unknown requirement"):
            PRD(metadata=metadata, overview="Overview", requirements=[req])

    def test_get_requirement_by_id(self):
        """Test getting a requirement by ID."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Test",
        )
        prd = PRD(metadata=metadata, overview="Overview", requirements=[req])
        
        found = prd.get_requirement("REQ-001")
        assert found is not None
        assert found.id == "REQ-001"
        
        not_found = prd.get_requirement("REQ-999")
        assert not_found is None

    def test_get_requirements_by_priority(self):
        """Test getting requirements by priority."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req1 = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="High priority",
        )
        req2 = PRDRequirement(
            id="REQ-002",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.LOW,
            description="Low priority",
        )
        prd = PRD(metadata=metadata, overview="Overview", requirements=[req1, req2])
        
        high_reqs = prd.get_requirements_by_priority(RequirementPriority.HIGH)
        assert len(high_reqs) == 1
        assert high_reqs[0].id == "REQ-001"

    def test_get_requirements_by_type(self):
        """Test getting requirements by type."""
        metadata = PRDMetadata(
            title="Test PRD", version="1.0.0", author="Author"
        )
        req1 = PRDRequirement(
            id="REQ-001",
            type=RequirementType.FEATURE,
            priority=RequirementPriority.HIGH,
            description="Feature",
        )
        req2 = PRDRequirement(
            id="REQ-002",
            type=RequirementType.TESTING,
            priority=RequirementPriority.HIGH,
            description="Test",
        )
        prd = PRD(metadata=metadata, overview="Overview", requirements=[req1, req2])
        
        feature_reqs = prd.get_requirements_by_type(RequirementType.FEATURE)
        assert len(feature_reqs) == 1
        assert feature_reqs[0].id == "REQ-001"


class TestPRDTask:
    """Tests for PRDTask dataclass."""

    def test_create_valid_task(self):
        """Test creating a valid PRD task."""
        task = PRDTask(
            task_id="task-001",
            requirement_id="REQ-001",
            description="Test task",
            context={"key": "value"},
        )
        
        assert task.task_id == "task-001"
        assert task.requirement_id == "REQ-001"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.context["key"] == "value"
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None

    def test_empty_task_id_raises_error(self):
        """Test that empty task ID raises ValueError."""
        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            PRDTask(
                task_id="",
                requirement_id="REQ-001",
                description="Test",
            )

    def test_empty_requirement_id_raises_error(self):
        """Test that empty requirement ID raises ValueError."""
        with pytest.raises(ValueError, match="Requirement ID cannot be empty"):
            PRDTask(
                task_id="task-001",
                requirement_id="",
                description="Test",
            )

    def test_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            PRDTask(
                task_id="task-001",
                requirement_id="REQ-001",
                description="",
            )

    def test_mark_completed(self):
        """Test marking task as completed."""
        task = PRDTask(
            task_id="task-001",
            requirement_id="REQ-001",
            description="Test",
        )
        
        task.mark_completed()
        
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None

    def test_mark_failed(self):
        """Test marking task as failed."""
        task = PRDTask(
            task_id="task-001",
            requirement_id="REQ-001",
            description="Test",
        )
        
        task.mark_failed()
        
        assert task.status == TaskStatus.FAILED
        assert task.completed_at is not None

    def test_mark_in_progress(self):
        """Test marking task as in progress."""
        task = PRDTask(
            task_id="task-001",
            requirement_id="REQ-001",
            description="Test",
        )
        
        task.mark_in_progress()
        
        assert task.status == TaskStatus.IN_PROGRESS


class TestPRDValidationResult:
    """Tests for PRDValidationResult dataclass."""

    def test_create_valid_result(self):
        """Test creating a valid validation result."""
        result = PRDValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert isinstance(result.validated_at, datetime)

    def test_add_error(self):
        """Test adding an error."""
        result = PRDValidationResult(is_valid=True)
        
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_add_warning(self):
        """Test adding a warning."""
        result = PRDValidationResult(is_valid=True)
        
        result.add_warning("Test warning")
        
        assert result.is_valid is True  # Warnings don't affect validity
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Test warning"
