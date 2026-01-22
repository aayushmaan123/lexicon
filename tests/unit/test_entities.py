"""Unit tests for core domain entities.

Tests validate entity creation, immutability, and business rules.
"""

import pytest
from datetime import datetime
from uuid import UUID

from lexicon.domain.entities.core import (
    Document,
    DocumentType,
    Query,
    AgentResponse,
    AgentRole,
)


class TestDocument:
    """Tests for Document entity."""

    def test_create_document_with_defaults(self) -> None:
        """Test creating a document with default values."""
        doc = Document(title="Test Case", content="Legal content")

        assert isinstance(doc.id, UUID)
        assert doc.title == "Test Case"
        assert doc.content == "Legal content"
        assert doc.document_type == DocumentType.OTHER
        assert isinstance(doc.created_at, datetime)
        assert doc.embedding_id is None

    def test_create_document_with_metadata(self) -> None:
        """Test creating a document with custom metadata."""
        metadata = {"jurisdiction": "federal", "court": "supreme"}
        doc = Document(
            title="Roe v. Wade",
            content="...",
            document_type=DocumentType.CASE_LAW,
            metadata=metadata,
        )

        assert doc.document_type == DocumentType.CASE_LAW
        assert doc.metadata["jurisdiction"] == "federal"

    def test_document_immutability(self) -> None:
        """Test that documents are immutable."""
        doc = Document(title="Test", content="Content")

        with pytest.raises(Exception):  # FrozenInstanceError
            doc.title = "Modified"  # type: ignore

    def test_document_validation_fails_when_empty(self) -> None:
        """Test that document validation fails with no title or content."""
        with pytest.raises(ValueError, match="must have either title or content"):
            Document()


class TestQuery:
    """Tests for Query entity."""

    def test_create_query(self) -> None:
        """Test creating a query."""
        query = Query(text="What is contract law?")

        assert isinstance(query.id, UUID)
        assert query.text == "What is contract law?"
        assert query.context is None
        assert isinstance(query.created_at, datetime)

    def test_query_with_context(self) -> None:
        """Test creating a query with context."""
        query = Query(
            text="Analyze this contract",
            context="Employment agreement context...",
        )

        assert query.context == "Employment agreement context..."

    def test_query_validation_fails_when_empty(self) -> None:
        """Test that query validation fails with empty text."""
        with pytest.raises(ValueError, match="Query text cannot be empty"):
            Query()


class TestAgentResponse:
    """Tests for AgentResponse entity."""

    def test_create_agent_response(self) -> None:
        """Test creating an agent response."""
        response = AgentResponse(
            content="Based on the precedent...",
            agent_role=AgentRole.RESEARCHER,
            confidence=0.85,
        )

        assert isinstance(response.id, UUID)
        assert response.content == "Based on the precedent..."
        assert response.agent_role == AgentRole.RESEARCHER
        assert response.confidence == 0.85

    def test_agent_response_validation_fails_with_empty_content(self) -> None:
        """Test that response validation fails with empty content."""
        with pytest.raises(ValueError, match="Response content cannot be empty"):
            AgentResponse()

    def test_agent_response_validation_fails_with_invalid_confidence(self) -> None:
        """Test that confidence must be between 0.0 and 1.0."""
        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AgentResponse(content="test", confidence=1.5)

        with pytest.raises(ValueError, match="Confidence must be between 0.0 and 1.0"):
            AgentResponse(content="test", confidence=-0.1)
