"""Domain entities package."""

from lexicon.domain.entities.contract import (
    Clause,
    ClauseType,
    Contract,
    Party,
    PartyType,
    RiskAssessment,
    RiskCategory,
    RiskLevel,
)
from lexicon.domain.entities.document import (
    Document,
    DocumentChunk,
    DocumentStatus,
    DocumentType,
    ParsedDocument,
    Section,
)
from lexicon.domain.entities.legal_research import (
    CaseLaw,
    QueryType,
    ResearchQuery,
    ResearchResult,
    Statute,
)

__all__ = [
    "CaseLaw",
    "Clause",
    "ClauseType",
    "Contract",
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "DocumentType",
    "ParsedDocument",
    "Party",
    "PartyType",
    "QueryType",
    "ResearchQuery",
    "ResearchResult",
    "RiskAssessment",
    "RiskCategory",
    "RiskLevel",
    "Section",
    "Statute",
]
