# Lexicon: Orchestration Engine Feature Brief

Lexicon's Multi-PRD Orchestration engine provides a robust framework for managing complex software requirements. Below are the core pillars that ensure reliability and scalability:

## 1. Deterministic Task Mapping
- **Feature**: Every PRD requirement is mapped to a globally unique, compound Task ID (`task-{prd_id}-{req_id}`).
- **Benefit**: Ensures 100% repeatability across orchestration runs. Identical inputs always produce identical task graphs, crucial for debugging and auditing.

## 2. Fail-Fast Conflict Detection
- **Feature**: Resource (Database, FS) and output path collisions are identified *before* execution begins.
- **Benefit**: Prevents downstream failures and inconsistent states by stopping execution at the first sign of a contention.

## 3. Dependency-Ordered Execution (Kahn's Algorithm)
- **Feature**: Uses advanced topological sorting to group tasks into optimal execution waves.
- **Benefit**: Maximizes safe parallelism. Tasks are only executed once all their requirements (even cross-PRD) are met.

## 4. Immutable Feedback Loop
- **Feature**: Maintains a structured, read-only audit trail of every task result, error, and status.
- **Benefit**: provides clear metrics for PRD success and facilitates automated retries or rollback logic in future versions.

---

# Future Roadmap: Enhancement Suggestions

| Enhancement | Impact | Effort | Priority | Description |
|-------------|--------|--------|----------|-------------|
| **Priority-Based Scheduling** | High | Medium | 1 | Sort tasks within waves by requirement priority (Critical > High > Medium). |
| **Real-time Monitoring** | Medium | High | 2 | A dashboard to visualize wave execution and bottlenecks in real-time. |
| **Incremental Re-Orchestration** | High | High | 3 | Only re-execute waves affected by a changed PRD or a failure. |
| **External API Hooks** | Medium | Medium | 4 | Trigger external build systems (CI/CD) or Slack notifications on wave completion. |

## Feature Implementation Plan: Priority-Based Scheduling
**Goal**: Ensure that within each parallel execution wave, the most critical tasks are prioritized for resource allocation.

1. **Design**: Update `GlobalPlanBuilder` to sort `current_wave_ids` not just by ID, but primary sort by `task.priority`.
2. **Verification**: Create a test case where two independent tasks in wave 0 have different priorities. Verify the execution sequence.
3. **Integration**: No changes needed to `MultiPRDIntake` or `Resolver`. Minimal change to `GlobalPlanBuilder.build_execution_waves`.
