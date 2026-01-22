"""Core domain entities for the Lexicon AI platform.

This module defines the fundamental business objects used throughout the system.
All entities are immutable data classes following domain-driven design principles.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


class DocumentType(str, Enum):
    """Supported document types for legal research."""

    CASE_LAW = "case_law"
    STATUTE = "statute"
    REGULATION = "regulation"
    CONTRACT = "contract"
    BRIEF = "brief"
    MEMO = "memo"
    OTHER = "other"


class AgentRole(str, Enum):
    """Roles that AI agents can fulfill in the system."""

    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    SUMMARIZER = "summarizer"
    ORCHESTRATOR = "orchestrator"


@dataclass(frozen=True)
class Document:
    """Represents a legal document in the system.

    Attributes:
        id: Unique identifier for the document
        title: Document title
        content: Full text content
        document_type: Type/category of the document
        metadata: Additional document metadata
        created_at: Timestamp when document was created
        embedding_id: Optional reference to vector embedding
    """

    id: UUID = field(default_factory=uuid4)
    title: str = ""
    content: str = ""
    document_type: DocumentType = DocumentType.OTHER
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    embedding_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate document after initialization."""
        if not self.title and not self.content:
            raise ValueError("Document must have either title or content")


@dataclass(frozen=True)
class Query:
    """Represents a user query to the system.

    Attributes:
        id: Unique identifier for the query
        text: The query text
        context: Optional context for the query
        metadata: Additional query metadata
        created_at: Timestamp when query was created
    """

    id: UUID = field(default_factory=uuid4)
    text: str = ""
    context: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate query after initialization."""
        if not self.text:
            raise ValueError("Query text cannot be empty")


@dataclass(frozen=True)
class AgentResponse:
    """Represents a response from an AI agent.

    Attributes:
        id: Unique identifier for the response
        query_id: Reference to the original query
        content: The response content
        agent_role: Role of the agent that generated this response
        confidence: Confidence score (0.0 to 1.0)
        sources: List of document IDs used as sources
        metadata: Additional response metadata
        created_at: Timestamp when response was created
    """

    id: UUID = field(default_factory=uuid4)
    query_id: UUID = field(default_factory=uuid4)
    content: str = ""
    agent_role: AgentRole = AgentRole.RESEARCHER
    confidence: float = 0.0
    sources: list[UUID] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate response after initialization."""
        if not self.content:
            raise ValueError("Response content cannot be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
