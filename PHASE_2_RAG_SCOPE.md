# Lexicon Phase 2 RAG Scope

## Overview

This document defines the **exact scope, boundaries, and constraints** for Retrieval-Augmented Generation (RAG) in Phase 2. The goal is to establish RAG as a **memory and context system**, explicitly NOT as an autonomous decision-maker.

> ⚠️ **Critical Principle**: RAG provides context, never control. RAG is a library, not an oracle.

## RAG Purpose Statement

**What RAG IS**:
- A **persistent knowledge base** for project context
- A **pattern library** for common solutions
- An **error history** to prevent repeated mistakes
- A **grounding mechanism** for LLM outputs

**What RAG is NOT**:
- ❌ An autonomous decision-making system
- ❌ A replacement for business logic
- ❌ A control flow mechanism
- ❌ An architectural oracle

## Use Cases: What RAG Stores

### 1. Project Documentation

**Stored**:
- Phase 1 documentation (architecture, API specs, setup guides)
- PRD documents
- Architecture decision records (ADRs)
- Code comments and docstrings

**Retrieval Trigger**:
- Agent needs context about existing features
- User asks about system capabilities
- Planning phase requires architecture understanding

**Example Query**:
```python
query = "What API endpoints exist for document analysis?"
results = memory.retrieve_context(
    query=query,
    source_type="documentation",
    phase="phase_1",
    top_k=3
)
# Returns: Relevant sections from docs/api-spec.md
```

### 2. Execution Plans

**Stored**:
- Successfully executed plans
- Task decomposition patterns
- Estimated vs. actual durations
- Dependency graphs

**Retrieval Trigger**:
- Planner receives similar task
- Estimating task complexity
- Identifying potential blockers

**Example Query**:
```python
query = "How to add authentication to FastAPI"
results = memory.retrieve_context(
    query=query,
    source_type="plan",
    top_k=5
)
# Returns: Past plans for similar features
```

### 3. Code Patterns

**Stored**:
- Successfully generated code snippets
- Function/class templates
- Common implementation patterns
- Integration examples

**Retrieval Trigger**:
- Builder generating new code
- Looking for similar implementations
- Understanding coding conventions

**Example Query**:
```python
query = "FastAPI Pydantic model validation"
results = memory.retrieve_context(
    query=query,
    source_type="code",
    language="python",
    top_k=5
)
# Returns: Examples of Pydantic models from Phase 1
```

### 4. Error Patterns and Fixes

**Stored**:
- Failed validation checks
- Error messages and stack traces
- Applied fixes that resolved errors
- Root cause analysis

**Retrieval Trigger**:
- Reviewer detects validation failure
- Fixer searches for similar past errors
- Preventing known anti-patterns

**Example Query**:
```python
query = "TypeError: incompatible return type"
results = memory.retrieve_context(
    query=query,
    source_type="error",
    severity="error",
    top_k=3
)
# Returns: Similar errors and how they were fixed
```

### 5. Test Patterns

**Stored**:
- Test file structures
- Common test fixtures
- Mock patterns
- Assertion strategies

**Retrieval Trigger**:
- Builder generating test scaffolding
- Understanding test conventions
- Creating fixtures

**Example Query**:
```python
query = "pytest fixture for mocking OpenAI API"
results = memory.retrieve_context(
    query=query,
    source_type="test",
    framework="pytest",
    top_k=3
)
# Returns: Existing mock patterns from Phase 1 tests
```

## Use Cases: What RAG Does NOT Store

### Prohibited Storage

1. **Execution Logic**:
   - ❌ Control flow decisions
   - ❌ Business rules
   - ❌ Agent routing logic
   - ❌ Validation criteria

2. **Secrets and Credentials**:
   - ❌ API keys
   - ❌ Passwords
   - ❌ Tokens
   - ❌ Database credentials

3. **User Data**:
   - ❌ Uploaded documents (unless explicitly for training)
   - ❌ User queries (unless anonymized for learning)
   - ❌ Personal information

4. **Transient State**:
   - ❌ Current execution context (lives in Coordinator)
   - ❌ Temporary variables
   - ❌ Session data

## RAG Architecture

### Components

