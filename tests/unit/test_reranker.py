"""Unit tests for reranker."""

import pytest

from lexicon.services.reranker import Reranker


class TestReranker:
    """Test suite for Reranker."""

    @pytest.fixture
    def reranker(self):
        """Create reranker instance."""
        return Reranker()

    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            {
                "text": "Python is a great programming language for data science",
                "score": 0.8,
                "id": "1",
            },
            {
                "text": "Machine learning requires understanding of statistics",
                "score": 0.75,
                "id": "2",
            },
            {
                "text": "Python programming language is popular",
                "score": 0.7,
                "id": "3",
            },
        ]

    def test_init_default(self):
        """Test default initialization."""
        reranker = Reranker()
        assert reranker.k1 == 1.5
        assert reranker.b == 0.75
        assert reranker.use_bm25 is True

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        reranker = Reranker(k1=2.0, b=0.5, use_bm25=False)
        assert reranker.k1 == 2.0
        assert reranker.b == 0.5
        assert reranker.use_bm25 is False

    def test_rerank_empty_documents(self, reranker):
        """Test reranking with empty document list."""
        result = reranker.rerank("test query", [], top_k=5)
        assert result == []

    def test_rerank_bm25(self, reranker, sample_documents):
        """Test BM25 reranking."""
        query = "Python programming"
        result = reranker.rerank(query, sample_documents, top_k=3)

        assert len(result) == 3
        assert all("rerank_score" in doc for doc in result)
        assert all("bm25_score" in doc for doc in result)
        # Scores should be in descending order
        scores = [doc["rerank_score"] for doc in result]
        assert scores == sorted(scores, reverse=True)

    def test_rerank_similarity(self, sample_documents):
        """Test similarity-based reranking."""
        reranker = Reranker(use_bm25=False)
        query = "Python programming"
        result = reranker.rerank(query, sample_documents, top_k=3)

        assert len(result) == 3
        assert all("rerank_score" in doc for doc in result)
        assert all("jaccard_score" in doc for doc in result)

    def test_rerank_top_k_limit(self, reranker, sample_documents):
        """Test top_k limit in reranking."""
        result = reranker.rerank("query", sample_documents, top_k=2)
        assert len(result) == 2

    def test_rerank_preserves_original_data(self, reranker, sample_documents):
        """Test that reranking preserves original document data."""
        result = reranker.rerank("query", sample_documents, top_k=3)

        for orig_doc in sample_documents:
            # Find corresponding result
            matching = [r for r in result if r.get("id") == orig_doc["id"]]
            if matching:
                assert matching[0]["text"] == orig_doc["text"]
                assert matching[0]["score"] == orig_doc["score"]

    def test_tokenize(self, reranker):
        """Test tokenization."""
        text = "This is a Test"
        tokens = reranker._tokenize(text)
        assert tokens == ["this", "is", "a", "test"]

    def test_calculate_document_frequencies(self, reranker, sample_documents):
        """Test document frequency calculation."""
        query_tokens = ["python", "programming"]
        doc_freqs = reranker._calculate_document_frequencies(
            query_tokens, sample_documents
        )

        assert "python" in doc_freqs
        assert "programming" in doc_freqs
        assert doc_freqs["python"] == 2  # Appears in 2 documents
        assert doc_freqs["programming"] == 2  # Appears in 2 documents

    def test_calculate_bm25_score(self, reranker):
        """Test BM25 score calculation."""
        query_tokens = ["python", "programming"]
        document = {"text": "Python is a programming language"}
        doc_length = 5
        avg_doc_length = 6.0
        doc_freqs = {"python": 1, "programming": 1}
        total_docs = 3

        score = reranker._calculate_bm25_score(
            query_tokens=query_tokens,
            document=document,
            doc_length=doc_length,
            avg_doc_length=avg_doc_length,
            doc_freqs=doc_freqs,
            total_docs=total_docs,
        )

        assert isinstance(score, float)
        assert score >= 0

    def test_batch_rerank(self, reranker, sample_documents):
        """Test batch reranking."""
        queries = ["Python programming", "Machine learning"]
        documents_list = [sample_documents, sample_documents]

        results = reranker.batch_rerank(queries, documents_list, top_k=2)

        assert len(results) == 2
        assert all(len(r) == 2 for r in results)

    def test_batch_rerank_mismatch(self, reranker, sample_documents):
        """Test batch rerank with mismatched lengths."""
        queries = ["query1", "query2"]
        documents_list = [sample_documents]

        with pytest.raises(ValueError):
            reranker.batch_rerank(queries, documents_list, top_k=2)

    def test_get_relevance_scores(self, reranker, sample_documents):
        """Test getting relevance scores."""
        query = "Python programming"
        scores = reranker.get_relevance_scores(query, sample_documents)

        assert len(scores) == len(sample_documents)
        assert all(isinstance(s, (int, float)) for s in scores)

    def test_rerank_handles_missing_text(self, reranker):
        """Test reranking with documents missing text field."""
        docs = [{"score": 0.8}, {"score": 0.7}]
        result = reranker.rerank("query", docs, top_k=2)
        assert len(result) == 2

    def test_rerank_handles_missing_score(self, reranker):
        """Test reranking with documents missing score field."""
        docs = [{"text": "test document 1"}, {"text": "test document 2"}]
        result = reranker.rerank("query", docs, top_k=2)
        assert len(result) == 2

    def test_rerank_combines_scores(self, reranker, sample_documents):
        """Test that rerank combines original and new scores."""
        result = reranker.rerank("query", sample_documents, top_k=3)

        for doc in result:
            assert "rerank_score" in doc
            assert "score" in doc
            # Rerank score should be influenced by both original and BM25
            assert 0 <= doc["rerank_score"] <= 1
