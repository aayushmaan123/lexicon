# Phase 4.1: CLI Layer Analysis (Read-Only Planning)

**Document Type**: Read-Only Analysis  
**Phase**: 4.1 (CLI Layer Planning)  
**Phase 3 Status**: LOCKED at v3.0-complete  
**Modifications Made**: NONE

---

## Executive Summary

This document analyzes how a user-facing CLI would integrate with the existing Phase 3 orchestration pipeline. **No code has been modified.** Phase 3 is treated as a complete, certified black box.

The analysis identifies:
- Entry points into the Phase 3 pipeline
- Input/output interfaces
- Command specifications (planning only)
- Data flow patterns
- Error handling requirements

---

## Phase 3 Architecture Overview

### Orchestration Pipeline (Certified v3.0-complete)

```
PRD Files
    ↓
[3.2.1 Intake] → NormalizedPRDCollection
    ↓
[3.2.2 Resolver] → ResolvedDependencyGraph
    ↓
[3.2.3 Conflict Detector] → Conflict-Free Validation
    ↓
[3.2.4 Plan Builder] → GlobalExecutionPlan (Waves)
    ↓
[3.2.5 Scheduler] → Task Execution Results
    ↓
[3.3 Feedback] → ExecutionReport (Immutable Audit)
```

### Key Characteristics

- **Deterministic**: Same inputs → same outputs
- **Fail-Fast**: Errors detected before execution
- **Immutable**: Audit trail cannot be modified
- **Stateless**: Each stage is independent
- **Well-Defined Interfaces**: Clear inputs/outputs

---

## CLI Integration Points

### 1. Multi-PRD Intake Entry Point

**Module**: `lexicon.orchestrator.multi_prd_intake`

**Entry Interface**:
```python
from lexicon.orchestrator import MultiPRDInput, MultiPRDIntake, MultiPRDMetadata
from lexicon.pipeline import PRD, AdvancedPRD

# CLI would construct:
input_data = MultiPRDInput(
    prds=[prd1, prd2, ...],  # Mixed PRD and AdvancedPRD
    metadata=MultiPRDMetadata(
        orchestration_id="cli-run-20260207",
        source="cli",
        description="User initiated from command line"
    )
)

# CLI would invoke:
intake = MultiPRDIntake()
normalized = intake.normalize(input_data)
```

**Output**: `NormalizedPRDCollection`
- `tasks`: List of `DecomposedTask` objects
- `prd_sources`: Dict mapping task_id → prd_id
- `task_count_by_prd`: Dict of task counts per PRD

**CLI Responsibilities**:
- Parse PRD files (YAML/JSON/Markdown)
- Create PRD objects using existing parsers
- Generate orchestration_id
- Handle file I/O errors

**Phase 3 Responsibilities**:
- Normalize mixed PRD types
- Generate deterministic task IDs
- Validate PRD structure
- Detect duplicate task IDs

---

### 2. Cross-PRD Resolver Entry Point

**Module**: `lexicon.orchestrator.cross_prd_resolver`

**Entry Interface**:
```python
from lexicon.orchestrator import CrossPRDResolver

# CLI would invoke:
resolver = CrossPRDResolver()
resolved_graph = resolver.resolve(normalized)
```

**Output**: `ResolvedDependencyGraph`
- `global_dependency_graph`: Dict[str, Set[str]]
- `task_metadata`: Dict with task info
- Validated cycle-free

**Exceptions to Handle**:
- `CircularDependencyError`: Cycle detected
- `MissingDependencyError`: Dependency not found
- `SelfDependencyError`: Task depends on itself

**CLI Responsibilities**:
- Catch exceptions
- Format error messages
- Exit with error code

**Phase 3 Responsibilities**:
- DFS cycle detection
- Global dependency validation
- Reference checking

---

### 3. Conflict Detector Entry Point

**Module**: `lexicon.orchestrator.conflict_detector`

**Entry Interface**:
```python
from lexicon.orchestrator import ConflictDetector

# CLI would invoke:
detector = ConflictDetector()
conflict_report = detector.detect_conflicts(resolved_graph, normalized)
```

**Output**: `ConflictReport`
- `has_conflicts`: Boolean
- `resource_conflicts`: List of overlaps
- `output_conflicts`: List of collisions

**Exceptions to Handle**:
- `ResourceConflictError`: Same resource in same wave
- `OutputConflictError`: Multiple tasks writing same file

