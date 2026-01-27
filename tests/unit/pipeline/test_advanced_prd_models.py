"""
Tests for Phase 3.1 advanced PRD models.

Tests cover:
- AdvancedPRDRequirement creation and validation
- AdvancedPRD creation and hierarchy operations
- DecomposedTask creation
- Resource type handling
- Optional/required subtask logic
"""

import pytest
from datetime import datetime, UTC

from lexicon.pipeline.advanced_prd_models import (
    AdvancedPRD,
    AdvancedPRDRequirement,
    DecomposedTask,
    ResourceType,
)
from lexicon.pipeline.prd_models import PRDMetadata, RequirementPriority


class TestResourceType:
    """Test ResourceType enum."""
    
    def test_resource_types(self):
        """Test all resource type values."""
        assert ResourceType.FILE_WRITE == "file_write"
        assert ResourceType.FILE_READ == "file_read"
        assert ResourceType.DATABASE == "database"
        assert ResourceType.NETWORK == "network"
        assert ResourceType.COMPUTE == "compute"
        assert ResourceType.MEMORY == "memory"


class TestAdvancedPRDRequirement:
    """Test AdvancedPRDRequirement model."""
    
    def test_create_basic_requirement(self):
        """Test creating a basic requirement with minimal fields."""
        req = AdvancedPRDRequirement(
            id="req1",
            description="Test requirement",
        )
        
        assert req.id == "req1"
        assert req.description == "Test requirement"
        assert req.dependencies == []
        assert req.type == "feature"
        assert req.parent_id is None
        assert req.optional is False
        assert req.priority == RequirementPriority.MEDIUM
    
    def test_create_nested_requirement(self):
        """Test creating a nested requirement with parent."""
        req = AdvancedPRDRequirement(
            id="req1.1",
            description="Subtask",
            parent_id="req1",
            optional=True,
            priority=RequirementPriority.LOW,
        )
        
        assert req.parent_id == "req1"
        assert req.optional is True
        assert not req.is_root()
        assert not req.is_required()
    
    def test_create_with_resources(self):
        """Test requirement with resources."""
        req = AdvancedPRDRequirement(
            id="req1",
            description="Database task",
            resources=["database", "network"],
        )
        
        assert req.resources == ["database", "network"]
        resource_types = req.get_resource_types()
        assert ResourceType.DATABASE in resource_types
        assert ResourceType.NETWORK in resource_types
    
    def test_parent_id_not_in_dependencies(self):
        """Test that parent_id cannot be in dependencies."""
        with pytest.raises(ValueError, match="parent_id must not appear in dependencies"):
            AdvancedPRDRequirement(
                id="req1.1",
                description="Bad requirement",
                parent_id="req1",
                dependencies=["req1"],  # Invalid!
            )
    
    def test_empty_id_rejected(self):
        """Test that empty ID is rejected."""
        with pytest.raises(ValueError, match="Requirement ID cannot be empty"):
            AdvancedPRDRequirement(
                id="",
                description="Test",
            )
    
    def test_empty_description_rejected(self):
        """Test that empty description is rejected."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            AdvancedPRDRequirement(
                id="req1",
                description="",
            )
    
    def test_negative_estimated_hours(self):
        """Test that negative hours are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            AdvancedPRDRequirement(
                id="req1",
                description="Test",
                estimated_hours=-5.0,
            )
    
    def test_is_root(self):
        """Test is_root method."""
        root = AdvancedPRDRequirement(id="req1", description="Root")
        child = AdvancedPRDRequirement(id="req2", description="Child", parent_id="req1")
        
        assert root.is_root()
        assert not child.is_root()
    
    def test_is_required(self):
        """Test is_required method."""
        required = AdvancedPRDRequirement(id="req1", description="Required", optional=False)
        optional = AdvancedPRDRequirement(id="req2", description="Optional", optional=True)
        
        assert required.is_required()
        assert not optional.is_required()


