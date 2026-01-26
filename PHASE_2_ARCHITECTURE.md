# Lexicon Phase 2 Architecture

## Executive Summary

Phase 2 introduces **multi-agent orchestration**, **project memory**, and **self-healing execution** to the Lexicon toolkit. This document outlines the overall architecture, design decisions, and boundaries for Phase 2.

> ⚠️ **Critical Constraint**: Phase 1 remains completely unchanged. Phase 2 extends capabilities without modifying existing functionality.

## Architecture Overview

### High-Level Design

Phase 2 adds a new orchestration layer above Phase 1, enabling:

1. **Intelligent Task Planning**: Decompose complex workflows into executable steps
2. **Autonomous Execution**: Build, validate, and deploy with minimal human intervention
3. **Memory Persistence**: Learn from past executions to improve future performance
4. **Self-Correction**: Detect and fix failures automatically

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 2: Orchestration Layer             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │  Planner   │→ │  Builder   │→ │  Reviewer  │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│         ↓                ↓               ↓                   │
│  ┌────────────────────────────────────────────┐            │
│  │      Coordinator (Execution Loop)          │            │
│  └────────────────────────────────────────────┘            │
│         ↓                                                    │
│  ┌────────────────────────────────────────────┐            │
│  │      Project Memory (Scoped RAG)           │            │
│  └────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│               Phase 1: Core Services (Unchanged)            │
│  Document Analysis | Contract Review | Legal Research      │
│  RAG Pipeline | Vector Store | LLM Abstractions            │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Multi-Agent System

**Purpose**: Decompose complex tasks into specialized operations

**Components**:
- **Planner Agent**: Task decomposition and planning
- **Builder Agent**: Code generation and artifact creation
- **Reviewer Agent**: Quality validation and compliance checks
- **Fixer Agent**: Error detection and automated remediation

**Key Design Decision**: Agents are **stateless**. All state flows through the Coordinator and Memory subsystem.

### 2. Coordinator

**Purpose**: Orchestrates agent interactions and manages execution flow

**Responsibilities**:
- Agent lifecycle management
- Task routing and sequencing
- State transitions
- Failure detection and recovery

**Key Design Decision**: Coordinator owns the execution loop but delegates decisions to agents.

### 3. Project Memory (Scoped RAG)

**Purpose**: Persistent context for learning and grounding

**Scope**:
- ✅ **Stores**: Documentation, PRDs, architecture decisions, error patterns, generated artifacts
- ❌ **Does NOT**: Make execution decisions, replace business logic, control architecture

**Key Design Decision**: RAG is a **read-only knowledge base** for agents, not an autonomous decision-maker.

### 4. Validation Pipeline

**Purpose**: Automated quality gates before deployment

**Checks**:
- Code formatting (ruff)
- Type checking (mypy)
- Unit tests (pytest)
- Integration tests
- Security scanning (bandit/semgrep)

**Key Design Decision**: Validation is **mandatory** and **blocking**. No bypasses allowed.

### 5. PRD → Artifact Pipeline

**Purpose**: Repeatable workflow from requirements to deployable code

**Stages**:
1. PRD ingestion and parsing
2. Architecture planning
3. Code generation
4. Validation and testing
5. Artifact packaging
6. Deployment readiness check

**Key Design Decision**: Pipeline is **idempotent** and **resumable** at any stage.

## Folder Structure

Phase 2 adds new directories without reorganizing Phase 1:

```
lexicon/
├── agents/                    # NEW: Multi-agent system
│   ├── __init__.py
│   ├── base.py               # Agent base class
│   ├── planner.py            # Planner agent
│   ├── builder.py            # Builder agent
│   ├── reviewer.py           # Reviewer agent
│   └── fixer.py              # Fixer agent
├── orchestrator/              # NEW: Execution coordination
│   ├── __init__.py
│   ├── coordinator.py        # Main coordinator
│   ├── execution_loop.py     # Self-healing loop
│   └── state.py              # Execution state management
├── memory/                    # NEW: Project memory system
│   ├── __init__.py
│   ├── rag_store.py          # RAG storage interface
│   ├── retriever.py          # Context retrieval
│   ├── schemas.py            # Memory data models
│   └── embedder.py           # Lightweight embeddings
├── validation/                # NEW: Quality gates
│   ├── __init__.py
│   ├── lint.py               # Code formatting checks
│   ├── tests.py              # Test execution
│   ├── security.py           # Security scanning
│   └── pipeline.py           # Validation orchestration
├── pipelines/                 # NEW: PRD workflows
│   ├── __init__.py
│   ├── prd_parser.py         # PRD parsing
│   ├── artifact_builder.py   # Code generation
│   └── deployment.py         # Deployment preparation
│
├── api/                       # UNCHANGED
├── cli/                       # UNCHANGED
├── services/                  # UNCHANGED
├── domain/                    # UNCHANGED
├── infrastructure/            # UNCHANGED
└── shared/                    # UNCHANGED
```

## Data Flow

### Typical Execution Flow

1. **Input**: User provides PRD or task description
2. **Planning**: Planner agent analyzes requirements, queries memory for context
3. **Execution**: Builder agent generates artifacts based on plan
4. **Validation**: Reviewer agent checks quality, runs tests
5. **Self-Healing**: If failures occur, Fixer agent applies corrections
6. **Memory Update**: Successful patterns and failure fixes stored in RAG
7. **Output**: Validated, tested artifacts ready for deployment

### Memory Flow

