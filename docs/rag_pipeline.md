# RAG Pipeline - Milestone 5

This document describes the RAG (Retrieval-Augmented Generation) pipeline implementation for the Lexicon project.

## Overview

The RAG pipeline provides a complete solution for indexing documents and querying them with semantic search. It consists of three main components:

1. **RAGOrchestrator** - Main orchestration layer
2. **Reranker** - Document reranking for improved relevance
3. **CacheClient** - Redis-based caching for embeddings and queries

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAG Orchestrator                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Indexing Pipeline:                                         │
│  Document → Parse → Chunk → Embed → Store                  │
│     ↓         ↓        ↓       ↓       ↓                   │
│  PDF/DOCX  Parser  Chunker  OpenAI  ChromaDB              │
│                                                             │
│  Query Pipeline:                                            │
│  Query → Embed → Search → Rerank → Results                │
│    ↓       ↓        ↓        ↓         ↓                   │
│  Text   OpenAI  ChromaDB  BM25    Formatted                │
│                                                             │
│  Caching Layer:                                             │
│  • Embedding Cache (Redis)                                 │
│  • Semantic Query Cache (Redis)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. RAGOrchestrator

**Location**: `lexicon/services/rag_orchestrator.py`

The main orchestrator that coordinates the entire RAG workflow.

**Key Methods**:
- `index_document(document: Document) -> str` - Full indexing pipeline
- `query(query_text: str, top_k: int, filters: Optional[Dict]) -> List[Dict]` - Query pipeline
- `assemble_context(query: str, search_results: List[Dict]) -> str` - Assemble LLM context

**Features**:
- Automatic document type detection (PDF, DOCX)
- Smart chunking based on document type (contract, case law, general)
- OpenAI embedding generation with caching
- ChromaDB vector storage
- Cost tracking for embedding API calls
- Comprehensive error handling

**Usage**:
```python
from lexicon.services.rag_orchestrator import RAGOrchestrator
from lexicon.domain.entities.document import Document, DocumentType

orchestrator = RAGOrchestrator()

# Index a document
document = Document(
    id="doc-001",
    filename="contract.pdf",
    file_path="/path/to/contract.pdf",
    file_size=1024000,
    document_type=DocumentType.CONTRACT,
)
doc_id = orchestrator.index_document(document)

# Query documents
results = orchestrator.query(
    query_text="What are the payment terms?",
    top_k=10,
    rerank=True
)

# Assemble context for LLM
context = orchestrator.assemble_context(query, results)
```

### 2. Reranker

**Location**: `lexicon/services/reranker.py`

Improves search result relevance using BM25 and similarity-based scoring.

**Key Methods**:
- `rerank(query: str, documents: List[Dict], top_k: int) -> List[Dict]` - Rerank documents
- `batch_rerank(queries: List[str], documents_list: List[List[Dict]], top_k: int)` - Batch reranking

**Features**:
- BM25 scoring algorithm
- Jaccard similarity scoring
- Configurable parameters (k1, b)
- Combined scoring with vector similarity
- Batch processing support

**Usage**:
```python
from lexicon.services.reranker import Reranker

# BM25 reranking (default)
reranker = Reranker(k1=1.5, b=0.75, use_bm25=True)
reranked = reranker.rerank(
    query="payment terms",
    documents=search_results,
    top_k=10
)

# Similarity-based reranking
reranker = Reranker(use_bm25=False)
reranked = reranker.rerank(query, documents, top_k=10)
```

### 3. CacheClient

**Location**: `lexicon/infrastructure/cache_client.py`

Redis-based caching for embeddings and semantic queries.

**Key Methods**:
- `get(key: str) -> Optional[str]` - Get cached value
- `set(key: str, value: str, ttl: Optional[int])` - Set cached value
- `get_embedding_cache(text: str) -> Optional[List[float]]` - Get cached embedding
- `set_embedding_cache(text: str, embedding: List[float])` - Cache embedding
- `get_semantic_cache(query: str, threshold: float) -> Optional[str]` - Get cached query result
- `set_semantic_cache(query: str, response: str)` - Cache query result

**Features**:
- Automatic connection handling with fallback
- TTL-based expiration
- Embedding caching to reduce API calls
- Semantic query caching for faster repeated queries
- Cosine similarity calculation
- Comprehensive error handling

