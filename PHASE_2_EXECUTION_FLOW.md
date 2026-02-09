# Lexicon Phase 2 Execution Flow

## Overview

This document defines the **execution loop lifecycle**, **self-healing mechanisms**, and **state transitions** for Phase 2. It explains how the Coordinator orchestrates agents to transform a PRD into validated, deployable artifacts.

## Execution Loop Philosophy

### Core Principles

1. **Deterministic Flow**: Same inputs produce same outputs (barring LLM non-determinism)
2. **Fail-Fast**: Detect errors immediately, don't propagate
3. **Self-Healing**: Attempt automated recovery before escalating
4. **Idempotent**: Can restart from any checkpoint
5. **Observable**: Every state transition is logged and trackable

### Loop Guarantees

- ✅ Every step is validated before proceeding
- ✅ Failures are captured and stored in memory
- ✅ At most 3 retry attempts for recoverable failures
- ✅ Phase 1 is never modified during execution
- ✅ Rollback capability for failed executions

## Execution States

### State Machine

```
[START]
   ↓
[PLANNING] → [PLAN_FAILED] → [ESCALATE]
   ↓
[BUILDING] → [BUILD_FAILED] → [ESCALATE]
   ↓
[VALIDATING] → [VALIDATION_FAILED] → [FIXING]
   ↓                                      ↓
[VALIDATED]                          [FIX_FAILED] → [ESCALATE]
   ↓                                      ↓
[MEMORY_UPDATE]                      [RETRY_VALIDATION]
   ↓                                      ↓
[COMPLETED]                          [VALIDATED] (if fixed)
```

### State Definitions

**START**:
- Initial state
- Receives user input (PRD, task description)
- Initializes execution context

**PLANNING**:
- Planner agent analyzes task
- Queries memory for context
- Produces execution plan
- **Transitions**: BUILDING (success) | PLAN_FAILED (failure)

**PLAN_FAILED**:
- Planning could not complete
- Reason: unclear requirements, missing context, impossible constraints
- **Transitions**: ESCALATE

**BUILDING**:
- Builder agent generates artifacts based on plan
- Queries memory for patterns
- Creates code, tests, docs
- **Transitions**: VALIDATING (success) | BUILD_FAILED (failure)

**BUILD_FAILED**:
- Code generation failed
- Reason: template errors, syntax issues, resource unavailability
- **Transitions**: ESCALATE

**VALIDATING**:
- Reviewer agent runs quality checks
- Executes linting, type checking, tests, security scans
- **Transitions**: VALIDATED (pass) | VALIDATION_FAILED (fail)

**VALIDATION_FAILED**:
- One or more validation checks failed
- Failures are categorized (linting, tests, security, etc.)
- **Transitions**: FIXING

