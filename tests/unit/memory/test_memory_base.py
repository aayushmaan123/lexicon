"""Unit tests for memory base classes and data models."""

from datetime import datetime

import pytest

from lexicon.memory.base import MemoryChunk, MemoryMetadata, RetrievalResult


class TestMemoryMetadata:
    """Test MemoryMetadata dataclass."""
    
    def test_create_minimal_metadata(self):
        """Test creating metadata with only required fields."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15, 10, 30),
        )
        
        assert metadata.source_type == "code"
        assert metadata.phase == "phase_1"
        assert metadata.timestamp == datetime(2024, 1, 15, 10, 30)
        assert metadata.agent is None
        assert metadata.file_path is None
        assert metadata.language is None
        assert metadata.framework is None
        assert metadata.tags == []
    
    def test_create_full_metadata(self):
        """Test creating metadata with all fields."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15, 10, 30),
            agent="builder",
            file_path="src/main.py",
            language="python",
            framework="fastapi",
            tags=["api", "endpoint"],
        )
        
        assert metadata.agent == "builder"
        assert metadata.file_path == "src/main.py"
        assert metadata.language == "python"
        assert metadata.framework == "fastapi"
        assert metadata.tags == ["api", "endpoint"]
    
    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = MemoryMetadata(
            source_type="documentation",
            phase="phase_2",
            timestamp=datetime(2024, 1, 15, 10, 30),
            file_path="docs/api.md",
            tags=["api", "rest"],
        )
        
        result = metadata.to_dict()
        
        assert result["source_type"] == "documentation"
        assert result["phase"] == "phase_2"
        assert result["timestamp"] == "2024-01-15T10:30:00"
        assert result["file_path"] == "docs/api.md"
        assert result["tags"] == "api,rest"  # Now comma-separated string
        # agent is None, so it should be filtered out
        assert "agent" not in result
    
    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "source_type": "error",
            "phase": "phase_1",
            "timestamp": "2024-01-15T10:30:00",
            "agent": "reviewer",
            "tags": ["validation"],
        }
        
        metadata = MemoryMetadata.from_dict(data)
        
        assert metadata.source_type == "error"
        assert metadata.phase == "phase_1"
        assert metadata.timestamp == datetime(2024, 1, 15, 10, 30)
        assert metadata.agent == "reviewer"
        assert metadata.tags == ["validation"]
    
    def test_from_dict_with_datetime_object(self):
        """Test from_dict handles datetime objects correctly."""
        data = {
            "source_type": "code",
            "phase": "phase_1",
            "timestamp": datetime(2024, 1, 15, 10, 30),
        }
        
        metadata = MemoryMetadata.from_dict(data)
        
        assert metadata.timestamp == datetime(2024, 1, 15, 10, 30)
    
    def test_roundtrip_conversion(self):
        """Test that to_dict and from_dict are inverses."""
        original = MemoryMetadata(
            source_type="test",
            phase="phase_2",
            timestamp=datetime(2024, 1, 15, 10, 30),
            agent="builder",
            file_path="tests/test_main.py",
            language="python",
            framework="pytest",
            tags=["unit", "integration"],
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = MemoryMetadata.from_dict(data)
        
        assert restored.source_type == original.source_type
        assert restored.phase == original.phase
        assert restored.timestamp == original.timestamp
        assert restored.agent == original.agent
        assert restored.file_path == original.file_path
        assert restored.language == original.language
        assert restored.framework == original.framework
        assert restored.tags == original.tags


class TestMemoryChunk:
    """Test MemoryChunk dataclass."""
    
    def test_create_chunk(self):
        """Test creating a memory chunk."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime.now(),
        )
        
        chunk = MemoryChunk(
            chunk_id="test_123",
            content="def hello(): pass",
            embedding=[0.1, 0.2, 0.3],
            metadata=metadata,
        )
        
        assert chunk.chunk_id == "test_123"
        assert chunk.content == "def hello(): pass"
        assert chunk.embedding == [0.1, 0.2, 0.3]
        assert chunk.metadata == metadata


class TestRetrievalResult:
    """Test RetrievalResult dataclass."""
    
    def test_create_result(self):
        """Test creating a retrieval result."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15),
        )
        
        chunk = MemoryChunk(
            chunk_id="test_123",
            content="def hello(): pass",
            embedding=[],
            metadata=metadata,
        )
        
        result = RetrievalResult(
            chunk=chunk,
            similarity_score=0.85,
            rank=0,
        )
        
        assert result.chunk == chunk
        assert result.similarity_score == 0.85
        assert result.rank == 0
    
    def test_format_for_context_with_filepath(self):
        """Test formatting result with file path."""
        metadata = MemoryMetadata(
            source_type="code",
            phase="phase_1",
            timestamp=datetime(2024, 1, 15),
            file_path="src/main.py",
        )
        
        chunk = MemoryChunk(
            chunk_id="test_123",
            content="def hello():\n    return 'world'",
            embedding=[],
            metadata=metadata,
        )
        
        result = RetrievalResult(chunk=chunk, similarity_score=0.9, rank=0)
        formatted = result.format_for_context()
        
        assert "[Source: src/main.py" in formatted
        assert "Phase: phase_1" in formatted
        assert "2024-01-15" in formatted
        assert "def hello():" in formatted
    
    def test_format_for_context_without_filepath(self):
        """Test formatting result without file path."""
        metadata = MemoryMetadata(
            source_type="documentation",
            phase="phase_2",
            timestamp=datetime(2024, 1, 15),
        )
        
        chunk = MemoryChunk(
            chunk_id="test_123",
            content="# API Documentation\nThis is the API...",
            embedding=[],
            metadata=metadata,
        )
        
        result = RetrievalResult(chunk=chunk, similarity_score=0.8, rank=1)
        formatted = result.format_for_context()
        
        # Should use source_type when no file_path
        assert "[Source: documentation" in formatted
        assert "Phase: phase_2" in formatted
        assert "# API Documentation" in formatted
