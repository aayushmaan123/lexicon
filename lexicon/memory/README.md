# Lexicon Memory System (Phase 2.2)

## Overview

The Lexicon Memory System provides RAG-based (Retrieval-Augmented Generation) persistent knowledge storage for the multi-agent system. It enables agents to learn from past executions, code patterns, documentation, and error patterns.

## Key Features

- **Vector-based semantic search** using ChromaDB and sentence-transformers
- **Multiple content types**: Code, documentation, errors, fixes, test patterns
- **Intelligent chunking** strategies for different content types
- **Metadata filtering** for precise retrieval (source type, phase, language, etc.)
- **Deduplication** to avoid storing redundant information
- **Recency-based ranking** to prefer recent patterns
- **Token budget management** for LLM context assembly
- **Local persistence** - no external services required

## Architecture

```
┌─────────────────────────────────────────┐
│         MemoryRetriever                 │  ← High-level API for agents
│  - retrieve_context()                   │
│  - retrieve_code_examples()             │
│  - retrieve_similar_errors()            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│         MemoryStore (Abstract)          │
│  - store()                              │
│  - retrieve()                           │
│  - delete()                             │
│  - clear()                              │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      ChromaMemoryStore (Concrete)       │
│  - ChromaDB vector storage              │
│  - sentence-transformers embeddings     │
│  - Cosine similarity search             │
└─────────────────────────────────────────┘
```

## Installation

Required dependencies (already in pyproject.toml):
- chromadb
- sentence-transformers

## Usage

### Basic Usage

```python
from datetime import datetime
from lexicon.memory import (
    ChromaMemoryStore,
    MemoryRetriever,
    MemoryMetadata,
)

# Initialize store and retriever
store = ChromaMemoryStore()
retriever = MemoryRetriever(store)

# Store a code example
metadata = MemoryMetadata(
    source_type="code",
    phase="phase_1",
    timestamp=datetime.now(),
    language="python",
    file_path="example.py",
)
store.store("def hello(): return 'world'", metadata)

# Retrieve similar code
results = retriever.retrieve_code_examples(
    query="greeting function",
    language="python",
    top_k=5,
)

# Assemble context for LLM
context = retriever.assemble_context(results)
```

### Chunking Code

```python
from lexicon.memory import chunk_code

python_code = '''
def calculate_sum(numbers):
    return sum(numbers)

class Calculator:
    def add(self, a, b):
        return a + b
'''

# Chunk at function/class level
chunks = list(chunk_code(python_code, "calc.py", "python"))

for content, metadata in chunks:
    print(f"Type: {metadata['type']}")
    print(f"Name: {metadata['name']}")
    print(f"Content: {content[:50]}...")
```

### Chunking Documentation

```python
from lexicon.memory import chunk_documentation

markdown_doc = '''
## API Reference

### Authentication

All requests require an API key...

### Endpoints

The following endpoints are available...
'''

# Chunk by semantic sections
chunks = list(chunk_documentation(markdown_doc, "markdown"))

for content, metadata in chunks:
    print(f"Heading: {metadata.get('heading')}")
    print(f"Words: {metadata['word_count']}")
```

### Storing Error Patterns

```python
from lexicon.memory import chunk_error, MemoryMetadata

error_msg = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
context = "File: main.py, Line: 42"
fix = "Convert string to int before addition: int(value) + number"

content, meta = chunk_error(error_msg, context=context, fix=fix)

metadata = MemoryMetadata(
    source_type="fix",
    phase="phase_1",
    timestamp=datetime.now(),
    tags=["TypeError", "type_conversion"],
)

store.store(content, metadata)
```

### Retrieving Similar Errors

```python
# Later, when encountering a similar error
results = retriever.retrieve_similar_errors(
    error_message="TypeError: can't add str and int",
    include_fixes=True,
    top_k=5,
)

for result in results:
    print(f"Similarity: {result.similarity_score:.2f}")
    print(f"Content: {result.chunk.content}")
```

## Data Models

### MemoryMetadata

```python
@dataclass
class MemoryMetadata:
    source_type: str      # "code", "documentation", "plan", "error", "fix", "test"
    phase: str            # "phase_1", "phase_2", "phase_3"
    timestamp: datetime
    agent: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None    # e.g., "python"
    framework: Optional[str] = None   # e.g., "pytest", "fastapi"
    tags: list[str] = field(default_factory=list)
```

### MemoryChunk