**CLI Responsibilities**:
- Display conflicts to user
- Suggest resolution (manual PRD fixes)
- Exit before execution

**Phase 3 Responsibilities**:
- Resource overlap detection
- Output path collision detection
- Wave-level conflict analysis

---

### 4. Global Plan Builder Entry Point

**Module**: `lexicon.orchestrator.global_plan_builder`

**Entry Interface**:
```python
from lexicon.orchestrator import GlobalPlanBuilder

# CLI would invoke:
builder = GlobalPlanBuilder(orchestration_id="cli-run-001")
plan = builder.build_execution_plan(normalized, resolved_graph)
```

**Output**: `GlobalExecutionPlan`
- `waves`: List of `ExecutionWave` objects
- `total_tasks`: Task count
- `total_prds`: PRD count
- `parallel_capacity`: Max tasks per wave
- `critical_path_length`: Number of waves

**CLI Responsibilities**:
- Display execution plan (if `explain` command)
- Show wave structure
- Display parallelism stats

**Phase 3 Responsibilities**:
- Kahn's topological sort
- Wave generation
- Deterministic ordering within waves
- Statistics calculation

---

### 5. Scheduler Entry Point

**Module**: `lexicon.orchestrator.scheduler`

**Entry Interface**:
```python
from lexicon.orchestrator import Scheduler

# CLI would provide a task executor:
def task_executor(task: DecomposedTask) -> Any:
    # Execute task (shell, python, mock, etc.)
    return result

# CLI would invoke:
scheduler = Scheduler(plan)
results = scheduler.execute(task_executor)
```

**Output**: Dict[str, Any] (task_id → result)

**Exceptions to Handle**:
- `ExecutionError`: Task execution failed

**CLI Responsibilities**:
- Provide task executor (pluggable)
- Handle execution errors
- Display progress (optional)

**Phase 3 Responsibilities**:
- Wave-by-wave execution
- Deterministic task ordering
- Fail-fast on errors
- Result collection

---

### 6. Feedback Collector Entry Point

**Module**: `lexicon.orchestrator.feedback_loop`

**Entry Interface**:
```python
from lexicon.orchestrator import FeedbackCollector, TaskExecutionRecord, TaskExecutionStatus

# CLI would create collector:
collector = FeedbackCollector(orchestration_id="cli-run-001")

# CLI would add records after each task:
record = TaskExecutionRecord(
    task_id="task-prd-0-req-1",
    prd_id="prd-0",
    wave_number=0,
    status=TaskExecutionStatus.SUCCESS,
    result=result
)
collector.add_record(record)

# CLI would generate final report:
report = collector.generate_report()
```

**Output**: `ExecutionReport` (immutable)
- `orchestration_id`: String
- `records`: List of task records
- `total_tasks`: Int
- `successful_tasks`: Int
- `failed_tasks`: Int
- `skipped_tasks`: Int
- `started_at`: Timestamp
- `completed_at`: Timestamp

**CLI Responsibilities**:
- Create execution records
- Format report for display
- Save report to file (optional)

**Phase 3 Responsibilities**:
- Aggregate results
- Calculate metrics
- Provide immutable audit trail
- Per-PRD statistics

---

## Proposed CLI Commands (Planning Only)

### Command 1: `lexicon run`

**Purpose**: Execute one or more PRDs end-to-end

**Usage**:
```bash
lexicon run prd1.yaml prd2.json
lexicon run --prds-dir ./requirements/
lexicon run prd.yaml --executor shell
lexicon run prd.yaml --output report.json
```

**Pipeline Flow**:
1. Parse PRD files → PRD objects
2. MultiPRDIntake → normalize
3. CrossPRDResolver → validate dependencies
4. ConflictDetector → check conflicts
5. GlobalPlanBuilder → generate plan
6. Scheduler → execute waves
7. FeedbackCollector → generate report
8. Display/save report

**Arguments**:
- PRD file paths (positional)
- `--prds-dir`: Directory of PRD files
- `--executor`: Task executor type (shell, python, mock)
- `--output`: Save report to file
- `--verbose`: Show detailed logs

**Output**:
- Success summary
- Task statistics
- Per-PRD metrics
- Exit code 0 (success) or 1 (failure)

---

### Command 2: `lexicon validate`

**Purpose**: Validate PRDs without execution

**Usage**:
```bash
lexicon validate prd1.yaml prd2.json
lexicon validate --prds-dir ./requirements/
```

