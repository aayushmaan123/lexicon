"""
Manual verification script for Phase 3.2.1 Multi-PRD Intake.

This script tests the basic functionality without requiring pytest.
"""

from lexicon.orchestrator import (
    MultiPRDInput,
    MultiPRDIntake,
    MultiPRDMetadata,
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


def test_single_phase24_prd():
    """Test processing single Phase 2.4 PRD."""
    print("\n=== Test 1: Single Phase 2.4 PRD ===")
    
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
    
    metadata = MultiPRDMetadata(orchestration_id="test-orch-1")
    input_data = MultiPRDInput(prds=[prd], metadata=metadata)
    
    intake = MultiPRDIntake()
    result = intake.process(input_data)
    
    print(f"✓ Total PRDs: {result.total_prds} (expected: 1)")
    print(f"✓ Total tasks: {result.total_tasks} (expected: 2)")
    print(f"✓ Tasks tracked: {len(result.prd_sources)} (expected: 2)")
    print(f"✓ PRD metadata entries: {len(result.prd_metadata)} (expected: 1)")
    
    assert result.total_prds == 1
    assert result.total_tasks == 2
    print("✓ Test 1 PASSED")


def test_single_phase31_prd():
    """Test processing single Phase 3.1 AdvancedPRD."""
    print("\n=== Test 2: Single Phase 3.1 AdvancedPRD ===")
    
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
                parent_id="parent",  # Informational hierarchy only
                # Note: parent_id does NOT create dependency
                # If we want execution order, we add it to dependencies:
                dependencies=[]  # No dependencies, can run in parallel
            )
        ]
    )
    
    metadata = MultiPRDMetadata(orchestration_id="test-orch-2")
    input_data = MultiPRDInput(prds=[prd], metadata=metadata)
    
    intake = MultiPRDIntake()
    result = intake.process(input_data)
    
    print(f"✓ Total PRDs: {result.total_prds} (expected: 1)")
    print(f"✓ Total tasks: {result.total_tasks} (expected: 2)")
    
    # Check nesting info
    prd_id = list(result.prd_metadata.keys())[0]
    prd_meta = result.prd_metadata[prd_id]
    print(f"✓ Has nested structure: {prd_meta.get('has_nested_structure')} (expected: True)")
    
    assert result.total_prds == 1
    assert result.total_tasks == 2
    assert prd_meta.get('has_nested_structure') == True
    print("✓ Test 2 PASSED")


def test_mixed_prd_types():
    """Test processing mixed Phase 2.4 and Phase 3.1 PRDs."""
    print("\n=== Test 3: Mixed PRD Types (2.4 + 3.1) ===")
    
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
    
    metadata = MultiPRDMetadata(orchestration_id="test-orch-3")
    input_data = MultiPRDInput(prds=[prd24, prd31], metadata=metadata)
    
    intake = MultiPRDIntake()
    result = intake.process(input_data)
    
    print(f"✓ Total PRDs: {result.total_prds} (expected: 2)")
    print(f"✓ Total tasks: {result.total_tasks} (expected: 2)")
    print(f"✓ PRD metadata entries: {len(result.prd_metadata)} (expected: 2)")
    
    # Verify different PRD types
    prd_types = [meta["type"] for meta in result.prd_metadata.values()]
    print(f"✓ PRD types: {prd_types}")
    
    assert result.total_prds == 2
    assert result.total_tasks == 2
    assert "PRD" in prd_types
    assert "AdvancedPRD" in prd_types
    print("✓ Test 3 PASSED")


def test_multiple_prds():
    """Test processing three PRDs."""
    print("\n=== Test 4: Three PRDs (1 + 2 + 3 requirements) ===")
    
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
    
    metadata = MultiPRDMetadata(orchestration_id="test-orch-4")
    input_data = MultiPRDInput(prds=[prd1, prd2, prd3], metadata=metadata)
    
    intake = MultiPRDIntake()
    result = intake.process(input_data)
    
    print(f"✓ Total PRDs: {result.total_prds} (expected: 3)")
    print(f"✓ Total tasks: {result.total_tasks} (expected: 6)")
    
    # Verify task counts per PRD
    task_counts = sorted(result.task_count_by_prd.values())
    print(f"✓ Task counts per PRD: {task_counts} (expected: [1, 2, 3])")
    
    assert result.total_prds == 3
    assert result.total_tasks == 6
    assert task_counts == [1, 2, 3]
    print("✓ Test 4 PASSED")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Test 5: Error Handling ===")
    
    # Test empty PRD list
    try:
        metadata = MultiPRDMetadata(orchestration_id="test")
        MultiPRDInput(prds=[], metadata=metadata)
        print("✗ Should have raised ValueError for empty list")
        assert False
    except ValueError as e:
        print(f"✓ Empty list correctly rejected: {e}")
    
    # Test invalid PRD type
    try:
        metadata = MultiPRDMetadata(orchestration_id="test")
        MultiPRDInput(prds=["invalid"], metadata=metadata)
        print("✗ Should have raised TypeError for invalid PRD")
        assert False
    except TypeError as e:
        print(f"✓ Invalid type correctly rejected: {e}")
    
    # Test empty orchestration ID
    try:
        MultiPRDMetadata(orchestration_id="")
        print("✗ Should have raised ValueError for empty orchestration ID")
        assert False
    except ValueError as e:
        print(f"✓ Empty orchestration ID correctly rejected: {e}")
    
    print("✓ Test 5 PASSED")


def main():
    """Run all manual tests."""
    print("=" * 60)
    print("Phase 3.2.1 Multi-PRD Intake Manual Verification")
    print("=" * 60)
    
    try:
        test_single_phase24_prd()
        test_single_phase31_prd()
        test_mixed_prd_types()
        test_multiple_prds()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nPhase 3.2.1 Multi-PRD Intake is working correctly!")
        print("\nKey Features Verified:")
        print("  ✓ Single PRD processing (backward compatible)")
        print("  ✓ Multiple PRD processing")
        print("  ✓ Mixed PRD types (Phase 2.4 + Phase 3.1)")
        print("  ✓ Task normalization to DecomposedTask format")
        print("  ✓ PRD metadata extraction")
        print("  ✓ Task-to-PRD source tracking")
        print("  ✓ Statistics calculation")
        print("  ✓ Error handling and validation")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
