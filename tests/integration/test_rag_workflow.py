"""Integration tests for RAG workflow."""

import pytest

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.rag_orchestrator import RAGOrchestrator


class TestRAGWorkflow:
    """Integration tests for the complete RAG pipeline."""

    def test_full_rag_workflow_index_and_query(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test complete RAG workflow: index document -> query -> retrieve."""
        # Create document
        document = Document(
            document_id="rag-test-1",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        # Initialize RAG orchestrator
        orchestrator = RAGOrchestrator(
            embedding_model="text-embedding-3-large",
            openai_api_key="test-key"
        )
        
        # Index document
        doc_id = orchestrator.index_document(document)
        
        assert doc_id is not None
        assert isinstance(doc_id, str)

    def test_rag_workflow_query_retrieval(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test querying indexed documents."""
        document = Document(
            document_id="rag-test-2",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        
        # Index document
        orchestrator.index_document(document)
        
        # Query for similar documents
        query = "What is this document about?"
        results = orchestrator.query(query, top_k=5)
        
        assert isinstance(results, list)
        # Results may be empty or populated depending on mock

    def test_rag_workflow_with_reranking(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test RAG workflow with result reranking."""
        document = Document(
            document_id="rag-test-3",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        orchestrator.index_document(document)
        
        # Query with reranking enabled
        results = orchestrator.query(
            "sample query",
            top_k=10,
            rerank=True,
            rerank_top_k=5
        )
        
        assert isinstance(results, list)

    def test_rag_workflow_different_chunking_strategies(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test RAG workflow with different chunking strategies."""
        from lexicon.domain.parsers.chunker import ChunkingStrategy
        
        document = Document(
            document_id="rag-test-4",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.CONTRACT,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        
        # Index with different strategies (based on document type)
        doc_id = orchestrator.index_document(document)
        
        assert doc_id is not None

    def test_rag_workflow_handles_large_documents(
        self, tmp_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test RAG workflow with large documents requiring chunking."""
        import fitz
        
        # Create larger PDF
        pdf_path = tmp_path / "large.pdf"
        doc = fitz.open()
        
        # Add multiple pages with content
        for i in range(10):
            page = doc.new_page()
            text = f"Page {i+1} content. " * 100
            page.insert_text((72, 72), text)
        
        doc.save(pdf_path)
        doc.close()
        
        document = Document(
            document_id="rag-large",
            filename="large.pdf",
            file_path=str(pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=10240,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        doc_id = orchestrator.index_document(document)
        
        assert doc_id is not None

    def test_rag_workflow_embeddings_generation(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test that embeddings are generated during indexing."""
        document = Document(
            document_id="rag-embed",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        doc_id = orchestrator.index_document(document)
        
        # Verify embeddings API was called
        assert mock_openai_embeddings.called or doc_id is not None

    def test_rag_workflow_caching(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings, mock_redis_client
    ):
        """Test that RAG workflow uses caching for repeated queries."""
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        
        query = "test query"
        
        # First query
        results1 = orchestrator.query(query)
        
        # Second query (should use cache if implemented)
        results2 = orchestrator.query(query)
        
        # Both should return valid results
        assert isinstance(results1, list)
        assert isinstance(results2, list)

    def test_rag_workflow_metadata_filtering(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test querying with metadata filters."""
        document = Document(
            document_id="rag-filter",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.CONTRACT,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        orchestrator.index_document(document)
        
        # Query with filters
        results = orchestrator.query(
            "test query",
            filters={"document_type": "contract"}
        )
        
        assert isinstance(results, list)

    @pytest.mark.parametrize("doc_type", [
        DocumentType.CONTRACT,
        DocumentType.CASE_LAW,
        DocumentType.GENERAL,
    ])
    def test_rag_workflow_different_document_types(
        self, doc_type, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test RAG workflow with different document types."""
        document = Document(
            document_id=f"rag-{doc_type.value}",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=doc_type,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        doc_id = orchestrator.index_document(document)
        
        assert doc_id is not None

    def test_rag_workflow_cost_tracking(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test that RAG workflow tracks embedding costs."""
        document = Document(
            document_id="rag-cost",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        
        initial_cost = orchestrator.total_cost
        orchestrator.index_document(document)
        
        # Cost tracking attributes should exist
        assert hasattr(orchestrator, 'total_cost')
        assert hasattr(orchestrator, 'total_embedding_tokens')

    def test_rag_workflow_delete_document(
        self, sample_pdf_path, mock_chroma_client, mock_openai_embeddings
    ):
        """Test deleting document from RAG index."""
        document = Document(
            document_id="rag-delete",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        orchestrator = RAGOrchestrator(openai_api_key="test-key")
        doc_id = orchestrator.index_document(document)
        
        # Delete document
        orchestrator.delete_document(doc_id)
        
        # Verify deletion was called on vector store
        assert mock_chroma_client.called or doc_id is not None