```python
@dataclass
class MemoryChunk:
    chunk_id: str
    content: str
    embedding: list[float]  # 384-dimensional vector
    metadata: MemoryMetadata
```

### RetrievalResult

```python
@dataclass
class RetrievalResult:
    chunk: MemoryChunk
    similarity_score: float  # 0-1, cosine similarity
    rank: int  # Position in results
```

## Chunking Strategies

### Code Chunking

- **Unit**: One function or class per chunk
- **Overlap**: Class context included for methods
- **Metadata**: File path, language, imports
- **Languages**: Python (full support), others (fallback)

### Documentation Chunking

- **Unit**: H2 or H3 heading + content
- **Size**: 10-500 words per chunk
- **Overlap**: Parent section title included
- **Metadata**: Heading hierarchy, word count

### Error Chunking

- **Unit**: Error message + context + fix
- **Size**: Complete pattern in one chunk
- **Overlap**: None
- **Metadata**: Error type, severity, resolution status

## Retrieval Features

### Metadata Filtering

```python
results = retriever.retrieve_context(
    query="FastAPI endpoint implementation",
    source_type="code",
    phase="phase_1",
    language="python",
    framework="fastapi",
    top_k=5,
)
```

### Recency Preference

```python
results = retriever.retrieve_context(
    query="authentication logic",
    prefer_recent=True,
    recency_days=30,  # Boost chunks from last 30 days
)
```

### Token Budget Management

```python
# Retriever respects token budget when assembling context
retriever = MemoryRetriever(store, max_context_tokens=2000)
results = retriever.retrieve_context(query="...", top_k=10)
context = retriever.assemble_context(results)  # Won't exceed 2000 tokens
```

## Access Control

- **Agents**: READ-only access via `MemoryRetriever`
- **Coordinator**: WRITE access via `MemoryStore.store()`

This enforces the principle that agents query memory for context, but only the coordinator records new patterns.

## Security Constraints

**PROHIBITED** from storage:
- ❌ API keys, passwords, tokens
- ❌ Database credentials
- ❌ User data or PII
- ❌ Execution state (belongs in Coordinator)
- ❌ Business logic or control flow

**ALLOWED** for storage:
- ✅ Code examples and patterns
- ✅ Documentation and guides
- ✅ Error patterns and fixes
- ✅ Test patterns
- ✅ Successfully executed plans

## Performance

- **Retrieval latency**: < 1 second for typical queries
- **Storage limit**: Up to 10GB for vector index
- **Chunk limit**: Max 10,000 chunks per source type
- **Embedding model**: all-MiniLM-L6-v2 (384 dimensions, ~80MB)
- **Similarity threshold**: Default 0.7 (configurable)

## Testing

```bash
# Run unit tests
pytest tests/unit/memory/ -v

# Run integration tests
pytest tests/integration/memory/ -v

# Run all memory tests
pytest tests/unit/memory/ tests/integration/memory/ -v

# With coverage
pytest tests/unit/memory/ tests/integration/memory/ --cov=lexicon.memory
```

## Limitations (Phase 2.2)

1. **Language Support**: Only Python code is fully parsed. Other languages use simple fallback chunking.
2. **Reranking**: Basic recency boost only. No advanced reranking algorithms.
3. **Timestamp Filters**: Metadata filtering by timestamp ranges not yet implemented.
4. **Token Estimation**: Uses rough approximation (4 chars ≈ 1 token).
5. **Offline Only**: Requires pre-downloaded embedding model (no internet access in tests).

## Future Enhancements (Phase 2.3+)

- [ ] Support for more programming languages (JavaScript, Go, etc.)
- [ ] Advanced reranking algorithms (MMR, diversity-based)
- [ ] Timestamp range filtering
- [ ] Precise token counting
- [ ] Automatic cleanup of stale/unused chunks
- [ ] Memory health metrics dashboard
- [ ] Cross-phase pattern learning

## Example: Complete Workflow

See `examples/demo_memory.py` for a complete demonstration of:
1. Initializing the memory system
2. Storing code and documentation
3. Retrieving relevant chunks
4. Assembling context for agents
5. Getting memory statistics

## References

- [PHASE_2_RAG_SCOPE.md](../../PHASE_2_RAG_SCOPE.md) - Complete specification
- [PHASE_2_ARCHITECTURE.md](../../PHASE_2_ARCHITECTURE.md) - System architecture
- [PHASE_2_AGENT_MODEL.md](../../PHASE_2_AGENT_MODEL.md) - Agent interaction patterns