**Pipeline Flow**:
1. Parse PRD files → PRD objects
2. MultiPRDIntake → normalize
3. CrossPRDResolver → validate dependencies
4. ConflictDetector → check conflicts
5. STOP (no execution)

**Arguments**:
- PRD file paths (positional)
- `--prds-dir`: Directory of PRD files
- `--verbose`: Show detailed validation

**Output**:
- ✅ Valid (no errors)
- ❌ Invalid (show errors)
  - Dependency errors
  - Circular dependencies
  - Resource conflicts
  - Output collisions
- Exit code 0 (valid) or 1 (invalid)

---

### Command 3: `lexicon explain`

**Purpose**: Show execution plan without running

**Usage**:
```bash
lexicon explain prd1.yaml prd2.json
lexicon explain --prds-dir ./requirements/ --format tree
```

**Pipeline Flow**:
1. Parse PRD files → PRD objects
2. MultiPRDIntake → normalize
3. CrossPRDResolver → validate dependencies
4. ConflictDetector → check conflicts
5. GlobalPlanBuilder → generate plan
6. STOP (no execution)
7. Display plan

**Arguments**:
- PRD file paths (positional)
- `--prds-dir`: Directory of PRD files
- `--format`: Display format (tree, json, table)

**Output**:
- Execution waves
- Task dependencies
- Parallelism stats
- Critical path length
- Resource usage per wave
- Exit code 0 (success) or 1 (planning error)

---

### Command 4: `lexicon status`

**Purpose**: Show status of previous run

**Usage**:
```bash
lexicon status cli-run-001
lexicon status --latest
```

**Pipeline Flow**:
1. Load saved ExecutionReport
2. Display metrics

**Arguments**:
- Orchestration ID (positional)
- `--latest`: Show most recent run
- `--format`: Display format (summary, detailed, json)

**Output**:
- Orchestration ID
- Total tasks / successful / failed / skipped
- Per-PRD metrics
- Execution duration
- Exit code 0 (found) or 1 (not found)

---

## Data Models (Existing - No Changes)

### Input Models

**PRD (Phase 2.4)**:
```python
from lexicon.pipeline import PRD, PRDMetadata, PRDRequirement

prd = PRD(
    metadata=PRDMetadata(title="...", version="...", author="..."),
    overview="...",
    requirements=[
        PRDRequirement(id="...", description="...", dependencies=[...])
    ]
)
```

**AdvancedPRD (Phase 3.1)**:
```python
from lexicon.pipeline import AdvancedPRD, AdvancedPRDRequirement

prd = AdvancedPRD(
    metadata=PRDMetadata(...),
    overview="...",
    requirements=[
        AdvancedPRDRequirement(
            id="...",
            description="...",
            parent_id="...",  # Nested support
            optional=False,
            priority="HIGH",
            resources=["database", "network"]
        )
    ]
)
```

### Output Models

**ExecutionReport**:
```python
@dataclass(frozen=True)
class ExecutionReport:
    orchestration_id: str
    records: List[TaskExecutionRecord]
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    skipped_tasks: int
    started_at: datetime
    completed_at: datetime
```

**GlobalExecutionPlan**:
```python
@dataclass
class GlobalExecutionPlan:
    orchestration_id: str
    waves: List[ExecutionWave]
    total_tasks: int
    total_prds: int
    parallel_capacity: int
    critical_path_length: int
    is_deterministic: bool
```

---

## Error Handling Patterns

### Phase 3 Exceptions

**Intake Stage**:
- `DuplicateTaskIDError`: Same task ID in multiple PRDs
  - CLI Action: Show which PRDs have conflict
  - User Action: Rename task IDs to be unique

**Resolver Stage**:
- `CircularDependencyError`: Dependency cycle detected
  - CLI Action: Show cycle path (A → B → C → A)
  - User Action: Break the cycle in PRD
- `MissingDependencyError`: Dependency doesn't exist
  - CLI Action: Show task and missing dependency
  - User Action: Add missing task or fix reference
- `SelfDependencyError`: Task depends on itself
  - CLI Action: Show problematic task
  - User Action: Remove self-dependency

**Conflict Stage**:
- `ResourceConflictError`: Resource overlap in same wave
  - CLI Action: Show conflicting tasks and resource
  - User Action: Add dependency to serialize access
