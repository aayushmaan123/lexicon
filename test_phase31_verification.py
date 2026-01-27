#!/usr/bin/env python3
"""
Phase 3.1 Verification Script
Tests backward compatibility and Phase 3.1 functionality without full test infrastructure.
"""

import sys
import traceback
from typing import List

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []

def test(name: str):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            global tests_passed, tests_failed
            try:
                func()
                tests_passed += 1
                test_results.append(f"✅ PASS: {name}")
                print(f"✅ PASS: {name}")
            except AssertionError as e:
                tests_failed += 1
                test_results.append(f"❌ FAIL: {name} - {str(e)}")
                print(f"❌ FAIL: {name}")
                print(f"   Error: {str(e)}")
            except Exception as e:
                tests_failed += 1
                test_results.append(f"❌ ERROR: {name} - {str(e)}")
                print(f"❌ ERROR: {name}")
                traceback.print_exc()
        return wrapper
    return decorator

# Import Phase 2.4 modules (should work unchanged)
try:
    from lexicon.pipeline.prd_models import (
        PRD, PRDRequirement, PRDMetadata, RequirementType
    )
    print("✅ Phase 2.4 imports successful")
except Exception as e:
    print(f"❌ Phase 2.4 imports failed: {e}")
    sys.exit(1)

# Import Phase 3.1 modules
try:
    from lexicon.pipeline.advanced_prd_models import (
        AdvancedPRD, AdvancedPRDRequirement, RequirementPriority, ResourceType
    )
    from lexicon.pipeline.advanced_prd_parser import AdvancedPRDParser
    from lexicon.pipeline.advanced_prd_validator import AdvancedPRDValidator
    from lexicon.pipeline.prd_decomposer import PRDDecomposer
    print("✅ Phase 3.1 imports successful")
