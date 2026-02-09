# Phase 3.3: Feedback & Learning Integration

## Overview

Phase 3.3 introduces feedback-driven learning by tracking execution outcomes in RAG memory, collecting metrics, and generating informational improvement suggestions. This enables data-driven PRD refinement while maintaining strict determinism and human decision-making authority.

**Status**: Design Document  
**Dependencies**: Phase 2.2 (RAG Memory), Phase 2.3 (Execution Loop), Phase 3.2 (Multi-PRD Orchestration)  
**Version**: 1.0

---

## Objectives

1. Track task execution outcomes (success, failure, retry patterns)
2. Store execution summaries in RAG memory for pattern analysis
3. Collect metrics on execution performance and agent effectiveness
4. Generate informational suggestions for PRD improvement
5. Maintain read-only RAG access for agents, write-only for coordinator

---

## Architecture

### Components

```
lexicon/
└── feedback/
    ├── __init__.py
    ├── outcome_tracker.py          # Track execution outcomes
    ├── metrics_collector.py        # Collect execution metrics
    ├── suggestion_generator.py     # Generate improvement suggestions
    └── rag_integration.py          # Write outcomes to RAG memory
```

---

## Outcome Tracking

### Outcome Tracker

```python
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from lexicon.orchestrator import ExecutionResult

@dataclass
class TaskOutcome:
    """Record of a single task execution."""
    task_id: str
    task_description: str
    success: bool
    execution_time_seconds: float
    retry_count: int
    agent_used: str  # e.g., "planner", "builder", "fixer"
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    fix_applied: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class OutcomeTracker:
    """Track execution outcomes for analysis."""
    
    def __init__(self):
        self.outcomes: List[TaskOutcome] = []
    
    def record_outcome(self, result: ExecutionResult, task: PRDTask):
        """Record outcome from execution result."""
        outcome = TaskOutcome(
            task_id=task.id,
            task_description=task.description,
            success=result.success,
            execution_time_seconds=result.execution_time,
            retry_count=self._count_retries(result.trace),
            agent_used=self._identify_primary_agent(result.trace),
            error_type=self._extract_error_type(result),
            error_message=self._extract_error_message(result),
            fix_applied=self._was_fix_applied(result.trace)
        )
        self.outcomes.append(outcome)
        return outcome
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate."""
        if not self.outcomes:
            return 0.0
        successful = sum(1 for o in self.outcomes if o.success)
        return (successful / len(self.outcomes)) * 100
    
    def get_average_execution_time(self) -> float:
        """Calculate average execution time."""
        if not self.outcomes:
            return 0.0
        return sum(o.execution_time_seconds for o in self.outcomes) / len(self.outcomes)
    
    def get_retry_statistics(self) -> Dict[str, float]:
        """Calculate retry statistics."""
        if not self.outcomes:
            return {"avg_retries": 0.0, "max_retries": 0, "retry_rate": 0.0}
        
        total_retries = sum(o.retry_count for o in self.outcomes)
        max_retries = max(o.retry_count for o in self.outcomes)
        tasks_with_retries = sum(1 for o in self.outcomes if o.retry_count > 0)
        
        return {
            "avg_retries": total_retries / len(self.outcomes),
            "max_retries": max_retries,
            "retry_rate": (tasks_with_retries / len(self.outcomes)) * 100
        }
```

---

## Metrics Collection

### Metrics Collector

