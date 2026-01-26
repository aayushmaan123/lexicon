"""
Lexicon Phase 2 Agent System.

This module provides the multi-agent architecture for Phase 2, including:
- Planner Agent: Task decomposition and planning
- Builder Agent: Code generation and artifact creation
- Reviewer Agent: Quality validation and compliance checks
- Fixer Agent: Error detection and automated remediation

All agents are stateless and communicate through the Coordinator.
"""

from lexicon.agents.base import Agent, AgentError, AgentErrorType, AgentResult
from lexicon.agents.builder import BuilderAgent
from lexicon.agents.fixer import FixerAgent
from lexicon.agents.planner import ExecutionPlan, PlannerAgent, Task
from lexicon.agents.reviewer import ReviewerAgent

__all__ = [
    "Agent",
    "AgentError",
    "AgentErrorType",
    "AgentResult",
    "PlannerAgent",
    "BuilderAgent",
    "ReviewerAgent",
    "FixerAgent",
    "ExecutionPlan",
    "Task",
]
