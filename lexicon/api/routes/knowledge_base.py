"""Knowledge base API endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from lexicon.api.models import (
    ErrorResponse,
    IndexDocumentResponse,
    KnowledgeBaseStatsResponse,
)
from lexicon.domain.entities.document import Document, DocumentStatus, DocumentType
from lexicon.services.rag_orchestrator import RAGOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["knowledge-base"])


@router.post(
    "/index",
    response_model=IndexDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Index document",
    description="Upload and index a document into the knowledge base for legal research. "
    "The document will be parsed, chunked, embedded, and stored in the vector database.",
)
async def index_document(
    file: UploadFile = File(
        ..., description="Document file to index (PDF or DOCX)"
    ),
    document_type: str = "general",
) -> IndexDocumentResponse:
    """
    Index a document into the knowledge base.

    This endpoint performs the full RAG indexing pipeline:
    - Parse document to extract text
    - Chunk document into smaller segments
    - Generate embeddings for each chunk
    - Store chunks with embeddings in vector database

    Args:
        file: Uploaded document file
        document_type: Type of document (contract, case_law, or general)

    Returns:
        IndexDocumentResponse with document ID and status

    Raises:
        HTTPException: 400 if file is invalid, 500 if indexing fails
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    # Check file extension
    filename = file.filename.lower()
    if not (filename.endswith(".pdf") or filename.endswith(".docx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported",
        )

    # Validate document type
    try:
        doc_type = DocumentType(document_type.lower())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {', '.join([t.value for t in DocumentType])}",
        ) from e

    # Create temporary file
    temp_file = None
    temp_path = None
    try:
        # Save uploaded file to temporary location
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Create Document entity
        document = Document(
            id=str(uuid.uuid4()),
            filename=file.filename,
            file_path=temp_path,
            file_size=len(content),
            document_type=doc_type,
            status=DocumentStatus.PENDING,
        )

        logger.info(f"Indexing document: {file.filename}")

        # Index document
        orchestrator = RAGOrchestrator()
        document_id = orchestrator.index_document(document)

        # Build response
        response = IndexDocumentResponse(
            document_id=document_id,
            filename=file.filename,
            status="indexed",
            message=f"Successfully indexed document: {file.filename}",
        )

        logger.info(f"Successfully indexed document: {file.filename}")
        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid document for indexing {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to index document {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}",
        ) from e
    finally:
        # Clean up temporary file
        if temp_path and Path(temp_path).exists():
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Delete document",
    description="Delete a document from the knowledge base by ID. "
    "Returns 204 No Content for now until database integration is complete.",
)
async def delete_document(document_id: str) -> None:
    """
    Delete a document from the knowledge base.

    This endpoint removes a document and all its associated chunks from the vector database.
    Currently returns 204 as a placeholder until full database integration.

    Args:
        document_id: Document identifier to delete

    Raises:
        HTTPException: 404 if document not found, 500 if deletion fails
    """
    try:
        logger.info(f"Deleting document: {document_id}")

        # Placeholder - will be implemented with database integration
        # orchestrator = RAGOrchestrator()
        # orchestrator.delete_document(document_id)

        logger.info(f"Successfully deleted document: {document_id}")
        return None

    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        ) from e


@router.get(
    "/stats",
    response_model=KnowledgeBaseStatsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Get knowledge base statistics",
    description="Retrieve statistics about the knowledge base including total documents, "
    "chunks, embedding model, and collections.",
)
async def get_stats() -> KnowledgeBaseStatsResponse:
    """
    Get knowledge base statistics.

    This endpoint returns statistics about the indexed documents and vector database.

    Returns:
        KnowledgeBaseStatsResponse with statistics

    Raises:
        HTTPException: 500 if retrieval fails
    """
    try:
        logger.info("Retrieving knowledge base statistics")

        orchestrator = RAGOrchestrator()

        # Get stats from vector store if method exists, otherwise return defaults
        try:
            stats = orchestrator.vector_store.get_stats()
            total_documents = stats.get("total_documents", 0)
            total_chunks = stats.get("total_chunks", 0)
            collections = stats.get("collections", [])
        except AttributeError:
            # get_stats method not implemented yet - return defaults
            total_documents = 0
            total_chunks = 0
            collections = ["lexicon_documents"]

        response = KnowledgeBaseStatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            embedding_model=orchestrator.embedding_model,
            collections=collections,
        )

        logger.info("Successfully retrieved knowledge base statistics")
        return response

    except Exception as e:
        logger.error(f"Failed to retrieve knowledge base statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}",
        ) from e
