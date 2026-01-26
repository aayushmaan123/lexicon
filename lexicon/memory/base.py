"""Abstract base classes and data models for the RAG-based memory system."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class MemoryMetadata:
    """Metadata for filtering and attribution of memory chunks.
    
    Attributes:
        source_type: Type of content - "documentation", "code", "plan", "error", "fix", "test"
        phase: Project phase - "phase_1", "phase_2", "phase_3"
        timestamp: When the chunk was created/stored
        agent: Which agent created this (optional, None for user-provided content)
        file_path: Source file path (optional)
        language: Programming language (optional, for code chunks)
        framework: Framework name (optional, e.g., "pytest", "fastapi")
        tags: Additional categorization tags
    """
    
    source_type: str
    phase: str
    timestamp: datetime
    agent: Optional[str] = None
    file_path: Optional[str] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary format for storage.
        
        Note: Filters out None values and empty strings as ChromaDB doesn't accept them.
        """
        data = {
            "source_type": self.source_type,
            "phase": self.phase,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "file_path": self.file_path,
            "language": self.language,
            "framework": self.framework,
            "tags": ",".join(self.tags) if self.tags else "",
        }
        # Filter out None values and empty strings for ChromaDB compatibility
        return {k: v for k, v in data.items() if v is not None and v != ""}
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryMetadata":
        """Create metadata from dictionary format."""
        # Handle timestamp parsing
        timestamp = data["timestamp"]
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        # Handle tags parsing (can be string or list)
        tags_data = data.get("tags", "")
        if isinstance(tags_data, list):
            tags = tags_data
        elif isinstance(tags_data, str):
            tags = [t.strip() for t in tags_data.split(",") if t.strip()] if tags_data else []
        else:
            tags = []
        
        return cls(
            source_type=data["source_type"],
            phase=data["phase"],
            timestamp=timestamp,
            agent=data.get("agent"),
            file_path=data.get("file_path"),
            language=data.get("language"),
            framework=data.get("framework"),
            tags=tags,
        )


@dataclass
class MemoryChunk:
    """Atomic unit of stored knowledge.
    
    Attributes:
        chunk_id: Unique identifier for the chunk
        content: The actual text content
        embedding: Vector embedding of the content
        metadata: Associated metadata for filtering and attribution
    """
    
    chunk_id: str
    content: str
    embedding: list[float]
    metadata: MemoryMetadata


@dataclass
class RetrievalResult:
    """Result from a memory retrieval query.
    
    Attributes:
        chunk: The retrieved memory chunk
        similarity_score: Cosine similarity score (0-1)
        rank: Position in the result list (0-indexed)
    """
    
    chunk: MemoryChunk
    similarity_score: float
    rank: int
    
    def format_for_context(self) -> str:
        """Format the result for inclusion in agent context.
        
        Returns:
            Formatted string with metadata and content
        """
        meta = self.chunk.metadata
        source = meta.file_path or meta.source_type
        
        header = f"[Source: {source} | Phase: {meta.phase} | Timestamp: {meta.timestamp.strftime('%Y-%m-%d')}]"
        return f"{header}\n{self.chunk.content}"


class MemoryStore(ABC):
    """Abstract interface for memory storage and retrieval.
    
    This is the core interface that all storage implementations must provide.
    Agents have READ-only access, Coordinator has WRITE access.
    """
    
    @abstractmethod
    def store(self, content: str, metadata: MemoryMetadata) -> str:
        """Store a new memory chunk.
        
        Args:
            content: The text content to store
            metadata: Metadata for the chunk
            
        Returns:
            The chunk_id of the stored chunk
            
        Note:
            This method should handle deduplication by checking for
            similar chunks (similarity >0.95) and updating timestamp
            instead of creating duplicates.
        """
        pass
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> list[RetrievalResult]:
        """Retrieve memory chunks matching a query.
        
        Args:
            query: Natural language query to search for
            filters: Optional metadata filters (e.g., {"source_type": "code"})
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of retrieval results ordered by relevance
            
        Note:
            Results should be ordered by similarity score (descending).
            Only chunks with similarity >= similarity_threshold are returned.
        """
        pass
    
    @abstractmethod
    def delete(self, chunk_id: str) -> bool:
        """Delete a specific memory chunk.
        
        Args:
            chunk_id: Unique identifier of the chunk to delete
            
        Returns:
            True if chunk was deleted, False if not found
        """
        pass
    
    @abstractmethod
    def clear(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Clear memory chunks matching filters.
        
        Args:
            filters: Optional metadata filters. If None, clears ALL memory.
            
        Returns:
            Number of chunks deleted
            
        Warning:
            Calling without filters will delete ALL stored memory.
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about stored memory.
        
        Returns:
            Dictionary containing:
                - total_chunks: Total number of chunks
                - chunks_by_source_type: Breakdown by source type
                - chunks_by_phase: Breakdown by phase
                - storage_size_mb: Approximate storage size in MB
        """
        pass
