"""Unit tests for RAG orchestrator."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.rag_orchestrator import RAGOrchestrator


class TestRAGOrchestrator:
    """Test suite for RAGOrchestrator."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch("lexicon.services.rag_orchestrator.OpenAI") as mock:
            client = MagicMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def mock_vector_store(self):
        """Mock ChromaVectorStore."""
        mock = MagicMock()
        mock.get_collection_stats.return_value = {
            "name": "test_collection",
            "count": 0,
        }
        return mock

    @pytest.fixture
    def mock_cache_client(self):
        """Mock CacheClient."""
        mock = MagicMock()
        mock.get_semantic_cache.return_value = None
        mock.get_embedding_cache.return_value = None
        return mock

    @pytest.fixture
    def mock_reranker(self):
        """Mock Reranker."""
        return MagicMock()

    @pytest.fixture
    def orchestrator(
        self,
        mock_openai_client,
        mock_vector_store,
        mock_cache_client,
        mock_reranker,
    ):
        """Create RAG orchestrator with mocked dependencies."""
        return RAGOrchestrator(
            vector_store=mock_vector_store,
            cache_client=mock_cache_client,
            reranker=mock_reranker,
        )

    @pytest.fixture
    def sample_document(self):
        """Sample document for testing."""
        return Document(
            id="test-123",
            filename="test.pdf",
            file_path="/tmp/test.pdf",
            file_size=1024,
            document_type=DocumentType.GENERAL,
        )

    def test_init(self, orchestrator):
        """Test initialization."""
        assert orchestrator.embedding_model is not None
        assert orchestrator.vector_store is not None
        assert orchestrator.cache_client is not None
        assert orchestrator.reranker is not None

    def test_index_document_unsupported_type(self, orchestrator):
        """Test indexing with unsupported file type."""
        doc = Document(
            id="test",
            filename="test.txt",
            file_path="/tmp/test.txt",
            file_size=100,
            document_type=DocumentType.GENERAL,
        )

        with pytest.raises(ValueError, match="Unsupported file type"):
            orchestrator.index_document(doc)

    @patch("lexicon.services.rag_orchestrator.PDFParser")
    @patch("lexicon.services.rag_orchestrator.sliding_window_chunker")
    def test_index_document_pdf(
        self,
        mock_chunker,
        mock_parser_class,
        orchestrator,
        sample_document,
        mock_openai_client,
    ):
        """Test indexing a PDF document."""
        # Setup mocks
        parsed_doc = MagicMock()
        parsed_doc.full_text = "Test document content"
        parsed_doc.document_id = "test-123"

        mock_parser = MagicMock()
        mock_parser.parse.return_value = parsed_doc
        mock_parser_class.return_value = mock_parser
        orchestrator.parsers["pdf"] = mock_parser

        chunk = MagicMock()
        chunk.content = "Test chunk"
        chunk.chunk_id = "chunk-1"
        chunk.document_id = "test-123"
        chunk.chunk_index = 0
        chunk.token_count = 10
        chunk.metadata = {"filename": "test.pdf", "document_type": "general"}
        chunk.page_number = None
        chunk.section_title = None
        mock_chunker.return_value = [chunk]

        # Mock embedding response
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        embedding_response.usage.total_tokens = 10
        mock_openai_client.embeddings.create.return_value = embedding_response

        # Execute
        doc_id = orchestrator.index_document(sample_document)

        # Verify
        assert doc_id == "test-123"
        mock_parser.parse.assert_called_once()
        mock_chunker.assert_called_once()
        orchestrator.vector_store.add_documents.assert_called_once()

    def test_query_with_cache_hit(
        self,
        orchestrator,
        mock_cache_client,
    ):
        """Test query with cache hit."""
        import json

        cached_results = [{"text": "cached result", "score": 0.9}]
        mock_cache_client.get_semantic_cache.return_value = json.dumps(cached_results)

        result = orchestrator.query("test query", top_k=5)

        assert result == cached_results
        mock_cache_client.get_semantic_cache.assert_called_once()

    def test_query_no_cache(
        self,
        orchestrator,
        mock_cache_client,
        mock_openai_client,
        mock_vector_store,
        mock_reranker,
    ):
        """Test query without cache hit."""
        # Mock embedding response
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        embedding_response.usage.total_tokens = 5
        mock_openai_client.embeddings.create.return_value = embedding_response

        # Mock search results
        search_results = [
            {"text": "result 1", "score": 0.9},
            {"text": "result 2", "score": 0.8},
        ]
        mock_vector_store.search.return_value = search_results

        # Mock reranker
        mock_reranker.rerank.return_value = search_results

        result = orchestrator.query("test query", top_k=2, rerank=True)

        assert len(result) == 2
        mock_vector_store.search.assert_called_once()
        mock_reranker.rerank.assert_called_once()
        mock_cache_client.set_semantic_cache.assert_called_once()

    def test_query_no_rerank(
        self,
        orchestrator,
        mock_openai_client,
        mock_vector_store,
        mock_reranker,
    ):
        """Test query without reranking."""
        # Mock embedding response
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        embedding_response.usage.total_tokens = 5
        mock_openai_client.embeddings.create.return_value = embedding_response

        # Mock search results
        search_results = [{"text": "result 1", "score": 0.9}]
        mock_vector_store.search.return_value = search_results

        result = orchestrator.query("test query", top_k=1, rerank=False)

        assert len(result) == 1
        mock_reranker.rerank.assert_not_called()

    def test_query_with_filters(
        self,
        orchestrator,
        mock_openai_client,
        mock_vector_store,
    ):
        """Test query with metadata filters."""
        # Mock embedding response
        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        embedding_response.usage.total_tokens = 5
        mock_openai_client.embeddings.create.return_value = embedding_response

        mock_vector_store.search.return_value = []

        filters = {"document_type": "contract"}
        orchestrator.query("test query", top_k=5, filters=filters, rerank=False)

        # Verify filters were passed
        call_args = mock_vector_store.search.call_args
        assert call_args[1]["filters"] == filters

    def test_assemble_context_empty(self, orchestrator):
        """Test assembling context with empty results."""
        context = orchestrator.assemble_context("test query", [])
        assert context == ""

    def test_assemble_context_with_results(self, orchestrator):
        """Test assembling context with results."""
        results = [
            {
                "text": "Result 1 content",
                "score": 0.9,
                "metadata": {"filename": "doc1.pdf", "chunk_index": 0},
            },
            {
                "text": "Result 2 content",
                "score": 0.8,
                "metadata": {"filename": "doc2.pdf", "chunk_index": 1},
            },
        ]

        context = orchestrator.assemble_context("test query", results)

        assert "test query" in context
        assert "Result 1 content" in context
        assert "Result 2 content" in context
        assert "doc1.pdf" in context
        assert "doc2.pdf" in context

    def test_assemble_context_max_length(self, orchestrator):
        """Test context assembly with max length limit."""
        results = [
            {
                "text": "A" * 2000,
                "score": 0.9,
                "metadata": {},
            },
            {
                "text": "B" * 2000,
                "score": 0.8,
                "metadata": {},
            },
            {
                "text": "C" * 2000,
                "score": 0.7,
                "metadata": {},
            },
        ]

        context = orchestrator.assemble_context(
            "test query", results, max_context_length=3000
        )

        # Should include query and at least first result, but not all
        assert len(context) <= 3000

    def test_generate_embeddings_with_cache(
        self,
        orchestrator,
        mock_cache_client,
    ):
        """Test embedding generation with cache hit."""
        chunks = [MagicMock(content="test content", chunk_id="chunk-1")]
        cached_embedding = [0.1, 0.2, 0.3]
        mock_cache_client.get_embedding_cache.return_value = cached_embedding

        embeddings = orchestrator._generate_embeddings(chunks)

        assert embeddings == [cached_embedding]
        mock_cache_client.get_embedding_cache.assert_called_once()

    def test_generate_embeddings_without_cache(
        self,
        orchestrator,
        mock_cache_client,
        mock_openai_client,
    ):
        """Test embedding generation without cache."""
        chunks = [MagicMock(content="test content", chunk_id="chunk-1")]
        mock_cache_client.get_embedding_cache.return_value = None

        embedding_response = MagicMock()
        embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        embedding_response.usage.total_tokens = 5
        mock_openai_client.embeddings.create.return_value = embedding_response

        embeddings = orchestrator._generate_embeddings(chunks)

        assert len(embeddings) == 1
        mock_cache_client.set_embedding_cache.assert_called_once()

    def test_get_stats(self, orchestrator):
        """Test getting usage statistics."""
        orchestrator.total_embedding_tokens = 1000
        orchestrator.total_cost = 0.05

        stats = orchestrator.get_stats()

        assert stats["total_embedding_tokens"] == 1000
        assert stats["total_cost"] == 0.05
        assert "embedding_model" in stats
        assert "vector_store_stats" in stats

    def test_reset_stats(self, orchestrator):
        """Test resetting statistics."""
        orchestrator.total_embedding_tokens = 1000
        orchestrator.total_cost = 0.05

        orchestrator.reset_stats()

        assert orchestrator.total_embedding_tokens == 0
        assert orchestrator.total_cost == 0.0

    def test_calculate_embedding_cost(self, orchestrator):
        """Test cost calculation."""
        cost = orchestrator._calculate_embedding_cost(1000000)
        assert cost > 0
        assert isinstance(cost, float)

    def test_chunk_document_contract(self, orchestrator):
        """Test chunking for contract documents."""
        from lexicon.domain.entities.document import ParsedDocument

        parsed_doc = ParsedDocument(
            document_id="test",
            filename="test.pdf",
            document_type=DocumentType.CONTRACT,
            full_text="This is a test contract.",
        )

        with patch("lexicon.services.rag_orchestrator.clause_aware_chunker") as mock:
            mock.return_value = []
            orchestrator._chunk_document(parsed_doc, DocumentType.CONTRACT)
            mock.assert_called_once()

    def test_chunk_document_case_law(self, orchestrator):
        """Test chunking for case law documents."""
        from lexicon.domain.entities.document import ParsedDocument

        parsed_doc = ParsedDocument(
            document_id="test",
            filename="test.pdf",
            document_type=DocumentType.CASE_LAW,
            full_text="This is case law.",
        )

        with patch("lexicon.services.rag_orchestrator.section_based_chunker") as mock:
            mock.return_value = []
            orchestrator._chunk_document(parsed_doc, DocumentType.CASE_LAW)
            mock.assert_called_once()

    def test_chunk_document_general(self, orchestrator):
        """Test chunking for general documents."""
        from lexicon.domain.entities.document import ParsedDocument

        parsed_doc = ParsedDocument(
            document_id="test",
            filename="test.pdf",
            document_type=DocumentType.GENERAL,
            full_text="This is a general document.",
        )

        with patch("lexicon.services.rag_orchestrator.sliding_window_chunker") as mock:
            mock.return_value = []
            orchestrator._chunk_document(parsed_doc, DocumentType.GENERAL)
            mock.assert_called_once()