**FIXING**:
- Fixer agent attempts automated remediation
- Queries memory for similar past fixes
- Applies minimal corrective changes
- **Transitions**: RETRY_VALIDATION (fix applied) | FIX_FAILED (can't fix)

**FIX_FAILED**:
- Fixer exhausted retry attempts or cannot auto-fix
- **Transitions**: ESCALATE

**RETRY_VALIDATION**:
- Re-run validation checks after fix
- **Transitions**: VALIDATED (success) | FIXING (still failing, retry)

**VALIDATED**:
- All quality checks passed
- Artifacts ready for use
- **Transitions**: MEMORY_UPDATE

**MEMORY_UPDATE**:
- Store successful execution in memory
- Index plan, code, test patterns
- **Transitions**: COMPLETED

**COMPLETED**:
- Terminal success state
- Artifacts are ready
- Execution summary available

**ESCALATE**:
- Terminal failure state
- Requires human intervention
- Detailed error report provided

## Detailed Execution Flow

### Phase 1: Initialization

```python
def execute_workflow(task_description: str, context: Optional[Dict] = None):
    """
    Main execution entry point.
    """
    # 1. Create execution context
    execution_id = generate_uuid()
    execution_context = ExecutionContext(
        id=execution_id,
        task=task_description,
        user_context=context,
        state=ExecutionState.START,
        created_at=datetime.now(UTC)
    )
    
    # 2. Initialize agents
    planner = PlannerAgent(llm=llm, memory=memory)
    builder = BuilderAgent(llm=llm, memory=memory)
    reviewer = ReviewerAgent(validators=validators)
    fixer = FixerAgent(llm=llm, memory=memory)
    
    # 3. Create coordinator
    coordinator = Coordinator(
        agents={
            "planner": planner,
            "builder": builder,
            "reviewer": reviewer,
            "fixer": fixer
        },
        memory=memory,
        config=config
    )
    
    # 4. Execute
    result = coordinator.run(execution_context)
    
    return result
```

### Phase 2: Planning

```python
def planning_phase(context: ExecutionContext) -> ExecutionPlan:
    """
    Planning phase: Analyze task and create execution plan.
    """
    try:
        # Update state
        context.state = ExecutionState.PLANNING
        log_state_transition(context)
        
        # Query memory for similar tasks
        similar_plans = memory.retrieve_context(
            query=context.task,
            filters={"source_type": "plan"},
            top_k=5
        )
        
        # Query Phase 1 documentation
        documentation = memory.retrieve_context(
            query=context.task,
            filters={"source_type": "documentation", "phase": "phase_1"},
            top_k=5
        )
        
        # Execute planning
        plan = planner.plan(
            task_description=context.task,
            context=context.user_context,
            similar_plans=similar_plans,
            documentation=documentation
        )
        
        # Validate plan
        if not is_valid_plan(plan):
            context.state = ExecutionState.PLAN_FAILED
            context.error = "Invalid plan structure"
            return escalate(context)
        
        # Store plan in context
        context.plan = plan
        
        return plan
        
    except Exception as e:
        context.state = ExecutionState.PLAN_FAILED
        context.error = str(e)
        return escalate(context)
```

### Phase 3: Building

```python
def building_phase(context: ExecutionContext) -> BuildResult:
    """
    Building phase: Generate code and artifacts.
    """
    try:
        # Update state
        context.state = ExecutionState.BUILDING
        log_state_transition(context)
        
        # Query memory for code patterns
        code_patterns = memory.retrieve_context(
            query=context.plan.description,
            filters={"source_type": "code"},
            top_k=5
        )
        
        # Query test patterns
        test_patterns = memory.retrieve_context(
            query="test patterns for " + context.plan.description,
            filters={"source_type": "test"},
            top_k=3
        )
        
        # Execute building
        build_result = builder.build(
            task=context.plan.tasks[0],  # Start with first task
            plan=context.plan,
            code_patterns=code_patterns,
            test_patterns=test_patterns
        )
        
        # Store result
        context.build_result = build_result
        
        return build_result
        
    except Exception as e:
        context.state = ExecutionState.BUILD_FAILED
        context.error = str(e)
        return escalate(context)
```

### Phase 4: Validation

```python
def validation_phase(context: ExecutionContext) -> ReviewReport:
    """
    Validation phase: Run quality checks.
    """
    try:
        # Update state
        context.state = ExecutionState.VALIDATING
        log_state_transition(context)
        
        # Run validation suite
        review_report = reviewer.review(
            build_result=context.build_result,
            standards=context.config.quality_standards
        )
        
        # Store review
        context.review_report = review_report
        
        # Check if passed
        if review_report.overall_status == "passed":
            context.state = ExecutionState.VALIDATED
            return review_report
        else:
            context.state = ExecutionState.VALIDATION_FAILED
            return review_report
        
    except Exception as e:
        context.state = ExecutionState.VALIDATION_FAILED
        context.error = str(e)
        return None
```

### Phase 5: Self-Healing (Fixing)

```python
def fixing_phase(context: ExecutionContext, max_attempts: int = 3) -> FixResult:
    """
    Fixing phase: Attempt automated remediation.
    """
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # Update state
            context.state = ExecutionState.FIXING
            context.fix_attempt = attempt + 1
            log_state_transition(context)
            
            # Query memory for similar fixes
            similar_fixes = memory.retrieve_context(
                query=str(context.review_report.issues),
                filters={"source_type": "fix"},
                top_k=5
            )
            
            # Query error patterns
            error_patterns = memory.retrieve_context(
                query=str(context.review_report.issues),
                filters={"source_type": "error", "resolved": True},
                top_k=3
            )
            
            # Attempt fix
            fix_result = fixer.fix(
                review_report=context.review_report,
                build_result=context.build_result,
                similar_fixes=similar_fixes,
                error_patterns=error_patterns
            )
            
            if fix_result.status == "success":
                # Re-run validation
                context.state = ExecutionState.RETRY_VALIDATION
                new_review = reviewer.review(
                    build_result=fix_result.updated_build,
                    standards=context.config.quality_standards
                )
                
                if new_review.overall_status == "passed":
                    # Fix successful!
                    context.state = ExecutionState.VALIDATED
                    context.build_result = fix_result.updated_build
                    context.fix_result = fix_result
                    
                    # Store successful fix in memory for future use
                    memory.store(
                        chunk=create_fix_chunk(context.review_report, fix_result),
                        metadata={
                            "source_type": "fix",
                            "phase": "phase_2",
                            "agent": "fixer",
                            "timestamp": datetime.now(UTC)
                        }
                    )
                    
                    return fix_result
                else:
                    # Still failing, retry
                    context.review_report = new_review
                    attempt += 1
            else:
                # Fix failed
                attempt += 1
        
        except Exception as e:
            attempt += 1
            context.error = str(e)
    
    # Exhausted attempts
    context.state = ExecutionState.FIX_FAILED
    return escalate(context)
```

### Phase 6: Memory Update & Completion

```python
def completion_phase(context: ExecutionContext):
    """
    Completion phase: Store successful execution in memory.
    """
    try:
        # Update state
        context.state = ExecutionState.MEMORY_UPDATE
        log_state_transition(context)
        
        # Store successful plan
        memory.store(
            chunk=create_plan_chunk(context.plan),
            metadata={
                "source_type": "plan",
                "phase": "phase_2",
                "agent": "planner",
                "timestamp": datetime.now(UTC),
                "task_type": infer_task_type(context.task)
            }
        )
        
        # Store generated code patterns
        for file in context.build_result.generated_files:
            memory.store(
                chunk=create_code_chunk(file),
                metadata={
                    "source_type": "code",
                    "phase": "phase_2",
                    "agent": "builder",
                    "file_path": file.path,
                    "language": file.language,
                    "timestamp": datetime.now(UTC)
                }
            )
        
        # Store test patterns
        for file in context.build_result.test_files:
            memory.store(
                chunk=create_test_chunk(file),
                metadata={
                    "source_type": "test",
                    "phase": "phase_2",
                    "agent": "builder",
                    "file_path": file.path,
                    "framework": "pytest",
                    "timestamp": datetime.now(UTC)
                }
            )
        
        # Mark as completed
        context.state = ExecutionState.COMPLETED
        context.completed_at = datetime.now(UTC)
        
        # Generate execution summary
        summary = ExecutionSummary(
            execution_id=context.id,
            task=context.task,
            duration=context.completed_at - context.created_at,
            state=context.state,
            plan=context.plan,
            artifacts=context.build_result.generated_files,
            validation_passed=True,
            fix_applied=context.fix_result is not None
        )
        
        return summary
        
    except Exception as e:
        logger.error(f"Memory update failed: {e}")
        # Don't fail execution if memory update fails
        context.state = ExecutionState.COMPLETED
        return create_summary_without_memory(context)
```

## Self-Healing Mechanisms

### Failure Detection

Failures are detected at multiple levels:

1. **Syntax Errors**: Caught during code generation
2. **Linting Failures**: Detected by ruff/black
3. **Type Errors**: Detected by mypy
4. **Test Failures**: Detected by pytest
5. **Security Issues**: Detected by bandit

### Recovery Strategies

**Level 1: Automatic Fix**:
- Common, well-understood issues
- Example: Missing type annotations, formatting issues
- Action: Fixer agent applies standard fix

**Level 2: Pattern-Based Fix**:
- Similar to past issues
- Example: Import errors, common test failures
- Action: Fixer queries memory for similar fixes, applies pattern

**Level 3: LLM-Assisted Fix**:
- Novel but fixable issues
- Example: Logic errors in generated code
- Action: Fixer uses LLM to generate fix based on error context

**Level 4: Escalation**:
- Cannot auto-fix
- Example: Fundamental architecture issues, ambiguous requirements
- Action: Return detailed error report to user

### Retry Logic

```python
class RetryConfig:
    max_attempts: int = 3
    backoff_factor: float = 1.5
    initial_delay: float = 1.0
    
def retry_with_backoff(func, config: RetryConfig):
    """
    Retry function with exponential backoff.
    """
    attempt = 0
    delay = config.initial_delay
    
    while attempt < config.max_attempts:
        try:
            return func()
        except RecoverableError as e:
            attempt += 1
            if attempt >= config.max_attempts:
                raise
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= config.backoff_factor
    
    raise MaxRetriesExceeded()
```

## Checkpointing and Resume

### Checkpoint Strategy

After each major phase, save execution state:

```python
def save_checkpoint(context: ExecutionContext):
    """
    Save execution state to disk for resumability.
    """
    checkpoint = {
        "execution_id": context.id,
        "state": context.state.value,
        "task": context.task,
        "plan": context.plan.dict() if context.plan else None,
        "build_result": context.build_result.dict() if context.build_result else None,
        "timestamp": datetime.now(UTC).isoformat()
    }
    
    checkpoint_file = f".lexicon/checkpoints/{context.id}.json"
    with open(checkpoint_file, 'w') as f:
        json.dump(checkpoint, f, indent=2)
```

### Resume Execution

```python
def resume_execution(execution_id: str):
    """
    Resume a previously interrupted execution.
    """
    checkpoint_file = f".lexicon/checkpoints/{execution_id}.json"
    
    if not os.path.exists(checkpoint_file):
        raise CheckpointNotFound(execution_id)
    
    with open(checkpoint_file, 'r') as f:
        checkpoint = json.load(f)
    
    # Reconstruct execution context
    context = ExecutionContext.from_checkpoint(checkpoint)
    
    # Resume from last state
    coordinator = Coordinator(...)
    
    if context.state == ExecutionState.PLANNING:
        return coordinator.run_from_planning(context)
    elif context.state == ExecutionState.BUILDING:
        return coordinator.run_from_building(context)
    # ... etc
```

## Observability

### Logging

Every state transition and agent invocation is logged:

```python
def log_state_transition(context: ExecutionContext):
    """
    Log state transition for debugging and monitoring.
    """
    logger.info(
        f"[{context.id}] State transition: {context.previous_state} → {context.state}",
        extra={
            "execution_id": context.id,
            "from_state": context.previous_state.value if context.previous_state else None,
            "to_state": context.state.value,
            "timestamp": datetime.now(UTC).isoformat()
        }
    )
```

### Execution Tracing

Complete execution trace available for debugging:

```python
@dataclass
class ExecutionTrace:
    """
    Complete trace of execution for debugging.
    """
    execution_id: str
    events: List[ExecutionEvent]
    
@dataclass
class ExecutionEvent:
    """
    Single event in execution trace.
    """
    timestamp: datetime
    agent: str
    action: str
    inputs: Dict
    outputs: Dict
    duration: float
    success: bool
```

## Error Handling

### Error Categories

1. **User Error**: Invalid input, unclear requirements
2. **System Error**: Infrastructure failures, resource exhaustion
3. **Logic Error**: Bugs in generated code
4. **Validation Error**: Failed quality checks

### Error Response Format

```python
@dataclass
class ExecutionError:
    """
    Structured error response.
    """
    error_type: ErrorType
    message: str
    context: Dict[str, Any]
    recoverable: bool
    suggested_action: str
    stack_trace: Optional[str]
    execution_id: str
```

## Performance Optimization

### Parallel Execution

Where possible, run independent validations in parallel:

```python
async def run_validations_parallel(build_result: BuildResult):
    """
    Run independent validation checks in parallel.
    """
    tasks = [
        run_linting(build_result),
        run_type_checking(build_result),
        run_security_scan(build_result),
        run_tests(build_result)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return combine_validation_results(results)
```

### Caching

Cache expensive operations:
- LLM responses for identical queries
- Validation results for unchanged files
- Memory retrievals for common queries

## Conclusion

The Phase 2 execution flow provides:

- **Deterministic**: Predictable state transitions
- **Resilient**: Self-healing with automatic retry
- **Observable**: Complete logging and tracing
- **Resumable**: Checkpointing for long operations
- **Safe**: Phase 1 remains untouched

This design enables autonomous execution while maintaining control, debuggability, and safety.

---

**Document Version**: 1.0  
**Status**: Design Review  
**Dependencies**: PHASE_2_ARCHITECTURE.md, PHASE_2_AGENT_MODEL.md, PHASE_2_RAG_SCOPE.md
