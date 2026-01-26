"""Integration tests for knowledge base API endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from lexicon.api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestKnowledgeBaseAPI:
    """Test suite for knowledge base API endpoints."""

    def test_index_document_success(
        self, client, sample_pdf_path, mock_openai_embeddings, mock_chroma_client
    ):
        """Test indexing document to knowledge base."""
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("document.pdf", f, "application/pdf")}
            
            with patch("lexicon.api.routes.knowledge_base.RAGOrchestrator") as mock_rag:
                mock_instance = Mock()
                mock_instance.index_document.return_value = "doc-123"
                mock_rag.return_value = mock_instance
                
                response = client.post("/api/v1/knowledge-base/index", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data

    def test_query_knowledge_base_success(
        self, client, mock_openai_embeddings, mock_chroma_client
    ):
        """Test querying knowledge base."""
        with patch("lexicon.api.routes.knowledge_base.RAGOrchestrator") as mock_rag:
            mock_instance = Mock()
            mock_instance.query.return_value = [
                {
                    "text": "Relevant text chunk",
                    "metadata": {"source": "doc1.pdf"},
                    "score": 0.95
                }
            ]
            mock_rag.return_value = mock_instance
            
            response = client.post(
                "/api/v1/knowledge-base/query",
                json={"query": "What is contract law?", "top_k": 5}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_delete_document_success(self, client, mock_chroma_client):
        """Test deleting document from knowledge base."""
        with patch("lexicon.api.routes.knowledge_base.RAGOrchestrator") as mock_rag:
            mock_instance = Mock()
            mock_instance.delete_document.return_value = None
            mock_rag.return_value = mock_instance
            
            response = client.delete("/api/v1/knowledge-base/documents/doc-123")
        
        assert response.status_code == 200

    def test_get_stats_success(self, client, mock_chroma_client):
        """Test getting knowledge base statistics."""
        with patch("lexicon.api.routes.knowledge_base.RAGOrchestrator") as mock_rag:
            mock_instance = Mock()
            mock_instance.vector_store.get_collection_stats.return_value = {
                "name": "lexicon_documents",
                "count": 42,
                "persist_directory": "./chroma_data"
            }
            mock_rag.return_value = mock_instance
            
            response = client.get("/api/v1/knowledge-base/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "count" in data

    def test_query_with_filters(self, client, mock_chroma_client, mock_openai_embeddings):
        """Test querying with metadata filters."""
        with patch("lexicon.api.routes.knowledge_base.RAGOrchestrator") as mock_rag:
            mock_instance = Mock()
            mock_instance.query.return_value = []
            mock_rag.return_value = mock_instance
            
            response = client.post(
                "/api/v1/knowledge-base/query",
                json={
                    "query": "test query",
                    "top_k": 10,
                    "filters": {"document_type": "contract"}
                }
            )
        
        assert response.status_code == 200
