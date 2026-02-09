
from lexicon.orchestrator import (
    ResolvedDependencyGraph,
    GlobalPlanBuilder,
    ExecutionWave,
)
from lexicon.pipeline.advanced_prd_models import DecomposedTask

def create_mock_graph(tasks: list, prd_sources: dict):
    """Helper to create a ResolvedDependencyGraph directly."""
    adjacency_list = {t.task_id: set(t.dependencies) for t in tasks}
    return ResolvedDependencyGraph(
        tasks={t.task_id: t for t in tasks},
        edges=[], 
        adjacency_list=adjacency_list,
        prd_sources=prd_sources,
        orchestration_id="test-orch"
    )

def test_single_prd_plan():
    """Test plan building for a simple linear dependency in one PRD."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", dependencies=["t1"])
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-0"})
    builder = GlobalPlanBuilder(graph)
    plan = builder.generate_global_plan()
    
    assert len(plan.waves) == 2
    assert plan.waves[0].tasks[0].task_id == "t1"
    assert plan.waves[1].tasks[0].task_id == "t2"

def test_multi_prd_parallel_plan():
    """Test that independent tasks from different PRDs are grouped in the same wave."""
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2")
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    builder = GlobalPlanBuilder(graph)
    plan = builder.generate_global_plan()
    
    # Both should be in Wave 0 since they have 0 dependencies
    assert len(plan.waves) == 1
    wave0_ids = [t.task_id for t in plan.waves[0].tasks]
    assert "t1" in wave0_ids
    assert "t2" in wave0_ids
    assert len(wave0_ids) == 2

def test_cross_prd_dependency_plan():
    """Test plan building with a dependency spanning two PRDs."""
    # PRD 0 has t1
    # PRD 1 has t2 which depends on t1
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", dependencies=["t1"])
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-1"})
    builder = GlobalPlanBuilder(graph)
    plan = builder.generate_global_plan()
    
    assert len(plan.waves) == 2
    assert plan.waves[0].tasks[0].task_id == "t1"
    assert plan.waves[1].tasks[0].task_id == "t2"

def test_determinism_and_sorting():
    """Test that tasks within a wave are sorted lexicographically."""
    # t3, t1, t2 all independent
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1")
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2")
    t3 = DecomposedTask(task_id="t3", requirement_id="r3", description="D3")
    
    graph = create_mock_graph([t1, t2, t3], {"t1": "prd-0", "t2": "prd-0", "t3": "prd-0"})
    builder = GlobalPlanBuilder(graph)
    plan = builder.generate_global_plan()
    
    wave0_ids = [t.task_id for t in plan.waves[0].tasks]
    assert wave0_ids == ["t1", "t2", "t3"]

def test_incomplete_plan_error():
    """Test that validate_plan catches missing tasks (e.g. cycles)."""
    # Create a cycle: t1 -> t2 -> t1
    t1 = DecomposedTask(task_id="t1", requirement_id="r1", description="D1", dependencies=["t2"])
    t2 = DecomposedTask(task_id="t2", requirement_id="r2", description="D2", dependencies=["t1"])
    
    graph = create_mock_graph([t1, t2], {"t1": "prd-0", "t2": "prd-0"})
    builder = GlobalPlanBuilder(graph)
    
    # build_execution_waves will return an empty list because no task has 0 in-degree
    try:
        builder.validate_plan()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "2 tasks were not assigned" in str(e)

if __name__ == "__main__":
    import sys
    try:
        test_single_prd_plan()
        test_multi_prd_parallel_plan()
        test_cross_prd_dependency_plan()
        test_determinism_and_sorting()
        test_incomplete_plan_error()
        print("ALL PLAN BUILDER TESTS PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
