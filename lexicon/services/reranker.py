"""Document reranking service for RAG pipeline."""

import logging
import math
from collections import Counter

logger = logging.getLogger(__name__)


class Reranker:
    """Reranker for improving relevance of search results.

    Uses BM25-style scoring and similarity-based reranking to improve
    the quality of retrieved documents.
    """

    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        use_bm25: bool = True,
    ):
        """Initialize the reranker.

        Args:
            k1: BM25 k1 parameter (term frequency saturation)
            b: BM25 b parameter (length normalization)
            use_bm25: Whether to use BM25 scoring (otherwise uses cosine similarity)
        """
        self.k1 = k1
        self.b = b
        self.use_bm25 = use_bm25

    def rerank(
        self,
        query: str,
        documents: list[dict],
        top_k: int = 10,
    ) -> list[dict]:
        """Rerank documents based on relevance to query.

        Args:
            query: Query text
            documents: List of document dictionaries with 'text' and 'score' fields
            top_k: Number of top results to return

        Returns:
            Reranked list of documents with updated scores
        """
        if not documents:
            logger.debug("No documents to rerank")
            return []

        try:
            if self.use_bm25:
                reranked = self._rerank_bm25(query, documents)
            else:
                reranked = self._rerank_similarity(query, documents)

            # Sort by rerank score and take top_k
            reranked = sorted(
                reranked,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True,
            )[:top_k]

            logger.info(f"Reranked {len(documents)} documents, returning top {len(reranked)}")
            return reranked

        except Exception as e:
            logger.error(f"Reranking failed: {str(e)}")
            # Fall back to original ranking
            return documents[:top_k]

    def _rerank_bm25(
        self,
        query: str,
        documents: list[dict],
    ) -> list[dict]:
        """Rerank using BM25 algorithm.

        Args:
            query: Query text
            documents: List of documents to rerank

        Returns:
            Reranked documents with BM25 scores
        """
        # Tokenize query
        query_tokens = self._tokenize(query)

        # Calculate average document length
        doc_lengths = [len(self._tokenize(doc.get("text", ""))) for doc in documents]
        avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0

        # Calculate document frequencies for query terms
        doc_freqs = self._calculate_document_frequencies(query_tokens, documents)

        # Calculate BM25 score for each document
        reranked_docs = []
        for doc, doc_length in zip(documents, doc_lengths, strict=True):
            bm25_score = self._calculate_bm25_score(
                query_tokens=query_tokens,
                document=doc,
                doc_length=doc_length,
                avg_doc_length=avg_doc_length,
                doc_freqs=doc_freqs,
                total_docs=len(documents),
            )

            # Combine with original vector similarity score
            original_score = doc.get("score", 0)
            combined_score = 0.7 * original_score + 0.3 * bm25_score

            doc_copy = doc.copy()
            doc_copy["rerank_score"] = combined_score
            doc_copy["bm25_score"] = bm25_score
            reranked_docs.append(doc_copy)

        return reranked_docs

    def _rerank_similarity(
        self,
        query: str,
        documents: list[dict],
    ) -> list[dict]:
        """Rerank using simple similarity-based scoring.

        Args:
            query: Query text
            documents: List of documents to rerank

        Returns:
            Reranked documents with similarity scores
        """
        query_tokens = set(self._tokenize(query))

        reranked_docs = []
        for doc in documents:
            doc_tokens = set(self._tokenize(doc.get("text", "")))

            # Calculate Jaccard similarity
            if not query_tokens or not doc_tokens:
                jaccard_score = 0.0
            else:
                intersection = len(query_tokens & doc_tokens)
                union = len(query_tokens | doc_tokens)
                jaccard_score = intersection / union if union > 0 else 0.0

            # Combine with original score
            original_score = doc.get("score", 0)
            combined_score = 0.8 * original_score + 0.2 * jaccard_score

            doc_copy = doc.copy()
            doc_copy["rerank_score"] = combined_score
            doc_copy["jaccard_score"] = jaccard_score
            reranked_docs.append(doc_copy)

        return reranked_docs

    def _calculate_bm25_score(
        self,
        query_tokens: list[str],
        document: dict,
        doc_length: int,
        avg_doc_length: float,
        doc_freqs: dict[str, int],
        total_docs: int,
    ) -> float:
        """Calculate BM25 score for a document.

        Args:
            query_tokens: Tokenized query
            document: Document to score
            doc_length: Length of the document
            avg_doc_length: Average document length
            doc_freqs: Document frequencies for query terms
            total_docs: Total number of documents

        Returns:
            BM25 score
        """
        doc_text = document.get("text", "")
        doc_tokens = self._tokenize(doc_text)
        doc_term_freqs = Counter(doc_tokens)

        score = 0.0
        for term in query_tokens:
            if term not in doc_term_freqs:
                continue

            # Term frequency in document
            term_freq = doc_term_freqs[term]

            # Document frequency (number of docs containing term)
            doc_freq = doc_freqs.get(term, 0)

            # IDF calculation
            idf = math.log((total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)

            # BM25 formula
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (
                1 - self.b + self.b * (doc_length / avg_doc_length)
            )

            score += idf * (numerator / denominator)

        # Normalize score
        return score / (len(query_tokens) + 1)

    def _calculate_document_frequencies(
        self,
        query_tokens: list[str],
        documents: list[dict],
    ) -> dict[str, int]:
        """Calculate document frequencies for query terms.

        Args:
            query_tokens: Tokenized query
            documents: List of documents

        Returns:
            Dictionary mapping terms to document frequencies
        """
        doc_freqs = {}
        for term in set(query_tokens):
            count = 0
            for doc in documents:
                doc_text = doc.get("text", "")
                if term in self._tokenize(doc_text):
                    count += 1
            doc_freqs[term] = count

        return doc_freqs

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of lowercase tokens
        """
        # Simple whitespace tokenization with lowercasing
        # Could be improved with proper NLP tokenization
        return text.lower().split()

    def batch_rerank(
        self,
        queries: list[str],
        documents_list: list[list[dict]],
        top_k: int = 10,
    ) -> list[list[dict]]:
        """Rerank documents for multiple queries.

        Args:
            queries: List of query texts
            documents_list: List of document lists (one per query)
            top_k: Number of top results to return per query

        Returns:
            List of reranked document lists
        """
        if len(queries) != len(documents_list):
            raise ValueError("Number of queries must match number of document lists")

        results = []
        for query, documents in zip(queries, documents_list, strict=True):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)

        return results

    def get_relevance_scores(
        self,
        query: str,
        documents: list[dict],
    ) -> list[float]:
        """Get relevance scores for documents without reranking.

        Args:
            query: Query text
            documents: List of documents

        Returns:
            List of relevance scores
        """
        reranked = self.rerank(query, documents, top_k=len(documents))
        return [doc.get("rerank_score", 0) for doc in reranked]
