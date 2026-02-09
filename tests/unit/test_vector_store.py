"""Unit tests for ChromaVectorStore."""

import pytest

from lexicon.infrastructure.chroma_client import ChromaVectorStore


class TestChromaVectorStore:
    """Test suite for ChromaVectorStore."""

    def test_init_creates_collection(self, mock_chroma_client):
        """Test initialization creates or gets collection."""
        store = ChromaVectorStore(
            collection_name="test_collection",
            persist_directory="./test_data"
        )
        
        assert store.collection_name == "test_collection"
        assert store.persist_directory == "./test_data"
        assert store.collection is not None

    def test_add_documents_success(self, mock_vector_store, sample_embedding):
        """Test adding documents to vector store."""
        documents = [
            {"text": "Document 1"},
            {"text": "Document 2"},
        ]
        embeddings = [sample_embedding, sample_embedding]
        metadata = [
            {"source": "test1.pdf", "page": 1},
            {"source": "test2.pdf", "page": 1},
        ]
        
        doc_ids = mock_vector_store.add_documents(documents, embeddings, metadata)
        
        assert len(doc_ids) == 2
        assert all(isinstance(doc_id, str) for doc_id in doc_ids)

    def test_add_documents_empty_list(self, mock_vector_store):
        """Test adding empty list of documents."""
        doc_ids = mock_vector_store.add_documents([], [], [])
        
        assert doc_ids == []

    def test_search_returns_results(self, mock_vector_store, sample_embedding):
        """Test searching returns formatted results."""
        results = mock_vector_store.search(
            query_embedding=sample_embedding,
            top_k=5
        )
        
        assert isinstance(results, list)
        assert len(results) == 2
        assert "id" in results[0]
        assert "text" in results[0]
        assert "metadata" in results[0]
        assert "score" in results[0]

    def test_search_with_filters(self, mock_vector_store, sample_embedding):
        """Test searching with metadata filters."""
        filters = {"source": "test1.pdf"}
        
        results = mock_vector_store.search(
            query_embedding=sample_embedding,
            top_k=5,
            filters=filters
        )
        
        assert isinstance(results, list)

    def test_search_calculates_similarity_score(self, mock_vector_store, sample_embedding):
        """Test that search calculates similarity scores from distances."""
        results = mock_vector_store.search(
            query_embedding=sample_embedding,
            top_k=2
        )
        
        # Score should be 1 - distance
        assert results[0]["score"] == pytest.approx(1 - 0.1)
        assert results[1]["score"] == pytest.approx(1 - 0.2)

    def test_delete_documents_success(self, mock_vector_store):
        """Test deleting documents from vector store."""
        doc_ids = ["doc1", "doc2", "doc3"]
        
        # Should not raise an error
        mock_vector_store.delete_documents(doc_ids)
        
        # Verify delete was called
        mock_vector_store.collection.delete.assert_called_once()

    def test_get_collection_stats_returns_info(self, mock_vector_store):
        """Test getting collection statistics."""
        stats = mock_vector_store.get_collection_stats()
        
        assert "name" in stats
        assert "count" in stats
        assert "persist_directory" in stats
        assert stats["name"] == "test_collection"

    def test_clear_collection_recreates_collection(self, mock_vector_store):
        """Test clearing collection deletes and recreates it."""
        mock_vector_store.clear_collection()
        
        # Verify collection was deleted and recreated
        mock_vector_store.client.delete_collection.assert_called_once_with(
            name="test_collection"
        )
        mock_vector_store.client.create_collection.assert_called_once()

    @pytest.mark.parametrize("top_k", [1, 5, 10, 20])
    def test_search_respects_top_k_parameter(self, mock_vector_store, sample_embedding, top_k):
        """Test that search respects top_k parameter."""
        results = mock_vector_store.search(
            query_embedding=sample_embedding,
            top_k=top_k
        )
        
        # Verify top_k was passed to query
        call_args = mock_vector_store.collection.query.call_args
        assert call_args[1]["n_results"] == top_k

    def test_add_documents_extracts_text_from_dict(self, mock_vector_store, sample_embedding):
        """Test that add_documents extracts text field from document dicts."""
        documents = [
            {"text": "Content 1", "other": "data"},
            {"text": "Content 2", "other": "data"},
        ]
        embeddings = [sample_embedding, sample_embedding]
        metadata = [{}, {}]
        
        doc_ids = mock_vector_store.add_documents(documents, embeddings, metadata)
        
        # Verify texts were extracted correctly
        call_args = mock_vector_store.collection.add.call_args
        assert call_args[1]["documents"] == ["Content 1", "Content 2"]

    def test_search_handles_empty_results(self, mock_vector_store, sample_embedding):
        """Test that search handles empty results gracefully."""
        # Mock empty results
        mock_vector_store.collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }
        
        results = mock_vector_store.search(sample_embedding)
        
        assert results == []

    def test_search_handles_missing_metadata(self, mock_vector_store, sample_embedding):
        """Test that search handles missing metadata gracefully."""
        # Mock results with None metadata
        mock_vector_store.collection.query.return_value = {
            "ids": [["doc1"]],
            "documents": [["Text"]],
            "metadatas": [[None]],
            "distances": [[0.5]],
        }
        
        results = mock_vector_store.search(sample_embedding)
        
        assert len(results) == 1
        assert results[0]["metadata"] == {}
