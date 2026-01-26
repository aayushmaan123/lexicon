"""Unit tests for memory retriever."""

import hashlib
import tempfile
from datetime import datetime, timedelta

import pytest

from lexicon.memory.base import MemoryMetadata
from lexicon.memory.chroma_store import ChromaMemoryStore
from lexicon.memory.retriever import MemoryRetriever


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
def memory_store(temp_db_dir):
    """Create a ChromaMemoryStore instance."""
    return ChromaMemoryStore(
        collection_name="test_retriever",
        persist_directory=temp_db_dir,
        embedding_function=simple_embedding_function,
    )


@pytest.fixture
def retriever(memory_store):
    """Create a MemoryRetriever instance."""
    return MemoryRetriever(memory_store)


@pytest.fixture
def populated_store(memory_store):
    """Create a store with sample data."""
    # Store some code chunks
    memory_store.store(
        "def calculate_sum(numbers): return sum(numbers)",
        MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime.now() - timedelta(days=5),
            language="python",
        ),
    )
    
    memory_store.store(
        "def greet(name): return f'Hello, {name}'",
        MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime.now() - timedelta(days=1),
            language="python",
        ),
    )
    
    # Store documentation
    memory_store.store(
        "# API Documentation\n\nThis API provides endpoints for data analysis.",
        MemoryMetadata(
            source_type="documentation",
            phase="phase_1",
            timestamp=datetime.now() - timedelta(days=10),
        ),
    )
    
    # Store error pattern
    memory_store.store(
        "ERROR: TypeError: expected str, got int\nFIX: Convert input to string",
        MemoryMetadata(
            source_type="fix",
            phase="phase_1",
            timestamp=datetime.now() - timedelta(days=2),
        ),
    )
    
    return memory_store


