"""Abstract interfaces for Retrieval-Augmented Generation (RAG).

This module defines provider-agnostic interfaces for RAG operations including
vector storage, document retrieval, and semantic search.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from uuid import UUID

from lexicon.domain.entities.core import Document


@dataclass(frozen=True)
class VectorSearchConfig:
    """Configuration for vector search operations.

    Attributes:
        top_k: Number of top results to return
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        metadata_filter: Optional metadata filters
        rerank: Whether to apply re-ranking
    """

    top_k: int = 5
    similarity_threshold: float = 0.7
    metadata_filter: dict[str, Any] | None = None
    rerank: bool = False


@dataclass(frozen=True)
class SearchResult:
    """Result from vector search operation.

    Attributes:
        document: Retrieved document
        score: Similarity score
        metadata: Additional result metadata
    """

    document: Document
    score: float
    metadata: dict[str, Any] | None = None


class IVectorStore(ABC):
    """Abstract interface for vector storage providers.

    Implementations can use Pinecone, Weaviate, Qdrant, FAISS, etc.
    This interface ensures the RAG layer remains provider-agnostic.
    """

    @abstractmethod
    async def add_document(
        self,
        document: Document,
        embedding: list[float],
    ) -> str:
        """Add a document with its embedding to the vector store.

        Args:
            document: Document to store
            embedding: Vector embedding of the document

        Returns:
            Embedding ID for reference

        Raises:
            VectorStoreError: If storage fails
        """
        pass

    @abstractmethod
    async def search(
        self,
        query_embedding: list[float],
        config: Optional[VectorSearchConfig] = None,
    ) -> list[SearchResult]:
        """Search for similar documents using vector similarity.

        Args:
            query_embedding: Query vector embedding
            config: Optional search configuration

        Returns:
            List of search results ordered by similarity

        Raises:
            VectorStoreError: If search fails
        """
        pass

    @abstractmethod
    async def delete_document(self, embedding_id: str) -> bool:
        """Delete a document from the vector store.

        Args:
            embedding_id: ID of the embedding to delete

        Returns:
            True if deletion successful, False otherwise

        Raises:
            VectorStoreError: If deletion fails
        """
        pass

    @abstractmethod
    async def get_document(self, embedding_id: str) -> Optional[Document]:
        """Retrieve a document by its embedding ID.

        Args:
            embedding_id: ID of the embedding

        Returns:
            Document if found, None otherwise

        Raises:
            VectorStoreError: If retrieval fails
        """
        pass


class IDocumentRetriever(ABC):
    """Abstract interface for document retrieval strategies.

    This interface defines how documents are retrieved for RAG operations.
    Implementations can use hybrid search, re-ranking, or other strategies.
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        config: Optional[VectorSearchConfig] = None,
    ) -> list[SearchResult]:
        """Retrieve relevant documents for a query.

        Args:
            query: Query text
            config: Optional retrieval configuration

        Returns:
            List of relevant documents with scores

        Raises:
            RetrievalError: If retrieval fails
        """
        pass


class IRAGPipeline(ABC):
    """Abstract interface for complete RAG pipeline.

    This interface orchestrates the full RAG workflow:
    1. Query processing
    2. Document retrieval
    3. Context augmentation
    4. Response generation
    """

    @abstractmethod
    async def query(
        self,
        query_text: str,
        config: Optional[VectorSearchConfig] = None,
    ) -> tuple[str, list[Document]]:
        """Execute RAG query and return response with sources.

        Args:
            query_text: User query
            config: Optional RAG configuration

        Returns:
            Tuple of (generated_response, source_documents)

        Raises:
            RAGError: If pipeline fails
        """
        pass