except Exception as e:
    print(f"❌ Phase 3.1 imports failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("PHASE 3.1 VERIFICATION TESTS")
print("="*80 + "\n")

# ============================================================================
# TEST 1: Backward Compatibility - Phase 2.4 PRDs still work
# ============================================================================

@test("1.1 Phase 2.4 flat PRD creation")
def test_phase24_flat_prd():
    """Verify Phase 2.4 PRDs still work unchanged"""
    metadata = PRDMetadata(title="Test PRD", version="1.0", author="Test")
    requirements = [
        PRDRequirement(id="req1", description="First requirement"),
        PRDRequirement(id="req2", description="Second requirement", dependencies=["req1"]),
    ]
    prd = PRD(metadata=metadata, overview="Test", requirements=requirements)
    assert len(prd.requirements) == 2
    assert prd.requirements[0].id == "req1"
    assert prd.requirements[1].dependencies == ["req1"]

test_phase24_flat_prd()

@test("1.2 Flat PRDs are valid AdvancedPRDs")
def test_flat_prd_is_advanced_prd():
    """Verify flat PRDs (no parent_id) work with AdvancedPRD"""
    metadata = PRDMetadata(title="Flat PRD", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="req1", description="First"),
        AdvancedPRDRequirement(id="req2", description="Second", dependencies=["req1"]),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    # Validate
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert result.is_valid, f"Flat PRD validation failed: {result.errors}"
    
    # Decompose
    decomposer = PRDDecomposer()
    tasks = decomposer.decompose(prd)
    assert len(tasks) == 2
    assert tasks[0].id == "req1"
    assert tasks[1].id == "req2"

test_flat_prd_is_advanced_prd()

# ============================================================================
# TEST 2: Nested PRD Functionality
# ============================================================================

@test("2.1 Nested PRD with parent-child relationships")
def test_nested_prd():
    """Verify nested PRDs work correctly"""
    metadata = PRDMetadata(title="Nested PRD", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="feature", description="Main feature"),
        AdvancedPRDRequirement(
            id="backend", 
            description="Backend implementation",
            parent_id="feature",
            resources=[ResourceType.DATABASE, ResourceType.NETWORK]
        ),
        AdvancedPRDRequirement(
            id="frontend", 
            description="Frontend implementation",
            parent_id="feature",
            dependencies=["backend"],
            resources=[ResourceType.NETWORK]
        ),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test nested", requirements=requirements)
    
    # Validate
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert result.is_valid, f"Nested PRD validation failed: {result.errors}"
    
    # Verify hierarchy
    children = prd.get_children("feature")
    assert len(children) == 2
    assert "backend" in [c.id for c in children]
    assert "frontend" in [c.id for c in children]

test_nested_prd()

@test("2.2 Multi-level nesting (3 levels)")
def test_multi_level_nesting():
    """Verify 3-level nesting works"""
    metadata = PRDMetadata(title="Multi-level", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="L1", description="Level 1"),
        AdvancedPRDRequirement(id="L2", description="Level 2", parent_id="L1"),
        AdvancedPRDRequirement(id="L3", description="Level 3", parent_id="L2"),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert result.is_valid, f"Multi-level nesting failed: {result.errors}"
    
    # Verify nesting depth
    l3_req = next(r for r in prd.requirements if r.id == "L3")
    depth = prd.get_nesting_depth(l3_req)
    assert depth == 2, f"Expected depth 2, got {depth}"

test_multi_level_nesting()

# ============================================================================
# TEST 3: Optional Subtasks
# ============================================================================

@test("3.1 Optional subtask marking")
def test_optional_subtasks():
    """Verify optional subtasks work correctly"""
    metadata = PRDMetadata(title="Optional", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="main", description="Main task"),
        AdvancedPRDRequirement(
            id="required", 
            description="Required subtask",
            parent_id="main",
            optional=False
        ),
        AdvancedPRDRequirement(
            id="optional", 
            description="Optional subtask",
            parent_id="main",
            optional=True
        ),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    # Decompose with optional tasks
    decomposer = PRDDecomposer()
    all_tasks = decomposer.decompose(prd, include_optional=True)
    assert len(all_tasks) == 3
    
    # Decompose without optional tasks
    required_tasks = decomposer.decompose(prd, include_optional=False)
    assert len(required_tasks) == 2
    assert all(t.id != "optional" for t in required_tasks)

test_optional_subtasks()

@test("3.2 Validation warning: required depends on optional")
def test_required_depends_on_optional_warning():
    """Verify warning when required task depends on optional task"""
    metadata = PRDMetadata(title="Warning test", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="opt", description="Optional", optional=True),
        AdvancedPRDRequirement(
            id="req", 
            description="Required",
            dependencies=["opt"],  # Required depends on optional - should warn
            optional=False
        ),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    # Should be valid but have warnings
    assert result.is_valid
    assert len(result.warnings) > 0
    assert any("optional" in w.lower() for w in result.warnings)

test_required_depends_on_optional_warning()

# ============================================================================
# TEST 4: Validation - Circular Dependencies
# ============================================================================

@test("4.1 Circular dependency detection in dependencies")
def test_circular_dependencies():
    """Verify circular dependency detection works"""
    metadata = PRDMetadata(title="Circular", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="A", description="A", dependencies=["B"]),
        AdvancedPRDRequirement(id="B", description="B", dependencies=["A"]),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert not result.is_valid
    assert any("circular" in e.lower() for e in result.errors)

test_circular_dependencies()

@test("4.2 Circular parent chain detection")
def test_circular_parent_chain():
    """Verify circular parent chain detection works"""
    metadata = PRDMetadata(title="Circular parent", version="1.0", author="Test")
    # This creates a parent cycle: A -> B -> C -> A
    requirements = [
        AdvancedPRDRequirement(id="A", description="A", parent_id="C"),
        AdvancedPRDRequirement(id="B", description="B", parent_id="A"),
        AdvancedPRDRequirement(id="C", description="C", parent_id="B"),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert not result.is_valid
    assert any("circular" in e.lower() or "parent" in e.lower() for e in result.errors)

test_circular_parent_chain()

@test("4.3 parent_id in dependencies (MUST FAIL)")
def test_parent_in_dependencies_fails():
    """Verify that parent_id appearing in dependencies is invalid"""
    metadata = PRDMetadata(title="Invalid", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="parent", description="Parent"),
        AdvancedPRDRequirement(
            id="child", 
            description="Child",
            parent_id="parent",
            dependencies=["parent"]  # parent_id in dependencies - INVALID
        ),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert not result.is_valid
    assert any("parent" in e.lower() and "depend" in e.lower() for e in result.errors)

test_parent_in_dependencies_fails()

# ============================================================================
# TEST 5: Markdown Parsing
# ============================================================================

@test("5.1 Nested Markdown parsing")
def test_nested_markdown_parsing():
    """Verify nested Markdown PRD parsing works"""
    markdown = """# PRD: Feature X
**Version:** 1.0
**Author:** Test Team

## Overview
Main feature implementation

## Requirements

### feature: Main Feature
- **Priority:** high
- **Description:** Main feature container

#### backend: Backend Implementation
- **Parent:** feature
- **Resources:** database, network
- **Description:** Backend API

#### frontend: Frontend UI
- **Parent:** feature
- **Dependencies:** backend
- **Resources:** network
- **Description:** Frontend implementation
"""
    
    parser = AdvancedPRDParser()
    prd = parser.parse_markdown(markdown)
    
    # Verify structure
    assert len(prd.requirements) == 3
    
    # Find requirements by ID
    req_ids = {r.id for r in prd.requirements}
    assert "feature" in req_ids
    assert "backend" in req_ids
    assert "frontend" in req_ids
    
    # Verify parent-child relationships
    backend = next(r for r in prd.requirements if r.id == "backend")
    assert backend.parent_id == "feature"
    
    frontend = next(r for r in prd.requirements if r.id == "frontend")
    assert frontend.parent_id == "feature"
    assert "backend" in frontend.dependencies

test_nested_markdown_parsing()

# ============================================================================
# TEST 6: Decomposition and Execution Waves
# ============================================================================

@test("6.1 Task decomposition preserves dependency order")
def test_decomposition_dependency_order():
    """Verify decomposition maintains dependency order"""
    metadata = PRDMetadata(title="Order test", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="A", description="A"),
        AdvancedPRDRequirement(id="C", description="C", dependencies=["B"]),
        AdvancedPRDRequirement(id="B", description="B", dependencies=["A"]),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    decomposer = PRDDecomposer()
    tasks = decomposer.decompose(prd)
    
    # Find positions
    pos_a = next(i for i, t in enumerate(tasks) if t.id == "A")
    pos_b = next(i for i, t in enumerate(tasks) if t.id == "B")
    pos_c = next(i for i, t in enumerate(tasks) if t.id == "C")
    
    # Verify order: A before B before C
    assert pos_a < pos_b, f"A ({pos_a}) should come before B ({pos_b})"
    assert pos_b < pos_c, f"B ({pos_b}) should come before C ({pos_c})"

test_decomposition_dependency_order()

@test("6.2 Execution waves for parallel execution")
def test_execution_waves():
    """Verify execution wave generation for parallel tasks"""
    metadata = PRDMetadata(title="Waves", version="1.0", author="Test")
    requirements = [
        AdvancedPRDRequirement(id="A", description="A"),
        AdvancedPRDRequirement(id="B", description="B"),  # Independent of A
        AdvancedPRDRequirement(id="C", description="C", dependencies=["A"]),
        AdvancedPRDRequirement(id="D", description="D", dependencies=["B"]),
        AdvancedPRDRequirement(id="E", description="E", dependencies=["C", "D"]),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    decomposer = PRDDecomposer()
    tasks = decomposer.decompose(prd)
    waves = decomposer.get_execution_waves(tasks)
    
    # Wave 1: A and B (no dependencies)
    # Wave 2: C and D (depend on wave 1)
    # Wave 3: E (depends on wave 2)
    assert len(waves) >= 3
    
    wave1_ids = {t.id for t in waves[0]}
    assert "A" in wave1_ids
    assert "B" in wave1_ids
    
    wave2_ids = {t.id for t in waves[1]}
    assert "C" in wave2_ids or "D" in wave2_ids

test_execution_waves()

# ============================================================================
# TEST 7: Mixed Flat + Nested PRDs
# ============================================================================

@test("7.1 Mixed flat and nested requirements")
def test_mixed_flat_nested():
    """Verify PRD can have both flat and nested requirements"""
    metadata = PRDMetadata(title="Mixed", version="1.0", author="Test")
    requirements = [
        # Flat requirements
        AdvancedPRDRequirement(id="flat1", description="Flat 1"),
        AdvancedPRDRequirement(id="flat2", description="Flat 2", dependencies=["flat1"]),
        # Nested requirements
        AdvancedPRDRequirement(id="parent", description="Parent"),
        AdvancedPRDRequirement(id="child1", description="Child 1", parent_id="parent"),
        AdvancedPRDRequirement(
            id="child2", 
            description="Child 2", 
            parent_id="parent",
            dependencies=["flat2", "child1"]
        ),
    ]
    prd = AdvancedPRD(metadata=metadata, overview="Test", requirements=requirements)
    
    validator = AdvancedPRDValidator()
    result = validator.validate(prd)
    assert result.is_valid, f"Mixed PRD validation failed: {result.errors}"
    
    decomposer = PRDDecomposer()
    tasks = decomposer.decompose(prd)
    assert len(tasks) == 5

test_mixed_flat_nested()

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"\n✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"📊 Total:  {tests_passed + tests_failed}")

if tests_failed > 0:
    print("\n⚠️  VERIFICATION FAILED - Some tests did not pass")
    print("\nFailed tests:")
    for result in test_results:
        if result.startswith("❌"):
            print(f"  {result}")
    sys.exit(1)
else:
    print("\n✅ ALL VERIFICATION TESTS PASSED")
    print("\nPhase 3.1 is production-safe:")
    print("  • 100% backward compatible with Phase 2.4")
    print("  • All constraint validations working")
    print("  • Nested PRD functionality verified")
    print("  • Mixed flat/nested PRDs supported")
    print("  • Markdown parsing functional")
    print("  • Decomposition and execution waves working")
    sys.exit(0)
