"""Legal research API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status

from lexicon.api.models import (
    ErrorResponse,
    ResearchQueryRequest,
    ResearchResultResponse,
)
from lexicon.domain.entities.legal_research import QueryType, ResearchQuery
from lexicon.services.legal_research import LegalResearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.post(
    "/query",
    response_model=ResearchResultResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Perform legal research",
    description="Execute a legal research query using RAG (Retrieval-Augmented Generation) "
    "to search indexed legal documents and synthesize a comprehensive answer with citations.",
)
async def research_query(
    request: ResearchQueryRequest,
) -> ResearchResultResponse:
    """
    Perform legal research query.

    This endpoint executes a comprehensive legal research workflow:
    - Query relevant documents from the knowledge base using RAG
    - Filter by jurisdiction and query type if specified
    - Assess relevance of retrieved documents
    - Extract legal citations
    - Synthesize a comprehensive answer
    - Calculate confidence and relevance scores

    Args:
        request: Research query request with query text and filters

    Returns:
        ResearchResultResponse with answer, citations, and sources

    Raises:
        HTTPException: 400 if request is invalid, 500 if research fails
    """
    if not request.query_text or not request.query_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query text cannot be empty",
        )

    try:
        logger.info(f"Processing research query: {request.query_text[:100]}...")

        # Map API query type to domain QueryType
        query_type = QueryType(request.query_type.value)

        # Create research query
        query = ResearchQuery(
            query_text=request.query_text,
            jurisdiction=request.jurisdiction,
            query_type=query_type,
            user_context=request.user_context,
        )

        # Execute research
        service = LegalResearchService()
        result = service.research(query)

        # Build response
        response = ResearchResultResponse(
            answer=result.answer,
            confidence_score=result.confidence_score,
            relevance_score=result.relevance_score,
            sources=result.sources,
            citations=result.citations,
        )

        logger.info(
            f"Successfully completed research query with {len(result.sources)} sources"
        )
        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid research query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to execute research query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute research query: {str(e)}",
        ) from e