```python
from collections import defaultdict
from typing import Dict, List

class MetricsCollector:
    """Collect and aggregate execution metrics."""
    
    def __init__(self):
        self.outcomes: List[TaskOutcome] = []
    
    def add_outcomes(self, outcomes: List[TaskOutcome]):
        """Add outcomes for analysis."""
        self.outcomes.extend(outcomes)
    
    def get_agent_performance(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance by agent."""
        agent_stats = defaultdict(lambda: {"successes": 0, "failures": 0, "total_time": 0.0})
        
        for outcome in self.outcomes:
            agent = outcome.agent_used
            if outcome.success:
                agent_stats[agent]["successes"] += 1
            else:
                agent_stats[agent]["failures"] += 1
            agent_stats[agent]["total_time"] += outcome.execution_time_seconds
        
        # Calculate rates
        result = {}
        for agent, stats in agent_stats.items():
            total = stats["successes"] + stats["failures"]
            result[agent] = {
                "success_rate": (stats["successes"] / total * 100) if total > 0 else 0,
                "avg_time": stats["total_time"] / total if total > 0 else 0,
                "total_executions": total
            }
        
        return result
    
    def get_failure_patterns(self) -> Dict[str, int]:
        """Identify common failure patterns."""
        error_counts = defaultdict(int)
        
        for outcome in self.outcomes:
            if not outcome.success and outcome.error_type:
                error_counts[outcome.error_type] += 1
        
        # Sort by frequency
        return dict(sorted(error_counts.items(), key=lambda x: x[1], reverse=True))
    
    def get_execution_time_distribution(self) -> Dict[str, float]:
        """Analyze execution time distribution."""
        if not self.outcomes:
            return {}
        
        times = [o.execution_time_seconds for o in self.outcomes]
        times.sort()
        
        return {
            "min": min(times),
            "max": max(times),
            "median": times[len(times) // 2],
            "p95": times[int(len(times) * 0.95)],
            "avg": sum(times) / len(times)
        }
    
    def get_fix_effectiveness(self) -> Dict[str, float]:
        """Analyze effectiveness of automated fixes."""
        fixed = [o for o in self.outcomes if o.fix_applied]
        if not fixed:
            return {"fix_success_rate": 0.0, "total_fixes": 0}
        
        successful_fixes = sum(1 for o in fixed if o.success)
        
        return {
            "fix_success_rate": (successful_fixes / len(fixed)) * 100,
            "total_fixes": len(fixed),
            "successful_fixes": successful_fixes
        }
```

---

## RAG Integration

### RAG Writer

```python
from lexicon.memory import ChromaMemoryStore, MemoryChunk, MemoryMetadata
from lexicon.memory import chunk_error
from datetime import datetime, timezone

class FeedbackRAGIntegration:
    """Store execution outcomes in RAG memory (coordinator-only)."""
    
    def __init__(self, memory_store: ChromaMemoryStore):
        self.memory_store = memory_store
    
    def store_outcome(self, outcome: TaskOutcome):
        """Store task outcome in RAG memory."""
        # Create outcome summary
        content = self._create_outcome_summary(outcome)
        
        # Chunk for storage
        chunks = self._chunk_outcome(content, outcome)
        
        # Store in RAG (coordinator-only operation)
        for chunk in chunks:
            self.memory_store.store(chunk)
    
    def _create_outcome_summary(self, outcome: TaskOutcome) -> str:
        """Create human-readable outcome summary."""
        status = "SUCCESS" if outcome.success else "FAILURE"
        
        summary_parts = [
            f"Task: {outcome.task_description}",
            f"Status: {status}",
            f"Execution Time: {outcome.execution_time_seconds:.2f}s",
            f"Retry Count: {outcome.retry_count}"
        ]
        
        if outcome.agent_used:
            summary_parts.append(f"Primary Agent: {outcome.agent_used}")
        
        if not outcome.success:
            if outcome.error_type:
                summary_parts.append(f"Error Type: {outcome.error_type}")
            if outcome.error_message:
                summary_parts.append(f"Error: {outcome.error_message}")
        
        if outcome.fix_applied:
            fix_status = "successful" if outcome.success else "unsuccessful"
            summary_parts.append(f"Automated Fix: {fix_status}")
        
        return "\n".join(summary_parts)
    
    def _chunk_outcome(self, content: str, outcome: TaskOutcome) -> List[MemoryChunk]:
        """Create memory chunks from outcome."""
        # Use error chunking for failures
        if not outcome.success and outcome.error_message:
            return chunk_error(
                error_message=outcome.error_message,
                context=f"Task: {outcome.task_description}",
                fix_applied=outcome.fix_applied,
                source_file=f"task_{outcome.task_id}",
                phase="phase_3"
            )
        
        # Store as single chunk for successes
        metadata = MemoryMetadata(
            source=f"task_{outcome.task_id}",
            source_type="execution_outcome",
            phase="phase_3",
            agent="coordinator",
            timestamp=outcome.timestamp.isoformat(),
            custom_metadata={
                "task_id": outcome.task_id,
                "success": outcome.success,
                "execution_time": outcome.execution_time_seconds,
                "retry_count": outcome.retry_count
            }
        )
        
        return [MemoryChunk(
            content=content,
            metadata=metadata,
            chunk_id=f"outcome_{outcome.task_id}_{outcome.timestamp.timestamp()}"
        )]
```

