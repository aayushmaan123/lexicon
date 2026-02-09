
"""
Lexicon Phase 3: Multi-PRD Orchestration Demo

This script demonstrates the full pipeline:
Intake -> Resolution -> Conflict Detection -> Plan Building -> Execution -> Feedback.

It uses a representative scenario with:
- PRD 1 (Backend - Phase 2.4)
- PRD 2 (Frontend - Phase 3.1 Advanced)
- Cross-PRD Dependencies
- Resource usage
"""

import logging
import sys
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

# Minimal logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def run_demo():
    print("="*60)
    print(" LEXICON MULTI-PRD ORCHESTRATION DEMO")
    print("="*60)
    
    orch_id = "DEMO-RUN-001"
    print(f"\n1. INTAKE PHASE: Orchestrating mixed PRDs (ID: {orch_id})")
    
    # PRD A: Backend API
    prd_a = PRD(
        metadata=PRDMetadata(title="CORE-API", version="2.0", author="Backend-Team"),
        overview="Essential API services.",
        requirements=[
            PRDRequirement(id="init-db", type=RequirementType.INFRASTRUCTURE, priority=RequirementPriority.CRITICAL, description="Initialize database schema"),
            PRDRequirement(id="user-auth", type=RequirementType.FEATURE, priority=RequirementPriority.HIGH, description="User authentication endpoint", dependencies=["init-db"]),
        ]
    )
    
    # PRD B: Mobile User Interface
    prd_b = AdvancedPRD(
        metadata=PRDMetadata(title="MOBILE-UI", version="1.0", author="Mobile-Team"),
        overview="Mobile frontend application.",
        requirements=[
            AdvancedPRDRequirement(id="login-view", description="Secure login screen", resources=["network"]),
            AdvancedPRDRequirement(id="data-sync", description="Sync user data", dependencies=[]),
        ]
    )

    intake = MultiPRDIntake()
    input_data = MultiPRDInput(prds=[prd_a, prd_b], metadata=MultiPRDMetadata(orchestration_id=orch_id))
    normalized = intake.process(input_data)
    
    print(f"   [OK] Normalized {len(normalized.tasks)} tasks.")
    for task in normalized.tasks:
        print(f"        - {task.task_id} (Source: {normalized.prd_sources[task.task_id]})")

    print(f"\n2. RESOLUTION PHASE: Validating cross-PRD dependencies")
    # Manually inject cross-PRD dependency for demo
    # Data Sync (Mobile) depends on User Auth (Backend)
    auth_task = next(t for t in normalized.tasks if t.requirement_id == "user-auth")
    sync_task = next(t for t in normalized.tasks if t.requirement_id == "data-sync")
    sync_task.dependencies.append(auth_task.task_id)
    
    resolver = CrossPRDResolver()
    graph = resolver.resolve(normalized)
    print(f"   [OK] Validated {len(graph.edges)} dependency edges. No cycles found.")

    print(f"\n3. CONFLICT DETECTION PHASE: Analyzing resource and path collisions")
    # Simulate a potential conflict check
    detector = ConflictDetector(graph)
    detector.detect()
    print("   [OK] No resource (database/network) or output collisions detected.")

    print(f"\n4. PLAN BUILDING PHASE: Generating execution waves (Kahn's Algorithm)")
    builder = GlobalPlanBuilder(graph)
    plan = builder.generate_global_plan()
    print(f"   [OK] Plan ready with {len(plan.waves)} execution waves.")
    for wave in plan.waves:
        tids = [t.task_id for t in wave.tasks]
        print(f"        Wave {wave.wave_number}: {', '.join(tids)}")

    print(f"\n5. EXECUTION PHASE: Wave-by-wave orchestration")
    feedback = FeedbackCollector(orch_id)
    scheduler = Scheduler(plan)

    def demo_executor(task):
        print(f"      - Executing {task.task_id}...")
        record = TaskExecutionRecord(
            task_id=task.task_id,
            prd_id=graph.prd_sources[task.task_id],
            wave_number=next(w.wave_number for w in plan.waves if task in w.tasks),
            status=TaskExecutionStatus.SUCCESS,
            result="Execution successful."
        )
        feedback.add_record(record)
        return "Success"

    scheduler.execute(demo_executor)

    print(f"\n6. FEEDBACK PHASE: Aggregating results")
    report = feedback.generate_report()
    print(f"   [OK] Report generated for {report.orchestration_id}")
    print(f"   TOTAL TASKS   : {report.total_tasks}")
    print(f"   SUCCESSFUL    : {report.successful_tasks}")
    
    print("\n" + "="*60)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("="*60)

if __name__ == "__main__":
    run_demo()
