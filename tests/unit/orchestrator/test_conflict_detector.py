
from lexicon.orchestrator import (
    MultiPRDMetadata,
    ResolvedDependencyGraph,
    ConflictDetector,
    ResourceConflictError,
    OutputConflictError,
)
from lexicon.orchestrator.cross_prd_resolver import DependencyEdge
from lexicon.pipeline.advanced_prd_models import DecomposedTask, ResourceType

def create_mock_graph(tasks: list, prd_sources: dict):
    """Helper to create a ResolvedDependencyGraph directly."""
    adjacency_list = {t.task_id: set(t.dependencies) for t in tasks}
    return ResolvedDependencyGraph(
        tasks={t.task_id: t for t in tasks},
        edges=[], # Not needed for detector
        adjacency_list=adjacency_list,
        prd_sources=prd_sources,
        orchestration_id="test-orch"
    )

def test_no_conflicts():
    """Test scenario with no conflicts."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2")
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    detector = ConflictDetector(graph)
    report = detector.detect()
    assert not report.has_conflicts

def test_resource_conflict():
    """Test detection of resource overlap in the same wave."""
    # t1 and t2 have no dependencies, so they will be in the same wave
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1", resources=[ResourceType.DATABASE])
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", resources=[ResourceType.DATABASE])
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    detector = ConflictDetector(graph)
    
    try:
        detector.detect()
        assert False, "Should have raised ResourceConflictError"
    except ResourceConflictError as e:
        assert "database" in str(e).lower()
        assert "t1" in str(e)
        assert "t2" in str(e)

def test_output_conflict():
    """Test detection of output path collision."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1", metadata={"output_path": "/data/out.json"})
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", metadata={"output_path": "/data/out.json"})
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    detector = ConflictDetector(graph)
    
    try:
        detector.detect()
        assert False, "Should have raised OutputConflictError"
    except OutputConflictError as e:
        assert "/data/out.json" in str(e)
        assert "t1" in str(e)
        assert "t2" in str(e)

def test_mixed_conflict():
    """Test that it fails on the first conflict (output path first in my impl)."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1", 
                        resources=[ResourceType.DATABASE], metadata={"output_path": "/out.json"})
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", 
                        resources=[ResourceType.DATABASE], metadata={"output_path": "/out.json"})
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    detector = ConflictDetector(graph)
    
    try:
        detector.detect()
    except OutputConflictError:
        pass # Expected since detect() checks output conflicts first
    except Exception as e:
        assert False, f"Raised wrong exception: {type(e).__name__}"

def test_determinism():
    """Test that detection results are deterministic."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1", resources=[ResourceType.DATABASE])
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", resources=[ResourceType.DATABASE])
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    
    # Run twice and check if they produce same error message (fail-fast)
    try:
        ConflictDetector(graph).detect()
    except ResourceConflictError as e1:
        try:
            ConflictDetector(graph).detect()
        except ResourceConflictError as e2:
            assert str(e1) == str(e2)

if __name__ == "__main__":
    import sys
    try:
        test_no_conflicts()
        test_resource_conflict()
        test_output_conflict()
        test_mixed_conflict()
        test_determinism()
        print("ALL CONFLICT DETECTOR TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
