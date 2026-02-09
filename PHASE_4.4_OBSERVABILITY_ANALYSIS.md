# Phase 4.4: Observability & Logging Analysis (Read-Only)

**Document Type**: Read-Only Analysis  
**Status**: Planning Phase  
**Phase 3 Status**: LOCKED at v3.0-complete  
**Created**: 2026-02-08

## Executive Summary

This document analyzes how Phase 3's developer-oriented `ExecutionReport` can be transformed into user-facing observability outputs for Phase 4.4. The analysis confirms that **all necessary data already exists** in Phase 3's feedback loop. Phase 4.4 would only need to **transform outputs** without changing data collection.

### Key Finding

**No Phase 3 Modifications Required**: The `ExecutionReport` and `TaskExecutionRecord` data structures contain comprehensive execution information. Phase 4.4 formatters can be implemented externally without touching the orchestration engine.

---

## 1. Existing Data Structures (Phase 3)

### 1.1 ExecutionReport

From `lexicon/orchestrator/feedback_loop.py`:

```python
@dataclass(frozen=True)
class ExecutionReport:
    """Immutable final report of a plan execution."""
    orchestration_id: str              # Unique orchestration identifier
    records: List[TaskExecutionRecord] # All task execution records
    total_tasks: int                   # Total number of tasks
    successful_tasks: int              # Count of successful tasks
    failed_tasks: int                  # Count of failed tasks
    skipped_tasks: int                 # Count of skipped tasks
    started_at: datetime               # Orchestration start time
    completed_at: datetime             # Orchestration completion time
```

**Available Information**:
- ✅ Orchestration identifier (unique ID)
- ✅ Complete task history (all records)
- ✅ Aggregated metrics (total, success, failed, skipped)
- ✅ Execution timing (start, end timestamps)
- ✅ Immutable (frozen=True ensures audit trail integrity)

### 1.2 TaskExecutionRecord

```python
@dataclass(frozen=True)
class TaskExecutionRecord:
    """Immutable record of a single task execution."""
    task_id: str                       # Unique task identifier
    prd_id: str                        # Source PRD identifier
    wave_number: int                   # Execution wave (parallelism group)
    status: TaskExecutionStatus        # SUCCESS, FAILED, or SKIPPED
    result: Any = None                 # Task execution result
    error: Optional[str] = None        # Error message if failed
    started_at: datetime               # Task start time
    completed_at: datetime             # Task completion time
```

**Available Information**:
- ✅ Task identification (ID, source PRD)
- ✅ Execution wave (parallelism grouping)
- ✅ Status (success, failed, skipped)
- ✅ Results and errors
- ✅ Per-task timing (start, end)

### 1.3 GlobalExecutionPlan

From `lexicon/orchestrator/global_plan_builder.py`:

```python
@dataclass(frozen=True)
class GlobalExecutionPlan:
    """The complete execution plan across all orchestrated PRDs."""
    waves: List[ExecutionWave]  # Ordered execution waves
    total_tasks: int             # Total tasks in plan
    total_prds: int              # Number of PRDs
    orchestration_id: str        # Unique identifier
```

**Available Information**:
- ✅ Wave structure (parallel execution groups)
- ✅ Task counts (total tasks, total PRDs)
- ✅ Orchestration identifier

### 1.4 ExecutionWave

```python
@dataclass(frozen=True)
class ExecutionWave:
    """A group of tasks that can be executed in parallel."""
    tasks: List[DecomposedTask]  # Tasks in this wave
    wave_number: int             # Wave sequence number
```

**Available Information**:
- ✅ Tasks in each wave (parallel execution group)
- ✅ Wave ordering (sequence number)

---

## 2. Available Metrics

### 2.1 Overall Metrics (from ExecutionReport)

**Direct Fields**:
- `total_tasks`: Total number of tasks executed
- `successful_tasks`: Count of successful tasks
- `failed_tasks`: Count of failed tasks
- `skipped_tasks`: Count of skipped tasks

**Calculated Metrics**:
- **Success Rate**: `successful_tasks / total_tasks × 100`
- **Failure Rate**: `failed_tasks / total_tasks × 100`
- **Duration**: `completed_at - started_at`

### 2.2 Per-PRD Metrics

From `FeedbackCollector.get_prd_metrics(prd_id)`:

```python
{
    "total_tasks": int,         # Tasks from this PRD
    "successful_tasks": int,    # Successful tasks from this PRD
    "failed_tasks": int,        # Failed tasks from this PRD
    "skipped_tasks": int,       # Skipped tasks from this PRD
    "success_rate": float       # Success rate (0.0 to 1.0)
}
```

### 2.3 Per-Wave Metrics (calculated from records)

```python
wave_metrics = {
    "wave_number": int,
    "total_tasks": len([r for r in records if r.wave_number == wave_num]),
    "successful_tasks": len([r for r in records if r.wave_number == wave_num 
                             and r.status == SUCCESS]),
    "duration": max([r.completed_at for r in wave_records]) - 
                min([r.started_at for r in wave_records])
}
```

