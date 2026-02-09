
from lexicon.orchestrator import (
    MultiPRDInput,
    MultiPRDIntake,
    MultiPRDMetadata,
    CrossPRDResolver,
    ConflictDetector,
    GlobalPlanBuilder,
    ResourceConflictError,
    OutputConflictError,
)
from lexicon.pipeline import PRDMetadata, PRDRequirement, PRD, RequirementType, RequirementPriority

def run_pipeline(prds: list, orchestration_id: str):
    """Executes the full orchestration pipeline."""
    print(f"\n--- Orchestrating {len(prds)} PRDs (ID: {orchestration_id}) ---")
    
    # 1. Intake
    metadata = MultiPRDMetadata(orchestration_id=orchestration_id)
    input_data = MultiPRDInput(prds=prds, metadata=metadata)
    intake = MultiPRDIntake()
    normalized = intake.process(input_data)
    print(f"Intake complete: {len(normalized.tasks)} tasks normalized.")
    
    # 2. Resolver
    resolver = CrossPRDResolver()
    resolved_graph = resolver.resolve(normalized)
    print(f"Resolution complete: {len(resolved_graph.edges)} dependencies validated.")
    
    # 3. Conflict Detector
    detector = ConflictDetector(resolved_graph)
    detector.detect() # Will raise if conflict found
    print("Conflict detection complete: No conflicts found.")
    
    # 4. Global Plan Builder
    builder = GlobalPlanBuilder(resolved_graph)
    plan = builder.generate_global_plan()
    print(f"Plan generation complete: {len(plan.waves)} waves generated.")
    return plan

def test_success_case():
    """Verify a valid multi-PRD scenario using Phase 2.4 models."""
    print("\nRunning Success Case (Cross-PRD Dependencies)...")
    
    # PRD A: Backend
    prd_a = PRD(
        metadata=PRDMetadata(title="Backend", version="1.0", author="B"),
        overview="API implementation",
        requirements=[
            PRDRequirement(
                id="api-1", 
                type=RequirementType.INFRASTRUCTURE,
                priority=RequirementPriority.HIGH,
                description="Init database"
            ),
            PRDRequirement(
                id="api-2", 
                type=RequirementType.FEATURE,
                priority=RequirementPriority.MEDIUM,
                description="User endpoint", 
                dependencies=["api-1"]
            )
        ]
    )
    
    # PRD B: Frontend
    prd_b = PRD(
        metadata=PRDMetadata(title="Frontend", version="1.0", author="F"),
        overview="UI implementation",
        requirements=[
            PRDRequirement(
                id="ui-1", 
                type=RequirementType.FEATURE,
                priority=RequirementPriority.MEDIUM,
                description="Login screen", 
                dependencies=[]
            )
        ]
    )
    # Bypass __post_init__ validation for cross-PRD dependency
    # The dependency must match the transformed task ID: task-{prd_id}-{req_id}
    prd_b.requirements[0].dependencies = ["task-prd-0-backend-api-2"]
    
    try:
        plan = run_pipeline([prd_a, prd_b], "success-test")
        assert len(plan.waves) == 3
        # Wave 0: api-1
        # Wave 1: api-2
        # Wave 2: ui-1
        print("Success test: PASSED")
    except Exception as e:
        print(f"Success test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        raise

def test_resource_conflict_case():
    """Verify detection of resource conflicts in the pipeline."""
    print("\nRunning Resource Conflict Case...")
    
    prd_a = PRD(
        metadata=PRDMetadata(title="A", version="1.0", author="A"),
        overview="A",
        requirements=[
            PRDRequirement(
                id="task-a", 
                type=RequirementType.FEATURE,
                priority=RequirementPriority.MEDIUM,
                description="A"
            )
        ]
    )
    # Inject resource requirement (Phase 2.4 requirements don't have resources field, 
    # but DecomposedTask will pick it up if we put it in metadata or if we use AdvancedPRD.
    # Actually, MultiPRDIntake._convert_prd_to_decomposed doesn't handle resources.
    # Let's use AdvancedPRD for conflict tests since they don't need cross-PRD dependencies.)
    from lexicon.pipeline import AdvancedPRD, AdvancedPRDRequirement
    
    apr_a = AdvancedPRD(
        metadata=PRDMetadata(title="A", version="1.0", author="A"),
        overview="A",
        requirements=[
            AdvancedPRDRequirement(
                id="task-a", 
                description="A",
                resources=["database"]
            )
        ]
    )
    apr_b = AdvancedPRD(
        metadata=PRDMetadata(title="B", version="1.0", author="B"),
        overview="B",
        requirements=[
            AdvancedPRDRequirement(
                id="task-b", 
                description="B",
                resources=["database"]
            )
        ]
    )
    
    try:
        run_pipeline([apr_a, apr_b], "resource-conflict-test")
        print("Resource conflict test: FAILED (No exception raised)")
    except ResourceConflictError as e:
        print(f"Resource conflict test: PASSED (Detected: {e})")
    except Exception as e:
        print(f"Resource conflict test: FAILED (Wrong exception: {type(e).__name__})")

def test_output_conflict_case():
    """Verify detection of output conflicts in the pipeline."""
    print("\nRunning Output Conflict Case...")
    from lexicon.pipeline import AdvancedPRD, AdvancedPRDRequirement
    
    apr_a = AdvancedPRD(
        metadata=PRDMetadata(title="A", version="1.0", author="A"),
        overview="A",
        requirements=[
            AdvancedPRDRequirement(
                id="task-a", 
                description="A"
            )
        ]
    )
    apr_a.requirements[0].metadata["output_path"] = "/config/settings.yaml"
    
    apr_b = AdvancedPRD(
        metadata=PRDMetadata(title="B", version="1.0", author="B"),
        overview="B",
        requirements=[
            AdvancedPRDRequirement(
                id="task-b", 
                description="B"
            )
        ]
    )
    apr_b.requirements[0].metadata["output_path"] = "/config/settings.yaml"
    
    try:
        run_pipeline([apr_a, apr_b], "output-conflict-test")
        print("Output conflict test: FAILED (No exception raised)")
    except OutputConflictError as e:
        print(f"Output conflict test: PASSED (Detected: {e})")
    except Exception as e:
        print(f"Output conflict test: FAILED (Wrong exception: {type(e).__name__})")

if __name__ == "__main__":
    try:
        test_success_case()
        test_resource_conflict_case()
        test_output_conflict_case()
        print("\n--- ALL INTEGRATION VERIFICATIONS COMPLETE ---")
    except Exception:
        import sys
        sys.exit(1)
