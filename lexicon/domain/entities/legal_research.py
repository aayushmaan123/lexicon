"""Legal research domain entities for the Lexicon application."""

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class QueryType(str, Enum):
    """Type of legal research query."""

    CASE_LAW = "case_law"
    STATUTE = "statute"
    GENERAL = "general"
    PRECEDENT = "precedent"
    REGULATORY = "regulatory"


class CaseLaw(BaseModel):
    """Represents a case law citation and details."""

    model_config = ConfigDict(use_enum_values=True)

    case_name: str
    citation: str
    court: str
    decision_date: date | None = None
    jurisdiction: str
    summary: str
    key_holdings: list[str] = Field(default_factory=list)


class Statute(BaseModel):
    """Represents a statute citation and details."""

    model_config = ConfigDict(use_enum_values=True)

    title: str
    citation: str
    jurisdiction: str
    effective_date: date | None = None
    summary: str
    section_number: str | None = None


class ResearchQuery(BaseModel):
    """Represents a legal research query."""

    model_config = ConfigDict(use_enum_values=True)

    query_text: str
    jurisdiction: str | None = None
    query_type: QueryType = QueryType.GENERAL
    user_context: str | None = None


class ResearchResult(BaseModel):
    """Represents the result of a legal research query."""

    model_config = ConfigDict(use_enum_values=True)

    answer: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    sources: list[dict] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0)