### 2.4 Per-Task Metrics (from TaskExecutionRecord)

**Direct Fields**:
- `task_id`, `prd_id`, `wave_number`
- `status` (SUCCESS, FAILED, SKIPPED)
- `result`, `error`

**Calculated Metrics**:
- **Duration**: `completed_at - started_at`
- **Dependencies**: (available from DecomposedTask)
- **Resources**: (available from DecomposedTask)

---

## 3. Output Formats

### 3.1 Summary Format

**Purpose**: High-level executive overview (5-10 lines)

**Example**:
```
╭─────────────────────────────────────────────╮
│ Orchestration Report                        │
├─────────────────────────────────────────────┤
│ ID: orch-20260208-183000                    │
│ Status: ✓ COMPLETED                         │
│ Duration: 12.34s                            │
│                                             │
│ Tasks: 15 total                             │
│   ✓ Success: 13 (86.7%)                     │
│   ✗ Failed: 2 (13.3%)                       │
│   ○ Skipped: 0 (0.0%)                       │
│                                             │
│ PRDs: 3 (database-setup, user-interface,    │
│          analytics)                         │
│ Waves: 5                                    │
│ Parallel Capacity: max 4 tasks/wave         │
╰─────────────────────────────────────────────╯
```

**Data Sources**:
- `orchestration_id` → ID
- `completed_at - started_at` → Duration
- `total_tasks`, `successful_tasks`, `failed_tasks`, `skipped_tasks` → Task counts
- `len(set(r.prd_id for r in records))` → PRD count
- `max(r.wave_number for r in records) + 1` → Wave count
- `max(len([r for r in records if r.wave_number == w]) for w in waves)` → Parallel capacity

### 3.2 Detailed Format

**Purpose**: Task-by-task breakdown organized by wave

**Example**:
```
═══════════════════════════════════════════════
 Execution Details: orch-20260208-183000
═══════════════════════════════════════════════
Started: 2026-02-08 18:30:00 UTC
Completed: 2026-02-08 18:30:12 UTC
Duration: 12.34s

Wave 0 (2 tasks, 0.5s)
─────────────────────────────────────────────
  ✓ task-prd-0-database-setup-db-1 [0.3s]
    Description: Create database
    PRD: database-setup
    Result: Database 'prod_db' created successfully
    Started: 18:30:00.100
    Completed: 18:30:00.400

  ✓ task-prd-1-user-interface-ui-1 [0.2s]
    Description: Login page
    PRD: user-interface
    Result: Login page rendered
    Started: 18:30:00.100
    Completed: 18:30:00.300

Wave 1 (3 tasks, 1.2s)
─────────────────────────────────────────────
  ✓ task-prd-0-database-setup-db-2 [0.8s]
    Description: Add user table
    PRD: database-setup
    Dependencies: task-prd-0-database-setup-db-1
    Result: User table created with 5 columns
    Started: 18:30:00.500
    Completed: 18:30:01.300

  ✗ task-prd-2-analytics-analytics-1 [0.4s]
    Description: Setup tracking
    PRD: analytics
    Error: Connection timeout to analytics.example.com:443
           Suggestion: Check network connectivity and firewall rules
    Started: 18:30:00.500
    Failed: 18:30:00.900
    
  ✓ task-prd-1-user-interface-ui-2 [0.6s]
    Description: Dashboard
    PRD: user-interface
    Dependencies: task-prd-0-database-setup-db-2
    Result: Dashboard view created
    Started: 18:30:01.100
    Completed: 18:30:01.700

[... remaining waves ...]
```

**Data Sources**:
- Group records by `wave_number`
- Sort within wave by `task_id` (deterministic)
- Extract: `status`, `task_id`, `result`, `error`, timing
- Calculate per-task duration: `completed_at - started_at`
- Calculate per-wave duration: max(completed_at) - min(started_at)

### 3.3 JSON Format

**Purpose**: Machine-readable structured export