```
┌─────────────────────────────────────────────────┐
│              RAG Store Interface                 │
├─────────────────────────────────────────────────┤
│  - store(chunk, metadata)                       │
│  - retrieve(query, filters, top_k)              │
│  - delete(chunk_id)                             │
│  - clear(filters)                               │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│          Vector Database (FAISS/Chroma)         │
├─────────────────────────────────────────────────┤
│  - Embeddings: sentence-transformers           │
│  - Similarity: Cosine                           │
│  - Storage: Local disk persistence              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│              Metadata Index                      │
├─────────────────────────────────────────────────┤
│  - source_type, phase, timestamp, agent         │
│  - Filterable, queryable                        │
└─────────────────────────────────────────────────┘
```

### Data Model

```python
@dataclass
class MemoryChunk:
    """Atomic unit of stored knowledge."""
    
    chunk_id: str
    content: str
    embedding: List[float]
    metadata: MemoryMetadata
    
@dataclass
class MemoryMetadata:
    """Metadata for filtering and attribution."""
    
    source_type: str      # "doc", "code", "plan", "error", "fix", "test"
    phase: str            # "phase_1", "phase_2", "phase_3"
    timestamp: datetime
    agent: Optional[str]  # Which agent created this
    file_path: Optional[str]
    language: Optional[str]
    framework: Optional[str]
    tags: List[str]
```

### Chunking Strategy

**Code Chunking**:
- **Unit**: Function or class
- **Size**: One function/class per chunk
- **Overlap**: Include class context for methods
- **Metadata**: File path, language, imports

**Documentation Chunking**:
- **Unit**: Semantic section (H2 or H3 heading + content)
- **Size**: 200-500 words
- **Overlap**: Include parent section title
- **Metadata**: Document type, section hierarchy

**Error Chunking**:
- **Unit**: One error + fix pattern
- **Size**: Error message + context + solution
- **Overlap**: None
- **Metadata**: Error type, severity, resolution

## Retrieval Strategy

### Query Processing

1. **Embed Query**: Convert natural language query to vector
2. **Similarity Search**: Find top-k most similar chunks
3. **Metadata Filtering**: Apply filters (source_type, phase, etc.)
4. **Rerank**: Order by relevance and recency
5. **Assemble Context**: Combine chunks into coherent context

### Filtering Rules

```python
# Example: Retrieve only Phase 1 documentation
results = memory.retrieve_context(
    query="How does document parsing work?",
    filters={
        "source_type": "documentation",
        "phase": "phase_1"
    },
    top_k=5
)

# Example: Retrieve recent error fixes
results = memory.retrieve_context(
    query="Type checking error",
    filters={
        "source_type": "fix",
        "timestamp_after": datetime.now() - timedelta(days=30)
    },
    top_k=3
)
```

### Context Assembly

**Budget Management**:
- Max tokens per retrieval: 2000 tokens
- If chunks exceed budget, truncate oldest first
- Always include metadata attribution

**Deduplication**:
- Remove duplicate chunks based on content similarity
- Prefer more recent chunks when duplicates exist

**Format**:
```
Retrieved Context:

[Source: docs/api-spec.md | Phase: phase_1 | Timestamp: 2026-01-25]
<chunk content here>

[Source: lexicon/api/routes/documents.py | Phase: phase_1 | Timestamp: 2026-01-25]
<chunk content here>
```

## RAG Constraints

### Operational Constraints

1. **Response Time**: Retrieval must complete in <1 second
2. **Storage Limit**: Max 10GB for vector index
3. **Chunk Limit**: Max 10,000 chunks per source type
4. **Query Frequency**: No rate limits (local operation)

### Quality Constraints

1. **Relevance Threshold**: Only return chunks with similarity >0.7
2. **Freshness**: Prefer chunks from last 30 days when available
3. **Diversity**: Include variety of source types when possible
4. **Attribution**: Always include source metadata

### Security Constraints

1. **No Sensitive Data**: Automated scan to detect secrets before storage
2. **Access Control**: Memory is project-scoped (single project per instance)
3. **Audit Trail**: Log all retrievals with query and results
4. **Data Retention**: Configurable retention policy (default: 90 days for errors)

## Integration with Agents

### Agent Query Patterns

**Planner Agent**:
```python
# Query for similar past plans
past_plans = memory.retrieve_context(
    query=f"Plan for: {task_description}",
    filters={"source_type": "plan"},
    top_k=3
)

# Query for documentation
docs = memory.retrieve_context(
    query=task_description,
    filters={"source_type": "documentation", "phase": "phase_1"},
    top_k=5
)
```

**Builder Agent**:
```python
# Query for code examples
examples = memory.retrieve_context(
    query=f"Implementation of {feature_name}",
    filters={"source_type": "code", "language": "python"},
    top_k=5
)

# Query for patterns
patterns = memory.retrieve_context(
    query=f"{framework} {pattern_type} pattern",
    filters={"source_type": "code"},
    top_k=3
)
```

