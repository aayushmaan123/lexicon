"""Retrieval logic and context assembly for memory queries."""

from datetime import datetime, timedelta
from typing import Any, Optional

from lexicon.memory.base import MemoryStore, RetrievalResult


class MemoryRetriever:
    """High-level retrieval interface with context assembly.
    
    This class wraps the MemoryStore and provides convenient methods
    for agents to query memory with proper filtering and formatting.
    
    Features:
    - Query embedding and similarity search (delegated to store)
    - Metadata filtering
    - Reranking by recency and relevance
    - Context assembly with token budget management
    - Result deduplication
    
    Attributes:
        store: The underlying memory store
        max_context_tokens: Maximum tokens for assembled context (default: 2000)
    """
    
    def __init__(self, store: MemoryStore, max_context_tokens: int = 2000):
        """Initialize the memory retriever.
        
        Args:
            store: The memory store implementation
            max_context_tokens: Maximum tokens for context assembly
        """
        self.store = store
        self.max_context_tokens = max_context_tokens
    
    def retrieve_context(
        self,
        query: str,
        source_type: Optional[str] = None,
        phase: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        agent: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        prefer_recent: bool = True,
        recency_days: int = 30,
    ) -> list[RetrievalResult]:
        """Retrieve and assemble context for a query.
        
        Args:
            query: Natural language query
            source_type: Filter by source type (e.g., "code", "documentation")
            phase: Filter by phase (e.g., "phase_1")
            language: Filter by programming language
            framework: Filter by framework
            agent: Filter by agent that created the chunk
            top_k: Maximum results to return
            similarity_threshold: Minimum similarity score
            prefer_recent: Whether to boost scores of recent chunks
            recency_days: Consider chunks within this many days as "recent"
            
        Returns:
            List of retrieval results ordered by relevance
        """
        # Build filters
        filters = self._build_filters(
            source_type=source_type,
            phase=phase,
            language=language,
            framework=framework,
            agent=agent,
        )
        
        # Query the store
        results = self.store.retrieve(
            query=query,
            filters=filters,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
        
        # Rerank if requested
        if prefer_recent and results:
            results = self._rerank_by_recency(results, recency_days)
        
        # Deduplicate
        results = self._deduplicate(results)
        
        return results
    
    def retrieve_similar_errors(
        self,
        error_message: str,
        top_k: int = 5,
        include_fixes: bool = True,
    ) -> list[RetrievalResult]:
        """Retrieve similar error patterns and fixes.
        
        Args:
            error_message: The error message to search for
            top_k: Maximum results to return
            include_fixes: Whether to include fix patterns
            
        Returns:
            List of similar error patterns
        """
        source_types = ["error"]
        if include_fixes:
            source_types.append("fix")
        
        filters = {"source_type": source_types}
        
        results = self.store.retrieve(
            query=error_message,
            filters=filters,
            top_k=top_k,
            similarity_threshold=0.6,  # Lower threshold for error matching
        )
        
        return results
    
    def retrieve_code_examples(
        self,
        query: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Retrieve code examples matching a query.
        
        Args:
            query: Natural language description of desired code
            language: Filter by programming language
            framework: Filter by framework
            top_k: Maximum results to return
            
        Returns:
            List of code examples
        """
        filters = {"source_type": "code"}
        
        if language:
            filters["language"] = language
        if framework:
            filters["framework"] = framework
        
        results = self.store.retrieve(
            query=query,
            filters=filters,
            top_k=top_k,
            similarity_threshold=0.7,
        )
        
        return results
    
    def assemble_context(
        self,
        results: list[RetrievalResult],
        include_metadata: bool = True,
    ) -> str:
        """Assemble retrieval results into formatted context.
        
        Args:
            results: List of retrieval results
            include_metadata: Whether to include metadata headers
            
        Returns:
            Formatted context string ready for LLM consumption
        """
        if not results:
            return ""
        
        sections = []
        total_tokens = 0
        
        for result in results:
            if include_metadata:
                formatted = result.format_for_context()
            else:
                formatted = result.chunk.content
            
            # Rough token estimation (1 token ≈ 4 characters)
            chunk_tokens = len(formatted) // 4
            
            if total_tokens + chunk_tokens > self.max_context_tokens:
                # Would exceed budget, stop here
                break
            
            sections.append(formatted)
            total_tokens += chunk_tokens
        
        if not sections:
            return ""
        
        # Assemble with header
        context = "Retrieved Context:\n\n" + "\n\n---\n\n".join(sections)
        return context
    
    def _build_filters(
        self,
        source_type: Optional[str] = None,
        phase: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        agent: Optional[str] = None,
    ) -> dict[str, Any]:
        """Build filter dictionary from parameters."""
        filters: dict[str, Any] = {}
        
        if source_type:
            filters["source_type"] = source_type
        if phase:
            filters["phase"] = phase
        if language:
            filters["language"] = language
        if framework:
            filters["framework"] = framework
        if agent:
            filters["agent"] = agent
        
        return filters
    
    def _rerank_by_recency(
        self,
        results: list[RetrievalResult],
        recency_days: int,
    ) -> list[RetrievalResult]:
        """Rerank results to prefer recent chunks.
        
        Strategy:
        - Boost similarity scores of chunks from last N days by 10%
        - Maintain relative ordering within recent/old groups
        
        Args:
            results: Original results
            recency_days: Number of days to consider "recent"
            
        Returns:
            Reranked results
        """
        cutoff_date = datetime.now() - timedelta(days=recency_days)
        
        # Apply recency boost
        boosted_results = []
        for result in results:
            chunk_date = result.chunk.metadata.timestamp
            
            if chunk_date >= cutoff_date:
                # Recent chunk - boost score
                boosted_score = min(1.0, result.similarity_score * 1.1)
                boosted_result = RetrievalResult(
                    chunk=result.chunk,
                    similarity_score=boosted_score,
                    rank=result.rank,
                )
                boosted_results.append(boosted_result)
            else:
                boosted_results.append(result)
        
        # Re-sort by boosted scores
        boosted_results.sort(key=lambda r: r.similarity_score, reverse=True)
        
        # Update ranks
        for rank, result in enumerate(boosted_results):
            result.rank = rank
        
        return boosted_results
    
    def _deduplicate(self, results: list[RetrievalResult]) -> list[RetrievalResult]:
        """Remove duplicate chunks based on content similarity.
        
        Strategy:
        - Compare each result with all previous results
        - If content is >90% similar, skip the later one
        - Prefer higher-ranked (more relevant) chunks
        
        Args:
            results: Original results
            
        Returns:
            Deduplicated results
        """
        if len(results) <= 1:
            return results
        
        deduplicated = []
        
        for result in results:
            is_duplicate = False
            
            for existing in deduplicated:
                if self._are_similar_contents(result.chunk.content, existing.chunk.content):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        return deduplicated
    
    def _are_similar_contents(self, content1: str, content2: str, threshold: float = 0.9) -> bool:
        """Check if two content strings are very similar.
        
        Uses simple character-level similarity (Jaccard).
        For production, could use more sophisticated methods.
        
        Args:
            content1: First content string
            content2: Second content string
            threshold: Similarity threshold (0-1)
            
        Returns:
            True if contents are similar
        """
        # Simple length check first
        len1, len2 = len(content1), len(content2)
        if abs(len1 - len2) / max(len1, len2) > 0.2:
            # Lengths differ by >20%, likely not duplicates
            return False
        
        # Character-level Jaccard similarity
        set1 = set(content1)
        set2 = set(content2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        if union == 0:
            return True  # Both empty
        
        similarity = intersection / union
        return similarity >= threshold