**Example**:
```json
{
  "orchestration_id": "orch-20260208-183000",
  "status": "COMPLETED",
  "started_at": "2026-02-08T18:30:00.000Z",
  "completed_at": "2026-02-08T18:30:12.340Z",
  "duration_seconds": 12.34,
  "metrics": {
    "total_tasks": 15,
    "successful_tasks": 13,
    "failed_tasks": 2,
    "skipped_tasks": 0,
    "success_rate": 0.867,
    "failure_rate": 0.133
  },
  "prds": {
    "database-setup": {
      "total_tasks": 5,
      "successful_tasks": 5,
      "failed_tasks": 0,
      "skipped_tasks": 0,
      "success_rate": 1.0
    },
    "user-interface": {
      "total_tasks": 6,
      "successful_tasks": 6,
      "failed_tasks": 0,
      "skipped_tasks": 0,
      "success_rate": 1.0
    },
    "analytics": {
      "total_tasks": 4,
      "successful_tasks": 2,
      "failed_tasks": 2,
      "skipped_tasks": 0,
      "success_rate": 0.5
    }
  },
  "waves": [
    {
      "wave_number": 0,
      "total_tasks": 2,
      "successful_tasks": 2,
      "failed_tasks": 0,
      "duration_seconds": 0.5
    },
    {
      "wave_number": 1,
      "total_tasks": 3,
      "successful_tasks": 2,
      "failed_tasks": 1,
      "duration_seconds": 1.2
    }
  ],
  "tasks": [
    {
      "task_id": "task-prd-0-database-setup-db-1",
      "prd_id": "database-setup",
      "wave_number": 0,
      "status": "SUCCESS",
      "duration_seconds": 0.3,
      "started_at": "2026-02-08T18:30:00.100Z",
      "completed_at": "2026-02-08T18:30:00.400Z",
      "result": "Database 'prod_db' created successfully"
    },
    {
      "task_id": "task-prd-2-analytics-analytics-1",
      "prd_id": "analytics",
      "wave_number": 1,
      "status": "FAILED",
      "duration_seconds": 0.4,
      "started_at": "2026-02-08T18:30:00.500Z",
      "completed_at": "2026-02-08T18:30:00.900Z",
      "error": "Connection timeout to analytics.example.com:443"
    }
  ]
}
```

**Transformation Logic**:
```python
def to_json(report: ExecutionReport) -> dict:
    return {
        "orchestration_id": report.orchestration_id,
        "status": "COMPLETED",
        "started_at": report.started_at.isoformat(),
        "completed_at": report.completed_at.isoformat(),
        "duration_seconds": (report.completed_at - report.started_at).total_seconds(),
        "metrics": {
            "total_tasks": report.total_tasks,
            "successful_tasks": report.successful_tasks,
            "failed_tasks": report.failed_tasks,
            "skipped_tasks": report.skipped_tasks,
            "success_rate": report.successful_tasks / report.total_tasks 
                            if report.total_tasks > 0 else 0,
        },
        "prds": {...},  # get_prd_metrics() for each PRD
        "waves": [...], # aggregate by wave_number
        "tasks": [record_to_dict(r) for r in report.records]
    }
```

### 3.4 Tree Format

**Purpose**: Hierarchical PRD → Wave → Task visualization

**Example**:
```
Orchestration: orch-20260208-183000 (12.34s, 86.7% success)
│
├─ PRD: database-setup (5 tasks, 100% success)
│  ├─ Wave 0 (1 task, 0.3s)
│  │  └─ ✓ db-1: Create database [0.3s]
│  │     Result: Database 'prod_db' created successfully
│  │
│  └─ Wave 1 (1 task, 0.8s)
│     └─ ✓ db-2: Add user table [0.8s]
│        Dependencies: db-1
│        Result: User table created with 5 columns
│
├─ PRD: user-interface (6 tasks, 100% success)
│  ├─ Wave 0 (1 task, 0.2s)
│  │  └─ ✓ ui-1: Login page [0.2s]
│  │     Result: Login page rendered
│  │
│  └─ Wave 1 (1 task, 0.6s)
│     └─ ✓ ui-2: Dashboard [0.6s]
│        Dependencies: db-2
│        Result: Dashboard view created
│
└─ PRD: analytics (4 tasks, 50% success)
   └─ Wave 1 (2 tasks, 0.9s)
      ├─ ✗ analytics-1: Setup tracking [0.4s]
      │  Error: Connection timeout to analytics.example.com:443
      │  
      └─ ✓ analytics-2: Configure events [0.5s]
         Result: Event tracking configured
```

**Transformation Logic**:
1. Group records by `prd_id`
2. Within each PRD, group by `wave_number`
3. Sort tasks within wave by `task_id`
4. Build tree structure with ASCII box-drawing characters

### 3.5 Timeline Format (Gantt-style)

**Purpose**: Visual timeline showing execution waves and parallelism

**Example**:
```
Timeline (12.34s total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Wave 0 │████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│ 0.0s - 0.5s (2 tasks)
Wave 1 │░░░░██████████░░░░░░░░░░░░░░░░░░░░░░░░│ 0.5s - 1.7s (3 tasks)
Wave 2 │░░░░░░░░░░░░████████░░░░░░░░░░░░░░░░░░│ 1.7s - 3.5s (4 tasks)
Wave 3 │░░░░░░░░░░░░░░░░░░████████░░░░░░░░░░░░│ 3.5s - 5.2s (3 tasks)
Wave 4 │░░░░░░░░░░░░░░░░░░░░░░░░████████░░░░░░│ 5.2s - 6.8s (3 tasks)

Legend: █ executing  ░ idle/waiting
        ✓ all success  ✗ has failures  ○ skipped

Per-Wave Breakdown:
  Wave 0: 2 tasks (✓✓) - 0.5s
  Wave 1: 3 tasks (✓✗✓) - 1.2s (1 failed: analytics-1)
  Wave 2: 4 tasks (✓✓✓✓) - 1.8s
  Wave 3: 3 tasks (✓✓✓) - 1.7s
  Wave 4: 3 tasks (✓✓✓) - 1.6s

Critical Path: 5 waves (sequential dependency chain)
Max Parallelism: 4 tasks (wave 2)
```

