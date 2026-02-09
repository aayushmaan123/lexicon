# Phase 4.3: Execution Adapters - Read-Only Analysis

**Status**: Read-Only Analysis (NO CODE MODIFICATIONS)  
**Date**: 2026-02-08  
**Phase 3 State**: LOCKED at v3.0-complete

## Executive Summary

This document analyzes how task execution is currently invoked in the Phase 3 orchestration engine and identifies where pluggable execution adapter boundaries would exist.

**Key Finding**: The Phase 3 Scheduler already provides a clean adapter boundary through its `task_executor` callback parameter. No engine modifications are required to support pluggable executors.

## Table of Contents

1. [Current Execution Model](#current-execution-model)
2. [Adapter Boundary Identification](#adapter-boundary-identification)
3. [Executor Interface Specification](#executor-interface-specification)
4. [Executor Types](#executor-types)
5. [Integration Patterns](#integration-patterns)
6. [Error Handling](#error-handling)
7. [Resource Management](#resource-management)
8. [Phase 3 Compatibility](#phase-3-compatibility)
9. [Examples](#examples)
10. [Constraints](#constraints)

---

## Current Execution Model

### Scheduler Role

The Phase 3 Scheduler (`lexicon/orchestrator/scheduler.py`) orchestrates the execution of a `GlobalExecutionPlan`. Its responsibilities are:

1. **Wave Management**: Execute waves sequentially
2. **Task Ordering**: Execute tasks within waves deterministically (lexicographically sorted)
3. **Fail-Fast**: Stop immediately on task failure
4. **Result Collection**: Aggregate task results into a dictionary

### Current Invocation Pattern

```python
# From Scheduler.execute() - Line 40-74
def execute(self, task_executor: Callable[[DecomposedTask], Any]) -> Dict[str, Any]:
    """
    Execute the plan wave by wave.
    
    Args:
        task_executor: A function that takes a DecomposedTask and returns its result.
        
    Returns:
        A dictionary of task_id to execution result.
        
    Raises:
        ExecutionError: If any task execution fails.
    """
    for wave in self.plan.waves:
        for task in wave.tasks:
            try:
                result = task_executor(task)  # ← ADAPTER BOUNDARY
                self.task_results[task.task_id] = result
            except Exception as e:
                raise ExecutionError(f"Task {task.task_id} failed: {str(e)}") from e
    
    return self.task_results
```

### Key Observations

**Adapter Boundary Already Exists**:
- The `task_executor` parameter is a callback: `Callable[[DecomposedTask], Any]`
- Scheduler doesn't care HOW tasks are executed
- Scheduler only cares THAT tasks are executed and return results
- This is a perfect adapter pattern

**Current Usage** (from `verify_full_orchestration_with_feedback.py`):
```python
def task_executor(task):
    # Mock execution logic
    print(f"Executing {task.task_id}...")
    record = TaskExecutionRecord(...)
    feedback.add_record(record)
    return record.result

scheduler.execute(task_executor)
```

### Execution Flow

```
GlobalExecutionPlan
    ↓
Scheduler.execute(task_executor)
    ↓
For each ExecutionWave:
    ↓
    For each DecomposedTask (lexicographically sorted):
        ↓
        task_executor(task) ← ADAPTER BOUNDARY
        ↓
        Collect result
        ↓
        (Fail fast on exception)
    ↓
    Next wave
↓
Return all task results
```

---

## Adapter Boundary Identification

### Entry Point

**Module**: `lexicon/orchestrator/scheduler.py`  
**Class**: `Scheduler`  
**Method**: `execute(self, task_executor: Callable[[DecomposedTask], Any])`  
**Line**: 40

### Interface Contract

```python
task_executor: Callable[[DecomposedTask], Any]
```

**Input**: `DecomposedTask` object  
**Output**: Any (task execution result)  
**Exceptions**: May raise any exception (caught by Scheduler as ExecutionError)

### DecomposedTask Structure

From `lexicon/pipeline/advanced_prd_models.py`:

```python
@dataclass
class DecomposedTask:
    """
    A task after decomposition from potentially nested structure.
    
    This is the flattened representation ready for execution.
    """
    task_id: str                    # Unique task identifier
    requirement_id: str             # Source requirement ID
    description: str                # Task description for agents
    dependencies: List[str]         # Flattened dependency list
    is_optional: bool = False       # Whether task is optional
    priority: RequirementPriority   # Priority for scheduling hints
    resources: List[ResourceType]   # Resource types needed
    context: Dict[str, Any]         # Additional execution context
    metadata: Dict[str, Any]        # Additional metadata
```

### Available Task Context

Executors have access to:

1. **Identification**:
   - `task.task_id`: Unique identifier (e.g., "task-prd-0-db-setup-db-1")
   - `task.requirement_id`: Source requirement (e.g., "db-1")

2. **Description**:
   - `task.description`: Human-readable description

3. **Dependencies**:
   - `task.dependencies`: List of task IDs this depends on
   - Note: Dependencies are already satisfied when executor is called

4. **Resources**:
   - `task.resources`: List of ResourceType (FILE_WRITE, DATABASE, NETWORK, etc.)
   - Used by Phase 3 for conflict detection
   - Executors can validate resource availability

5. **Context**:
   - `task.context`: Dict with arbitrary execution data
   - Could contain: commands, code, inputs, outputs, etc.
   - Executor-specific data goes here

6. **Metadata**:
   - `task.metadata`: Additional task metadata
   - `task.priority`: Priority level
   - `task.is_optional`: Optional flag

---

## Executor Interface Specification

### Abstract Base Class (Conceptual)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class TaskResult:
    """Structured result from task execution."""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class TaskExecutor(ABC):
    """
    Abstract base class for task executors.
    
    Executors implement the strategy for how to execute tasks.
    """
    
    @abstractmethod
    def execute(self, task: DecomposedTask) -> TaskResult:
        """
        Execute a single task.
        
        Args:
            task: The task to execute
            
        Returns:
            TaskResult with execution outcome
            
        Raises:
            ExecutionError: If task execution fails critically
        """
        pass
    
    def validate_resources(self, task: DecomposedTask) -> bool:
        """
        Validate that required resources are available.
        
        Args:
            task: The task to validate
            
        Returns:
            True if all resources available, False otherwise
        """
        return True
    
    def cleanup(self, task: DecomposedTask) -> None:
        """
        Cleanup resources after task execution.
        
        Args:
            task: The task to cleanup after
        """
        pass
```

### Interface Contract

**Executors MUST**:
1. Accept a `DecomposedTask` object
2. Return a result (Any type, or structured TaskResult)
3. Raise exceptions for critical failures
4. Be stateless (no state between calls)

**Executors MAY**:
1. Validate resources before execution
2. Cleanup resources after execution
3. Log execution details
4. Return structured results

**Executors MUST NOT**:
1. Modify the GlobalExecutionPlan
2. Execute tasks out of order
3. Retry failed tasks (Scheduler handles this)
4. Access other tasks' results during execution

---

## Executor Types

### 1. ShellExecutor

**Purpose**: Execute shell commands  
**Input Format**: `task.context["command"]` contains shell command  
**Output**: stdout/stderr from command  
**Errors**: Non-zero exit codes raise ExecutionError

**Conceptual Specification**:
```python
class ShellExecutor(TaskExecutor):
    """Executes tasks as shell commands."""
    
    def execute(self, task: DecomposedTask) -> TaskResult:
        """
        Execute task as shell command.
        
        Expects task.context to contain:
        - "command": Shell command to execute
        - "cwd": Working directory (optional)
        - "env": Environment variables (optional)
        - "timeout": Timeout in seconds (optional)
        """
        command = task.context.get("command")
        if not command:
            raise ValueError(f"Task {task.task_id} missing 'command' in context")
        
        # Execute shell command
        # Capture stdout/stderr
        # Check exit code
        # Return result
        pass
```

**Example Task Context**:
```python
task.context = {
    "command": "python setup.py install",
    "cwd": "/path/to/project",
    "timeout": 300
}
```

### 2. PythonExecutor

**Purpose**: Execute Python code  
**Input Format**: `task.context["code"]` contains Python code or function  
**Output**: Return value from code execution  
**Errors**: Python exceptions raised during execution

**Conceptual Specification**:
```python
class PythonExecutor(TaskExecutor):
    """Executes tasks as Python code."""
    
    def execute(self, task: DecomposedTask) -> TaskResult:
        """
        Execute task as Python code.
        
        Expects task.context to contain:
        - "code": Python code string to exec()
        - "function": Python function to call
        - "args": Function arguments (optional)
        - "kwargs": Function keyword arguments (optional)
        """
        if "function" in task.context:
            # Call Python function
            func = task.context["function"]
            args = task.context.get("args", [])
            kwargs = task.context.get("kwargs", {})
            result = func(*args, **kwargs)
        elif "code" in task.context:
            # Execute Python code
            code = task.context["code"]
            exec(code)
        
        return TaskResult(success=True, output=result)
```

**Example Task Context**:
```python
def create_database(name):
    # Database creation logic
    return f"Created database {name}"

task.context = {
    "function": create_database,
    "args": ["users_db"]
}
```

### 3. MockExecutor

**Purpose**: Return mock results for testing  
**Input Format**: `task.context["mock_result"]` contains expected result  
**Output**: The mock result  
**Errors**: Only if explicitly configured to fail

**Conceptual Specification**:
```python
class MockExecutor(TaskExecutor):
    """Returns mock results for testing."""
    
    def execute(self, task: DecomposedTask) -> TaskResult:
        """
        Return mock result.
        
        Expects task.context to contain:
        - "mock_result": Result to return
        - "mock_error": Error to raise (optional)
        - "mock_delay": Delay in seconds (optional)
        """
        if "mock_error" in task.context:
            raise ExecutionError(task.context["mock_error"])
        
        result = task.context.get("mock_result", f"Mock result for {task.task_id}")
        return TaskResult(success=True, output=result)
```

**Example Task Context**:
```python
task.context = {
    "mock_result": {"status": "success", "rows_created": 100}
}
```

### 4. NoopExecutor

**Purpose**: Do nothing (dry-run mode)  
**Input Format**: N/A  
**Output**: Success message  
**Errors**: Never fails

**Conceptual Specification**:
```python
class NoopExecutor(TaskExecutor):
    """Does nothing - dry run mode."""
    
    def execute(self, task: DecomposedTask) -> TaskResult:
        """
        Do nothing, just return success.
        
        Useful for:
        - Dry-run validation
        - Plan verification
        - Dependency graph testing
        """
        return TaskResult(
            success=True,
            output=f"Noop execution of {task.task_id}"
        )
```

---

## Integration Patterns

### Executor Selection

**By Task Type**:
```python
def get_executor(task: DecomposedTask) -> TaskExecutor:
    """Select executor based on task context."""
    if "command" in task.context:
        return ShellExecutor()
    elif "function" in task.context or "code" in task.context:
        return PythonExecutor()
    elif "mock_result" in task.context:
        return MockExecutor()
    else:
        return NoopExecutor()
```

**By Configuration**:
```python
# Global configuration
executor_config = {
    "default": "noop",  # Dry-run by default
    "mode": "shell"     # Or "python", "mock"
}

def create_executor(config: Dict) -> TaskExecutor:
    """Create executor from configuration."""
    mode = config.get("mode", "noop")
    if mode == "shell":
        return ShellExecutor()
    elif mode == "python":
        return PythonExecutor()
    elif mode == "mock":
        return MockExecutor()
    else:
        return NoopExecutor()
```

### Usage with Scheduler

**Pattern 1: Direct Callback**
```python
executor = ShellExecutor()
scheduler.execute(executor.execute)
```

**Pattern 2: Executor Wrapper**
```python
def task_executor_wrapper(task):
    executor = get_executor(task)
    result = executor.execute(task)
    return result.output if result.success else None

scheduler.execute(task_executor_wrapper)
```

**Pattern 3: With Feedback**
```python
def task_executor_with_feedback(task):
    executor = get_executor(task)
    try:
        result = executor.execute(task)
        record = TaskExecutionRecord(
            task_id=task.task_id,
            status=TaskExecutionStatus.SUCCESS,
            result=result.output
        )
        feedback.add_record(record)
        return result.output
    except Exception as e:
        record = TaskExecutionRecord(
            task_id=task.task_id,
            status=TaskExecutionStatus.FAILED,
            error=str(e)
        )
        feedback.add_record(record)
        raise

scheduler.execute(task_executor_with_feedback)
```

---

## Error Handling

### Executor Error Responsibilities

**Executors Should**:
1. Catch execution errors
2. Format error messages clearly
3. Raise ExecutionError for critical failures
4. Log execution details
5. Cleanup resources on error

**Example Error Handling**:
```python
class ShellExecutor(TaskExecutor):
    def execute(self, task: DecomposedTask) -> TaskResult:
        try:
            # Execute command
            result = subprocess.run(...)
            
            if result.returncode != 0:
                raise ExecutionError(
                    f"Command failed with exit code {result.returncode}: "
                    f"{result.stderr}"
                )
            
            return TaskResult(success=True, output=result.stdout)
            
        except subprocess.TimeoutExpired as e:
            raise ExecutionError(f"Command timeout after {e.timeout}s")
        except Exception as e:
            raise ExecutionError(f"Execution failed: {str(e)}") from e
        finally:
            self.cleanup(task)
```

### Scheduler Error Handling (Unchanged)

From Phase 3 Scheduler:
```python
try:
    result = task_executor(task)
    self.task_results[task.task_id] = result
except Exception as e:
    logger.error(f"Critical failure in task {task.task_id}: {str(e)}")
    raise ExecutionError(f"Task {task.task_id} failed: {str(e)}") from e
```

**Scheduler Behavior**:
1. Catches any executor exception
2. Logs the error
3. Wraps in ExecutionError
4. Re-raises to stop execution
5. No retry (fail-fast)

### Error Types

**ExecutionError**: Critical task failure (stops orchestration)
```python
class ExecutionError(Exception):
    """Raised when a task execution fails critically."""
    pass
```

**Executor-Specific Errors**:
- `ShellError`: Command execution failed
- `PythonError`: Code execution failed
- `ResourceError`: Required resource unavailable
- `TimeoutError`: Execution timeout
- `ValidationError`: Pre-execution validation failed

---

## Resource Management

### Resource Types

From Phase 3 (`lexicon/pipeline/advanced_prd_models.py`):

```python
class ResourceType(str, Enum):
    FILE_WRITE = "file_write"
    FILE_READ = "file_read"
    DATABASE = "database"
    NETWORK = "network"
    COMPUTE = "compute"
    MEMORY = "memory"
```

### Executor Resource Responsibilities

**Pre-Execution**:
1. Validate required resources are available
2. Acquire resources (open files, connect to DB, etc.)
3. Check resource permissions
4. Raise error if resources unavailable

**During Execution**:
1. Use resources as needed
2. Monitor resource usage
3. Handle resource errors gracefully

**Post-Execution**:
1. Release resources (close files, disconnect, etc.)
2. Clean up temporary resources
3. Free memory/compute

### Example Resource Validation

```python
class ShellExecutor(TaskExecutor):
    def validate_resources(self, task: DecomposedTask) -> bool:
        """Validate required resources."""
        for resource in task.resources:
            if resource == ResourceType.FILE_WRITE:
                # Check write permissions
                pass
            elif resource == ResourceType.DATABASE:
                # Check database connection
                pass
            elif resource == ResourceType.NETWORK:
                # Check network availability
                pass
        return True
    
    def cleanup(self, task: DecomposedTask) -> None:
        """Cleanup resources."""
        for resource in task.resources:
            if resource == ResourceType.FILE_WRITE:
                # Close file handles
                pass
            elif resource == ResourceType.DATABASE:
                # Close database connections
                pass
```

### Resource Context

Executors can use `task.context` to specify resources:

```python
task.context = {
    "command": "python setup.py install",
    "resources": {
        "files": ["/tmp/output.txt"],
        "database": "postgresql://localhost/mydb",
        "network": "https://api.example.com"
    }
}
```

---

## Phase 3 Compatibility

### No Engine Modifications Required

**Key Insight**: The Phase 3 Scheduler already provides a perfect adapter boundary through the `task_executor` callback parameter.

**Current Interface** (Phase 3):
```python
scheduler.execute(task_executor: Callable[[DecomposedTask], Any])
```

**Future Interface** (Phase 4.3):
```python
scheduler.execute(task_executor: Callable[[DecomposedTask], Any])
```

**No Change**: The callback signature remains identical.

### Backward Compatibility

**Phase 3 Code** (continues to work):
```python
def simple_executor(task):
    print(f"Executing {task.task_id}")
    return f"Result for {task.task_id}"

scheduler.execute(simple_executor)
```

**Phase 4.3 Code** (new, but compatible):
```python
executor = ShellExecutor()
scheduler.execute(executor.execute)
```

**Both Work**: The interface is the same, only the implementation differs.

### Determinism Preserved

**Phase 3 Guarantees**:
1. Tasks execute in wave order
2. Tasks within waves execute in lexicographic order
3. Same inputs → same outputs

**Phase 4.3 Maintains**:
1. Executors are stateless
2. Executors don't affect task ordering
3. Executors are deterministic (same task → same result)
4. Executors don't modify the plan

**Constraint**: Executors MUST be deterministic for reproducibility.

---

## Examples

### Example 1: Simple Mock Executor

```python
class SimpleMockExecutor:
    """Minimal executor for testing."""
    
    def execute(self, task: DecomposedTask) -> str:
        """Return mock success message."""
        return f"Successfully executed {task.task_id}"

# Usage
executor = SimpleMockExecutor()
scheduler.execute(executor.execute)
```

### Example 2: Shell Command Executor

```python
import subprocess

class SimpleShellExecutor:
    """Execute shell commands from task context."""
    
    def execute(self, task: DecomposedTask) -> str:
        """Execute shell command."""
        command = task.context.get("command")
        if not command:
            raise ValueError(f"No command in {task.task_id}")
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise ExecutionError(
                f"Command failed: {result.stderr}"
            )
        
        return result.stdout

# Usage
executor = SimpleShellExecutor()
scheduler.execute(executor.execute)
```

### Example 3: Python Function Executor

```python
class SimplePythonExecutor:
    """Execute Python functions from task context."""
    
    def execute(self, task: DecomposedTask) -> Any:
        """Execute Python function."""
        func = task.context.get("function")
        if not func:
            raise ValueError(f"No function in {task.task_id}")
        
        args = task.context.get("args", [])
        kwargs = task.context.get("kwargs", {})
        
        return func(*args, **kwargs)

# Usage with actual function
def create_table(name, columns):
    return f"Created table {name} with {columns} columns"

task.context = {
    "function": create_table,
    "args": ["users", 5]
}

executor = SimplePythonExecutor()
scheduler.execute(executor.execute)
```

### Example 4: Executor with Feedback Integration

```python
class FeedbackAwareExecutor:
    """Executor that integrates with FeedbackCollector."""
    
    def __init__(self, feedback: FeedbackCollector, base_executor: TaskExecutor):
        self.feedback = feedback
        self.base_executor = base_executor
    
    def execute(self, task: DecomposedTask) -> Any:
        """Execute task and record feedback."""
        try:
            result = self.base_executor.execute(task)
            
            record = TaskExecutionRecord(
                task_id=task.task_id,
                prd_id=task.metadata.get("prd_id"),
                wave_number=task.metadata.get("wave_number"),
                status=TaskExecutionStatus.SUCCESS,
                result=result
            )
            self.feedback.add_record(record)
            return result
            
        except Exception as e:
            record = TaskExecutionRecord(
                task_id=task.task_id,
                prd_id=task.metadata.get("prd_id"),
                wave_number=task.metadata.get("wave_number"),
                status=TaskExecutionStatus.FAILED,
                error=str(e)
            )
            self.feedback.add_record(record)
            raise

# Usage
feedback = FeedbackCollector("orch-123")
base = ShellExecutor()
executor = FeedbackAwareExecutor(feedback, base)

scheduler.execute(executor.execute)
report = feedback.generate_report()
```

### Example 5: Executor Selection by Task Type

```python
class CompositeExecutor:
    """Selects appropriate executor based on task context."""
    
    def __init__(self):
        self.shell = ShellExecutor()
        self.python = PythonExecutor()
        self.mock = MockExecutor()
        self.noop = NoopExecutor()
    
    def execute(self, task: DecomposedTask) -> Any:
        """Select and execute with appropriate executor."""
        if "command" in task.context:
            return self.shell.execute(task)
        elif "function" in task.context or "code" in task.context:
            return self.python.execute(task)
        elif "mock_result" in task.context:
            return self.mock.execute(task)
        else:
            return self.noop.execute(task)

# Usage
executor = CompositeExecutor()
scheduler.execute(executor.execute)
```

---

## Constraints

### Analysis Constraints

✅ **Read-Only**: No code modifications made  
✅ **Planning Only**: Conceptual specifications only  
✅ **Black Box**: Phase 3 treated as complete  
✅ **No Implementation**: No actual executor code generated  
✅ **No Engine Changes**: Scheduler interface unchanged

### Design Constraints (for future Phase 4.3)

**Executors MUST**:
- Be stateless
- Accept DecomposedTask
- Return results
- Be deterministic
- Not modify the plan

**Executors MUST NOT**:
- Modify orchestration logic
- Change task ordering
- Access other tasks during execution
- Retry tasks (Scheduler handles this)
- Introduce async execution (out of scope)

### Out of Scope

❌ **Async Execution**: Tasks execute sequentially (Phase 3 design)  
❌ **Distributed Execution**: Single-machine orchestration  
❌ **Retries**: Fail-fast behavior (Phase 3 design)  
❌ **Fault Tolerance**: No automatic recovery  
❌ **Priority Scheduling**: Wave-based only (Phase 3 design)  
❌ **Real-Time Monitoring**: Batch execution only

---

## Conclusion

### Key Findings

1. **Adapter Boundary Exists**: The Phase 3 Scheduler already provides a clean adapter boundary through the `task_executor` callback parameter.

2. **No Engine Changes Needed**: The current interface `Callable[[DecomposedTask], Any]` is sufficient for all executor types.

3. **External Implementation**: All executor logic can be implemented externally without modifying Phase 3 code.

4. **Backward Compatible**: Phase 3 code continues to work unchanged.

5. **Determinism Preserved**: Executor pattern maintains Phase 3's deterministic guarantees.

### Phase 4.3 Scope

**Would Include**:
- Formal TaskExecutor interface definition
- Concrete executor implementations (Shell, Python, Mock, Noop)
- Executor selection logic
- Resource management patterns
- Error handling standards
- Integration with FeedbackCollector

**Would NOT Include**:
- Scheduler modifications
- Orchestration logic changes
- Async execution
- Distributed execution
- Retry logic
- Fault tolerance

### Architecture Summary

```
Phase 3 Orchestration Engine (LOCKED)
    ↓
Scheduler.execute(task_executor)
    ↓
    ← ADAPTER BOUNDARY (already exists)
    ↓
Phase 4.3 Executors (external, pluggable)
    ├─ ShellExecutor
    ├─ PythonExecutor
    ├─ MockExecutor
    └─ NoopExecutor
```

### Next Steps (If Approved)

1. Define formal TaskExecutor interface
2. Implement concrete executors
3. Create executor factory/registry
4. Document executor usage patterns
5. Add executor examples
6. Test with Phase 3 orchestration

**Awaiting approval to proceed with implementation.**

---

**End of Analysis**
