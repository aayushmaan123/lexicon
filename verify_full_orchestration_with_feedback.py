
import logging
from datetime import datetime, UTC
from lexicon.orchestrator import (
    MultiPRDInput,
    MultiPRDIntake,
    MultiPRDMetadata,
    CrossPRDResolver,
    ConflictDetector,
    GlobalPlanBuilder,
    Scheduler,
    FeedbackCollector,
    TaskExecutionRecord,
    TaskExecutionStatus,
)
from lexicon.pipeline import PRDMetadata, PRDRequirement, PRD, RequirementType, RequirementPriority
from lexicon.pipeline import AdvancedPRD, AdvancedPRDRequirement

# Silence logs for clean output
logging.basicConfig(level=logging.ERROR)

def run_multi_prd_orchestration():
    print("\n=== Starting Lexicon Multi-PRD Orchestration Integration Test ===\n")
    orchestration_id = f"orch-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"
    
    # 1. Prepare PRDs
    # PRD A (Phase 2.4): Core Database
    prd_a = PRD(
        metadata=PRDMetadata(title="Database Setup", version="1.0", author="Alice"),
        overview="Setup the core database schema.",
        requirements=[
            PRDRequirement(id="db-1", type=RequirementType.INFRASTRUCTURE, priority=RequirementPriority.CRITICAL, description="Create database"),
            PRDRequirement(id="db-2", type=RequirementType.FEATURE, priority=RequirementPriority.HIGH, description="Add user table", dependencies=["db-1"]),
        ]
    )
    
    # PRD B (Phase 3.1): Frontend
    prd_b = AdvancedPRD(
        metadata=PRDMetadata(title="User Interface", version="1.1", author="Bob"),
        overview="Web frontend for users.",
        requirements=[
            AdvancedPRDRequirement(id="ui-1", description="Login page", resources=["network"]),
            AdvancedPRDRequirement(id="ui-2", description="Dashboard", dependencies=[], optional=True), # We'll inject cross-PRD dep later
        ]
    )
    # Inject cross-PRD dependency
    # ui-2 depends on db-2 (from PRD A)
    # The task id will be task-prd-0-database-setup-db-2
    # But let's verify exact ID via intake or just hardcode for proof
    
    print("1. Phase 3.2.1 Intake...")
    intake = MultiPRDIntake()
    input_data = MultiPRDInput(prds=[prd_a, prd_b], metadata=MultiPRDMetadata(orchestration_id=orchestration_id))
    normalized = intake.process(input_data)
    print(f"   Normalized {len(normalized.tasks)} tasks from {normalized.total_prds} PRDs.")

    # Manually inject the cross-PRD dependency for the test
    # Find ui-2 and db-2 task IDs
    ui2_task = next(t for t in normalized.tasks if t.requirement_id == "ui-2")
    db2_task = next(t for t in normalized.tasks if t.requirement_id == "db-2")
    ui2_task.dependencies.append(db2_task.task_id)

    print("2. Phase 3.2.2 Dependency Resolution...")
    resolver = CrossPRDResolver()
    resolved_graph = resolver.resolve(normalized)
    print(f"   Validated {len(resolved_graph.edges)} dependency edges.")

    print("3. Phase 3.2.3 Conflict Detection...")
    detector = ConflictDetector(resolved_graph)
    detector.detect() # Fail-fast
    print("   No resource or output conflicts detected.")

    print("4. Phase 3.2.4 Plan Building...")
    builder = GlobalPlanBuilder(resolved_graph)
    plan = builder.generate_global_plan()
    print(f"   Generated plan with {len(plan.waves)} execution waves.")

    print("5. Phase 3.2.5 Orchestrated Execution...")
    feedback = FeedbackCollector(orchestration_id)
    scheduler = Scheduler(plan)

    def task_executor(task):
        # Mock execution logic
        # ui-2 is optional, let's say it succeeds
        print(f"      [WAVE {next(w.wave_number for w in plan.waves if task in w.tasks)}] Executing {task.task_id}...")
        
        # Record feedback
        record = TaskExecutionRecord(
            task_id=task.task_id,
            prd_id=resolved_graph.prd_sources[task.task_id],
            wave_number=next(w.wave_number for w in plan.waves if task in w.tasks),
            status=TaskExecutionStatus.SUCCESS,
            result=f"Completed {task.task_id} flawlessly."
        )
        feedback.add_record(record)
        return record.result

    scheduler.execute(task_executor)
    
    print("\n6. Phase 3.3 Feedback Loop...")
    report = feedback.generate_report()
    print(f"   Execution Report generated for {report.orchestration_id}")
    print(f"   Final Status: {report.successful_tasks}/{report.total_tasks} tasks successful.")
    
    # Audit trail verification
    for pid in normalized.prd_metadata.keys():
        metrics = feedback.get_prd_metrics(pid)
        print(f"   PRD '{pid}': Success Rate {metrics['success_rate']*100:.0f}% ({metrics['successful_tasks']}/{metrics['total_tasks']} tasks)")

    print("\n=== Integration Test PASSED ===\n")

if __name__ == "__main__":
    try:
        run_multi_prd_orchestration()
    except Exception as e:
        print(f"\n!!! Integration Test FAILED !!!\n{str(e)}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)