**Transformation Logic**:
```python
def generate_timeline(report: ExecutionReport) -> str:
    total_duration = (report.completed_at - report.started_at).total_seconds()
    
    # Group records by wave
    waves = {}
    for record in report.records:
        if record.wave_number not in waves:
            waves[record.wave_number] = []
        waves[record.wave_number].append(record)
    
    # Calculate wave timings
    wave_timings = []
    for wave_num in sorted(waves.keys()):
        wave_records = waves[wave_num]
        start = min(r.started_at for r in wave_records)
        end = max(r.completed_at for r in wave_records)
        duration = (end - start).total_seconds()
        
        # Calculate offset from orchestration start
        offset = (start - report.started_at).total_seconds()
        
        wave_timings.append({
            "wave_number": wave_num,
            "offset": offset,
            "duration": duration,
            "tasks": len(wave_records),
            "has_failures": any(r.status == "FAILED" for r in wave_records)
        })
    
    # Generate ASCII timeline
    width = 50
    lines = []
    for wt in wave_timings:
        start_pos = int(wt["offset"] / total_duration * width)
        end_pos = int((wt["offset"] + wt["duration"]) / total_duration * width)
        
        bar = "░" * start_pos
        bar += "█" * (end_pos - start_pos)
        bar += "░" * (width - end_pos)
        
        status = "✗" if wt["has_failures"] else "✓"
        line = f"Wave {wt['wave_number']} │{bar}│ {wt['offset']:.1f}s - {wt['offset']+wt['duration']:.1f}s ({wt['tasks']} tasks) {status}"
        lines.append(line)
    
    return "\n".join(lines)
```

---

## 4. Human-Readable Summaries

### 4.1 Success Rate Visualization

**Text-based Progress Bar**:
```
Success Rate: 86.7%
[████████████████████░░░░] 13/15 tasks successful
```

**Color-coded Output** (ANSI codes):
```
Tasks: 15 total
  ✓ Success: 13 (86.7%)  [green]
  ✗ Failed: 2 (13.3%)    [red]
  ○ Skipped: 0 (0.0%)    [yellow]
```

### 4.2 Duration Formatting

**Human-Readable Format**:
- `< 1s`: "234ms"
- `< 60s`: "12.34s"
- `< 3600s`: "2m 15s"
- `>= 3600s`: "1h 23m 45s"

**Example Function**:
```python
def format_duration(seconds: float) -> str:
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"
```

### 4.3 Failed Task Highlighting

```
Failed Tasks (2):
  ┌─────────────────────────────────────────┐
  │ Task: analytics-1                       │
  │ Wave: 1                                 │
  │ Duration: 0.4s                          │
  │ Error: Connection timeout to            │
  │        analytics.example.com:443        │
  │ Suggestion: Check network connectivity  │
  │             and firewall rules          │
  └─────────────────────────────────────────┘
  
  ┌─────────────────────────────────────────┐
  │ Task: analytics-2                       │
  │ Wave: 2                                 │
  │ Duration: 0.3s                          │
  │ Error: API key validation failed        │
  │ Suggestion: Verify API key in           │
  │             configuration               │
  └─────────────────────────────────────────┘
```

---

## 5. Structured Logging

### 5.1 Log Levels

**INFO**: Normal execution events
```
[INFO] 2026-02-08T18:30:00.100Z orchestration_id=orch-001 wave=0 task_id=db-1 status=STARTED
[INFO] 2026-02-08T18:30:00.400Z orchestration_id=orch-001 wave=0 task_id=db-1 status=SUCCESS duration_ms=300
```

**WARNING**: Non-critical issues
```
[WARN] 2026-02-08T18:30:00.500Z orchestration_id=orch-001 prd_id=analytics task_id=analytics-1 message="Retrying connection"
```

**ERROR**: Task failures
```
[ERROR] 2026-02-08T18:30:00.900Z orchestration_id=orch-001 wave=1 task_id=analytics-1 status=FAILED error="Connection timeout" duration_ms=400
```

### 5.2 Structured Fields

**Standard Fields** (all log messages):
- `timestamp`: ISO 8601 format
- `level`: INFO, WARNING, ERROR
- `orchestration_id`: Unique orchestration ID
- `message`: Human-readable message

