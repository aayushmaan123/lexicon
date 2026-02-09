# Lexicon Phase 2 Agent Model

## Overview

This document defines the **multi-agent architecture** for Phase 2, including agent responsibilities, interfaces, communication patterns, and boundaries.

## Agent Philosophy

### Core Principles

1. **Single Responsibility**: Each agent has one clear purpose
2. **Stateless Execution**: Agents don't maintain internal state between calls
3. **Explicit Communication**: All inter-agent communication flows through the Coordinator
4. **Memory as Context**: Agents query memory for context, never for control flow decisions
5. **Fail Gracefully**: Agents return structured errors, not exceptions

### Agent Lifecycle

```
Initialize → Receive Task → Query Memory → Execute → Return Result → Cleanup
```

All agents follow this lifecycle. State persists only in:
- **Coordinator's execution context**
- **Memory subsystem (RAG)**
- **Explicit return values**

## Agent Definitions

### 1. Planner Agent

**Purpose**: Decompose complex tasks into structured execution plans

**Inputs**:
- Task description (PRD, user request, or high-level goal)
- Project context from memory (optional)
- Existing architecture constraints

**Outputs**:
- Structured execution plan (JSON/Pydantic model)
- Task dependencies and ordering
- Resource requirements
- Risk assessment

**Responsibilities**:
- ✅ Parse and understand task requirements
- ✅ Break down into atomic subtasks
- ✅ Identify dependencies between tasks
- ✅ Query memory for relevant prior plans
- ✅ Estimate complexity and duration
- ✅ Flag potential risks or blockers

**NOT Responsible For**:
- ❌ Writing code or generating artifacts
- ❌ Making architectural decisions (uses existing patterns)
- ❌ Executing tasks
- ❌ Validating outputs

**Interface**:

```python
class PlannerAgent:
    def plan(
        self,
        task_description: str,
        context: Optional[ProjectContext] = None,
        memory_query: Optional[str] = None
    ) -> ExecutionPlan:
        """
        Create an execution plan from task description.
        
        Returns:
            ExecutionPlan with subtasks, dependencies, and metadata
        """
        pass
```

**Example Output**:

```json
{
  "plan_id": "uuid-here",
  "task": "Add user authentication to API",
  "subtasks": [
    {
      "id": "task-1",
      "description": "Create user model and database schema",
      "dependencies": [],
      "estimated_duration": "30m",
      "risk_level": "low"
    },
    {
      "id": "task-2",
      "description": "Implement JWT token generation",
      "dependencies": ["task-1"],
      "estimated_duration": "45m",
      "risk_level": "medium"
    },
    {
      "id": "task-3",
      "description": "Add authentication middleware",
      "dependencies": ["task-2"],
      "estimated_duration": "20m",
      "risk_level": "low"
    }
  ],
  "total_estimated_duration": "95m",
  "overall_risk": "medium"
}
```

### 2. Builder Agent

**Purpose**: Generate code, configuration, and artifacts based on approved plans

**Inputs**:
- Execution plan (from Planner)
- Task specification
- Template/pattern references from memory
- Existing codebase context

**Outputs**:
- Generated code files
- Configuration files
- Test scaffolding
- Documentation updates
- File change manifest

**Responsibilities**:
- ✅ Generate syntactically correct code
- ✅ Follow existing code patterns and style
- ✅ Create corresponding test files
- ✅ Update documentation
- ✅ Query memory for similar implementations
- ✅ Respect project structure and conventions

**NOT Responsible For**:
- ❌ Testing the generated code
- ❌ Reviewing code quality
- ❌ Deploying artifacts
- ❌ Making architectural choices (follows plan)

**Interface**:

```python
class BuilderAgent:
    def build(
        self,
        task: Task,
        plan: ExecutionPlan,
        context: CodebaseContext
    ) -> BuildResult:
        """
        Generate artifacts based on task and plan.
        
        Returns:
            BuildResult with generated files and metadata
        """
        pass
```

**Example Output**:

```json
{
  "build_id": "uuid-here",
  "task_id": "task-1",
  "generated_files": [
    {
      "path": "lexicon/domain/entities/user.py",
      "type": "python_module",
      "lines": 87,
      "purpose": "User domain entity with authentication fields"
    },
    {
      "path": "tests/unit/test_user_entity.py",
      "type": "test",
      "lines": 45,
      "purpose": "Unit tests for User entity"
    }
  ],
  "modified_files": [
    {
      "path": "migrations/002_add_users_table.sql",
      "type": "migration",
      "change_type": "create"
    }
  ],
  "status": "success",
  "warnings": []
}
```

### 3. Reviewer Agent