**Reviewer Agent**:
```python
# Query for known issues
issues = memory.retrieve_context(
    query=error_message,
    filters={"source_type": "error"},
    top_k=5
)
```

**Fixer Agent**:
```python
# Query for fix patterns
fixes = memory.retrieve_context(
    query=error_message,
    filters={"source_type": "fix"},
    top_k=3
)

# Query for similar failures
similar = memory.retrieve_context(
    query=error_message,
    filters={"source_type": "error", "resolved": True},
    top_k=5
)
```

## Memory Write Operations

### When to Store

**Coordinator writes to memory**:
- ✅ After successful plan execution
- ✅ After successful build
- ✅ After validation pass/fail
- ✅ After successful fix
- ✅ On user-provided context (PRD, docs)

**Agents do NOT write to memory**:
- ❌ Agents are read-only consumers

### Storage Lifecycle

```
Agent Execution → Success? → Coordinator → Memory.store(chunk, metadata)
                     ↓ No
                  Failure → Coordinator → Memory.store(error + context)
```

### Deduplication on Write

Before storing:
1. Check if similar chunk exists (similarity >0.95)
2. If exists, update timestamp instead of creating duplicate
3. If new, store as new chunk

## Memory Maintenance

### Cleanup Strategies

1. **Age-Based**: Remove chunks older than retention policy
2. **Size-Based**: If approaching 10GB limit, remove oldest low-relevance chunks
3. **Relevance-Based**: Periodically remove never-retrieved chunks
4. **Manual**: CLI command to clear specific source types or phases

### Memory Health Metrics

Track and expose:
- Total chunks stored
- Storage size
- Retrieval frequency per source type
- Average relevance scores
- Duplicate rate

## Explicit Non-Uses

### What RAG is NOT Used For

1. **Tool Selection**:
   - ❌ "Should I use pytest or unittest?" → Hard-coded in agents
   - ✅ "How are tests written in this project?" → RAG provides examples

2. **Architecture Decisions**:
   - ❌ "Should I use microservices or monolith?" → Not RAG's job
   - ✅ "What architecture patterns exist in Phase 1?" → RAG shows patterns

3. **Code Execution**:
   - ❌ RAG does not execute code
   - ✅ RAG provides code examples

4. **Validation Logic**:
   - ❌ RAG does not define what "good code" is
   - ✅ RAG shows examples of code that passed validation

5. **Control Flow**:
   - ❌ RAG does not decide which agent to call next
   - ✅ RAG provides context for agents to make decisions

## Testing Strategy

### Unit Tests

- Embedding generation
- Similarity search
- Metadata filtering
- Chunk storage and retrieval
- Deduplication logic

### Integration Tests

- Agent → Memory query integration
- Coordinator → Memory write integration
- Full lifecycle: store → retrieve → update

### Performance Tests

- Retrieval latency (<1s requirement)
- Storage scalability (up to 10GB)
- Query throughput

## Embedding Model

### Choice: sentence-transformers/all-MiniLM-L6-v2

**Rationale**:
- Small model size (~80MB)
- Fast inference (<10ms per query)
- Good quality for code and documentation
- No external API calls
- Works offline

**Dimensions**: 384

**Trade-offs**:
- ✅ Speed and size
- ❌ Slightly lower quality than larger models (acceptable for our use case)

## Migration and Versioning

### Initial Population

On Phase 2 initialization:
1. Index all Phase 1 documentation
2. Index Phase 1 codebase (functions and classes)
3. Index Phase 1 test patterns
4. Create embeddings for all chunks

### Version Compatibility

- **Chunk Format**: Versioned schema
- **Embedding Model**: Pin to specific version
- **Migration**: Provide script to re-embed if model changes

## Conclusion

Phase 2 RAG is **scoped, constrained, and purposeful**:

- **Scoped**: Stores documentation, code, plans, errors, tests
- **Constrained**: Read-only for agents, no control flow, no secrets
- **Purposeful**: Provides context, not decisions

By establishing clear boundaries, we ensure RAG enhances agent capabilities without creating unpredictable behavior or hidden logic.

**Key Takeaway**: RAG is a **smart filing cabinet**, not a **decision-making oracle**.

---

**Document Version**: 1.0  
**Status**: Design Review  
**Dependencies**: PHASE_2_ARCHITECTURE.md, PHASE_2_AGENT_MODEL.md
