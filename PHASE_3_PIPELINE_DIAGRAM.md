# Lexicon: Multi-PRD Orchestration Pipeline

The following diagram illustrates the structural flow of the Lexicon orchestration engine, from initial PRD ingestion to final execution feedback.

```mermaid
graph TD
    subgraph "Phase 3.2.1: Intake"
        P1["PRD A (2.4)"] --> IN["MultiPRDIntake"]
        P2["PRD B (3.1)"] --> IN
        IN --> NC["NormalizedPRDCollection<br/>(Deterministic IDs)"]
    end

    subgraph "Phase 3.2.2: Resolver"
        NC --> RES["CrossPRDResolver"]
        RES --> RDG["ResolvedDependencyGraph<br/>(Validated & Cycle-Free)"]
    end

    subgraph "Phase 3.2.3: Conflict Detector"
        RDG --> CD["ConflictDetector"]
        CD -- "Overlap Found" --> ERR1["ResourceConflictError"]
        CD -- "Collision Found" --> ERR2["OutputConflictError"]
        CD -- "Clear" --> RDG2["Conflict-Free Graph"]
    end

    subgraph "Phase 3.2.4: Plan Builder"
        RDG2 --> PB["GlobalPlanBuilder<br/>(Kahn's Algorithm)"]
        PB --> GEP["GlobalExecutionPlan<br/>(Execution Waves)"]
    end

    subgraph "Phase 3.2.5: Scheduler"
        GEP --> SCHED["Scheduler"]
        SCHED --> EXEC["Task Execution<br/>(Deterministic Ordering)"]
    end

    subgraph "Phase 3.3: Feedback Loop"
        EXEC --> FB["FeedbackCollector"]
        FB --> ER["ExecutionReport<br/>(Immutable Audit)"]
    end
```

## Key Architectural Principles
- **Deterministic**: The same input always produces the same execution order.
- **Fail-Fast**: Structural, dependency, or conflict errors are caught before execution begins.
- **Isolated**: Clear separation of concerns between planning (3.2.1-3.2.4) and execution (3.2.5-3.3).
- **Immutable**: All intermediate and final reports are immutable for reliable auditing.
