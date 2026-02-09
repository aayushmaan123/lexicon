"""Abstract base class for vector store implementations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class VectorStore(ABC):
    """Abstract base class for vector store implementations."""

    @abstractmethod
    def add_documents(
        self,
        documents: List[Dict],
        embeddings: List[List[float]],
        metadata: List[Dict],
    ) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: List of document dictionaries containing text content
            embeddings: List of embedding vectors for each document
            metadata: List of metadata dictionaries for each document

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """Search for similar documents using a query embedding.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            filters: Optional metadata filters

        Returns:
            List of matching documents with metadata and similarity scores
        """
        pass

    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store.

        Args:
            document_ids: List of document IDs to delete
        """
        pass
