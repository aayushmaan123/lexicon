"""Legal research service using RAG and LLM for intelligent legal research."""

import json
import logging
from typing import Any

from pydantic import BaseModel

from lexicon.domain.citation_formatter import CitationFormatter
from lexicon.domain.entities.legal_research import (
    QueryType,
    ResearchQuery,
    ResearchResult,
)
from lexicon.infrastructure.openai_client import OpenAIProvider
from lexicon.services.rag_orchestrator import RAGOrchestrator
from lexicon.shared.config import settings
from lexicon.shared.prompts.legal_research import (
    ASSESS_RELEVANCE_PROMPT,
    EXTRACT_CITATIONS_PROMPT,
    RESEARCH_QUERY_PROMPT,
    SYNTHESIZE_ANSWER_PROMPT,
)
from lexicon.shared.retry_handler.handler import RetryHandler

logger = logging.getLogger(__name__)


class CitationsResponse(BaseModel):
    """Structured response model for citation extraction."""

    citations: list[dict[str, Any]]


class RelevanceResponse(BaseModel):
    """Structured response model for relevance assessment."""

    relevance_scores: list[dict[str, Any]]


class LegalResearchService:
    """Service for legal research using RAG and LLM capabilities."""

    def __init__(
        self,
        rag_orchestrator: RAGOrchestrator | None = None,
        llm_provider: OpenAIProvider | None = None,
        citation_formatter: CitationFormatter | None = None,
        retry_handler: RetryHandler | None = None,
    ):
        """Initialize legal research service.

        Args:
            rag_orchestrator: RAG orchestrator for document retrieval
            llm_provider: LLM provider for synthesis (uses GPT-4o by default)
            citation_formatter: Citation formatter instance
            retry_handler: Retry handler for robustness
        """
        self.rag = rag_orchestrator or RAGOrchestrator()
        self.llm = llm_provider or OpenAIProvider(model=settings.primary_llm_model)
        self.citation_formatter = citation_formatter or CitationFormatter()
        self.retry_handler = retry_handler or RetryHandler(
            max_retries=settings.max_retries,
            backoff_factor=settings.retry_backoff_factor,
        )

        logger.info(
            f"Initialized LegalResearchService with model: {self.llm.model}"
        )

    def research(self, query: ResearchQuery) -> ResearchResult:
        """Execute full research workflow.

        Pipeline:
        1. Process query with RAG to retrieve relevant documents
        2. Assess relevance of retrieved documents
        3. Extract citations from top documents
        4. Synthesize comprehensive answer
        5. Calculate confidence and relevance scores

        Args:
            query: Research query with context

        Returns:
            Research result with answer, citations, and scores

        Raises:
            Exception: If research workflow fails
        """
        try:
            logger.info(f"Starting research for query: {query.query_text[:100]}...")

            # Step 1: Retrieve relevant documents using RAG
            filters = {}
            if query.jurisdiction:
                filters["jurisdiction"] = query.jurisdiction
            if query.query_type != QueryType.GENERAL:
                filters["document_type"] = query.query_type.value

            search_results = self.rag.query(
                query_text=query.query_text,
                top_k=10,
                filters=filters if filters else None,
                rerank=True,
            )

            if not search_results:
                logger.warning("No documents found for query")
                return ResearchResult(
                    answer="No relevant documents found in the database for this query. "
                    "Please ensure the relevant legal documents have been indexed.",
                    confidence_score=0.0,
                    sources=[],
                    citations=[],
                    relevance_score=0.0,
                )

            logger.info(f"Retrieved {len(search_results)} documents")

            # Step 2: Assess relevance
            relevance_scores = self.assess_relevance(
                query=query.query_text,
                documents=search_results,
            )

            # Update search results with relevance scores
            for i, score in enumerate(relevance_scores):
                if i < len(search_results):
                    search_results[i]["relevance_score"] = score

            # Step 3: Extract citations from top documents
            all_citations = []
            for result in search_results[:5]:  # Top 5 documents
                citations = self.extract_citations(result.get("text", ""))
                all_citations.extend(citations)

            # Remove duplicates
            unique_citations = list(set(all_citations))
            logger.info(f"Extracted {len(unique_citations)} unique citations")

            # Step 4: Synthesize answer
            answer = self.synthesize_answer(
                query=query.query_text,
                context=search_results,
            )

            # Step 5: Calculate scores
            avg_relevance = (
                sum(relevance_scores) / len(relevance_scores)
                if relevance_scores
                else 0.0
            )

            # Confidence based on number of sources and average relevance
            confidence = min(
                1.0,
                (len(search_results) / 10.0) * avg_relevance,
            )

            result = ResearchResult(
                answer=answer,
                confidence_score=round(confidence, 3),
                sources=[
                    {
                        "text": r.get("text", "")[:200] + "...",
                        "metadata": r.get("metadata", {}),
                        "score": r.get("rerank_score") or r.get("score", 0),
                        "relevance_score": r.get("relevance_score", 0),
                    }
                    for r in search_results[:5]
                ],
                citations=unique_citations,
                relevance_score=round(avg_relevance, 3),
            )

            logger.info(
                f"Research completed. Confidence: {result.confidence_score}, "
                f"Relevance: {result.relevance_score}"
            )

            return result

        except Exception as e:
            logger.error(f"Research workflow failed: {str(e)}", exc_info=True)
            raise

    def process_query(
        self,
        query_text: str,
        jurisdiction: str | None = None,
    ) -> str:
        """Process a research query with RAG context.

        Args:
            query_text: The research query
            jurisdiction: Optional jurisdiction filter

        Returns:
            Processed answer with RAG context

        Raises:
            Exception: If query processing fails
        """
        try:
            logger.info(f"Processing query: {query_text[:100]}...")

            # Retrieve relevant documents
            filters = {"jurisdiction": jurisdiction} if jurisdiction else None
            search_results = self.rag.query(
                query_text=query_text,
                top_k=10,
                filters=filters,
                rerank=True,
            )

            # Assemble context
            rag_context = self.rag.assemble_context(
                query=query_text,
                search_results=search_results,
                max_context_length=4000,
            )

            # Format prompt
            user_context_str = ""
            prompt = RESEARCH_QUERY_PROMPT.format(
                query_text=query_text,
                jurisdiction=jurisdiction or "Not specified",
                query_type="general",
                user_context=user_context_str,
                rag_context=rag_context if rag_context else "No relevant context found.",
            )

            # Generate answer
            answer = self.retry_handler.execute(
                lambda: self.llm.generate(prompt, temperature=0.3)
            )

            logger.info("Query processed successfully")
            return answer

        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}", exc_info=True)
            raise

    def extract_citations(self, text: str) -> list[str]:
        """Extract legal citations from text.

        Args:
            text: Text to extract citations from

        Returns:
            List of citation strings

        Raises:
            Exception: If citation extraction fails
        """
        try:
            if not text or not text.strip():
                return []

            logger.debug(f"Extracting citations from {len(text)} characters")

            # Format prompt
            prompt = EXTRACT_CITATIONS_PROMPT.format(text=text[:5000])

            # Use structured output for reliable JSON parsing
            try:
                response = self.retry_handler.execute(
                    lambda: self.llm.generate_structured(
                        prompt=prompt,
                        response_model=CitationsResponse,
                    )
                )
                citations = [c.get("citation_text", "") for c in response.citations]
            except Exception as e:
                logger.warning(f"Structured extraction failed, using text: {str(e)}")
                # Fallback to text generation and manual parsing
                response_text = self.retry_handler.execute(
                    lambda: self.llm.generate(prompt, temperature=0.1)
                )
                try:
                    response_data = json.loads(response_text)
                    citations = [
                        c.get("citation_text", "")
                        for c in response_data.get("citations", [])
                    ]
                except json.JSONDecodeError:
                    logger.error("Failed to parse citation extraction response")
                    citations = []

            logger.debug(f"Extracted {len(citations)} citations")
            return citations

        except Exception as e:
            logger.error(f"Citation extraction failed: {str(e)}", exc_info=True)
            return []

    def synthesize_answer(
        self,
        query: str,
        context: list[dict],
    ) -> str:
        """Synthesize a comprehensive answer from retrieved documents.

        Args:
            query: Original research query
            context: List of retrieved document chunks with metadata

        Returns:
            Synthesized answer

        Raises:
            Exception: If synthesis fails
        """
        try:
            if not context:
                return (
                    "Unable to synthesize an answer: no relevant documents found."
                )

            logger.info(f"Synthesizing answer from {len(context)} documents")

            # Format context
            context_parts = []
            for i, doc in enumerate(context[:10]):  # Limit to top 10
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})
                score = doc.get("rerank_score") or doc.get("score", 0)

                context_str = f"\n[Document {i + 1}]"
                if "filename" in metadata:
                    context_str += f"\nSource: {metadata['filename']}"
                context_str += f"\nRelevance: {score:.3f}\n{text}\n"
                context_parts.append(context_str)

            context_text = "\n".join(context_parts)

            # Format prompt
            prompt = SYNTHESIZE_ANSWER_PROMPT.format(
                query=query,
                context=context_text,
            )

            # Generate synthesis
            answer = self.retry_handler.execute(
                lambda: self.llm.generate(prompt, temperature=0.3, max_tokens=1500)
            )

            logger.info("Answer synthesized successfully")
            return answer

        except Exception as e:
            logger.error(f"Answer synthesis failed: {str(e)}", exc_info=True)
            raise

    def assess_relevance(
        self,
        query: str,
        documents: list[dict],
    ) -> list[float]:
        """Assess relevance of documents to a query.

        Args:
            query: Research query
            documents: List of document chunks to assess

        Returns:
            List of relevance scores (0.0 to 1.0) for each document

        Raises:
            Exception: If relevance assessment fails
        """
        try:
            if not documents:
                return []

            logger.info(f"Assessing relevance of {len(documents)} documents")

            # Format documents for assessment
            docs_parts = []
            for i, doc in enumerate(documents[:10]):  # Limit to 10 for efficiency
                text = doc.get("text", "")[:500]  # Truncate for efficiency
                metadata = doc.get("metadata", {})
                docs_parts.append(
                    f"[Document {i}]\n"
                    f"Source: {metadata.get('filename', 'Unknown')}\n"
                    f"Text: {text}\n"
                )

            docs_text = "\n".join(docs_parts)

            # Format prompt
            prompt = ASSESS_RELEVANCE_PROMPT.format(
                query=query,
                documents=docs_text,
            )

            # Get relevance scores
            try:
                response = self.retry_handler.execute(
                    lambda: self.llm.generate_structured(
                        prompt=prompt,
                        response_model=RelevanceResponse,
                    )
                )
                scores = [s.get("score", 0.5) for s in response.relevance_scores]
            except Exception as e:
                logger.warning(
                    f"Structured relevance assessment failed, using text: {str(e)}"
                )
                # Fallback to text generation
                response_text = self.retry_handler.execute(
                    lambda: self.llm.generate(prompt, temperature=0.1)
                )
                try:
                    response_data = json.loads(response_text)
                    scores = [
                        s.get("score", 0.5)
                        for s in response_data.get("relevance_scores", [])
                    ]
                except json.JSONDecodeError:
                    logger.error("Failed to parse relevance scores, using defaults")
                    scores = [0.5] * min(len(documents), 10)

            # Extend scores if we have more documents
            while len(scores) < len(documents):
                scores.append(0.3)  # Lower score for unassessed documents

            logger.info(
                f"Assessed relevance: avg={sum(scores)/len(scores):.3f}"
            )
            return scores

        except Exception as e:
            logger.error(f"Relevance assessment failed: {str(e)}", exc_info=True)
            # Return default scores on error
            return [0.5] * len(documents)