**Task-Specific Fields** (task execution logs):
- `prd_id`: Source PRD identifier
- `wave`: Wave number
- `task_id`: Task identifier
- `status`: STARTED, SUCCESS, FAILED, SKIPPED
- `duration_ms`: Task duration in milliseconds

**Error Fields** (error logs):
- `error`: Error message
- `error_type`: Error category
- `stack_trace`: (optional) Stack trace

### 5.3 JSON Log Format

```json
{
  "timestamp": "2026-02-08T18:30:00.400Z",
  "level": "INFO",
  "orchestration_id": "orch-20260208-183000",
  "prd_id": "database-setup",
  "wave": 0,
  "task_id": "task-prd-0-database-setup-db-1",
  "status": "SUCCESS",
  "duration_ms": 300,
  "message": "Task completed successfully",
  "metadata": {
    "result": "Database 'prod_db' created successfully"
  }
}
```

```json
{
  "timestamp": "2026-02-08T18:30:00.900Z",
  "level": "ERROR",
  "orchestration_id": "orch-20260208-183000",
  "prd_id": "analytics",
  "wave": 1,
  "task_id": "task-prd-2-analytics-analytics-1",
  "status": "FAILED",
  "duration_ms": 400,
  "error": "Connection timeout to analytics.example.com:443",
  "error_type": "NetworkError",
  "message": "Task execution failed"
}
```

---

## 6. CLI Output Formatting

### 6.1 Terminal Colors (ANSI Codes)

**Color Definitions**:
```python
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    GRAY = "\033[90m"
```

**Usage**:
```python
def format_status(status: TaskExecutionStatus) -> str:
    if status == TaskExecutionStatus.SUCCESS:
        return f"{Colors.GREEN}✓ SUCCESS{Colors.RESET}"
    elif status == TaskExecutionStatus.FAILED:
        return f"{Colors.RED}✗ FAILED{Colors.RESET}"
    else:
        return f"{Colors.YELLOW}○ SKIPPED{Colors.RESET}"
```

### 6.2 Box Drawing Characters

**Characters**:
```python
class Box:
    TOP_LEFT = "╭"
    TOP_RIGHT = "╮"
    BOTTOM_LEFT = "╰"
    BOTTOM_RIGHT = "╯"
    HORIZONTAL = "─"
    VERTICAL = "│"
    TEE_RIGHT = "├"
    TEE_LEFT = "┤"
    BRANCH = "├─"
    LAST_BRANCH = "└─"
```

**Box Function**:
```python
def draw_box(content: List[str], title: str = "") -> str:
    max_width = max(len(line) for line in content)
    if title:
        max_width = max(max_width, len(title))
    
    lines = []
    lines.append(f"{Box.TOP_LEFT}{Box.HORIZONTAL * (max_width + 2)}{Box.TOP_RIGHT}")
    
    if title:
        lines.append(f"{Box.VERTICAL} {title.ljust(max_width)} {Box.VERTICAL}")
        lines.append(f"{Box.TEE_RIGHT}{Box.HORIZONTAL * (max_width + 2)}{Box.TEE_LEFT}")
    
    for line in content:
        lines.append(f"{Box.VERTICAL} {line.ljust(max_width)} {Box.VERTICAL}")
    
    lines.append(f"{Box.BOTTOM_LEFT}{Box.HORIZONTAL * (max_width + 2)}{Box.BOTTOM_RIGHT}")
    
    return "\n".join(lines)
```

### 6.3 Progress Indicators

**Spinner** (during execution):
```
⠋ Executing wave 0 (2 tasks)...
⠙ Executing wave 1 (3 tasks)...
⠹ Executing wave 2 (4 tasks)...
✓ Execution complete
```

**Progress Bar**:
```
Progress: [████████████████████░░░░] 13/15 tasks (86.7%)
```

---

## 7. Execution Timelines

### 7.1 Overall Timeline

**From**: `ExecutionReport.started_at`  
**To**: `ExecutionReport.completed_at`  
**Duration**: `completed_at - started_at`

**Example**:
```
Orchestration Timeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Start:    2026-02-08 18:30:00.000 UTC
End:      2026-02-08 18:30:12.340 UTC
Duration: 12.34s
```

### 7.2 Per-Wave Timeline

**Calculation**:
```python
def calculate_wave_timeline(report: ExecutionReport, wave_number: int):
    wave_records = [r for r in report.records if r.wave_number == wave_number]
    
    if not wave_records:
        return None
    
    start = min(r.started_at for r in wave_records)
    end = max(r.completed_at for r in wave_records)
    duration = (end - start).total_seconds()
    
    return {
        "wave_number": wave_number,
        "started_at": start,
        "completed_at": end,
        "duration": duration,
        "task_count": len(wave_records)
    }
```