**Purpose**: Validate generated code against quality standards

**Inputs**:
- Build artifacts (from Builder)
- Quality standards and rules
- Project conventions
- Security policies

**Outputs**:
- Review report (pass/fail per check)
- List of issues found
- Severity classification
- Suggested fixes
- Approval/rejection decision

**Responsibilities**:
- ✅ Run linting and formatting checks
- ✅ Execute type checking
- ✅ Verify test coverage
- ✅ Check for security vulnerabilities
- ✅ Validate against architecture patterns
- ✅ Ensure backward compatibility
- ✅ Check documentation completeness

**NOT Responsible For**:
- ❌ Fixing issues (delegates to Fixer)
- ❌ Making subjective design decisions
- ❌ Generating new code

**Interface**:

```python
class ReviewerAgent:
    def review(
        self,
        build_result: BuildResult,
        standards: QualityStandards
    ) -> ReviewReport:
        """
        Review build artifacts against quality standards.
        
        Returns:
            ReviewReport with pass/fail status and issues
        """
        pass
```

**Example Output**:

```json
{
  "review_id": "uuid-here",
  "build_id": "uuid-here",
  "overall_status": "failed",
  "checks": [
    {
      "name": "ruff_lint",
      "status": "passed",
      "issues": []
    },
    {
      "name": "type_check",
      "status": "failed",
      "issues": [
        {
          "file": "lexicon/domain/entities/user.py",
          "line": 42,
          "severity": "error",
          "message": "Incompatible return type",
          "code": "return-type"
        }
      ]
    },
    {
      "name": "security_scan",
      "status": "passed",
      "issues": []
    },
    {
      "name": "test_coverage",
      "status": "warning",
      "issues": [
        {
          "message": "Coverage below 80% threshold: 75%",
          "severity": "warning"
        }
      ]
    }
  ],
  "can_proceed": false,
  "blocker_count": 1,
  "warning_count": 1
}
```

### 4. Fixer Agent

**Purpose**: Automatically resolve validation failures and runtime errors

**Inputs**:
- Review report (from Reviewer)
- Failed validation checks
- Error messages and stack traces
- Memory of previous fixes for similar issues

**Outputs**:
- Fixed code files
- Explanation of changes made
- Success/failure status
- Escalation flag if fix is not possible

**Responsibilities**:
- ✅ Analyze validation failures
- ✅ Query memory for similar past failures
- ✅ Apply minimal corrective changes
- ✅ Re-run validations to confirm fix
- ✅ Document fix patterns for memory
- ✅ Escalate complex issues that can't be auto-fixed

**NOT Responsible For**:
- ❌ Making major architectural changes
- ❌ Bypassing validation checks
- ❌ Rewriting large sections of code
- ❌ Making subjective improvements

**Interface**:

```python
class FixerAgent:
    def fix(
        self,
        review_report: ReviewReport,
        build_result: BuildResult,
        max_attempts: int = 3
    ) -> FixResult:
        """
        Attempt to fix validation failures automatically.
        
        Returns:
            FixResult with fixed files or escalation notice
        """
        pass
```

**Example Output**:

```json
{
  "fix_id": "uuid-here",
  "review_id": "uuid-here",
  "status": "success",
  "fixes_applied": [
    {
      "issue_id": "type-check-error-1",
      "file": "lexicon/domain/entities/user.py",
      "line": 42,
      "change": "Added explicit return type annotation",
      "before": "def get_username(self):",
      "after": "def get_username(self) -> str:"
    }
  ],
  "validation_rerun": {
    "status": "passed",
    "all_checks_passed": true
  },
  "attempts": 1,
  "escalated": false
}
```

## Agent Communication

### Communication Flow

```
User/PRD
    ↓
Coordinator
    ↓
Planner ──[Plan]──→ Coordinator
                        ↓
                    Builder ──[Artifacts]──→ Coordinator
                                                ↓
                                            Reviewer ──[Report]──→ Coordinator
                                                                        ↓
                                                                    [Pass?]
                                                                    ↙     ↘
                                                            Yes: Deploy   No: Fixer
                                                                              ↓
                                                                        [Fixed] → Reviewer
```

### Key Rules

1. **No Direct Agent-to-Agent Communication**: All messages flow through Coordinator
2. **Structured Data Only**: Agents communicate via typed Pydantic models
3. **Idempotent Operations**: Re-running an agent with same inputs produces same outputs
4. **Clear Success/Failure**: Every agent returns explicit status

## Memory Integration

### How Agents Use Memory

Each agent can query memory for context:

**Planner**:
- Prior execution plans for similar tasks
- Common task decomposition patterns
- Historical duration estimates

