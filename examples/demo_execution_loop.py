"""
Demonstration of Phase 2.3 execution loop functionality.

This script demonstrates the deterministic execution loop with state machine
and self-healing capabilities.
"""

from lexicon.agents import PlannerAgent, BuilderAgent, ReviewerAgent, FixerAgent
from lexicon.orchestrator import Coordinator, ExecutionState


def demo_successful_execution():
    """Demonstrate a successful execution without fixing."""
    print("=== Demo 1: Successful Execution ===\n")
    
    # Create coordinator and register agents
    coordinator = Coordinator()
    coordinator.register_agent("planner", PlannerAgent())
    coordinator.register_agent("builder", BuilderAgent())
    coordinator.register_agent("reviewer", ReviewerAgent())
    coordinator.register_agent("fixer", FixerAgent())
    
    # Execute task
    result = coordinator.execute("Create a simple Python function to add two numbers")
    
    # Display results
    print(f"Success: {result.success}")
    print(f"Final State: {result.final_state.value}")
    print(f"Execution ID: {result.execution_id}")
    
    # Show state transitions
    print("\nState Transitions:")
    for transition in result.trace.state_transitions:
        print(f"  {transition.from_state.value} → {transition.to_state.value}")
        if transition.reason:
            print(f"    Reason: {transition.reason}")
    
    # Show artifacts
    if result.artifacts:
        print(f"\nFix Applied: {result.artifacts.get('fix_applied', False)}")
        print(f"Fix Attempts: {result.artifacts.get('fix_attempts', 0)}")
    
    print("\n" + "="*50 + "\n")
    return result


def demo_execution_with_custom_config():
    """Demonstrate execution with custom retry configuration."""
    print("=== Demo 2: Custom Retry Configuration ===\n")
    
    # Create coordinator with custom config
    config = {
        "max_retry_attempts": 5,
        "retry_backoff_factor": 2.0,
        "initial_retry_delay": 0.5
    }
    
    coordinator = Coordinator(config=config)
    coordinator.register_agent("planner", PlannerAgent())
    coordinator.register_agent("builder", BuilderAgent())
    coordinator.register_agent("reviewer", ReviewerAgent())
    coordinator.register_agent("fixer", FixerAgent())
    
    print(f"Retry Config:")
    print(f"  Max Attempts: {coordinator.retry_config.max_attempts}")
    print(f"  Backoff Factor: {coordinator.retry_config.backoff_factor}")
    print(f"  Initial Delay: {coordinator.retry_config.initial_delay}s")
    
    # Show exponential backoff delays
    print(f"\nDelay Schedule:")
    for attempt in range(coordinator.retry_config.max_attempts):
        delay = coordinator.retry_config.get_delay(attempt)
        print(f"  Attempt {attempt + 1}: {delay:.2f}s")
    
    print("\n" + "="*50 + "\n")


def demo_trace_inspection():
    """Demonstrate detailed trace inspection."""
    print("=== Demo 3: Execution Trace Inspection ===\n")
    
    coordinator = Coordinator()
    coordinator.register_agent("planner", PlannerAgent())
    coordinator.register_agent("builder", BuilderAgent())
    coordinator.register_agent("reviewer", ReviewerAgent())
    coordinator.register_agent("fixer", FixerAgent())
    
    result = coordinator.execute("Implement a function to calculate factorial")
    
    # Convert trace to dictionary for inspection
    trace_dict = result.trace.to_dict()
    
    print(f"Execution ID: {trace_dict['execution_id']}")
    print(f"Task: {trace_dict['task_description']}")
    print(f"Started: {trace_dict['started_at']}")
    print(f"Completed: {trace_dict['completed_at']}")
    print(f"Final State: {trace_dict['final_state']}")
    
    print(f"\nTotal State Transitions: {len(trace_dict['state_transitions'])}")
    print(f"Agents Invoked: {', '.join(trace_dict['agent_outputs'].keys())}")
    
    # Show agent execution order
    print("\nAgent Execution Order:")
    for agent_type in trace_dict['agent_outputs']:
        count = len(trace_dict['agent_outputs'][agent_type])
        print(f"  {agent_type}: {count} invocation(s)")
    
    print("\n" + "="*50 + "\n")


def demo_execution_context():
    """Demonstrate execution context with metadata."""
    print("=== Demo 4: Execution Context with Metadata ===\n")
    
    coordinator = Coordinator()
    coordinator.register_agent("planner", PlannerAgent())
    coordinator.register_agent("builder", BuilderAgent())
    coordinator.register_agent("reviewer", ReviewerAgent())
    coordinator.register_agent("fixer", FixerAgent())
    
    # Execute with metadata
    metadata = {
        "priority": "high",
        "project": "lexicon-phase-2",
        "user": "developer@example.com"
    }
    
    result = coordinator.execute(
        "Create a utility function for string manipulation",
        context_metadata=metadata
    )
    
    print(f"Task executed with metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\nExecution completed: {result.success}")
    print(f"Final state: {result.final_state.value}")
    
    print("\n" + "="*50 + "\n")


def main():
    """Run all demonstrations."""
    print("\n" + "="*50)
    print(" Phase 2.3: Execution Loop Demonstration")
    print("="*50 + "\n")
    
    try:
        demo_successful_execution()
        demo_execution_with_custom_config()
        demo_trace_inspection()
        demo_execution_context()
        
        print("\n✅ All demonstrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
