"""RAG orchestrator for document indexing and querying."""

import logging

from openai import OpenAI

from lexicon.domain.entities.document import Document, DocumentChunk, DocumentType
from lexicon.domain.parsers import (
    DOCXParser,
    PDFParser,
    clause_aware_chunker,
    section_based_chunker,
    sliding_window_chunker,
)
from lexicon.infrastructure.cache_client import CacheClient
from lexicon.infrastructure.chroma_client import ChromaVectorStore
from lexicon.services.reranker import Reranker
from lexicon.shared.config import settings

logger = logging.getLogger(__name__)


class RAGOrchestrator:
    """Orchestrates the RAG pipeline for document indexing and querying.

    This class coordinates the entire RAG workflow:
    1. Document parsing
    2. Chunking
    3. Embedding generation
    4. Vector storage
    5. Query processing
    6. Result reranking
    """

    # Pricing for embeddings (per 1M tokens)
    EMBEDDING_PRICING = {
        "text-embedding-3-large": 0.13,
        "text-embedding-3-small": 0.02,
        "text-embedding-ada-002": 0.10,
    }

    def __init__(
        self,
        embedding_model: str | None = None,
        vector_store: ChromaVectorStore | None = None,
        cache_client: CacheClient | None = None,
        reranker: Reranker | None = None,
        openai_api_key: str | None = None,
    ):
        """Initialize RAG orchestrator.

        Args:
            embedding_model: OpenAI embedding model name
            vector_store: Vector store instance (creates default if not provided)
            cache_client: Cache client instance (creates default if not provided)
            reranker: Reranker instance (creates default if not provided)
            openai_api_key: OpenAI API key (uses settings if not provided)
        """
        self.embedding_model = embedding_model or settings.embedding_model
        self.openai_api_key = openai_api_key or settings.openai_api_key
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Initialize components
        self.vector_store = vector_store or ChromaVectorStore()
        self.cache_client = cache_client or CacheClient()
        self.reranker = reranker or Reranker()

        # Initialize parsers
        self.parsers = {
            "pdf": PDFParser(),
            "docx": DOCXParser(),
        }

        # Track costs
        self.total_embedding_tokens = 0
        self.total_cost = 0.0

        logger.info(f"Initialized RAG orchestrator with model: {self.embedding_model}")

    def index_document(self, document: Document) -> str:
        """Full indexing pipeline for a document.

        Pipeline steps:
        1. Parse document to extract text
        2. Chunk document into smaller segments
        3. Generate embeddings for chunks
        4. Store chunks with embeddings in vector store

        Args:
            document: Document entity to index

        Returns:
            Document ID

        Raises:
            ValueError: If document type is unsupported or parsing fails
            Exception: If indexing pipeline fails
        """
        try:
            logger.info(f"Starting indexing pipeline for document: {document.filename}")

            # Step 1: Parse document
            parsed_doc = self._parse_document(document)
            logger.info(f"Parsed document: {len(parsed_doc.full_text)} characters")

            # Step 2: Chunk document
            chunks = self._chunk_document(parsed_doc, document.document_type)
            logger.info(f"Created {len(chunks)} chunks")

            if not chunks:
                raise ValueError("No chunks created from document")

            # Step 3: Generate embeddings
            chunk_embeddings = self._generate_embeddings(chunks)
            logger.info(f"Generated {len(chunk_embeddings)} embeddings")

            # Step 4: Store in vector store
            self._store_chunks(chunks, chunk_embeddings)
            logger.info(f"Stored {len(chunks)} chunks in vector store")

            logger.info(
                f"Successfully indexed document {document.id}. Total cost: ${self.total_cost:.4f}"
            )

            return document.id or parsed_doc.document_id

        except Exception as e:
            logger.error(f"Failed to index document {document.filename}: {str(e)}")
            raise

    def query(
        self,
        query_text: str,
        top_k: int = 10,
        filters: dict | None = None,
        rerank: bool = True,
    ) -> list[dict]:
        """Query pipeline for retrieving relevant documents.

        Pipeline steps:
        1. Check semantic cache for similar queries
        2. Generate query embedding
        3. Search vector store
        4. Rerank results (optional)
        5. Cache results

        Args:
            query_text: Query text
            top_k: Number of results to return
            filters: Optional metadata filters for vector search
            rerank: Whether to rerank results

        Returns:
            List of relevant document chunks with metadata and scores

        Raises:
            Exception: If query pipeline fails
        """
        try:
            logger.info(f"Processing query: {query_text[:100]}...")

            # Step 1: Check semantic cache
            cached_result = self.cache_client.get_semantic_cache(query_text)
            if cached_result:
                logger.info("Returning cached query results")
                import json

                return json.loads(cached_result)

            # Step 2: Generate query embedding
            query_embedding = self._generate_query_embedding(query_text)

            # Step 3: Search vector store
            # Request more results if we're going to rerank
            search_k = top_k * 2 if rerank else top_k
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=search_k,
                filters=filters,
            )
            logger.info(f"Found {len(search_results)} initial results")

            # Step 4: Rerank results
            if rerank and len(search_results) > 0:
                search_results = self.reranker.rerank(
                    query=query_text,
                    documents=search_results,
                    top_k=top_k,
                )
                logger.info(f"Reranked to top {len(search_results)} results")

            # Step 5: Cache results
            import json

            self.cache_client.set_semantic_cache(
                query=query_text,
                response=json.dumps(search_results),
            )

            logger.info(
                f"Query completed. Returning {len(search_results)} results. "
                f"Total cost: ${self.total_cost:.4f}"
            )

            return search_results

        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise

    def assemble_context(
        self,
        query: str,
        search_results: list[dict],
        max_context_length: int = 4000,
    ) -> str:
        """Assemble context for LLM from search results.

        Args:
            query: Original query text
            search_results: List of search results
            max_context_length: Maximum context length in characters

        Returns:
            Assembled context string ready for LLM
        """
        if not search_results:
            return ""

        context_parts = [f"Query: {query}\n\nRelevant Context:\n"]
        current_length = len(context_parts[0])

        for i, result in enumerate(search_results):
            # Extract relevant information
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            score = result.get("rerank_score") or result.get("score", 0)

            # Format chunk with metadata
            chunk_text = f"\n[Document {i + 1}]"
            if "filename" in metadata:
                chunk_text += f"\nSource: {metadata['filename']}"
            if "chunk_index" in metadata:
                chunk_text += f" (Chunk {metadata['chunk_index']})"
            chunk_text += f"\nRelevance: {score:.3f}\n{text}\n"

            # Check if adding this chunk would exceed max length
            if current_length + len(chunk_text) > max_context_length:
                logger.info(
                    f"Context length limit reached. Including {i} of {len(search_results)} chunks"
                )
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

        context = "".join(context_parts)
        logger.info(
            f"Assembled context: {current_length} characters from {len(context_parts) - 1} chunks"
        )

        return context

    def _parse_document(self, document: Document):
        """Parse document using appropriate parser.

        Args:
            document: Document to parse

        Returns:
            ParsedDocument

        Raises:
            ValueError: If file extension is unsupported
        """
        file_ext = document.filename.lower().split(".")[-1]

        if file_ext not in self.parsers:
            raise ValueError(
                f"Unsupported file type: {file_ext}. Supported types: {list(self.parsers.keys())}"
            )

        parser = self.parsers[file_ext]
        parsed_doc = parser.parse(document.file_path)

        return parsed_doc

    def _chunk_document(
        self,
        parsed_doc,
        document_type: DocumentType,
    ) -> list[DocumentChunk]:
        """Chunk document based on document type.

        Args:
            parsed_doc: ParsedDocument to chunk
            document_type: Type of document

        Returns:
            List of document chunks
        """
        if document_type == DocumentType.CONTRACT:
            chunker = clause_aware_chunker
        elif document_type == DocumentType.CASE_LAW:
            chunker = section_based_chunker
        else:
            chunker = sliding_window_chunker

        chunks = chunker(parsed_doc)

        return chunks

    def _generate_embeddings(
        self,
        chunks: list[DocumentChunk],
    ) -> list[list[float]]:
        """Generate embeddings for document chunks with caching.

        Args:
            chunks: List of document chunks

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for chunk in chunks:
            # Check cache first
            cached_embedding = self.cache_client.get_embedding_cache(chunk.content)
            if cached_embedding:
                embeddings.append(cached_embedding)
                logger.debug(f"Using cached embedding for chunk {chunk.chunk_id}")
                continue

            # Generate new embedding
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=chunk.content,
                )

                embedding = response.data[0].embedding

                # Cache the embedding
                self.cache_client.set_embedding_cache(chunk.content, embedding)

                # Track usage
                tokens_used = response.usage.total_tokens
                self.total_embedding_tokens += tokens_used
                cost = self._calculate_embedding_cost(tokens_used)
                self.total_cost += cost

                embeddings.append(embedding)

            except Exception as e:
                logger.error(f"Failed to generate embedding for chunk {chunk.chunk_id}: {str(e)}")
                raise

        return embeddings

    def _generate_query_embedding(self, query_text: str) -> list[float]:
        """Generate embedding for query text with caching.

        Args:
            query_text: Query text

        Returns:
            Query embedding vector
        """
        # Check cache first
        cached_embedding = self.cache_client.get_embedding_cache(query_text)
        if cached_embedding:
            logger.debug("Using cached query embedding")
            return cached_embedding

        # Generate new embedding
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query_text,
            )

            embedding = response.data[0].embedding

            # Cache the embedding
            self.cache_client.set_embedding_cache(query_text, embedding)

            # Track usage
            tokens_used = response.usage.total_tokens
            self.total_embedding_tokens += tokens_used
            cost = self._calculate_embedding_cost(tokens_used)
            self.total_cost += cost

            logger.debug(f"Generated query embedding: {tokens_used} tokens, ${cost:.6f}")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate query embedding: {str(e)}")
            raise

    def _store_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        """Store chunks with embeddings in vector store.

        Args:
            chunks: List of document chunks
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")

        # Prepare data for vector store
        documents = [{"text": chunk.content} for chunk in chunks]
        metadata = [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "filename": chunk.metadata.get("filename", ""),
                "document_type": chunk.metadata.get("document_type", ""),
                "token_count": chunk.token_count,
                "page_number": chunk.page_number,
                "section_title": chunk.section_title,
            }
            for chunk in chunks
        ]

        # Add to vector store
        self.vector_store.add_documents(
            documents=documents,
            embeddings=embeddings,
            metadata=metadata,
        )

    def _calculate_embedding_cost(self, tokens: int) -> float:
        """Calculate cost for embedding generation.

        Args:
            tokens: Number of tokens

        Returns:
            Cost in USD
        """
        price_per_million = self.EMBEDDING_PRICING.get(self.embedding_model, 0.13)
        return (tokens / 1_000_000) * price_per_million

    def get_stats(self) -> dict:
        """Get usage statistics.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "total_embedding_tokens": self.total_embedding_tokens,
            "total_cost": self.total_cost,
            "embedding_model": self.embedding_model,
            "vector_store_stats": self.vector_store.get_collection_stats(),
        }

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.total_embedding_tokens = 0
        self.total_cost = 0.0
        logger.info("Reset usage statistics")
