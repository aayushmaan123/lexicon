"""ChromaDB-based implementation of the memory store."""

import hashlib
import os
from datetime import datetime
from typing import Any, Callable, Optional

import chromadb
from chromadb.config import Settings

from lexicon.memory.base import MemoryChunk, MemoryMetadata, MemoryStore, RetrievalResult


# Module-level cache for embedding function
_embedding_function_cache = None


def _default_embedding_function():
    """Create the default sentence-transformers embedding function.
    
    Uses module-level caching to avoid recreating the model.
    """
    global _embedding_function_cache
    
    if _embedding_function_cache is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        _embedding_function_cache = lambda texts: model.encode(
            texts if isinstance(texts, list) else [texts]
        ).tolist()
    
    return _embedding_function_cache


class ChromaMemoryStore(MemoryStore):
    """ChromaDB implementation of the memory store.
    
    Features:
    - Vector storage using ChromaDB
    - Embeddings via sentence-transformers (all-MiniLM-L6-v2)
    - Local disk persistence
    - Metadata filtering
    - Deduplication on write
    
    Attributes:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory for local persistence
        DEDUPLICATION_THRESHOLD: Similarity threshold for detecting duplicates (0.95)
    """
    
    DEDUPLICATION_THRESHOLD = 0.95  # Threshold for detecting duplicate content
    """ChromaDB implementation of the memory store.
    
    Features:
    - Vector storage using ChromaDB
    - Embeddings via sentence-transformers (all-MiniLM-L6-v2)
    - Local disk persistence
    - Metadata filtering
    - Deduplication on write
    
    Attributes:
        collection_name: Name of the ChromaDB collection
        persist_directory: Directory for local persistence
        embedding_model: SentenceTransformer model for embeddings
    """
    
    def __init__(
        self,
        collection_name: str = "lexicon_memory",
        persist_directory: str = "./chroma_data",
        embedding_function: Optional[Callable] = None,
    ):
        """Initialize the ChromaDB memory store.
        
        Args:
            collection_name: Name for the ChromaDB collection
            persist_directory: Directory path for persistence
            embedding_function: Optional custom embedding function.
                If None, uses sentence-transformers/all-MiniLM-L6-v2
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client with persistence
        os.makedirs(persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )
        
        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )
        
        # Initialize embedding function
        if embedding_function is None:
            embedding_function = _default_embedding_function()
        self._embedding_function = embedding_function
    
    def store(self, content: str, metadata: MemoryMetadata) -> str:
        """Store a new memory chunk with deduplication.
        
        Args:
            content: The text content to store
            metadata: Metadata for the chunk
            
        Returns:
            The chunk_id of the stored chunk
        """
        # Generate embedding
        embedding = self._embedding_function(content)
        if isinstance(embedding, list) and isinstance(embedding[0], list):
            embedding = embedding[0]  # Handle batch output
        
        # Check for duplicates (similarity >0.95)
        chunk_id = self._check_duplicate(content, embedding, metadata)
        
        if chunk_id:
            # Update existing chunk's timestamp
            self._update_timestamp(chunk_id, metadata.timestamp)
            return chunk_id
        
        # Generate new chunk ID
        chunk_id = self._generate_chunk_id(content, metadata)
        
        # Prepare metadata for storage
        meta_dict = metadata.to_dict()
        
        # Store in ChromaDB
        self._collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[meta_dict],
        )
        
        return chunk_id
    
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
            filters: Optional metadata filters
            top_k: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of retrieval results ordered by relevance
        """
        # Generate query embedding
        query_embedding = self._embedding_function(query)
        if isinstance(query_embedding, list) and isinstance(query_embedding[0], list):
            query_embedding = query_embedding[0]  # Handle batch output
        
        # Build where clause from filters
        where_clause = self._build_where_clause(filters) if filters else None
        
        # Query ChromaDB
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause,
        )
        
        # Parse results
        retrieval_results = []
        
        if not results["ids"] or not results["ids"][0]:
            return retrieval_results
        
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0] if results["distances"] else None
        
        for rank, (chunk_id, doc, meta_dict) in enumerate(zip(ids, documents, metadatas)):
            # Convert distance to similarity (ChromaDB returns cosine distance)
            # For cosine distance: similarity = 1 - distance
            similarity = 1.0 - (distances[rank] if distances else 0.0)
            
            # Filter by threshold
            if similarity < similarity_threshold:
                continue
            
            # Reconstruct metadata
            metadata = MemoryMetadata.from_dict(meta_dict)
            
            # Reconstruct chunk (without embedding to save memory)
            chunk = MemoryChunk(
                chunk_id=chunk_id,
                content=doc,
                embedding=[],  # Don't return embeddings
                metadata=metadata,
            )
            
            result = RetrievalResult(
                chunk=chunk,
                similarity_score=similarity,
                rank=rank,
            )
            retrieval_results.append(result)
        
        return retrieval_results
    
    def delete(self, chunk_id: str) -> bool:
        """Delete a specific memory chunk.
        
        Args:
            chunk_id: Unique identifier of the chunk to delete
            
        Returns:
            True if chunk was deleted, False if not found
        """
        try:
            # Check if chunk exists
            result = self._collection.get(ids=[chunk_id])
            if not result["ids"]:
                return False
            
            # Delete the chunk
            self._collection.delete(ids=[chunk_id])
            return True
        except Exception:
            return False
    
    def clear(self, filters: Optional[dict[str, Any]] = None) -> int:
        """Clear memory chunks matching filters.
        
        Args:
            filters: Optional metadata filters. If None, clears ALL memory.
            
        Returns:
            Number of chunks deleted
        """
        if filters is None:
            # Clear all - delete and recreate collection
            count = self._collection.count()
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return count
        
        # Clear with filters
        where_clause = self._build_where_clause(filters)
        
        # Get all matching IDs
        results = self._collection.get(where=where_clause)
        
        if not results["ids"]:
            return 0
        
        # Delete them
        self._collection.delete(ids=results["ids"])
        return len(results["ids"])
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about stored memory.
        
        Returns:
            Dictionary with memory statistics
        """
        # Get all chunks
        all_chunks = self._collection.get()
        
        if not all_chunks["metadatas"]:
            return {
                "total_chunks": 0,
                "chunks_by_source_type": {},
                "chunks_by_phase": {},
                "storage_size_mb": 0.0,
            }
        
        total_chunks = len(all_chunks["metadatas"])
        
        # Count by source type
        chunks_by_source_type: dict[str, int] = {}
        chunks_by_phase: dict[str, int] = {}
        
        for meta in all_chunks["metadatas"]:
            source_type = meta.get("source_type", "unknown")
            phase = meta.get("phase", "unknown")
            
            chunks_by_source_type[source_type] = chunks_by_source_type.get(source_type, 0) + 1
            chunks_by_phase[phase] = chunks_by_phase.get(phase, 0) + 1
        
        # Estimate storage size (rough approximation)
        # Each embedding is 384 floats * 4 bytes = ~1.5KB
        # Plus document text
        total_text_size = sum(len(doc) for doc in all_chunks["documents"]) if all_chunks["documents"] else 0
        embedding_size = total_chunks * 384 * 4  # 384 dimensions, 4 bytes per float
        total_size_bytes = total_text_size + embedding_size
        storage_size_mb = total_size_bytes / (1024 * 1024)
        
        return {
            "total_chunks": total_chunks,
            "chunks_by_source_type": chunks_by_source_type,
            "chunks_by_phase": chunks_by_phase,
            "storage_size_mb": round(storage_size_mb, 2),
        }
    
    def _generate_chunk_id(self, content: str, metadata: MemoryMetadata) -> str:
        """Generate a unique chunk ID based on content and metadata."""
        # Use content hash + timestamp for uniqueness
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp_str = metadata.timestamp.strftime("%Y%m%d%H%M%S")
        return f"{metadata.source_type}_{timestamp_str}_{content_hash}"
    
    def _check_duplicate(
        self,
        content: str,
        embedding: list[float],
        metadata: MemoryMetadata,
    ) -> Optional[str]:
        """Check if a similar chunk already exists.
        
        Uses DEDUPLICATION_THRESHOLD (0.95) for similarity comparison.
        
        Returns:
            chunk_id if duplicate found, None otherwise
        """
        # Query for very similar chunks (top 1, high threshold)
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=1,
        )
        
        if not results["ids"] or not results["ids"][0]:
            return None
        
        # Check similarity
        distances = results["distances"][0] if results["distances"] else [1.0]
        similarity = 1.0 - distances[0]
        
        if similarity > self.DEDUPLICATION_THRESHOLD:
            return results["ids"][0][0]
        
        return None
    
    def _update_timestamp(self, chunk_id: str, timestamp: datetime) -> None:
        """Update the timestamp of an existing chunk."""
        # Get current metadata
        result = self._collection.get(ids=[chunk_id])
        
        if not result["metadatas"] or not result["metadatas"][0]:
            return
        
        # Update timestamp
        metadata = result["metadatas"][0]
        metadata["timestamp"] = timestamp.isoformat()
        
        # Update in collection
        self._collection.update(
            ids=[chunk_id],
            metadatas=[metadata],
        )
    
    def _build_where_clause(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Build a ChromaDB where clause from filters.
        
        Args:
            filters: Dictionary of filter conditions
            
        Returns:
            ChromaDB where clause
        """
        conditions = []
        
        for key, value in filters.items():
            if key.startswith("timestamp_"):
                # Skip timestamp filters for now (require special handling)
                continue
            
            if isinstance(value, list):
                # Multiple values - use $in operator
                conditions.append({key: {"$in": value}})
            else:
                # Single value - direct match
                conditions.append({key: value})
        
        if not conditions:
            return {}
        elif len(conditions) == 1:
            return conditions[0]
        else:
            # Multiple conditions - use $and
            return {"$and": conditions}