class TestMemoryRetriever:
    """Test MemoryRetriever class."""
    
    def test_initialization(self, memory_store):
        """Test retriever initialization."""
        retriever = MemoryRetriever(memory_store, max_context_tokens=1500)
        
        assert retriever.store == memory_store
        assert retriever.max_context_tokens == 1500
    
    def test_retrieve_context_basic(self, populated_store):
        """Test basic context retrieval."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="mathematical functions",
            top_k=5,
        )
        
        # Should return some results
        assert len(results) > 0
        
        # Results should have similarity scores
        for result in results:
            assert 0.0 <= result.similarity_score <= 1.0
    
    def test_retrieve_context_with_source_type_filter(self, populated_store):
        """Test filtering by source type."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="function",
            source_type="code",
            top_k=10,
        )
        
        # All results should be code
        for result in results:
            assert result.chunk.metadata.source_type == "code"
    
    def test_retrieve_context_with_language_filter(self, populated_store):
        """Test filtering by language."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="function",
            language="python",
            top_k=10,
        )
        
        # All results should be Python
        for result in results:
            metadata = result.chunk.metadata
            if metadata.language:  # Some chunks might not have language
                assert metadata.language == "python"
    
    def test_retrieve_context_with_phase_filter(self, populated_store):
        """Test filtering by phase."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="api",
            phase="phase_1",
            top_k=10,
        )
        
        # All results should be from phase_1
        for result in results:
            assert result.chunk.metadata.phase == "phase_1"
    
    def test_retrieve_context_prefers_recent(self, populated_store):
        """Test that recent chunks are boosted when prefer_recent=True."""
        retriever = MemoryRetriever(populated_store)
        
        # Retrieve with recency preference
        results_recent = retriever.retrieve_context(
            query="function definition",
            source_type="code",
            top_k=2,
            prefer_recent=True,
            recency_days=7,
        )
        
        # Retrieve without recency preference
        results_no_recent = retriever.retrieve_context(
            query="function definition",
            source_type="code",
            top_k=2,
            prefer_recent=False,
        )
        
        # Both should return results
        assert len(results_recent) > 0
        assert len(results_no_recent) > 0
        
        # The ordering might be different
        # Recent results might have different top result
        if len(results_recent) > 1 and len(results_no_recent) > 1:
            # Check that recent chunks get boost
            recent_chunk = results_recent[0]
            cutoff = datetime.now() - timedelta(days=7)
            
            # If top result is recent, it should have high score
            if recent_chunk.chunk.metadata.timestamp >= cutoff:
                assert recent_chunk.similarity_score > 0.6
    
    def test_retrieve_similar_errors(self, populated_store):
        """Test retrieving similar error patterns."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_similar_errors(
            error_message="TypeError: wrong type",
            top_k=5,
        )
        
        # Should find the fix we stored
        assert len(results) > 0
        
        # Should be error or fix type
        for result in results:
            assert result.chunk.metadata.source_type in ["error", "fix"]
    
    def test_retrieve_similar_errors_with_fixes(self, populated_store):
        """Test retrieving errors with fixes."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_similar_errors(
            error_message="type error",
            include_fixes=True,
            top_k=5,
        )
        
        # Should include fix patterns
        source_types = {r.chunk.metadata.source_type for r in results}
        if results:
            # At least one should be a fix (we stored one)
            assert "fix" in source_types or "error" in source_types
    
    def test_retrieve_code_examples(self, populated_store):
        """Test retrieving code examples."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_code_examples(
            query="sum calculation",
            language="python",
            top_k=5,
        )
        
        # Should find code chunks
        assert len(results) > 0
        
        # All should be code
        for result in results:
            assert result.chunk.metadata.source_type == "code"
            assert result.chunk.metadata.language == "python"
    
    def test_assemble_context_basic(self, populated_store):
        """Test basic context assembly."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="functions",
            source_type="code",
            top_k=3,
        )
        
        context = retriever.assemble_context(results, include_metadata=True)
        
        # Should have header
        assert "Retrieved Context:" in context
        
        # Should include chunk content
        if results:
            # At least some content should be present
            assert len(context) > len("Retrieved Context:")
    
    def test_assemble_context_without_metadata(self, populated_store):
        """Test context assembly without metadata."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="functions",
            top_k=2,
        )
        
        context = retriever.assemble_context(results, include_metadata=False)
        
        # Should not have metadata headers
        assert "[Source:" not in context or context == ""
        
        # But should have content if results exist
        if results:
            # Content should be in there somewhere
            for result in results:
                if result.chunk.content in context:
                    break
            else:
                # At least check we got some text
                assert len(context) > 0 or not results
    
    def test_assemble_context_respects_token_budget(self):
        """Test that context assembly respects token budget."""
        # Create store with large chunks
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ChromaMemoryStore(
                persist_directory=tmpdir,
                embedding_function=simple_embedding_function,
            )
            
            # Store chunks that are ~500 tokens each
            large_text = "word " * 500  # ~500 tokens
            for i in range(5):
                store.store(
                    large_text,
                    MemoryMetadata(
                        source_type="code",
                        phase="phase_1",
                        timestamp=datetime.now(),
                    ),
                )
            
            # Create retriever with small budget
            retriever = MemoryRetriever(store, max_context_tokens=800)
            
            results = retriever.retrieve_context(query="word", top_k=5)
            context = retriever.assemble_context(results)
            
            # Should not include all 5 chunks (would be ~2500 tokens)
            # Rough estimate: should be around 800*4 chars = 3200 chars
            assert len(context) < 4000  # Some margin for headers
    
    def test_assemble_context_empty_results(self, retriever):
        """Test assembling context with no results."""
        context = retriever.assemble_context([])
        
        assert context == ""
    
    def test_deduplication(self, memory_store):
        """Test that retriever deduplicates similar results."""
        retriever = MemoryRetriever(memory_store)
        
        # Store very similar chunks
        similar_content = "def calculate(): return 42"
        for i in range(3):
            memory_store.store(
                similar_content,  # Exactly same content
                MemoryMetadata(
                    source_type="code",
                    phase="phase_1",
                    timestamp=datetime.now() - timedelta(minutes=i),
                ),
            )
        
        results = retriever.retrieve_context(
            query="calculate function",
            top_k=10,
        )
        
        # Due to deduplication in store and retriever, should not get 3 identical results
        # ChromaStore deduplicates on write, so we'd only have 1 anyway
        assert len(results) <= 1
    
    def test_multiple_filters_combined(self, populated_store):
        """Test combining multiple filters."""
        retriever = MemoryRetriever(populated_store)
        
        results = retriever.retrieve_context(
            query="function",
            source_type="code",
            phase="phase_1",
            language="python",
            top_k=10,
        )
        
        # All results should match all filters
        for result in results:
            meta = result.chunk.metadata
            assert meta.source_type == "code"
            assert meta.phase == "phase_1"
            assert meta.language == "python"
