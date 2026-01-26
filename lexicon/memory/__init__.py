"""RAG-based Project Memory System for Lexicon Phase 2.

This module provides persistent knowledge storage and retrieval for the
multi-agent system. It stores documentation, code patterns, execution plans,
error patterns, and test patterns to provide context for agent operations.

Key Features:
- Vector-based semantic search using ChromaDB
- Metadata filtering for precise retrieval
- Chunking strategies for different content types
- Deduplication and recency-based ranking
- Local disk persistence

Usage Example:
    >>> from lexicon.memory import ChromaMemoryStore, MemoryRetriever, MemoryMetadata
    >>> from datetime import datetime
    >>> 
    >>> # Initialize store and retriever
    >>> store = ChromaMemoryStore()
    >>> retriever = MemoryRetriever(store)
    >>> 
    >>> # Store a code example
    >>> metadata = MemoryMetadata(
    ...     source_type="code",
    ...     phase="phase_1",
    ...     timestamp=datetime.now(),
    ...     language="python",
    ...     file_path="example.py",
    ... )
    >>> chunk_id = store.store("def hello(): return 'world'", metadata)
    >>> 
    >>> # Retrieve similar code
    >>> results = retriever.retrieve_code_examples("greeting function", language="python")
    >>> context = retriever.assemble_context(results)

Public Interfaces:
    - MemoryStore: Abstract base class for storage implementations
    - MemoryChunk: Data model for stored chunks
    - MemoryMetadata: Metadata for filtering and attribution
    - RetrievalResult: Result from a query operation
    - ChromaMemoryStore: ChromaDB-based storage implementation
    - MemoryRetriever: High-level retrieval interface
    - Chunking functions: chunk_code, chunk_documentation, chunk_error

Constraints (Phase 2.2):
    - Agents have READ-only access to memory
    - Coordinator has WRITE access to memory
    - NO storage of secrets, credentials, or user data
    - NO control flow or business logic in memory
    - All data persisted locally (no external services)
"""

from lexicon.memory.base import (
    MemoryChunk,
    MemoryMetadata,
    MemoryStore,
    RetrievalResult,
)
from lexicon.memory.chroma_store import ChromaMemoryStore
from lexicon.memory.chunker import chunk_code, chunk_documentation, chunk_error
from lexicon.memory.retriever import MemoryRetriever

__all__ = [
    # Base interfaces and data models
    "MemoryStore",
    "MemoryChunk",
    "MemoryMetadata",
    "RetrievalResult",
    # Implementations
    "ChromaMemoryStore",
    "MemoryRetriever",
    # Chunking functions
    "chunk_code",
    "chunk_documentation",
    "chunk_error",
]