---

## Suggestion Generation

### Suggestion Generator

```python
from typing import List
from dataclasses import dataclass
from lexicon.memory import MemoryRetriever

@dataclass
class PRDSuggestion:
    """Informational suggestion for PRD improvement."""
    type: str  # e.g., "dependency_optimization", "resource_allocation"
    description: str
    rationale: str  # Based on historical data
    affected_requirements: List[str]
    confidence: float  # 0.0 to 1.0
    
class SuggestionGenerator:
    """Generate informational suggestions from historical data."""
    
    def __init__(self, retriever: MemoryRetriever, metrics: MetricsCollector):
        self.retriever = retriever
        self.metrics = metrics
    
    def generate_suggestions(self, prd: PRD) -> List[PRDSuggestion]:
        """Generate suggestions for PRD based on historical data."""
        suggestions = []
        
        # Analyze similar past tasks
        suggestions.extend(self._suggest_dependency_changes(prd))
        suggestions.extend(self._suggest_resource_allocation(prd))
        suggestions.extend(self._suggest_task_splitting(prd))
        suggestions.extend(self._suggest_priority_adjustments(prd))
        
        # Sort by confidence
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        
        return suggestions
    
    def _suggest_dependency_changes(self, prd: PRD) -> List[PRDSuggestion]:
        """Suggest dependency optimizations."""
        suggestions = []
        
        # Query RAG for similar tasks
        for req in prd.requirements:
            similar_outcomes = self.retriever.retrieve_similar_errors(
                error_message=req.description,
                top_k=5
            )
            
            # Analyze patterns
            if self._has_common_dependency_issue(similar_outcomes):
                suggestions.append(PRDSuggestion(
                    type="dependency_optimization",
                    description=f"Consider reordering dependencies for {req.id}",
                    rationale="Similar tasks succeeded when dependencies were executed in different order",
                    affected_requirements=[req.id],
                    confidence=0.7
                ))
        
        return suggestions
    
    def _suggest_resource_allocation(self, prd: PRD) -> List[PRDSuggestion]:
        """Suggest resource allocation improvements."""
        suggestions = []
        
        # Analyze agent performance
        agent_perf = self.metrics.get_agent_performance()
        
        # Find underperforming agents
        for agent, stats in agent_perf.items():
            if stats["success_rate"] < 70:
                suggestions.append(PRDSuggestion(
                    type="resource_allocation",
                    description=f"Agent '{agent}' has low success rate ({stats['success_rate']:.1f}%)",
                    rationale=f"Based on {stats['total_executions']} executions",
                    affected_requirements=[],  # Applies to all
                    confidence=0.8
                ))
        
        return suggestions
    
    def _suggest_task_splitting(self, prd: PRD) -> List[PRDSuggestion]:
        """Suggest splitting complex tasks."""
        suggestions = []
        
        # Find tasks with high execution time
        time_dist = self.metrics.get_execution_time_distribution()
        if not time_dist:
            return suggestions
        
        threshold = time_dist.get("p95", 0)
        
        for req in prd.requirements:
            # Query historical data for this task type
            similar = self.retriever.retrieve_code_examples(
                query=req.description,
                language="task_description",
                top_k=5
            )
            
            # Check if similar tasks had long execution times
            if self._has_long_execution_pattern(similar, threshold):
                suggestions.append(PRDSuggestion(
                    type="task_splitting",
                    description=f"Consider splitting {req.id} into subtasks",
                    rationale=f"Similar tasks exceeded {threshold:.1f}s execution time",
                    affected_requirements=[req.id],
                    confidence=0.6
                ))
        
        return suggestions
```

