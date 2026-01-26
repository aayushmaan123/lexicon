"""Contract review API endpoints."""

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from lexicon.api.models import (
    ClauseResponse,
    ContractClausesResponse,
    ContractReviewResponse,
    ErrorResponse,
    PartyResponse,
    RiskAssessmentResponse,
)
from lexicon.domain.entities.document import Document, DocumentStatus, DocumentType
from lexicon.services.contract_review import ContractReviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


@router.post(
    "/review",
    response_model=ContractReviewResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file or request"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Review contract document",
    description="Upload a contract document (PDF or DOCX) and perform comprehensive review "
    "including clause extraction, risk analysis, and party identification.",
)
async def review_contract(
    file: UploadFile = File(
        ..., description="Contract file to review (PDF or DOCX)"
    ),
) -> ContractReviewResponse:
    """
    Review an uploaded contract document.

    This endpoint accepts PDF or DOCX contract files and performs comprehensive review:
    - Contract parsing and text extraction
    - Metadata extraction (parties, dates, jurisdiction)
    - Clause identification and classification
    - Risk analysis
    - Detection of unusual clauses

    Args:
        file: Uploaded contract file

    Returns:
        ContractReviewResponse with review results

    Raises:
        HTTPException: 400 if file is invalid, 500 if review fails
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
            document_type=DocumentType.CONTRACT,
            status=DocumentStatus.PENDING,
        )

        logger.info(f"Reviewing contract: {file.filename}")

        # Review contract
        service = ContractReviewService()
        contract = service.review_contract(document)

        # Build response
        parties = [
            PartyResponse(
                name=party.name,
                type=party.type.value,
                role=party.role,
                contact_info=party.contact_info,
            )
            for party in contract.parties
        ]

        clauses = [
            ClauseResponse(
                type=clause.type.value,
                title=clause.title,
                content=clause.content,
                page_number=clause.page_number,
                risk_level=clause.risk_level.value,
                is_unusual=clause.is_unusual,
            )
            for clause in contract.clauses
        ]

        risks = [
            RiskAssessmentResponse(
                category=risk.category.value,
                level=risk.level.value,
                description=risk.description,
                affected_clause=risk.affected_clause,
                mitigation=risk.mitigation,
            )
            for risk in contract.risks
        ]

        response = ContractReviewResponse(
            contract_id=contract.document_id,
            contract_type=contract.contract_type,
            parties=parties,
            clauses=clauses,
            risks=risks,
            effective_date=contract.effective_date,
            expiration_date=contract.expiration_date,
            jurisdiction=contract.jurisdiction,
            governing_law=contract.governing_law,
            overall_assessment=contract.overall_assessment,
        )

        logger.info(f"Successfully reviewed contract: {file.filename}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to review contract {file.filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review contract: {str(e)}",
        ) from e
    finally:
        # Clean up temporary file
        if temp_file and Path(temp_path).exists():
            try:
                Path(temp_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")


@router.get(
    "/{contract_id}/clauses",
    response_model=ContractClausesResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Contract not found"},
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
    summary="Get contract clauses",
    description="Retrieve all clauses for a specific contract by ID. "
    "Returns mock data for now until database integration is complete.",
)
async def get_contract_clauses(contract_id: str) -> ContractClausesResponse:
    """
    Get clauses for a specific contract.

    This endpoint retrieves all clauses associated with a contract.
    Currently returns mock data as a placeholder.

    Args:
        contract_id: Contract identifier

    Returns:
        ContractClausesResponse with list of clauses

    Raises:
        HTTPException: 404 if contract not found, 500 if retrieval fails
    """
    try:
        logger.info(f"Retrieving clauses for contract: {contract_id}")

        # Mock data for now - will be replaced with database query
        mock_clauses = [
            ClauseResponse(
                type="payment",
                title="Payment Terms",
                content="Payment shall be made within 30 days of invoice date.",
                page_number=2,
                risk_level="low",
                is_unusual=False,
            ),
            ClauseResponse(
                type="termination",
                title="Termination",
                content="Either party may terminate this agreement with 60 days written notice.",
                page_number=5,
                risk_level="medium",
                is_unusual=False,
            ),
            ClauseResponse(
                type="liability",
                title="Limitation of Liability",
                content="Total liability shall not exceed the amount paid under this agreement.",
                page_number=7,
                risk_level="high",
                is_unusual=True,
            ),
        ]

        response = ContractClausesResponse(
            contract_id=contract_id, clauses=mock_clauses
        )

        logger.info(
            f"Successfully retrieved {len(mock_clauses)} clauses for contract: {contract_id}"
        )
        return response

    except Exception as e:
        logger.error(
            f"Failed to retrieve clauses for contract {contract_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve contract clauses: {str(e)}",
        ) from e