- `OutputConflictError`: Multiple tasks write to same file
  - CLI Action: Show conflicting tasks and file path
  - User Action: Change output paths or add dependency

**Execution Stage**:
- `ExecutionError`: Task execution failed
  - CLI Action: Show task, error message, wave number
  - User Action: Fix task implementation or dependencies

### CLI Error Codes

```
0 - Success
1 - Validation Error (dependencies, conflicts)
2 - Execution Error (task failed)
3 - File Error (PRD not found, invalid format)
4 - Configuration Error (invalid arguments)
```

---

## File Format Support

### PRD File Formats (Existing Parsers)

**YAML** (Phase 2.4):
```yaml
metadata:
  title: "My PRD"
  version: "1.0"
  author: "Alice"
overview: "Build feature X"
requirements:
  - id: "req-1"
    description: "Setup database"
    type: "infrastructure"
    priority: "critical"
  - id: "req-2"
    description: "Add API"
    dependencies: ["req-1"]
```

**JSON** (Phase 2.4):
```json
{
  "metadata": {...},
  "overview": "...",
  "requirements": [...]
}
```

**Markdown** (Phase 3.1):
```markdown
# PRD: Feature X

**Version**: 1.0

## Requirements

### req-1: Setup Database
- **Priority**: critical
- **Type**: infrastructure

### req-2: Add API
- **Dependencies**: req-1
```

### Parsing Strategy

**CLI Approach**:
1. Read file extension (.yaml, .json, .md)
2. Use appropriate parser:
   - YAML/JSON: `PRDParser.parse_from_json()`
   - Markdown: `AdvancedPRDParser.parse_from_markdown()`
3. Return PRD or AdvancedPRD object
4. Handle parsing errors gracefully

**No New Parsers Needed**: Phase 3 provides all required parsers

---

## Validation Hooks

### Pre-Orchestration Validation

**File Level**:
- File exists
- File readable
- Valid YAML/JSON/Markdown syntax
- Required fields present

**PRD Level** (Existing Validators):
- `PRDValidator`: Phase 2.4 PRDs
- `AdvancedPRDValidator`: Phase 3.1 PRDs
- Validates metadata, requirements, structure

### Orchestration Validation

**Intake** (`MultiPRDIntake`):
- Duplicate task IDs
- Valid PRD types
- Non-empty PRD list

**Resolver** (`CrossPRDResolver`):
- Circular dependencies
- Missing dependencies
- Self-dependencies
- Valid references

**Detector** (`ConflictDetector`):
- Resource conflicts
- Output conflicts
- Constraint violations

### Post-Execution Validation

**Feedback** (`FeedbackCollector`):
- All tasks recorded
- Status consistency
- Metrics accuracy

---

## Output Formatting

### ExecutionReport Display

**Summary Format**:
```
Orchestration: cli-run-20260207
Status: ✅ SUCCESS
Duration: 45.2 seconds

Tasks: 15 total
  ✅ 14 successful (93.3%)
  ❌ 1 failed (6.7%)
  ⊘ 0 skipped (0.0%)

PRD Metrics:
  prd-0-backend: 8/8 tasks (100%)
  prd-1-frontend: 6/7 tasks (85.7%)
```

**Detailed Format**:
```
Wave 0 (2 tasks):
  ✅ task-prd-0-init-db [0.5s]
  ✅ task-prd-1-setup-env [0.3s]

Wave 1 (5 tasks):
  ✅ task-prd-0-create-schema [1.2s]
  ✅ task-prd-0-seed-data [0.8s]
  ✅ task-prd-1-install-deps [2.1s]
  ❌ task-prd-1-build-frontend [FAILED: npm error]
  ✅ task-prd-1-config-nginx [0.4s]
...
```

**JSON Format**:
```json
{
  "orchestration_id": "cli-run-001",
  "status": "SUCCESS",
  "total_tasks": 15,
  "successful_tasks": 14,
  "failed_tasks": 1,
  "execution_time_seconds": 45.2,
  "prds": [
    {
      "prd_id": "prd-0",
      "total_tasks": 8,
      "successful_tasks": 8,
      "success_rate": 1.0
    },
    ...
  ],
  "records": [...]
}
```

### ExecutionPlan Display