**Builder**:
- Code templates and patterns
- Similar implementations
- Common failure patterns to avoid

**Reviewer**:
- Past review failures
- Common anti-patterns
- Security vulnerability patterns

**Fixer**:
- Successful fix patterns
- Error message → fix mappings
- Multi-step fix sequences

### Memory Query Interface

```python
class MemoryQuery:
    def retrieve_context(
        self,
        query: str,
        source_type: str,  # "plan", "code", "error", "fix"
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[MemoryChunk]:
        """Retrieve relevant context from memory."""
        pass
```

### Memory Constraints

1. **Read-Only for Agents**: Agents query memory but don't write directly
2. **Coordinator Writes**: Only Coordinator persists new memory after successful execution
3. **Metadata Required**: Every memory chunk has source, timestamp, agent, phase
4. **Size Limits**: Retrievals capped to prevent token budget overflow

## Agent State Management

### Stateless Design

Agents do NOT maintain:
- ❌ Internal caches
- ❌ Execution history
- ❌ Configuration beyond initialization
- ❌ References to previous calls

Agents DO receive:
- ✅ Execution context (passed by Coordinator)
- ✅ Memory query interface (injected dependency)
- ✅ Configuration (at initialization)
- ✅ Task inputs (per invocation)

### Example Agent Initialization

```python
# Agent instances are created once per execution loop
coordinator = Coordinator()

planner = PlannerAgent(
    llm_provider=openai_provider,
    memory=memory_system,
    config=settings
)

builder = BuilderAgent(
    llm_provider=openai_provider,
    memory=memory_system,
    code_analyzer=analyzer,
    config=settings
)

# Coordinator manages execution
result = coordinator.execute(
    task="Add user auth",
    agents={
        "planner": planner,
        "builder": builder,
        "reviewer": reviewer,
        "fixer": fixer
    }
)
```

## Error Handling

### Agent Error Types

1. **ValidationError**: Invalid inputs
2. **ExecutionError**: Failed to complete task
3. **TimeoutError**: Exceeded time limit
4. **ResourceError**: Insufficient resources
5. **EscalationError**: Requires human intervention

### Error Response Format

```python
@dataclass
class AgentError:
    error_type: str
    message: str
    context: Dict[str, Any]
    recoverable: bool
    suggested_action: str
```

### Recovery Strategy

```
Error → Log → Store in Memory → Return to Coordinator
                                         ↓
                                    [Recoverable?]
                                    ↙           ↘
                            Yes: Retry/Fix    No: Escalate
```

## Testing Strategy

### Unit Tests

Each agent has:
- Input validation tests
- Output format tests
- Error handling tests
- Mock memory integration tests

### Integration Tests

- Agent → Memory interaction tests
- Coordinator → Agent communication tests
- Full execution loop tests

### Acceptance Tests

- End-to-end PRD → artifact workflow
- Self-healing loop with induced failures
- Memory persistence and retrieval

## Performance Considerations

### Response Time Targets

- **Planner**: <30 seconds for complex tasks
- **Builder**: <2 minutes for typical services
- **Reviewer**: <30 seconds for validation suite
- **Fixer**: <1 minute for common fixes

### Optimization Strategies

1. **Parallel Validation**: Run lint, type check, tests concurrently
2. **Incremental Builds**: Only rebuild changed components
3. **Memory Caching**: Cache frequent memory queries
4. **Timeout Enforcement**: Kill long-running operations

## Extensibility

### Adding New Agents (Phase 3)

Future agents can be added by:
1. Implementing `Agent` base class
2. Registering with Coordinator
3. Defining input/output schemas
4. Adding to execution loop

Example future agents:
- **DeployerAgent**: Handle deployment operations
- **MonitorAgent**: Track runtime metrics
- **OptimizerAgent**: Refactor and optimize code

### Agent Composition

Agents can be composed into meta-agents:
```python
class MetaAgent:
    def __init__(self, sub_agents: List[Agent]):
        self.sub_agents = sub_agents
    
    def execute(self, task):
        # Coordinate sub-agents
        pass
```

## Conclusion

The Phase 2 agent model provides:
- **Clear Responsibilities**: Each agent has one job
- **Loose Coupling**: Agents don't depend on each other
- **Stateless Design**: No hidden state, fully testable
- **Memory Integration**: Context-aware without being decision-driven
- **Extensibility**: Easy to add new agents

This architecture enables autonomous workflows while maintaining control, predictability, and debuggability.

---

**Document Version**: 1.0  
**Status**: Design Review  
**Dependencies**: PHASE_2_ARCHITECTURE.md
