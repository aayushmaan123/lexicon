"""Redis cache client for embedding and semantic caching."""

import hashlib
import json
import logging
import math

import redis

from lexicon.shared.config import settings

logger = logging.getLogger(__name__)


class CacheClient:
    """Redis cache client with support for semantic caching and embedding caching."""

    def __init__(
        self,
        redis_url: str | None = None,
        ttl: int | None = None,
    ):
        """Initialize Redis cache client.

        Args:
            redis_url: Redis connection URL (uses settings if not provided)
            ttl: Default TTL in seconds (uses settings if not provided)
        """
        self.redis_url = redis_url or settings.redis_url
        self.default_ttl = ttl or settings.redis_ttl
        self.client = None
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Redis with error handling."""
        try:
            self.client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            # Test connection
            self.client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {str(e)}")
            self.client = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {str(e)}")
            self.client = None

    def get(self, key: str) -> str | None:
        """Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or connection failed
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
            return value
        except redis.RedisError as e:
            logger.warning(f"Redis get failed for key {key}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting key {key}: {str(e)}")
            return None

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        """Set cached value with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        if not self.client:
            logger.debug("Cache client not available, skipping set operation")
            return

        try:
            cache_ttl = ttl or self.default_ttl
            self.client.setex(key, cache_ttl, value)
            logger.debug(f"Cached value for key: {key} with TTL: {cache_ttl}s")
        except redis.RedisError as e:
            logger.warning(f"Redis set failed for key {key}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error setting key {key}: {str(e)}")

    def get_semantic_cache(self, query: str, threshold: float = 0.95) -> str | None:
        """Look up semantically similar query in cache.

        This method searches for cached queries that are semantically similar
        to the input query based on cosine similarity of their embeddings.

        Args:
            query: Query text to search for
            threshold: Similarity threshold (0-1) for cache hit

        Returns:
            Cached response if similar query found, None otherwise
        """
        if not self.client:
            return None

        try:
            # Generate query hash for exact match lookup
            query_hash = self._hash_text(query)
            cache_key = f"semantic_cache:{query_hash}"

            # Try exact match first
            cached_value = self.get(cache_key)
            if cached_value:
                logger.info("Semantic cache: exact match found")
                return cached_value

            # For semantic similarity search, we would need:
            # 1. Query embedding
            # 2. Redis vector similarity search (requires RedisSearch/RediStack)
            # For now, we only support exact match
            # TODO: Implement true semantic search with RedisSearch or similar
            logger.debug("Semantic cache: no exact match found")
            return None

        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {str(e)}")
            return None

    def set_semantic_cache(self, query: str, response: str, ttl: int | None = None) -> None:
        """Cache a query-response pair for semantic lookup.

        Args:
            query: Query text
            response: Response to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        if not self.client:
            return

        try:
            query_hash = self._hash_text(query)
            cache_key = f"semantic_cache:{query_hash}"
            self.set(cache_key, response, ttl)
            logger.debug(f"Stored semantic cache for query hash: {query_hash}")
        except Exception as e:
            logger.warning(f"Failed to set semantic cache: {str(e)}")

    def get_embedding_cache(self, text: str) -> list[float] | None:
        """Get cached embedding for text.

        Args:
            text: Text to look up

        Returns:
            Cached embedding vector or None if not found
        """
        if not self.client:
            return None

        try:
            text_hash = self._hash_text(text)
            cache_key = f"embedding:{text_hash}"
            cached_value = self.get(cache_key)

            if cached_value:
                embedding = json.loads(cached_value)
                logger.debug(f"Embedding cache hit for text hash: {text_hash}")
                return embedding

            return None

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to decode cached embedding: {str(e)}")
            return None
        except Exception as e:
            logger.warning(f"Embedding cache lookup failed: {str(e)}")
            return None

    def set_embedding_cache(
        self, text: str, embedding: list[float], ttl: int | None = None
    ) -> None:
        """Cache an embedding vector for text.

        Args:
            text: Text that was embedded
            embedding: Embedding vector to cache
            ttl: Time-to-live in seconds (uses default if not provided)
        """
        if not self.client:
            return

        try:
            text_hash = self._hash_text(text)
            cache_key = f"embedding:{text_hash}"
            embedding_json = json.dumps(embedding)
            self.set(cache_key, embedding_json, ttl)
            logger.debug(f"Cached embedding for text hash: {text_hash}")
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {str(e)}")

    def get_similarity_score(self, embedding1: list[float], embedding2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            if len(embedding1) != len(embedding2):
                raise ValueError("Embeddings must have the same dimension")

            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=True))

            # Calculate norms
            norm1 = math.sqrt(sum(a * a for a in embedding1))
            norm2 = math.sqrt(sum(b * b for b in embedding2))

            if norm1 == 0 or norm2 == 0:
                return 0.0

            # Cosine similarity
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Failed to calculate similarity: {str(e)}")
            return 0.0

    def delete(self, key: str) -> None:
        """Delete a key from cache.

        Args:
            key: Cache key to delete
        """
        if not self.client:
            return

        try:
            self.client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
        except redis.RedisError as e:
            logger.warning(f"Redis delete failed for key {key}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting key {key}: {str(e)}")

    def flush_all(self) -> None:
        """Flush all keys from the cache (use with caution)."""
        if not self.client:
            return

        try:
            self.client.flushdb()
            logger.warning("Flushed all keys from Redis cache")
        except redis.RedisError as e:
            logger.error(f"Redis flush failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error flushing cache: {str(e)}")

    def _hash_text(self, text: str) -> str:
        """Generate a hash for text to use as cache key.

        Args:
            text: Text to hash

        Returns:
            MD5 hash of the text
        """
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def close(self) -> None:
        """Close the Redis connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Closed Redis connection")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {str(e)}")