---

## Usage Example

```python
from lexicon.feedback import OutcomeTracker, MetricsCollector, SuggestionGenerator, FeedbackRAGIntegration
from lexicon.memory import ChromaMemoryStore, MemoryRetriever

# Initialize components
memory_store = ChromaMemoryStore()
retriever = MemoryRetriever(memory_store)
tracker = OutcomeTracker()
metrics = MetricsCollector()
rag_integration = FeedbackRAGIntegration(memory_store)
suggestion_generator = SuggestionGenerator(retriever, metrics)

# Execute PRD and track outcomes
for task in prd_tasks:
    result = coordinator.execute(task.description, task.context)
    outcome = tracker.record_outcome(result, task)
    rag_integration.store_outcome(outcome)  # Store in RAG memory

# Collect metrics
metrics.add_outcomes(tracker.outcomes)

print("=== Execution Metrics ===")
print(f"Success Rate: {tracker.get_success_rate():.1f}%")
print(f"Avg Execution Time: {tracker.get_average_execution_time():.2f}s")
print(f"Retry Stats: {tracker.get_retry_statistics()}")

print("\n=== Agent Performance ===")
for agent, stats in metrics.get_agent_performance().items():
    print(f"{agent}: {stats['success_rate']:.1f}% success, {stats['avg_time']:.2f}s avg")

print("\n=== Failure Patterns ===")
for error_type, count in metrics.get_failure_patterns().items():
    print(f"{error_type}: {count} occurrences")

# Generate suggestions for next PRD
suggestions = suggestion_generator.generate_suggestions(next_prd)
print("\n=== Suggestions for Improvement ===")
for suggestion in suggestions[:5]:  # Top 5
    print(f"[{suggestion.type}] {suggestion.description}")
    print(f"  Rationale: {suggestion.rationale}")
    print(f"  Confidence: {suggestion.confidence:.1%}\n")
```

---

## Testing Strategy

### Unit Tests
- Outcome tracking accuracy
- Metrics calculation correctness
- RAG storage format
- Suggestion generation logic

### Integration Tests
- End-to-end feedback loop
- RAG retrieval for pattern analysis
- Multi-execution metric aggregation

---

## Backward Compatibility

- Phase 2.2 RAG access control unchanged
- Phase 2.3 execution loop unmodified
- Feedback system is optional (opt-in)

---

## Performance Targets

- **Outcome Tracking**: < 10ms overhead per task
- **RAG Storage**: < 100ms per outcome
- **Metrics Calculation**: < 1 second for 100 outcomes
- **Suggestion Generation**: < 5 seconds for complex PRD

---

## Out of Scope

- **Autonomous PRD Modification**: Suggestions are advisory only
- **Real-Time Suggestions**: Batch analysis after execution
- **LLM-Based Suggestions**: Pattern-based analysis only
- **Auto-Implementation**: Humans must approve all changes

---

## Success Criteria

- ✅ Track 100+ task executions
- ✅ Store outcomes in RAG memory
- ✅ Generate 5+ meaningful suggestions
- ✅ Maintain RAG read-only for agents
- ✅ All tests passing

---

## Summary

Phase 3.3 enables data-driven PRD improvement through execution tracking, metrics collection, and informational suggestions, while maintaining human decision-making authority and RAG access control.