**Tree Format**:
```
Execution Plan: cli-run-001
Total Tasks: 15 across 5 waves
Parallel Capacity: 5 tasks/wave max
Critical Path: 5 waves

Wave 0 (2 tasks, 0 dependencies):
  ├─ task-prd-0-init-db
  └─ task-prd-1-setup-env

Wave 1 (5 tasks, depends on Wave 0):
  ├─ task-prd-0-create-schema → [init-db]
  ├─ task-prd-0-seed-data → [create-schema]
  ├─ task-prd-1-install-deps → [setup-env]
  ├─ task-prd-1-build-frontend → [install-deps]
  └─ task-prd-1-config-nginx → [setup-env]
...
```

---

## Task Executors (Pluggable)

### Executor Interface

**CLI Provides**:
```python
from lexicon.pipeline.advanced_prd_models import DecomposedTask
from typing import Any

def task_executor(task: DecomposedTask) -> Any:
    """
    Execute a task and return result.
    
    Args:
        task: The task to execute
        
    Returns:
        Execution result (any type)
        
    Raises:
        Exception on failure
    """
    pass
```

### Executor Implementations (Future Phase 4.3)

**Shell Executor**:
```python
def shell_executor(task: DecomposedTask) -> str:
    # Execute task.description as shell command
    result = subprocess.run(task.description, shell=True, capture_output=True)
    if result.returncode != 0:
        raise Exception(result.stderr.decode())
    return result.stdout.decode()
```

**Python Executor**:
```python
def python_executor(task: DecomposedTask) -> Any:
    # Execute task.description as Python code
    exec_globals = {}
    exec(task.description, exec_globals)
    return exec_globals.get('result')
```

**Mock Executor** (Testing):
```python
def mock_executor(task: DecomposedTask) -> str:
    # Always succeed, return task ID
    return f"Mock execution of {task.task_id}"
```

**Custom Executor**:
```python
def custom_executor(task: DecomposedTask) -> Any:
    # User-defined execution logic
    # Could call APIs, run containers, etc.
    pass
```

---

## Configuration (Future)

### CLI Configuration File

**~/.lexicon/config.yaml**:
```yaml
default_executor: shell
output_format: summary
verbose: false
report_dir: ~/.lexicon/reports
```

**Project Configuration**:
```yaml
# .lexicon.yaml in project root
prds_dir: ./requirements
executor: python
output_dir: ./build
```

---

## Examples (Conceptual)

### Example 1: Simple Run

```bash
$ lexicon run backend.yaml

Orchestrating: backend.yaml
  ✓ Intake: 5 tasks normalized
  ✓ Resolver: 0 cycles, 4 dependencies
  ✓ Conflicts: 0 resource conflicts, 0 output collisions
  ✓ Plan: 3 waves, max 2 parallel tasks

Executing...
Wave 0: ✓ init-db (0.5s)
Wave 1: ✓ create-schema (1.2s) ✓ setup-auth (0.8s)
Wave 2: ✓ deploy-api (2.1s)

✅ SUCCESS: 5/5 tasks completed in 4.6s
```

### Example 2: Validation Error

```bash
$ lexicon validate frontend.yaml backend.yaml

Validating: 2 PRDs
  ✓ Intake: 12 tasks normalized
  ✗ Resolver: Circular dependency detected

❌ ERROR: Circular dependency
  frontend.yaml:ui-login → backend.yaml:api-auth
  backend.yaml:api-auth → backend.yaml:db-setup
  backend.yaml:db-setup → frontend.yaml:ui-login

Fix: Remove circular dependency in PRD files
Exit code: 1
```

### Example 3: Conflict Detection

```bash
$ lexicon validate service-a.yaml service-b.yaml

Validating: 2 PRDs
  ✓ Intake: 8 tasks normalized
  ✓ Resolver: 0 cycles, 6 dependencies
  ✗ Conflicts: 1 resource conflict

❌ ERROR: Resource conflict (DATABASE)
  Wave 2:
    - task-prd-0-migrate-db (service-a.yaml:migrate)
    - task-prd-1-seed-db (service-b.yaml:seed)

Fix: Add dependency: service-b.yaml:seed → service-a.yaml:migrate
Exit code: 1
```

### Example 4: Explain Plan

