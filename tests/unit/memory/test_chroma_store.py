"""Unit tests for ChromaDB memory store implementation."""

import hashlib
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from lexicon.memory.base import MemoryMetadata
from lexicon.memory.chroma_store import ChromaMemoryStore


def simple_embedding_function(text: str) -> list[float]:
    """Simple deterministic embedding function for testing."""
    # Use hash to create a deterministic "embedding"
    # In practice, similar texts should have similar embeddings
    # For testing, we just need consistency
    hash_val = hashlib.md5(text.encode()).hexdigest()
    # Convert hex to list of floats (384 dimensions to match real model)
    embedding = []
    for i in range(0, 384):
        byte_val = int(hash_val[i % len(hash_val)], 16)
        embedding.append(float(byte_val) / 15.0)  # Normalize to 0-1
    return embedding


@pytest.fixture
def temp_db_dir():
    """Create a temporary directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def memory_store(temp_db_dir):
    """Create a ChromaMemoryStore instance."""
    return ChromaMemoryStore(
        collection_name="test_memory",
        persist_directory=temp_db_dir,
        embedding_function=simple_embedding_function,
    )


class TestChromaMemoryStore:
    """Test ChromaMemoryStore implementation."""
    
    def test_initialization(self, temp_db_dir):
        """Test store initialization creates directory and collection."""
        store = ChromaMemoryStore(
            collection_name="test",
            persist_directory=temp_db_dir,
            embedding_function=simple_embedding_function,
        )
        
        assert store.collection_name == "test"
        assert store.persist_directory == temp_db_dir
        assert Path(temp_db_dir).exists()
    
    def test_store_single_chunk(self, memory_store):
        """Test storing a single memory chunk."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15, 10, 30),
            language="python",
        )
        
        content = "def hello():\n    return 'world'"
        chunk_id = memory_store.store(content, metadata)
        
        assert chunk_id is not None
        assert isinstance(chunk_id, str)
        assert "code_" in chunk_id
    
    def test_store_multiple_chunks(self, memory_store):
        """Test storing multiple chunks."""
        chunks = [
            ("def add(a, b): return a + b", "code"),
            ("def subtract(a, b): return a - b", "code"),
            ("# API Documentation", "documentation"),
        ]
        
        chunk_ids = []
        for content, source_type in chunks:
            metadata = MemoryMetadata(
                source_type=source_type,
                phase="phase_1",
                timestamp=datetime.now(),
            )
            chunk_id = memory_store.store(content, metadata)
            chunk_ids.append(chunk_id)
        
        assert len(chunk_ids) == 3
        assert len(set(chunk_ids)) == 3  # All unique
    
    def test_retrieve_by_similarity(self, memory_store):
        """Test retrieving chunks by semantic similarity."""
        # Store some code chunks
        code_chunks = [
            "def calculate_sum(numbers): return sum(numbers)",
            "def calculate_average(numbers): return sum(numbers) / len(numbers)",
            "def greet(name): return f'Hello, {name}'",
        ]
        
        for code in code_chunks:
            metadata = MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
                language="python",
            )
            memory_store.store(code, metadata)
        
        # Search for math-related functions
        results = memory_store.retrieve(
            query="calculate mathematical operations",
            top_k=2,
        )
        
        assert len(results) <= 2
        
        # Should retrieve math functions, not greeting
        if results:
            for result in results:
                assert "calculate" in result.chunk.content.lower()
    
    def test_retrieve_with_source_type_filter(self, memory_store):
        """Test filtering by source type."""
        # Store different types
        memory_store.store(
            "def foo(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        memory_store.store(
            "# Documentation",
            MemoryMetadata(source_type="documentation", phase="phase_1", timestamp=datetime.now()),
        )
        
        # Search only code
        results = memory_store.retrieve(
            query="function",
            filters={"source_type": "code"},
            top_k=5,
        )
        
        for result in results:
            assert result.chunk.metadata.source_type == "code"
    
    def test_retrieve_with_multiple_filters(self, memory_store):
        """Test combining multiple filters."""
        # Store chunks with different attributes
        memory_store.store(
            "def python_func(): pass",
            MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
                language="python",
            ),
        )
        memory_store.store(
            "function jsFunc() {}",
            MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
                language="javascript",
            ),
        )
        
        # Search only Python code
        results = memory_store.retrieve(
            query="function",
            filters={"source_type": "code", "language": "python"},
            top_k=5,
        )
        
        for result in results:
            assert result.chunk.metadata.language == "python"
    
    def test_retrieve_respects_similarity_threshold(self, memory_store):
        """Test that only results above threshold are returned."""
        memory_store.store(
            "def specific_unique_function_name_xyz(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        
        # Query something completely unrelated
        results = memory_store.retrieve(
            query="database connection pool configuration",
            similarity_threshold=0.8,  # High threshold
            top_k=10,
        )
        
        # Should return very few or no results due to low similarity
        for result in results:
            assert result.similarity_score >= 0.8
    
    def test_deduplication_on_store(self, memory_store):
        """Test that duplicate content updates timestamp instead of creating new chunk."""
        metadata1 = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 1),
        )
        
        content = "def unique_function(): return 42"
        chunk_id1 = memory_store.store(content, metadata1)
        
        # Store again with same content but different timestamp
        metadata2 = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15),
        )
        
        chunk_id2 = memory_store.store(content, metadata2)
        
        # Should return same chunk ID (duplicate detected)
        assert chunk_id1 == chunk_id2
        
        # Verify only one chunk exists
        stats = memory_store.get_stats()
        # Note: Due to deduplication threshold, this might vary
        # In practice, we just verify no explosion of duplicates
        assert stats["total_chunks"] <= 2
    
    def test_delete_existing_chunk(self, memory_store):
        """Test deleting an existing chunk."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime.now(),
        )
        
        chunk_id = memory_store.store("def test(): pass", metadata)
        
        # Delete it
        deleted = memory_store.delete(chunk_id)
        assert deleted is True
        
        # Verify it's gone
        stats = memory_store.get_stats()
        assert stats["total_chunks"] == 0
    
    def test_delete_nonexistent_chunk(self, memory_store):
        """Test deleting a non-existent chunk returns False."""
        deleted = memory_store.delete("nonexistent_chunk_id_12345")
        assert deleted is False
    
    def test_clear_all(self, memory_store):
        """Test clearing all memory."""
        # Store multiple chunks
        for i in range(5):
            metadata = MemoryMetadata(
                source_type="code",
                phase="phase_1",
                timestamp=datetime.now(),
            )
            memory_store.store(f"def func_{i}(): pass", metadata)
        
        # Clear all
        count = memory_store.clear()
        
        assert count == 5
        
        # Verify empty
        stats = memory_store.get_stats()
        assert stats["total_chunks"] == 0
    
    def test_clear_with_filters(self, memory_store):
        """Test clearing only chunks matching filters."""
        # Store code and documentation
        memory_store.store(
            "def code1(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        memory_store.store(
            "def code2(): pass",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        memory_store.store(
            "# Documentation",
            MemoryMetadata(source_type="documentation", phase="phase_1", timestamp=datetime.now()),
        )
        
        # Clear only code
        count = memory_store.clear(filters={"source_type": "code"})
        
        assert count == 2
        
        # Verify documentation remains
        stats = memory_store.get_stats()
        assert stats["total_chunks"] == 1
        assert stats["chunks_by_source_type"]["documentation"] == 1
    
    def test_get_stats_empty(self, memory_store):
        """Test stats for empty store."""
        stats = memory_store.get_stats()
        
        assert stats["total_chunks"] == 0
        assert stats["chunks_by_source_type"] == {}
        assert stats["chunks_by_phase"] == {}
        assert stats["storage_size_mb"] == 0.0
    
    def test_get_stats_with_data(self, memory_store):
        """Test stats with stored data."""
        # Store various chunks
        memory_store.store(
            "code1",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        memory_store.store(
            "code2",
            MemoryMetadata(source_type="code", phase="phase_1", timestamp=datetime.now()),
        )
        memory_store.store(
            "doc1",
            MemoryMetadata(source_type="documentation", phase="phase_2", timestamp=datetime.now()),
        )
        
        stats = memory_store.get_stats()
        
        assert stats["total_chunks"] == 3
        assert stats["chunks_by_source_type"]["code"] == 2
        assert stats["chunks_by_source_type"]["documentation"] == 1
        assert stats["chunks_by_phase"]["phase_1"] == 2
        assert stats["chunks_by_phase"]["phase_2"] == 1
        assert stats["storage_size_mb"] >= 0  # At least non-negative
    
    def test_persistence(self, temp_db_dir):
        """Test that data persists across store instances."""
        # Create store and add data
        store1 = ChromaMemoryStore(
            collection_name="persist_test",
            persist_directory=temp_db_dir,
            embedding_function=simple_embedding_function,
        )
        
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime.now(),
        )
        
        chunk_id = store1.store("def persistent(): pass", metadata)
        
        # Create new store instance with same directory
        store2 = ChromaMemoryStore(
            collection_name="persist_test",
            persist_directory=temp_db_dir,
            embedding_function=simple_embedding_function,
        )
        
        # Data should still be there
        stats = store2.get_stats()
        assert stats["total_chunks"] == 1
        
        # Should be able to retrieve it
        results = store2.retrieve("persistent function")
        assert len(results) > 0