**Example**:
```
Wave Timelines
──────────────────────────────────────────────
Wave 0: 18:30:00.100 → 18:30:00.500 (0.4s, 2 tasks)
Wave 1: 18:30:00.500 → 18:30:01.700 (1.2s, 3 tasks)
Wave 2: 18:30:01.700 → 18:30:03.500 (1.8s, 4 tasks)
Wave 3: 18:30:03.500 → 18:30:05.200 (1.7s, 3 tasks)
Wave 4: 18:30:05.200 → 18:30:06.800 (1.6s, 3 tasks)
```

### 7.3 Per-PRD Timeline

**Calculation**:
```python
def calculate_prd_timeline(report: ExecutionReport, prd_id: str):
    prd_records = [r for r in report.records if r.prd_id == prd_id]
    
    if not prd_records:
        return None
    
    start = min(r.started_at for r in prd_records)
    end = max(r.completed_at for r in prd_records)
    duration = (end - start).total_seconds()
    
    return {
        "prd_id": prd_id,
        "started_at": start,
        "completed_at": end,
        "duration": duration,
        "task_count": len(prd_records)
    }
```

### 7.4 Gantt Chart Visualization

**ASCII Gantt Chart**:
```
Gantt Chart (time →)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRD: database-setup
  db-1      ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  db-2      ░░░░░░████████░░░░░░░░░░░░░░░░░░░░░░░░░░░

PRD: user-interface  
  ui-1      ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ui-2      ░░░░░░░░██████░░░░░░░░░░░░░░░░░░░░░░░░░░░

PRD: analytics
  analytics-1 ░░░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ✗
  analytics-2 ░░░░░░░░░░████░░░░░░░░░░░░░░░░░░░░░░░░░░

Time:     0s    2s    4s    6s    8s   10s   12s
Legend:   █ executing  ░ idle  ✗ failed
```

---

## 8. Error Formatting

### 8.1 Error Categorization

**By Status** (from TaskExecutionRecord):
- `FAILED` → Critical errors
- `SKIPPED` → Dependency failures or optional tasks

**By Type** (inferred from error message):
- NetworkError: Connection timeouts, DNS failures
- ValidationError: Input validation failures
- ResourceError: File not found, permission denied
- ExecutionError: Command failures, exceptions

### 8.2 Error Report Format

```
Error Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Errors: 2

┌─────────────────────────────────────────────────────┐
│ Error 1: analytics-1                                │
├─────────────────────────────────────────────────────┤
│ Task ID: task-prd-2-analytics-analytics-1           │
│ PRD: analytics                                      │
│ Wave: 1                                             │
│ Duration: 0.4s                                      │
│                                                     │
│ Error Type: NetworkError                            │
│ Message: Connection timeout to                      │
│          analytics.example.com:443                  │
│                                                     │
│ Recovery Suggestions:                               │
│   • Check network connectivity                      │
│   • Verify firewall rules allow HTTPS (443)         │
│   • Confirm analytics service is running            │
│                                                     │
│ Affected Dependencies:                              │
│   • analytics-3 (skipped due to failure)            │
│   • analytics-4 (skipped due to failure)            │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Error 2: analytics-2                                │
├─────────────────────────────────────────────────────┤
│ Task ID: task-prd-2-analytics-analytics-2           │
│ PRD: analytics                                      │
│ Wave: 2                                             │
│ Duration: 0.3s                                      │
│                                                     │
│ Error Type: ValidationError                         │
│ Message: API key validation failed                  │
│                                                     │
│ Recovery Suggestions:                               │
│   • Verify API key in configuration                 │
│   • Check API key expiration date                   │
│   • Regenerate API key if necessary                 │
└─────────────────────────────────────────────────────┘
```

### 8.3 Stack Trace Formatting

**If Available** (from TaskExecutionRecord.error):
```
Stack Trace:
  File "task_executor.py", line 45, in execute
    result = subprocess.run(command, timeout=10)
  File "subprocess.py", line 491, in run
    with Popen(*popenargs, **kwargs) as process:
  subprocess.TimeoutExpired: Command timed out after 10 seconds
```

**Formatting**:
- Indent by 2 spaces
- Gray color for non-critical lines
- Red color for exception line
- Truncate to last 10 lines if too long

---

## 9. Metric Calculations

### 9.1 Success Rate

**Formula**:
```python
success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
```

**By Entity**:
- Overall: `report.successful_tasks / report.total_tasks`
- Per-PRD: `prd_metrics['successful_tasks'] / prd_metrics['total_tasks']`
- Per-Wave: `wave_successful / wave_total`

### 9.2 Duration Calculations

**Overall**:
```python
total_duration = (report.completed_at - report.started_at).total_seconds()
```

**Per-Task**:
```python
task_duration = (record.completed_at - record.started_at).total_seconds()
```

**Per-Wave**:
```python
wave_records = [r for r in report.records if r.wave_number == wave_num]
wave_start = min(r.started_at for r in wave_records)
wave_end = max(r.completed_at for r in wave_records)
wave_duration = (wave_end - wave_start).total_seconds()
```