```bash
$ lexicon explain app.yaml --format tree

Execution Plan: app.yaml
Total: 8 tasks across 4 waves
Parallelism: max 3 tasks/wave
Critical Path: 4 waves (5.2s estimated)

Wave 0 (1 task):
  └─ task-prd-0-setup-env

Wave 1 (3 tasks):
  ├─ task-prd-0-install-deps → [setup-env]
  ├─ task-prd-0-init-db → [setup-env]
  └─ task-prd-0-setup-cache → [setup-env]

Wave 2 (2 tasks):
  ├─ task-prd-0-build-app → [install-deps]
  └─ task-prd-0-migrate-db → [init-db]

Wave 3 (2 tasks):
  ├─ task-prd-0-test-app → [build-app, migrate-db]
  └─ task-prd-0-deploy-app → [build-app, migrate-db]

Resources by Wave:
  Wave 0: [filesystem]
  Wave 1: [network, database, filesystem]
  Wave 2: [network, database]
  Wave 3: [network, filesystem]
```

---

## Architecture Principles

### Separation of Concerns

**CLI Layer (Phase 4.1)**:
- ✅ User interaction
- ✅ File I/O
- ✅ Output formatting
- ✅ Error message translation
- ❌ NO orchestration logic
- ❌ NO validation logic
- ❌ NO scheduling logic

**Orchestration Layer (Phase 3 - LOCKED)**:
- ✅ Multi-PRD intake
- ✅ Dependency resolution
- ✅ Conflict detection
- ✅ Execution planning
- ✅ Task scheduling
- ✅ Feedback collection

### Interface Contract

**CLI → Phase 3**:
- CLI provides: PRD objects, metadata, task executor
- CLI calls: Phase 3 entry points
- CLI handles: Phase 3 exceptions

**Phase 3 → CLI**:
- Phase 3 provides: Data models, validators, orchestrators
- Phase 3 returns: Reports, plans, exceptions
- Phase 3 guarantees: Determinism, immutability, fail-fast

### No Modifications Required

Phase 3 is complete and requires **ZERO changes**:
- ✅ All interfaces exist
- ✅ All data models defined
- ✅ All exceptions defined
- ✅ All orchestration logic complete
- ✅ All validation complete

CLI only needs to:
- Parse files
- Create objects
- Call methods
- Format output

---

## Testing Strategy (Future)

### CLI Unit Tests

**Command Parsing**:
- Valid arguments
- Invalid arguments
- Help text
- Version info

**File Loading**:
- Valid PRD files
- Invalid syntax
- Missing files
- Permission errors

**Output Formatting**:
- Summary format
- Detailed format
- JSON format
- Error messages

### CLI Integration Tests

**End-to-End Workflows**:
- `lexicon run` with valid PRDs
- `lexicon validate` with conflicts
- `lexicon explain` with dependencies
- `lexicon status` with saved reports

**Error Handling**:
- Circular dependencies
- Resource conflicts
- Execution failures
- File errors

### CLI Acceptance Tests

**User Scenarios**:
- First-time user
- Multi-PRD orchestration
- Error recovery
- Report generation

---

## Documentation (Future)

### User Documentation

**README.md**:
- Installation
- Quick start
- Basic commands
- Examples

**User Guide**:
- Command reference
- PRD file formats
- Troubleshooting
- Best practices

**Examples**:
- Simple PRD
- Multi-PRD with dependencies
- Error scenarios
- Custom executors

### Developer Documentation

**API Reference**:
- Phase 3 interfaces
- Data models
- Exceptions

**Architecture Guide**:
- CLI design
- Integration patterns
- Extension points

---

## Constraints Verified

✅ **Read-Only Analysis**: No code modified  
✅ **Black Box Approach**: Phase 3 treated as complete  
✅ **Integration Points**: Entry points documented  
✅ **No Engine Changes**: All functionality exists  
✅ **No Future Features**: Only existing capabilities analyzed  
✅ **Planning Only**: No implementation provided  

---

## Conclusion

Phase 3 provides a complete, certified orchestration pipeline with well-defined interfaces. A CLI layer can be implemented without any modifications to Phase 3 by:

1. **Parsing PRD files** using existing parsers
2. **Creating input objects** (`MultiPRDInput`, etc.)
3. **Calling Phase 3 stages** sequentially
4. **Catching exceptions** and formatting errors
5. **Displaying results** from execution reports

**All orchestration logic remains in Phase 3 (locked at v3.0-complete).**

**No code modifications required or made.**

**Awaiting explicit instruction for next steps.**

---

**Document Status**: ✅ Complete  
**Modifications Made**: ❌ NONE  
**Phase 3 Status**: 🔒 LOCKED  
**Next Steps**: Awaiting approval for Phase 4.1 implementation