class TestAdvancedPRD:
    """Test AdvancedPRD model."""
    
    def test_create_flat_prd(self):
        """Test creating a flat PRD (backward compatible with Phase 2.4)."""
        metadata = PRDMetadata(
            title="Test PRD",
            version="1.0",
            author="Test Author",
        )
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="First req"),
            AdvancedPRDRequirement(id="req2", description="Second req", dependencies=["req1"]),
        ]
        
        prd = AdvancedPRD(
            metadata=metadata,
            overview="Test overview",
            requirements=requirements,
        )
        
        assert prd.metadata.title == "Test PRD"
        assert len(prd.requirements) == 2
        assert not prd.has_nested_structure()
        assert prd.get_max_depth() == 0
    
    def test_create_nested_prd(self):
        """Test creating a nested PRD with parent-child relationships."""
        metadata = PRDMetadata(
            title="Nested PRD",
            version="1.0",
            author="Test",
        )
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="Root task"),
            AdvancedPRDRequirement(id="req1.1", description="Subtask 1", parent_id="req1"),
            AdvancedPRDRequirement(id="req1.2", description="Subtask 2", parent_id="req1"),
            AdvancedPRDRequirement(id="req1.1.1", description="Sub-subtask", parent_id="req1.1"),
        ]
        
        prd = AdvancedPRD(
            metadata=metadata,
            overview="Nested test",
            requirements=requirements,
        )
        
        assert prd.has_nested_structure()
        assert prd.get_max_depth() == 2  # req1 -> req1.1 -> req1.1.1
        
        roots = prd.get_root_requirements()
        assert len(roots) == 1
        assert roots[0].id == "req1"
        
        children = prd.get_children("req1")
        assert len(children) == 2
        assert {c.id for c in children} == {"req1.1", "req1.2"}
    
    def test_get_subtree(self):
        """Test getting subtree of requirements."""
        metadata = PRDMetadata(title="Test", version="1.0", author="Test")
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="Root"),
            AdvancedPRDRequirement(id="req1.1", description="Child 1", parent_id="req1"),
            AdvancedPRDRequirement(id="req1.2", description="Child 2", parent_id="req1"),
            AdvancedPRDRequirement(id="req1.1.1", description="Grandchild", parent_id="req1.1"),
            AdvancedPRDRequirement(id="req2", description="Another root"),
        ]
        
        prd = AdvancedPRD(
            metadata=metadata,
            overview="Test",
            requirements=requirements,
        )
        
        subtree = prd.get_subtree("req1")
        subtree_ids = [r.id for r in subtree]
        
        assert "req1" in subtree_ids
        assert "req1.1" in subtree_ids
        assert "req1.2" in subtree_ids
        assert "req1.1.1" in subtree_ids
        assert "req2" not in subtree_ids
    
    def test_get_required_and_optional(self):
        """Test filtering by required/optional status."""
        metadata = PRDMetadata(title="Test", version="1.0", author="Test")
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="Required 1", optional=False),
            AdvancedPRDRequirement(id="req2", description="Optional 1", optional=True),
            AdvancedPRDRequirement(id="req3", description="Required 2", optional=False),
        ]
        
        prd = AdvancedPRD(
            metadata=metadata,
            overview="Test",
            requirements=requirements,
        )
        
        required = prd.get_required_requirements()
        optional = prd.get_optional_requirements()
        
        assert len(required) == 2
        assert len(optional) == 1
        assert {r.id for r in required} == {"req1", "req3"}
        assert optional[0].id == "req2"
    
    def test_duplicate_ids_rejected(self):
        """Test that duplicate IDs are rejected."""
        metadata = PRDMetadata(title="Test", version="1.0", author="Test")
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="First"),
            AdvancedPRDRequirement(id="req1", description="Duplicate"),
        ]
        
        with pytest.raises(ValueError, match="Duplicate requirement IDs"):
            AdvancedPRD(
                metadata=metadata,
                overview="Test",
                requirements=requirements,
            )
    
    def test_unknown_parent_rejected(self):
        """Test that unknown parent is rejected."""
        metadata = PRDMetadata(title="Test", version="1.0", author="Test")
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="Child", parent_id="unknown"),
        ]
        
        with pytest.raises(ValueError, match="unknown parent"):
            AdvancedPRD(
                metadata=metadata,
                overview="Test",
                requirements=requirements,
            )
    
    def test_unknown_dependency_rejected(self):
        """Test that unknown dependency is rejected."""
        metadata = PRDMetadata(title="Test", version="1.0", author="Test")
        
        requirements = [
            AdvancedPRDRequirement(id="req1", description="Test", dependencies=["unknown"]),
        ]
        
        with pytest.raises(ValueError, match="unknown requirement"):
            AdvancedPRD(
                metadata=metadata,
                overview="Test",
                requirements=requirements,
            )


class TestDecomposedTask:
    """Test DecomposedTask model."""
    
    def test_create_basic_task(self):
        """Test creating a basic decomposed task."""
        task = DecomposedTask(
            task_id="task1",
            requirement_id="req1",
            description="Test task",
        )
        
        assert task.task_id == "task1"
        assert task.requirement_id == "req1"
        assert task.description == "Test task"
        assert task.dependencies == []
        assert not task.is_optional
        assert task.priority == RequirementPriority.MEDIUM
    
    def test_create_with_dependencies(self):
        """Test creating task with dependencies."""
        task = DecomposedTask(
            task_id="task2",
            requirement_id="req2",
            description="Dependent task",
            dependencies=["task1"],
            is_optional=True,
            priority=RequirementPriority.HIGH,
        )
        
        assert task.dependencies == ["task1"]
        assert task.is_optional
        assert task.priority == RequirementPriority.HIGH
    
    def test_create_with_resources(self):
        """Test creating task with resources."""
        task = DecomposedTask(
            task_id="task1",
            requirement_id="req1",
            description="Task with resources",
            resources=[ResourceType.DATABASE, ResourceType.NETWORK],
        )
        
        assert len(task.resources) == 2
        assert ResourceType.DATABASE in task.resources
        assert ResourceType.NETWORK in task.resources
    
    def test_empty_task_id_rejected(self):
        """Test that empty task ID is rejected."""
        with pytest.raises(ValueError, match="Task ID cannot be empty"):
            DecomposedTask(
                task_id="",
                requirement_id="req1",
                description="Test",
            )
    
    def test_empty_requirement_id_rejected(self):
        """Test that empty requirement ID is rejected."""
        with pytest.raises(ValueError, match="Requirement ID cannot be empty"):
            DecomposedTask(
                task_id="task1",
                requirement_id="",
                description="Test",
            )
    
    def test_empty_description_rejected(self):
        """Test that empty description is rejected."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            DecomposedTask(
                task_id="task1",
                requirement_id="req1",
                description="",
            )
