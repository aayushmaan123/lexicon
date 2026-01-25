"""Document domain entities for the Lexicon application."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Document type enumeration."""

    CONTRACT = "contract"
    CASE_LAW = "case_law"
    GENERAL = "general"


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(BaseModel):
    """Represents an uploaded document."""

    model_config = ConfigDict(use_enum_values=True)

    id: str | None = None
    filename: str
    file_path: str
    file_size: int
    document_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Section(BaseModel):
    """Represents a section within a document."""

    title: str
    content: str
    page_number: int | None = None
    level: int = 1
    section_number: str | None = None


class ParsedDocument(BaseModel):
    """Represents a parsed document with extracted data."""

    model_config = ConfigDict(use_enum_values=True)

    document_id: str
    filename: str
    document_type: DocumentType
    full_text: str
    sections: list[Section] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    page_count: int | None = None
    parsed_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """Represents a document chunk for RAG."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    page_number: int | None = None
    section_title: str | None = None
    token_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
