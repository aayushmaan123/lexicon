
from lexicon.orchestrator import (
    MultiPRDMetadata,
    CrossPRDResolver,
    MissingDependencyError,
    CircularDependencyError,
    SelfDependencyError,
    ResolvedDependencyGraph,
    NormalizedPRDCollection,
)
from lexicon.pipeline.advanced_prd_models import DecomposedTask, RequirementPriority

def create_mock_normalized(tasks_data: list, prd_sources: dict):
    """
    Helper to create a NormalizedPRDCollection directly.
    tasks_data: List of DecomposedTask
    prd_sources: {task_id: prd_id}
    """
    metadata = MultiPRDMetadata(orchestration_id="test-orch")
    prd_ids = set(prd_sources.values())
    prd_metadata = {pid: {"title": pid} for pid in prd_ids}
    task_count_by_prd = {pid: list(prd_sources.values()).count(pid) for pid in prd_ids}
    
    return NormalizedPRDCollection(
        tasks=tasks_data,
        prd_sources=prd_sources,
        task_count_by_prd=task_count_by_prd,
        prd_metadata=prd_metadata,
        total_prds=len(prd_ids),
        total_tasks=len(tasks_data),
        orchestration_metadata=metadata
    )

def test_resolve_single_prd_success():
    """Test successful resolution within a single PRD."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="D2", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1, t2], {"t1": "prd-0", "t2": "prd-0"})
    resolver = CrossPRDResolver()
    graph = resolver.resolve(normalized)
    
    assert isinstance(graph, ResolvedDependencyGraph)
    assert len(graph.tasks) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].source_task_id == "t2"
    assert graph.edges[0].target_task_id == "t1"

def test_resolve_cross_prd_success():
    """Test successful resolution across multiple PRDs."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="D2", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    resolver = CrossPRDResolver()
    graph = resolver.resolve(normalized)
    
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.source_task_id == "t2"
    assert edge.target_task_id == "t1"
    assert edge.source_prd_id == "prd-1"
    assert edge.target_prd_id == "prd-0"

def test_resolve_missing_dependency():
    """Test detection of missing dependencies."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1", dependencies=["ghost"])
    
    normalized = create_mock_normalized([t1], {"t1": "prd-0"})
    resolver = CrossPRDResolver()
    
    try:
        resolver.resolve(normalized)
        assert False, "Should have raised MissingDependencyError"
    except MissingDependencyError as e:
        assert "ghost" in str(e)
        assert "t1" in str(e)

def test_resolve_self_dependency():
    """Test detection of self-dependencies."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1], {"t1": "prd-0"})
    resolver = CrossPRDResolver()
    
    try:
        resolver.resolve(normalized)
        assert False, "Should have raised SelfDependencyError"
    except SelfDependencyError as e:
        assert "t1" in str(e)

def test_resolve_circular_dependency_single():
    """Test detection of cycles within a single PRD."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1", dependencies=["t2"])
    t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="D2", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1, t2], {"t1": "prd-0", "t2": "prd-0"})
    resolver = CrossPRDResolver()
    
    try:
        resolver.resolve(normalized)
        assert False, "Should have raised CircularDependencyError"
    except CircularDependencyError as e:
        assert "t1" in str(e)
        assert "t2" in str(e)

def test_resolve_circular_dependency_cross():
    """Test detection of cycles across multiple PRDs."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1", dependencies=["t2"])
    t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="D2", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    resolver = CrossPRDResolver()
    
    try:
        resolver.resolve(normalized)
        assert False, "Should have raised CircularDependencyError"
    except CircularDependencyError as e:
        assert "t1" in str(e)
        assert "t2" in str(e)

def test_determinism():
    """Test that resolution is deterministic."""
    t1 = DecomposedTask(task_id="t1", requirement_id="req1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="req2", description="D2", dependencies=["t1"])
    
    normalized = create_mock_normalized([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    resolver = CrossPRDResolver()
    
    graph1 = resolver.resolve(normalized)
    graph2 = resolver.resolve(normalized)
    
    assert graph1.edges == graph2.edges
    assert graph1.adjacency_list == graph2.adjacency_list

if __name__ == "__main__":
    # If running with python directly instead of pytest
    import sys
    try:
        test_resolve_single_prd_success()
        test_resolve_cross_prd_success()
        test_resolve_missing_dependency()
        test_resolve_self_dependency()
        test_resolve_circular_dependency_single()
        test_resolve_circular_dependency_cross()
        test_determinism()
        print("ALL RESOLVER TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
