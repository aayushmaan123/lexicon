"""
Unit tests for Multi-PRD Intake (Phase 3.2.1).

Tests cover:
- Multi-PRD input validation
- Mixed PRD type handling (Phase 2.4 + Phase 3.1)
- Task normalization
- Backward compatibility (single PRD)
- Statistics tracking
- Error handling
"""

import pytest
from datetime import datetime, UTC

from lexicon.orchestrator import (
    MultiPRDInput,
    MultiPRDIntake,
    MultiPRDMetadata,
    NormalizedPRDCollection,
)
from lexicon.pipeline import (
    PRD,
    PRDMetadata,
    PRDRequirement,
    RequirementType,
    RequirementPriority,
    AdvancedPRD,
    AdvancedPRDRequirement,
)


class TestMultiPRDMetadata:
    """Test MultiPRDMetadata data class."""
    
    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = MultiPRDMetadata(
            orchestration_id="orch-123",
            source="api",
            description="Test orchestration",
            tags=["test", "demo"]
        )
        
        assert metadata.orchestration_id == "orch-123"
        assert metadata.source == "api"
        assert metadata.description == "Test orchestration"
        assert metadata.tags == ["test", "demo"]
        assert isinstance(metadata.created_at, datetime)
    
    def test_empty_orchestration_id_fails(self):
        """Test that empty orchestration ID raises ValueError."""
        with pytest.raises(ValueError, match="Orchestration ID cannot be empty"):
            MultiPRDMetadata(orchestration_id="")
    
    def test_whitespace_orchestration_id_fails(self):
        """Test that whitespace-only orchestration ID fails."""
        with pytest.raises(ValueError, match="Orchestration ID cannot be empty"):
            MultiPRDMetadata(orchestration_id="   ")
    
    def test_default_values(self):
        """Test default values for optional fields."""
        metadata = MultiPRDMetadata(orchestration_id="test")
        
        assert metadata.source == "api"
        assert metadata.description == ""
        assert metadata.tags == []