**Per-PRD**:
```python
prd_records = [r for r in report.records if r.prd_id == prd_id]
prd_start = min(r.started_at for r in prd_records)
prd_end = max(r.completed_at for r in prd_records)
prd_duration = (prd_end - prd_start).total_seconds()
```

### 9.3 Parallelism Metrics

**Max Parallelism** (tasks per wave):
```python
max_parallelism = max(
    len([r for r in report.records if r.wave_number == w])
    for w in set(r.wave_number for r in report.records)
)
```

**Average Parallelism**:
```python
avg_parallelism = total_tasks / num_waves
```

### 9.4 Critical Path Analysis

**Critical Path Length** (number of waves):
```python
critical_path_length = max(r.wave_number for r in report.records) + 1
```

**Critical Path Duration** (sum of wave durations if sequential):
```python
# This is total_duration if waves are strictly sequential
# If waves overlap, this requires more complex calculation
critical_path_duration = total_duration
```

---

## 10. Integration Points

### 10.1 ExecutionReport → Formatters

**Interface**:
```python
class ReportFormatter(ABC):
    @abstractmethod
    def format(self, report: ExecutionReport) -> str:
        """Transform ExecutionReport to formatted output."""
        pass
```

**Implementations**:
- `SummaryFormatter`: Generates summary format
- `DetailedFormatter`: Generates detailed format
- `JSONFormatter`: Generates JSON format
- `TreeFormatter`: Generates tree format
- `TimelineFormatter`: Generates timeline format

**Usage**:
```python
report = feedback.generate_report()

# Summary
summary_formatter = SummaryFormatter()
print(summary_formatter.format(report))

# JSON export
json_formatter = JSONFormatter()
with open("execution_report.json", "w") as f:
    f.write(json_formatter.format(report))
```

### 10.2 Formatters → CLI Output

**CLI Commands Would Call Formatters**:
```python
# lexicon run command
def run_command(prd_files):
    # ... orchestration logic ...
    report = feedback.generate_report()
    
    # Display summary
    formatter = SummaryFormatter()
    print(formatter.format(report))
    
    # Optionally display detailed view
    if args.verbose:
        detailed = DetailedFormatter()
        print(detailed.format(report))
```

### 10.3 Formatters → File Exports

**Export JSON**:
```python
def export_report(report: ExecutionReport, format: str, output_path: str):
    formatters = {
        "json": JSONFormatter(),
        "text": DetailedFormatter(),
        "summary": SummaryFormatter()
    }
    
    formatter = formatters.get(format)
    if not formatter:
        raise ValueError(f"Unknown format: {format}")
    
    content = formatter.format(report)
    
    with open(output_path, "w") as f:
        f.write(content)
```

### 10.4 Formatters → External Logging Systems

**Structured Log Export**:
```python
class StructuredLogger:
    def __init__(self, output_stream):
        self.stream = output_stream
    
    def log_orchestration(self, report: ExecutionReport):
        # Log start event
        self.stream.write(json.dumps({
            "timestamp": report.started_at.isoformat(),
            "event": "orchestration_started",
            "orchestration_id": report.orchestration_id,
            "total_tasks": report.total_tasks
        }) + "\n")
        
        # Log task events
        for record in report.records:
            self.stream.write(json.dumps({
                "timestamp": record.completed_at.isoformat(),
                "event": "task_completed",
                "orchestration_id": report.orchestration_id,
                "task_id": record.task_id,
                "prd_id": record.prd_id,
                "wave": record.wave_number,
                "status": record.status.value,
                "duration_ms": (record.completed_at - record.started_at).total_seconds() * 1000
            }) + "\n")
        
        # Log completion event
        self.stream.write(json.dumps({
            "timestamp": report.completed_at.isoformat(),
            "event": "orchestration_completed",
            "orchestration_id": report.orchestration_id,
            "metrics": {
                "total": report.total_tasks,
                "successful": report.successful_tasks,
                "failed": report.failed_tasks,
                "success_rate": report.successful_tasks / report.total_tasks
            }
        }) + "\n")
```

---

## 11. Transformation Patterns

### 11.1 Data Extraction

**From Nested Structures**:
```python
def extract_prd_ids(report: ExecutionReport) -> List[str]:
    """Extract unique PRD IDs from report."""
    return list(set(r.prd_id for r in report.records))

def extract_wave_numbers(report: ExecutionReport) -> List[int]:
    """Extract wave numbers in order."""
    return sorted(set(r.wave_number for r in report.records))
```

### 11.2 Aggregation

**Counts**:
```python
def count_by_status(records: List[TaskExecutionRecord]) -> Dict[str, int]:
    """Count records by status."""
    counts = {}
    for record in records:
        status = record.status.value
        counts[status] = counts.get(status, 0) + 1
    return counts
```

**Rates**:
```python
def calculate_success_rate(records: List[TaskExecutionRecord]) -> float:
    """Calculate success rate."""
    if not records:
        return 0.0
    successful = sum(1 for r in records if r.status == TaskExecutionStatus.SUCCESS)
    return successful / len(records)
```

