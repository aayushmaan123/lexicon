"""ChromaDB vector store implementation."""

import logging
from typing import Dict, List, Optional
from uuid import uuid4

import chromadb
from chromadb.config import Settings

from lexicon.domain.vector_store.base import VectorStore
from lexicon.shared.config import settings as app_settings

logger = logging.getLogger(__name__)


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of vector store."""

    def __init__(
        self,
        collection_name: str | None = None,
        persist_directory: str | None = None,
    ):
        """Initialize ChromaDB vector store.

        Args:
            collection_name: Name of the collection (uses settings if not provided)
            persist_directory: Directory to persist data (uses settings if not provided)
        """
        self.collection_name = collection_name or app_settings.chroma_collection_name
        self.persist_directory = (
            persist_directory or app_settings.chroma_persist_directory
        )

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection with cosine similarity
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        logger.info(
            f"Initialized ChromaDB collection '{self.collection_name}' "
            f"at {self.persist_directory}"
        )

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
        try:
            # Generate unique IDs for documents
            document_ids = [str(uuid4()) for _ in documents]

            # Extract text content from documents
            texts = [doc.get("text", str(doc)) for doc in documents]

            # Add to ChromaDB collection
            self.collection.add(
                ids=document_ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata,
            )

            logger.info(f"Added {len(document_ids)} documents to ChromaDB")
            return document_ids

        except Exception as e:
            logger.error(f"Failed to add documents to ChromaDB: {str(e)}")
            raise

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
        try:
            # Build where clause from filters
            where_clause = filters if filters else None

            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
            )

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": (
                            results["metadatas"][0][i]
                            if results["metadatas"][0]
                            else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else None
                        ),
                        "score": (
                            1 - results["distances"][0][i]
                            if results["distances"]
                            else None
                        ),
                    }
                    formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} similar documents")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search documents in ChromaDB: {str(e)}")
            raise

    def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store.

        Args:
            document_ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from ChromaDB")

        except Exception as e:
            logger.error(f"Failed to delete documents from ChromaDB: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "persist_directory": self.persist_directory,
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            raise

    def clear_collection(self) -> None:
        """Clear all documents from the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Cleared collection '{self.collection_name}'")

        except Exception as e:
            logger.error(f"Failed to clear collection: {str(e)}")
            raise