class TestMultiPRDInput:
    """Test MultiPRDInput data class."""
    
    def test_valid_input_single_prd(self):
        """Test creating valid input with single PRD."""
        prd = PRD(
            metadata=PRDMetadata(title="Test", version="1.0", author="Test"),
            overview="Test PRD",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Test requirement"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="test")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        assert len(input_data.prds) == 1
        assert input_data.prds[0] == prd
    
    def test_valid_input_multiple_prds(self):
        """Test creating valid input with multiple PRDs."""
        prd1 = PRD(
            metadata=PRDMetadata(title="PRD1", version="1.0", author="Test"),
            overview="First PRD",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Test requirement"
                )
            ]
        )
        
        prd2 = AdvancedPRD(
            metadata=PRDMetadata(title="PRD2", version="1.0", author="Test"),
            overview="Second PRD",
            requirements=[
                AdvancedPRDRequirement(
                    id="req2",
                    description="Advanced requirement"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="test")
        input_data = MultiPRDInput(prds=[prd1, prd2], metadata=metadata)
        
        assert len(input_data.prds) == 2
        assert isinstance(input_data.prds[0], PRD)
        assert isinstance(input_data.prds[1], AdvancedPRD)
    
    def test_empty_prd_list_fails(self):
        """Test that empty PRD list raises ValueError."""
        metadata = MultiPRDMetadata(orchestration_id="test")
        
        with pytest.raises(ValueError, match="prds list cannot be empty"):
            MultiPRDInput(prds=[], metadata=metadata)
    
    def test_non_list_prds_fails(self):
        """Test that non-list prds raises TypeError."""
        metadata = MultiPRDMetadata(orchestration_id="test")
        
        with pytest.raises(TypeError, match="prds must be a list"):
            MultiPRDInput(prds="not a list", metadata=metadata)
    
    def test_invalid_prd_type_fails(self):
        """Test that invalid PRD type raises TypeError."""
        metadata = MultiPRDMetadata(orchestration_id="test")
        
        with pytest.raises(TypeError, match="must be PRD or AdvancedPRD"):
            MultiPRDInput(prds=["invalid"], metadata=metadata)


class TestMultiPRDIntake:
    """Test MultiPRDIntake processor."""
    
    def test_process_single_phase24_prd(self):
        """Test processing single Phase 2.4 PRD."""
        prd = PRD(
            metadata=PRDMetadata(title="Test PRD", version="1.0", author="Tester"),
            overview="Test overview",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="First requirement"
                ),
                PRDRequirement(
                    id="req2",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.MEDIUM,
                    description="Second requirement",
                    dependencies=["req1"]
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="test-orch")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify structure
        assert isinstance(result, NormalizedPRDCollection)
        assert result.total_prds == 1
        assert result.total_tasks == 2
        assert len(result.tasks) == 2
        
        # Verify task IDs are tracked
        task_ids = [task.task_id for task in result.tasks]
        assert len(task_ids) == 2
        assert all(task_id in result.prd_sources for task_id in task_ids)
        
        # Verify statistics
        prd_id = list(result.task_count_by_prd.keys())[0]
        assert result.task_count_by_prd[prd_id] == 2
    
    def test_process_single_phase31_advanced_prd(self):
        """Test processing single Phase 3.1 AdvancedPRD."""
        prd = AdvancedPRD(
            metadata=PRDMetadata(title="Advanced PRD", version="1.0", author="Tester"),
            overview="Advanced test",
            requirements=[
                AdvancedPRDRequirement(
                    id="parent",
                    description="Parent task"
                ),
                AdvancedPRDRequirement(
                    id="child",
                    description="Child task",
                    parent_id="parent",
                    dependencies=["parent"]
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="test-orch")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify structure
        assert isinstance(result, NormalizedPRDCollection)
        assert result.total_prds == 1
        assert result.total_tasks == 2
        assert len(result.tasks) == 2
    
    def test_process_mixed_prd_types(self):
        """Test processing mixed Phase 2.4 and Phase 3.1 PRDs."""
        prd24 = PRD(
            metadata=PRDMetadata(title="PRD 2.4", version="1.0", author="Tester"),
            overview="Phase 2.4 PRD",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Requirement 1"
                )
            ]
        )
        
        prd31 = AdvancedPRD(
            metadata=PRDMetadata(title="PRD 3.1", version="1.0", author="Tester"),
            overview="Phase 3.1 PRD",
            requirements=[
                AdvancedPRDRequirement(
                    id="req2",
                    description="Requirement 2"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="mixed-test")
        input_data = MultiPRDInput(prds=[prd24, prd31], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify both PRDs processed
        assert result.total_prds == 2
        assert result.total_tasks == 2
        assert len(result.prd_sources) == 2
        assert len(result.task_count_by_prd) == 2
    
    def test_process_three_prds(self):
        """Test processing three PRDs of different types."""
        prd1 = PRD(
            metadata=PRDMetadata(title="First", version="1.0", author="Tester"),
            overview="First PRD",
            requirements=[
                PRDRequirement(
                    id="r1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Req 1"
                )
            ]
        )
        
        prd2 = PRD(
            metadata=PRDMetadata(title="Second", version="1.0", author="Tester"),
            overview="Second PRD",
            requirements=[
                PRDRequirement(
                    id="r2",
                    type=RequirementType.BUGFIX,
                    priority=RequirementPriority.MEDIUM,
                    description="Req 2"
                ),
                PRDRequirement(
                    id="r3",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.LOW,
                    description="Req 3"
                )
            ]
        )
        
        prd3 = AdvancedPRD(
            metadata=PRDMetadata(title="Third", version="1.0", author="Tester"),
            overview="Third PRD",
            requirements=[
                AdvancedPRDRequirement(id="r4", description="Req 4"),
                AdvancedPRDRequirement(id="r5", description="Req 5"),
                AdvancedPRDRequirement(id="r6", description="Req 6")
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="three-prds")
        input_data = MultiPRDInput(prds=[prd1, prd2, prd3], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify totals
        assert result.total_prds == 3
        assert result.total_tasks == 6  # 1 + 2 + 3
        assert len(result.tasks) == 6
        
        # Verify all tasks are tracked
        assert len(result.prd_sources) == 6
        assert len(result.task_count_by_prd) == 3
        
        # Verify task counts
        task_counts = list(result.task_count_by_prd.values())
        assert sorted(task_counts) == [1, 2, 3]
    
    def test_prd_metadata_extraction(self):
        """Test that PRD metadata is correctly extracted."""
        prd = PRD(
            metadata=PRDMetadata(
                title="Test PRD",
                version="2.0",
                author="John Doe",
                tags=["test", "demo"]
            ),
            overview="Test overview",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Test requirement"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="meta-test")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Get PRD metadata
        prd_id = list(result.prd_metadata.keys())[0]
        prd_meta = result.prd_metadata[prd_id]
        
        # Verify metadata
        assert prd_meta["title"] == "Test PRD"
        assert prd_meta["version"] == "2.0"
        assert prd_meta["author"] == "John Doe"
        assert prd_meta["tags"] == ["test", "demo"]
        assert prd_meta["type"] == "PRD"
        assert prd_meta["index"] == 0
    
    def test_advanced_prd_metadata_includes_nesting_info(self):
        """Test that AdvancedPRD metadata includes nesting information."""
        prd = AdvancedPRD(
            metadata=PRDMetadata(title="Nested PRD", version="1.0", author="Tester"),
            overview="Has nesting",
            requirements=[
                AdvancedPRDRequirement(id="parent", description="Parent"),
                AdvancedPRDRequirement(
                    id="child",
                    description="Child",
                    parent_id="parent"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="nesting-test")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Get PRD metadata
        prd_id = list(result.prd_metadata.keys())[0]
        prd_meta = result.prd_metadata[prd_id]
        
        # Verify nesting info
        assert prd_meta["type"] == "AdvancedPRD"
        assert prd_meta["has_nested_structure"] is True
        assert prd_meta["max_depth"] == 1
    
    def test_prd_id_generation_deterministic(self):
        """Test that PRD IDs are generated deterministically."""
        prd = PRD(
            metadata=PRDMetadata(title="Test PRD", version="1.0", author="Tester"),
            overview="Test",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Test"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="id-test")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        
        # Process twice
        result1 = intake.process(input_data)
        result2 = intake.process(input_data)
        
        # PRD IDs should be identical
        prd_ids1 = list(result1.prd_metadata.keys())
        prd_ids2 = list(result2.prd_metadata.keys())
        
        assert prd_ids1 == prd_ids2
    
    def test_backward_compatibility_single_prd(self):
        """Test backward compatibility: single PRD behaves identically."""
        # This test verifies that a single PRD in the list produces
        # the same tasks as processing that PRD alone
        
        prd = PRD(
            metadata=PRDMetadata(title="Single", version="1.0", author="Tester"),
            overview="Single PRD test",
            requirements=[
                PRDRequirement(
                    id="req1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="Requirement 1"
                ),
                PRDRequirement(
                    id="req2",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.MEDIUM,
                    description="Requirement 2",
                    dependencies=["req1"]
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="compat-test")
        input_data = MultiPRDInput(prds=[prd], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify single PRD processing
        assert result.total_prds == 1
        assert result.total_tasks == 2
        assert len(result.tasks) == 2
        
        # Verify task order (dependency order preserved)
        # req1 should come before req2
        task_ids = [task.task_id for task in result.tasks]
        req_ids = [task.requirement_id for task in result.tasks]
        
        # Find indices
        req1_idx = req_ids.index("req1")
        req2_idx = req_ids.index("req2")
        
        # req1 should come before req2 (dependency order)
        assert req1_idx < req2_idx
    
    def test_task_source_tracking(self):
        """Test that task-to-PRD source tracking is accurate."""
        prd1 = PRD(
            metadata=PRDMetadata(title="PRD 1", version="1.0", author="Tester"),
            overview="First",
            requirements=[
                PRDRequirement(
                    id="r1",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="From PRD 1"
                )
            ]
        )
        
        prd2 = PRD(
            metadata=PRDMetadata(title="PRD 2", version="1.0", author="Tester"),
            overview="Second",
            requirements=[
                PRDRequirement(
                    id="r2",
                    type=RequirementType.FEATURE,
                    priority=RequirementPriority.HIGH,
                    description="From PRD 2"
                )
            ]
        )
        
        metadata = MultiPRDMetadata(orchestration_id="tracking-test")
        input_data = MultiPRDInput(prds=[prd1, prd2], metadata=metadata)
        
        intake = MultiPRDIntake()
        result = intake.process(input_data)
        
        # Verify each task is tracked to its source PRD
        for task in result.tasks:
            assert task.task_id in result.prd_sources
            prd_id = result.prd_sources[task.task_id]
            assert prd_id in result.prd_metadata
        
        # Verify PRD IDs are different
        prd_ids = list(result.prd_metadata.keys())
        assert len(prd_ids) == 2
        assert prd_ids[0] != prd_ids[1]