**Durations**:
```python
def calculate_total_duration(records: List[TaskExecutionRecord]) -> float:
    """Calculate total duration (min start to max end)."""
    if not records:
        return 0.0
    start = min(r.started_at for r in records)
    end = max(r.completed_at for r in records)
    return (end - start).total_seconds()
```

### 11.3 Formatting

**Symbols**:
```python
def status_symbol(status: TaskExecutionStatus) -> str:
    """Convert status to symbol."""
    symbols = {
        TaskExecutionStatus.SUCCESS: "✓",
        TaskExecutionStatus.FAILED: "✗",
        TaskExecutionStatus.SKIPPED: "○"
    }
    return symbols.get(status, "?")
```

**Colors**:
```python
def colorize(text: str, status: TaskExecutionStatus) -> str:
    """Add color to text based on status."""
    colors = {
        TaskExecutionStatus.SUCCESS: Colors.GREEN,
        TaskExecutionStatus.FAILED: Colors.RED,
        TaskExecutionStatus.SKIPPED: Colors.YELLOW
    }
    color = colors.get(status, "")
    return f"{color}{text}{Colors.RESET}" if color else text
```

### 11.4 Filtering

**By Status**:
```python
def filter_failed(report: ExecutionReport) -> List[TaskExecutionRecord]:
    """Get only failed tasks."""
    return [r for r in report.records if r.status == TaskExecutionStatus.FAILED]
```

**By PRD**:
```python
def filter_by_prd(report: ExecutionReport, prd_id: str) -> List[TaskExecutionRecord]:
    """Get tasks from specific PRD."""
    return [r for r in report.records if r.prd_id == prd_id]
```

**By Wave**:
```python
def filter_by_wave(report: ExecutionReport, wave_num: int) -> List[TaskExecutionRecord]:
    """Get tasks from specific wave."""
    return [r for r in report.records if r.wave_number == wave_num]
```

---

## 12. Constraints

### 12.1 Analysis Constraints (This Document)

✅ **Observation Only**: This is a read-only analysis. No code has been modified.

✅ **No Logging Refactors**: Phase 3's FeedbackCollector and logging remain unchanged.

✅ **No Code Edits**: This document only analyzes existing structures.

✅ **Existing Data Only**: All metrics and formats are based on data already available in Phase 3.

### 12.2 Design Constraints (Future Implementation)

✅ **No Collection Changes**: Phase 4.4 must NOT modify how Phase 3 collects data.

✅ **Transform Only**: All formatters are pure functions that transform ExecutionReport.

✅ **Stateless**: Formatters have no side effects or state.

✅ **Backward Compatible**: Phase 3 orchestration continues to work without formatters.

### 12.3 Explicit Out-of-Scope

❌ **Real-time Monitoring**: Formatters work on completed ExecutionReport, not streaming.

❌ **Dashboard UI**: CLI output only, no web dashboard.

❌ **Custom Metrics**: Only use metrics available in ExecutionReport.

❌ **Log Aggregation**: Formatters produce logs, but don't aggregate from external systems.

❌ **Alerting**: No alerting system, only formatting and display.

---

## Conclusion

Phase 3's `ExecutionReport` and `TaskExecutionRecord` structures contain comprehensive execution information suitable for all observability needs. Phase 4.4 would only need to implement **transformation logic** to convert this developer-oriented data into user-facing formats.

### Key Insights

1. **Complete Data**: All necessary information for observability already exists in Phase 3.

2. **No Collection Changes**: All formatters can be implemented externally without modifying Phase 3 data collection.

3. **Multiple Views**: Same ExecutionReport supports summary, detailed, JSON, tree, and timeline formats.

4. **Per-Entity Metrics**: Can break down by PRD, wave, or task using existing fields.

5. **Timeline Reconstruction**: Timestamps enable complete timeline and Gantt chart generation.

6. **Error Context**: Failed tasks include error messages suitable for user-facing error reports.

7. **Extensible**: New formatters can be added without touching Phase 3.

### Implementation Requirements (Phase 4.4)

If Phase 4.4 proceeds to implementation, it would need:

1. **Formatter Classes**: SummaryFormatter, DetailedFormatter, JSONFormatter, TreeFormatter, TimelineFormatter
2. **CLI Output Utilities**: Terminal colors, box drawing, progress bars
3. **Structured Logger**: JSON log format for external systems
4. **Duration Formatter**: Human-readable duration strings
5. **Error Formatter**: Categorization and recovery suggestions

**All can be implemented without modifying Phase 3 orchestration engine.**

---

**End of Analysis**

This document provides a comprehensive read-only analysis of Phase 3's execution data structures and how they can be transformed for user-facing observability in Phase 4.4. No code modifications have been made to Phase 3.

**Awaiting explicit instruction for next steps.**