**Usage**:
```python
from lexicon.infrastructure.cache_client import CacheClient

cache = CacheClient()

# Cache an embedding
embedding = [0.1, 0.2, 0.3, ...]
cache.set_embedding_cache("document text", embedding)

# Retrieve cached embedding
cached = cache.get_embedding_cache("document text")

# Cache query results
cache.set_semantic_cache("query text", json.dumps(results))
cached_results = cache.get_semantic_cache("query text")
```

## Configuration

Settings are configured in `lexicon/shared/config.py`:

```python
# Embedding Configuration
embedding_model: str = "text-embedding-3-large"
embedding_dimensions: int = 3072

# ChromaDB Configuration
chroma_persist_directory: str = "./chroma_data"
chroma_collection_name: str = "lexicon_documents"

# Redis Configuration
redis_url: str = "redis://localhost:6379/0"
redis_ttl: int = 3600  # 1 hour

# Chunking Configuration
chunk_size_contract: int = 512
chunk_overlap_contract: int = 50
chunk_size_case_law: int = 1024
chunk_overlap_case_law: int = 100
chunk_size_general: int = 768
chunk_overlap_general: int = 75
```

## Cost Tracking

The RAG orchestrator tracks embedding API costs:

```python
orchestrator = RAGOrchestrator()

# After indexing/querying
stats = orchestrator.get_stats()
print(f"Total tokens: {stats['total_embedding_tokens']}")
print(f"Total cost: ${stats['total_cost']:.4f}")
```

**Pricing** (per 1M tokens):
- `text-embedding-3-large`: $0.13
- `text-embedding-3-small`: $0.02
- `text-embedding-ada-002`: $0.10

## Performance Optimizations

1. **Embedding Caching**: Embeddings are cached in Redis to avoid repeated API calls
2. **Semantic Query Caching**: Query results are cached for faster repeated queries
3. **Batch Processing**: Reranker supports batch operations for efficiency
4. **Connection Pooling**: Redis uses connection pooling for better performance
5. **Smart Chunking**: Document-type-specific chunking strategies

## Error Handling

All components include comprehensive error handling:

- **Connection Failures**: Redis gracefully handles connection failures
- **API Errors**: OpenAI API errors are logged and propagated
- **Parse Errors**: Document parsing errors include detailed messages
- **Vector Store Errors**: ChromaDB errors are caught and logged

## Testing

Comprehensive unit tests are included:

```bash
# Run all RAG pipeline tests
pytest tests/unit/test_rag_orchestrator.py -v
pytest tests/unit/test_reranker.py -v
pytest tests/unit/test_cache_client.py -v

# Run with coverage
pytest tests/unit/ --cov=lexicon --cov-report=html
```

**Test Coverage**:
- RAGOrchestrator: 92%
- Reranker: 96%
- CacheClient: 80%

## Examples

See `examples/rag_pipeline_example.py` for complete usage examples:

1. Document indexing
2. Querying with filters
3. Context assembly for LLM
4. Custom component configuration
5. Batch processing
6. Cache performance comparison

## Dependencies

Required packages:
- `openai>=1.10.0` - OpenAI API client
- `chromadb>=0.4.22` - Vector database
- `redis>=5.0.1` - Redis cache client
- `pydantic>=2.6.0` - Data validation

## Future Enhancements

Potential improvements for future milestones:

1. **Advanced Semantic Search**: Full Redis vector similarity search
2. **Multi-modal Support**: Image and table extraction from PDFs
3. **Hybrid Search**: Combine dense and sparse retrieval
4. **Query Expansion**: Automatic query enhancement
5. **Result Clustering**: Group similar results
6. **Streaming Results**: Support for large result sets
7. **Metadata Extraction**: Enhanced document metadata
8. **Custom Embeddings**: Support for alternative embedding models

## Troubleshooting

**Redis Connection Issues**:
```python
# Check Redis is running
redis-cli ping

# Use fallback if Redis unavailable
cache = CacheClient()  # Will log warning but continue
```

**ChromaDB Issues**:
```python
# Clear collection if needed
vector_store = ChromaVectorStore()
vector_store.clear_collection()
```

**OpenAI API Issues**:
```python
# Check API key
echo $OPENAI_API_KEY

# Monitor rate limits in logs
```

## License

This implementation is part of the Lexicon project.
