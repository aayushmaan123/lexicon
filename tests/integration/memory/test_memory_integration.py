"""Integration tests for the memory system."""

import hashlib
import tempfile
from datetime import datetime, timedelta

import pytest

from lexicon.memory import (
    ChromaMemoryStore,
    MemoryMetadata,
    MemoryRetriever,
    chunk_code,
    chunk_documentation,
    chunk_error,
)


def simple_embedding_function(text: str) -> list[float]:
    """Simple deterministic embedding function for testing."""
    hash_val = hashlib.md5(text.encode()).hexdigest()
    embedding = []
    for i in range(0, 384):
        byte_val = int(hash_val[i % len(hash_val)], 16)
        embedding.append(float(byte_val) / 15.0)
    return embedding


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def memory_system(temp_db_dir):
    """Create a complete memory system."""
    store = ChromaMemoryStore(
        persist_directory=temp_db_dir,
        embedding_function=simple_embedding_function,
    )
    retriever = MemoryRetriever(store)
    return store, retriever


class TestMemoryIntegration:
    """Integration tests for complete memory workflows."""
    
    def test_end_to_end_code_workflow(self, memory_system):
        """Test complete workflow: chunk code -> store -> retrieve."""
        store, retriever = memory_system
        
        # Step 1: Chunk some Python code
        python_code = '''
import os
from pathlib import Path

def read_config(path: str) -> dict:
    """Read configuration from file."""
    return json.loads(Path(path).read_text())

def save_config(path: str, config: dict):
    """Save configuration to file."""
    Path(path).write_text(json.dumps(config))
'''
        
        chunks = list(chunk_code(python_code, "config.py", "python"))
        
        # Step 2: Store all chunks
        chunk_ids = []
        for content, chunk_meta in chunks:
            metadata = MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
                file_path=chunk_meta.get("file_path"),
                language="python",
            )
            chunk_id = store.store(content, metadata)
            chunk_ids.append(chunk_id)
        
        assert len(chunk_ids) == len(chunks)
        
        # Step 3: Retrieve code examples
        results = retriever.retrieve_code_examples(
            query="read configuration from file",
            language="python",
            top_k=5,
        )
        
        # Should find the read_config function
        assert len(results) > 0
        
        found_read_config = False
        for result in results:
            if "read_config" in result.chunk.content:
                found_read_config = True
                break
        
        assert found_read_config
        
        # Step 4: Assemble context for an agent
        context = retriever.assemble_context(results)
        
        assert "Retrieved Context:" in context
        assert "config" in context.lower()
    
    def test_end_to_end_documentation_workflow(self, memory_system):
        """Test complete workflow: chunk docs -> store -> retrieve."""
        store, retriever = memory_system
        
        # Step 1: Chunk documentation
        markdown_doc = '''
# API Reference

## Authentication

All API requests require an API key in the header:

```
Authorization: Bearer <api_key>
```

The API key can be obtained from your account dashboard.

## Endpoints

### GET /api/documents

Retrieve a list of documents.

**Parameters:**
- limit (int): Maximum number of results
- offset (int): Pagination offset

**Response:**
Returns a JSON array of document objects.

### POST /api/documents

Upload a new document.

**Request Body:**
- file (binary): The document file
- title (string): Document title
'''
        
        chunks = list(chunk_documentation(markdown_doc, "markdown"))
        
        # Step 2: Store documentation chunks
        for content, chunk_meta in chunks:
            metadata = MemoryMetadata(
                source_type="documentation",
                phase="phase_1",
                timestamp=datetime.now(),
                tags=["api", "reference"],
            )
            store.store(content, metadata)
        
        # Step 3: Retrieve documentation about authentication
        results = retriever.retrieve_context(
            query="how to authenticate API requests",
            source_type="documentation",
            top_k=3,
        )
        
        assert len(results) > 0
        
        # Should find authentication section
        found_auth = False
        for result in results:
            if "authentication" in result.chunk.content.lower():
                found_auth = True
                break
        
        assert found_auth
    
    def test_end_to_end_error_workflow(self, memory_system):
        """Test complete workflow: chunk error -> store -> retrieve fix."""
        store, retriever = memory_system
        
        # Step 1: Create error pattern
        error_message = "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
        context = "File: calculator.py, Line: 42, Function: add_values"
        fix = "Convert string to int before addition: int(value) + number"
        
        content, chunk_meta = chunk_error(error_message, context=context, fix=fix)
        
        # Step 2: Store error pattern
        metadata = MemoryMetadata(
            source_type="fix",
            phase="phase_1",
            timestamp=datetime.now(),
            tags=["TypeError", "type_conversion"],
        )
        
        store.store(content, metadata)
        
        # Step 3: Later, retrieve similar error fix
        similar_error = "TypeError: can't add str and int"
        results = retriever.retrieve_similar_errors(
            error_message=similar_error,
            include_fixes=True,
            top_k=5,
        )
        
        assert len(results) > 0
        
        # Should find our stored fix
        found_fix = False
        for result in results:
            if "Convert string to int" in result.chunk.content:
                found_fix = True
                break
        
        assert found_fix
    
    def test_multi_phase_workflow(self, memory_system):
        """Test storing and retrieving across multiple phases."""
        store, retriever = memory_system
        
        # Store content from phase 1
        store.store(
            "def phase1_function(): pass",
            MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now() - timedelta(days=30),
                language="python",
            ),
        )
        
        # Store content from phase 2
        store.store(
            "def phase2_function(): pass",
            MemoryMetadata(
                source_type="code",
                phase="phase_2",
                timestamp=datetime.now(),
                language="python",
            ),
        )
        
        # Retrieve only phase 1
        phase1_results = retriever.retrieve_context(
            query="function",
            phase="phase_1",
            top_k=10,
        )
        
        for result in phase1_results:
            assert result.chunk.metadata.phase == "phase_1"
        
        # Retrieve only phase 2
        phase2_results = retriever.retrieve_context(
            query="function",
            phase="phase_2",
            top_k=10,
        )
        
        for result in phase2_results:
            assert result.chunk.metadata.phase == "phase_2"
    
    def test_memory_persistence_workflow(self, temp_db_dir):
        """Test that memory persists across system restarts."""
        # Create system and store data
        store1 = ChromaMemoryStore(
            persist_directory=temp_db_dir,
            embedding_function=simple_embedding_function,
        )
        
        store1.store(
            "def persistent_function(): return 'I persist'",
            MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
            ),
        )
        
        # "Restart" - create new instances
        store2 = ChromaMemoryStore(
            persist_directory=temp_db_dir,
            embedding_function=simple_embedding_function,
        )
        retriever2 = MemoryRetriever(store2)
        
        # Should still find the data
        results = retriever2.retrieve_context(
            query="persistent function",
            top_k=5,
        )
        
        assert len(results) > 0
        assert "persistent_function" in results[0].chunk.content
    
    def test_memory_statistics_workflow(self, memory_system):
        """Test getting memory statistics after various operations."""
        store, retriever = memory_system
        
        # Initially empty
        stats = store.get_stats()
        assert stats["total_chunks"] == 0
        
        # Add code
        store.store(
            "def code1(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        store.store(
            "def code2(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        
        # Add documentation
        store.store(
            "# Documentation",
            MemoryMetadata(source_type="documentation", phase="phase_1", timestamp=datetime.now()),
        )
        
        # Check stats
        stats = store.get_stats()
        assert stats["total_chunks"] == 3
        assert stats["chunks_by_source_type"]["code"] == 2
        assert stats["chunks_by_source_type"]["documentation"] == 1
        assert stats["chunks_by_phase"]["phase_1"] == 3
        assert stats["storage_size_mb"] >= 0  # At least non-negative
    
    def test_cleanup_workflow(self, memory_system):
        """Test cleaning up memory."""
        store, retriever = memory_system
        
        # Store various content
        store.store(
            "code",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        store.store(
            "doc",
            MemoryMetadata(source_type="documentation", phase="phase_1", timestamp=datetime.now()),
        )
        store.store(
            "test",
            MemoryMetadata(source_type="test", phase="phase_2", timestamp=datetime.now()),
        )
        
        # Clear only phase_1
        count = store.clear(filters={"phase": "phase_1"})
        assert count == 2
        
        # phase_2 should remain
        stats = store.get_stats()
        assert stats["total_chunks"] == 1
        assert stats["chunks_by_phase"]["phase_2"] == 1
    
    def test_complex_query_workflow(self, memory_system):
        """Test complex queries with multiple filters and ranking."""
        store, retriever = memory_system
        
        # Store diverse content with different attributes
        contents = [
            ("def old_python_func(): pass", "code", "phase_1", "python", 60),
            ("def new_python_func(): pass", "code", "phase_1", "python", 1),
            ("function jsFunc() {}", "code", "phase_1", "javascript", 1),
            ("# Python docs", "documentation", "phase_1", None, 5),
        ]
        
        for content, source_type, phase, language, days_ago in contents:
            metadata = MemoryMetadata(
                source_type=source_type,
                phase=phase,
                timestamp=datetime.now() - timedelta(days=days_ago),
                language=language,
            )
            store.store(content, metadata)
        
        # Query with multiple filters and recency preference
        results = retriever.retrieve_context(
            query="python function",
            source_type="code",
            language="python",
            prefer_recent=True,
            recency_days=30,
            top_k=5,
        )
        
        # Should find Python functions
        assert len(results) > 0
        
        # Should prefer recent ones (within 30 days)
        if len(results) > 1:
            # First result should be relatively recent
            assert results[0].chunk.metadata.timestamp >= datetime.now() - timedelta(days=30)
        
        # Should not include JavaScript
        for result in results:
            assert result.chunk.metadata.language != "javascript"
    
    def test_agent_context_assembly_workflow(self, memory_system):
        """Test assembling context for agent consumption."""
        store, retriever = memory_system
        
        # Simulate agent needing context for a task
        # Store relevant examples
        examples = [
            "def validate_email(email: str) -> bool:\n    return '@' in email",
            "def validate_phone(phone: str) -> bool:\n    return len(phone) == 10",
            "# Validation Module\n\nProvides validation utilities",
        ]
        
        for i, content in enumerate(examples):
            source_type = "code" if "def" in content else "documentation"
            metadata = MemoryMetadata(
                source_type=source_type,
                phase="phase_1",
                timestamp=datetime.now() - timedelta(hours=i),
            )
            store.store(content, metadata)
        
        # Agent queries for validation examples
        results = retriever.retrieve_context(
            query="email validation function",
            top_k=3,
        )
        
        # Assemble context with token budget
        context = retriever.assemble_context(results, include_metadata=True)
        
        # Context should be ready for LLM
        assert "Retrieved Context:" in context
        assert len(context) < retriever.max_context_tokens * 5  # Rough char estimate
        
        # Should include relevant example
        assert "validate_email" in context or "validation" in context.lower()
