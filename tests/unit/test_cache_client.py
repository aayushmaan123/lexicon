"""Unit tests for cache client."""

import json
from unittest.mock import MagicMock, patch

import pytest

from lexicon.infrastructure.cache_client import CacheClient


class TestCacheClient:
    """Test suite for CacheClient."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with patch("lexicon.infrastructure.cache_client.redis.from_url") as mock:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def cache_client(self, mock_redis):
        """Create cache client with mocked Redis."""
        return CacheClient()

    def test_init_success(self, mock_redis):
        """Test successful initialization."""
        client = CacheClient()
        assert client.client is not None
        mock_redis.ping.assert_called_once()

    def test_init_connection_failure(self):
        """Test initialization with connection failure."""
        with patch("lexicon.infrastructure.cache_client.redis.from_url") as mock:
            # Import redis exception from module
            from lexicon.infrastructure.cache_client import redis

            mock.side_effect = redis.ConnectionError("Connection failed")
            client = CacheClient()
            assert client.client is None

    def test_get_success(self, cache_client, mock_redis):
        """Test successful get operation."""
        mock_redis.get.return_value = "test_value"
        result = cache_client.get("test_key")
        assert result == "test_value"
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_not_found(self, cache_client, mock_redis):
        """Test get with non-existent key."""
        mock_redis.get.return_value = None
        result = cache_client.get("missing_key")
        assert result is None

    def test_get_redis_error(self, cache_client, mock_redis):
        """Test get with Redis error."""
        from lexicon.infrastructure.cache_client import redis

        mock_redis.get.side_effect = redis.RedisError("Redis error")
        result = cache_client.get("test_key")
        assert result is None

    def test_set_success(self, cache_client, mock_redis):
        """Test successful set operation."""
        cache_client.set("test_key", "test_value", ttl=300)
        mock_redis.setex.assert_called_once_with("test_key", 300, "test_value")

    def test_set_default_ttl(self, cache_client, mock_redis):
        """Test set with default TTL."""
        cache_client.set("test_key", "test_value")
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[0] == "test_key"
        assert args[2] == "test_value"

    def test_set_redis_error(self, cache_client, mock_redis):
        """Test set with Redis error."""
        from lexicon.infrastructure.cache_client import redis

        mock_redis.setex.side_effect = redis.RedisError("Redis error")
        # Should not raise exception
        cache_client.set("test_key", "test_value")

    def test_get_semantic_cache_exact_match(self, cache_client, mock_redis):
        """Test semantic cache with exact match."""
        query = "test query"
        response = "cached response"
        mock_redis.get.return_value = response

        result = cache_client.get_semantic_cache(query)
        assert result == response

    def test_get_semantic_cache_no_match(self, cache_client, mock_redis):
        """Test semantic cache with no match."""
        mock_redis.get.return_value = None
        result = cache_client.get_semantic_cache("test query")
        assert result is None

    def test_set_semantic_cache(self, cache_client, mock_redis):
        """Test setting semantic cache."""
        query = "test query"
        response = "test response"
        cache_client.set_semantic_cache(query, response, ttl=600)
        mock_redis.setex.assert_called_once()

    def test_get_embedding_cache_hit(self, cache_client, mock_redis):
        """Test embedding cache hit."""
        embedding = [0.1, 0.2, 0.3]
        mock_redis.get.return_value = json.dumps(embedding)

        result = cache_client.get_embedding_cache("test text")
        assert result == embedding

    def test_get_embedding_cache_miss(self, cache_client, mock_redis):
        """Test embedding cache miss."""
        mock_redis.get.return_value = None
        result = cache_client.get_embedding_cache("test text")
        assert result is None

    def test_get_embedding_cache_invalid_json(self, cache_client, mock_redis):
        """Test embedding cache with invalid JSON."""
        mock_redis.get.return_value = "invalid json"
        result = cache_client.get_embedding_cache("test text")
        assert result is None

    def test_set_embedding_cache(self, cache_client, mock_redis):
        """Test setting embedding cache."""
        embedding = [0.1, 0.2, 0.3]
        cache_client.set_embedding_cache("test text", embedding, ttl=600)
        mock_redis.setex.assert_called_once()

    def test_get_similarity_score(self, cache_client):
        """Test cosine similarity calculation."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        score = cache_client.get_similarity_score(emb1, emb2)
        assert score == pytest.approx(1.0)

    def test_get_similarity_score_orthogonal(self, cache_client):
        """Test similarity of orthogonal vectors."""
        emb1 = [1.0, 0.0]
        emb2 = [0.0, 1.0]
        score = cache_client.get_similarity_score(emb1, emb2)
        assert score == pytest.approx(0.0)

    def test_get_similarity_score_different_lengths(self, cache_client):
        """Test similarity with different length vectors."""
        emb1 = [1.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        score = cache_client.get_similarity_score(emb1, emb2)
        assert score == 0.0

    def test_delete(self, cache_client, mock_redis):
        """Test delete operation."""
        cache_client.delete("test_key")
        mock_redis.delete.assert_called_once_with("test_key")

    def test_flush_all(self, cache_client, mock_redis):
        """Test flush all operation."""
        cache_client.flush_all()
        mock_redis.flushdb.assert_called_once()

    def test_close(self, cache_client, mock_redis):
        """Test closing connection."""
        cache_client.close()
        mock_redis.close.assert_called_once()

    def test_operations_without_connection(self):
        """Test operations when client is not connected."""
        with patch("lexicon.infrastructure.cache_client.redis.from_url") as mock:
            from lexicon.infrastructure.cache_client import redis

            mock.side_effect = redis.ConnectionError("Connection failed")
            client = CacheClient()

            # All operations should handle None client gracefully
            assert client.get("key") is None
            client.set("key", "value")  # Should not raise
            assert client.get_semantic_cache("query") is None
            client.set_semantic_cache("query", "response")  # Should not raise
            assert client.get_embedding_cache("text") is None
            client.set_embedding_cache("text", [0.1, 0.2])  # Should not raise
            client.delete("key")  # Should not raise
            client.flush_all()  # Should not raise
