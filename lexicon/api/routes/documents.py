"""Document analysis API endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from lexicon.api.models import (
    DocumentAnalyzeResponse,
    DocumentSummarizeRequest,
    DocumentSummarizeResponse,
    ErrorResponse,
)
from lexicon.domain.entities.document import Document, DocumentStatus, DocumentType
from lexicon.services.document_analysis import DocumentAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post(
    "/analyze",
    response_model=DocumentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Upload and analyze document",
    description="Upload a document (PDF or DOCX) and perform comprehensive analysis including "
    "summarization, key point extraction, party identification, and classification.",
)
async def analyze_document(
    file: UploadFile = File(
        ..., description="Document file to analyze (PDF or DOCX)"
    ),
) -> DocumentAnalyzeResponse:
    """
    Analyze an uploaded document.

    This endpoint accepts PDF or DOCX files and performs comprehensive analysis:
    - Document parsing and text extraction
    - Summarization
    - Key point extraction
    - Party and date extraction
    - Document classification

    Args:
        file: Uploaded document file

    Returns:
        DocumentAnalyzeResponse with analysis results

    Raises:
        HTTPException: 400 if file is invalid, 500 if analysis fails
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

    # Create temporary file
    temp_file = None
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
            document_type=DocumentType.GENERAL,
            status=DocumentStatus.PENDING,
        )

        logger.info(f"Analyzing document: {file.filename}")

        # Analyze document
        service = DocumentAnalysisService()
        parsed_doc = service.analyze_document(document)

        # Build response
        response = DocumentAnalyzeResponse(
            document_id=parsed_doc.document_id,
            filename=parsed_doc.filename,
            document_type=parsed_doc.metadata.get(
                "classified_type", DocumentType.GENERAL.value
            ),
            summary=parsed_doc.metadata.get("summary", ""),
            key_points=parsed_doc.metadata.get("key_points", []),
            parties=parsed_doc.metadata.get("parties", []),
            dates=parsed_doc.metadata.get("dates", []),
            page_count=parsed_doc.page_count,
            metadata=parsed_doc.metadata,
        )

        logger.info(f"Successfully analyzed document: {file.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze document {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document: {str(e)}",
        ) from e
    finally:
        # Clean up temporary file
        if temp_file and Path(temp_path).exists():
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@router.post(
    "/summarize",
    response_model=DocumentSummarizeResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Summarize document text",
    description="Generate a concise summary of the provided document text using LLM.",
)
async def summarize_document(
    request: DocumentSummarizeRequest,
) -> DocumentSummarizeResponse:
    """
    Summarize provided document text.

    This endpoint accepts plain text and generates a concise summary.

    Args:
        request: Request containing document text

    Returns:
        DocumentSummarizeResponse with generated summary

    Raises:
        HTTPException: 400 if text is empty, 500 if summarization fails
    """
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty",
        )

    try:
        logger.info("Summarizing document text")

        service = DocumentAnalysisService()
        summary = service.summarize_document(request.text)

        logger.info("Successfully generated summary")
        return DocumentSummarizeResponse(summary=summary)

    except Exception as e:
        logger.error(f"Failed to summarize document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to summarize document: {str(e)}",
        ) from e
