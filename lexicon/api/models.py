"""Pydantic request/response models for the Lexicon API."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


# Enums
class DocumentTypeEnum(str, Enum):
    """Document type enumeration."""

    CONTRACT = "contract"
    CASE_LAW = "case_law"
    GENERAL = "general"


class QueryTypeEnum(str, Enum):
    """Type of legal research query."""

    CASE_LAW = "case_law"
    STATUTE = "statute"
    GENERAL = "general"
    PRECEDENT = "precedent"
    REGULATORY = "regulatory"


class RiskLevelEnum(str, Enum):
    """Risk severity levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Document Analysis Models
class DocumentAnalyzeResponse(BaseModel):
    """Response model for document analysis."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: str = Field(..., description="Classified document type")
    summary: str = Field(..., description="Document summary")
    key_points: list[str] = Field(
        default_factory=list, description="Extracted key points"
    )
    parties: list[dict] = Field(
        default_factory=list, description="Extracted parties"
    )
    dates: list[dict] = Field(default_factory=list, description="Extracted dates")
    page_count: int | None = Field(None, description="Number of pages")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class DocumentSummarizeRequest(BaseModel):
    """Request model for document summarization."""

    text: str = Field(
        ..., description="Document text to summarize", min_length=1
    )


class DocumentSummarizeResponse(BaseModel):
    """Response model for document summarization."""

    summary: str = Field(..., description="Generated summary")


# Contract Review Models
class ClauseResponse(BaseModel):
    """Response model for contract clause."""

    type: str = Field(..., description="Clause type")
    title: str = Field(..., description="Clause title")
    content: str = Field(..., description="Clause content")
    page_number: int | None = Field(None, description="Page number")
    risk_level: RiskLevelEnum = Field(..., description="Risk level")
    is_unusual: bool = Field(False, description="Flag for unusual clause")


class RiskAssessmentResponse(BaseModel):
    """Response model for risk assessment."""

    category: str = Field(..., description="Risk category")
    level: RiskLevelEnum = Field(..., description="Risk severity level")
    description: str = Field(..., description="Risk description")
    affected_clause: str | None = Field(
        None, description="Related clause title"
    )
    mitigation: str | None = Field(None, description="Mitigation recommendation")


class PartyResponse(BaseModel):
    """Response model for contract party."""

    name: str = Field(..., description="Party name")
    type: str = Field(..., description="Party type")
    role: str = Field(..., description="Party role")
    contact_info: str | None = Field(None, description="Contact information")


class ContractReviewResponse(BaseModel):
    """Response model for contract review."""

    contract_id: str = Field(..., description="Contract identifier")
    contract_type: str = Field(..., description="Type of contract")
    parties: list[PartyResponse] = Field(
        default_factory=list, description="Contract parties"
    )
    clauses: list[ClauseResponse] = Field(
        default_factory=list, description="Extracted clauses"
    )
    risks: list[RiskAssessmentResponse] = Field(
        default_factory=list, description="Identified risks"
    )
    effective_date: date | None = Field(None, description="Effective date")
    expiration_date: date | None = Field(None, description="Expiration date")
    jurisdiction: str | None = Field(None, description="Jurisdiction")
    governing_law: str | None = Field(None, description="Governing law")
    overall_assessment: str = Field(..., description="Overall assessment summary")


class ContractClausesResponse(BaseModel):
    """Response model for contract clauses list."""

    contract_id: str = Field(..., description="Contract identifier")
    clauses: list[ClauseResponse] = Field(
        default_factory=list, description="List of clauses"
    )


# Legal Research Models
class ResearchQueryRequest(BaseModel):
    """Request model for legal research query."""

    query_text: str = Field(
        ..., description="Research query text", min_length=1
    )
    jurisdiction: str | None = Field(
        None, description="Jurisdiction filter (e.g., 'US', 'CA', 'NY')"
    )
    query_type: QueryTypeEnum = Field(
        default=QueryTypeEnum.GENERAL, description="Type of research query"
    )
    user_context: str | None = Field(
        None, description="Additional user context"
    )


class ResearchResultResponse(BaseModel):
    """Response model for legal research result."""

    answer: str = Field(..., description="Synthesized research answer")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0-1)"
    )
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    sources: list[dict] = Field(
        default_factory=list, description="Source documents"
    )
    citations: list[str] = Field(
        default_factory=list, description="Legal citations"
    )


# Knowledge Base Models
class IndexDocumentRequest(BaseModel):
    """Request model for document indexing."""

    document_type: DocumentTypeEnum = Field(
        default=DocumentTypeEnum.GENERAL,
        description="Type of document to index",
    )


class IndexDocumentResponse(BaseModel):
    """Response model for document indexing."""

    document_id: str = Field(..., description="Indexed document identifier")
    filename: str = Field(..., description="Document filename")
    status: str = Field(..., description="Indexing status")
    message: str = Field(..., description="Status message")


class KnowledgeBaseStatsResponse(BaseModel):
    """Response model for knowledge base statistics."""

    total_documents: int = Field(..., description="Total indexed documents")
    total_chunks: int = Field(..., description="Total document chunks")
    embedding_model: str = Field(..., description="Embedding model used")
    collections: list[str] = Field(
        default_factory=list, description="Vector store collections"
    )


# Error Response Models
class ErrorDetail(BaseModel):
    """Error detail model."""

    message: str = Field(..., description="Error message")
    type: str | None = Field(None, description="Error type")
    details: dict | None = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: ErrorDetail = Field(..., description="Error information")


# Health Check Model
class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