```
User Input → Planner → [Query Memory] → Get Context
                ↓
          Build Artifacts → [Store in Memory]
                ↓
          Validation → [Store Results]
                ↓
          Failures? → Fixer → [Store Fix Pattern]
                ↓
          Success → [Store Success Pattern]
```

## Design Principles

### 1. Separation of Concerns

- **Agents**: Specialized logic (plan, build, review, fix)
- **Coordinator**: Orchestration and flow control
- **Memory**: Context persistence and retrieval
- **Validation**: Quality enforcement

### 2. Stateless Agents

Each agent is **stateless** and **reentrant**. State flows through:
- Coordinator's execution context
- Memory subsystem (RAG)
- Explicit parameter passing

### 3. Fail-Fast with Recovery

- Detect failures immediately
- Capture failure context
- Apply automated fixes when possible
- Escalate when automation cannot resolve

### 4. Memory as Support, Not Control

RAG provides **context and grounding**, never **decision-making logic**:
- ✅ "What documentation exists for this feature?"
- ✅ "What errors have we seen before?"
- ❌ "Should we use architecture pattern X?"
- ❌ "Which tools should we use?"

### 5. Backward Compatibility

Phase 2 is **additive only**:
- No Phase 1 API changes
- No Phase 1 CLI changes
- No Phase 1 service modifications
- All Phase 1 tests pass unchanged

## Technology Stack

### New Dependencies

- **LangChain/LangGraph**: Agent orchestration framework
- **FAISS** or **Chroma**: Lightweight vector store for memory
- **sentence-transformers**: Small embedding model (all-MiniLM-L6-v2)
- **mypy**: Type checking
- **bandit**: Security scanning

### Rationale

- **LangChain**: Industry-standard for agent workflows
- **FAISS/Chroma**: Lightweight, no external dependencies
- **MiniLM**: Small model (<100MB), fast, good quality
- **mypy/bandit**: Standard Python quality tools

## Explicit Out of Scope for Phase 2

### What Phase 2 Does NOT Include

1. **Cloud Deployment**: No AWS/GCP/Azure deployment automation
2. **Authentication/Authorization**: No user management
3. **Distributed Execution**: Single-node only
4. **Real-time Monitoring**: Basic logging only
5. **GUI/Web Interface**: CLI and API only
6. **Multi-tenancy**: Single project context
7. **Advanced LLM Features**: No fine-tuning, no model training
8. **Production SLAs**: Development/testing environment only
9. **External Integrations**: No CI/CD platform integrations (GitHub Actions, GitLab CI)
10. **Cost Optimization**: No automatic model selection or cost limits

### Deferred to Phase 3

1. **Multi-project support**: Handling multiple projects simultaneously
2. **Distributed agents**: Running agents across multiple machines
3. **Advanced memory**: Hierarchical or temporal memory structures
4. **Plugin system**: Third-party agent extensions
5. **Interactive debugging**: Step-through execution with breakpoints

## Success Metrics

Phase 2 is considered successful when:

### Functional Requirements

1. ✅ All Phase 1 tests pass without modification
2. ✅ Can ingest a PRD and produce executable code
3. ✅ Self-healing loop corrects at least one induced test failure
4. ✅ Memory system stores and retrieves context correctly
5. ✅ Validation pipeline blocks invalid artifacts

### Non-Functional Requirements

1. ✅ No breaking changes to Phase 1 APIs
2. ✅ Clear separation between Phase 1 and Phase 2
3. ✅ Comprehensive documentation
4. ✅ Test coverage >80% for new code
5. ✅ Execution loop completes in <5 minutes for simple tasks

## Risk Mitigation

### Risk 1: RAG Scope Creep

**Mitigation**: Strict interfaces. RAG only returns context, never executes logic.

### Risk 2: Phase 1 Breakage

**Mitigation**: Automated regression testing. Phase 1 test suite runs on every Phase 2 change.

### Risk 3: Over-Engineering

**Mitigation**: Start minimal. Add complexity only when justified by use cases.

### Risk 4: Agent Hallucination

**Mitigation**: Validation gates. All outputs must pass linting, typing, and testing.

### Risk 5: Memory Pollution

**Mitigation**: Metadata tagging. Clear attribution (source, phase, timestamp, agent).

## Implementation Approach

### Phase 2.1: Core Agent Architecture

**Deliverables**:
- Agent base class and interface
- Planner, Builder, Reviewer, Fixer implementations
- Unit tests for each agent

**Validation**: Agents can operate independently with mocked inputs.

### Phase 2.2: Memory System

**Deliverables**:
- RAG store implementation
- Embedder and retriever
- Memory schemas and metadata

**Validation**: Store and retrieve arbitrary context with metadata filtering.

### Phase 2.3: Execution Loop

**Deliverables**:
- Coordinator implementation
- Self-healing loop
- Validation pipeline integration

**Validation**: End-to-end execution from plan to validated artifact.

### Phase 2.4: PRD Pipeline

**Deliverables**:
- PRD parser
- Artifact builder
- Deployment preparation

**Validation**: Complete PRD → deployable service workflow.

## Conclusion

Phase 2 transforms Lexicon from a **document analysis toolkit** into a **self-improving development platform**. By adding intelligent orchestration, persistent memory, and self-healing capabilities, Phase 2 enables automated workflows while maintaining the solid foundation of Phase 1.

The design prioritizes:
- **Clarity**: Simple, understandable architecture
- **Safety**: No Phase 1 modifications
- **Extensibility**: Clean interfaces for Phase 3 evolution
- **Pragmatism**: Deliver value without over-engineering

---

**Document Version**: 1.0  
**Status**: Design Review  
**Next Steps**: Create detailed agent model, RAG scope, and execution flow documents
