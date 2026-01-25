"""Contract domain entities for the Lexicon application."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PartyType(str, Enum):
    """Type of contract party."""

    INDIVIDUAL = "individual"
    CORPORATION = "corporation"
    LLC = "llc"
    PARTNERSHIP = "partnership"
    GOVERNMENT = "government"
    OTHER = "other"


class ClauseType(str, Enum):
    """Types of contract clauses."""

    PAYMENT = "payment"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INDEMNIFICATION = "indemnification"
    LIABILITY = "liability"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    WARRANTIES = "warranties"
    FORCE_MAJEURE = "force_majeure"
    NON_COMPETE = "non_compete"
    ASSIGNMENT = "assignment"
    AMENDMENT = "amendment"
    SEVERABILITY = "severability"
    NOTICE = "notice"
    GENERAL = "general"


class RiskLevel(str, Enum):
    """Risk severity levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskCategory(str, Enum):
    """Categories of contract risks."""

    FINANCIAL = "financial"
    LEGAL = "legal"
    OPERATIONAL = "operational"
    REPUTATIONAL = "reputational"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"


class Party(BaseModel):
    """Represents a party in a contract."""

    model_config = ConfigDict(use_enum_values=True)

    name: str
    type: PartyType = PartyType.OTHER
    role: str  # e.g., "Seller", "Buyer", "Service Provider"
    contact_info: str | None = None


class Clause(BaseModel):
    """Represents a contract clause."""

    model_config = ConfigDict(use_enum_values=True)

    type: ClauseType
    title: str
    content: str
    page_number: int | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    unusual: bool = False
    obligations: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Represents a risk assessment for a contract."""

    model_config = ConfigDict(use_enum_values=True)

    severity: RiskLevel
    category: RiskCategory
    description: str
    recommendation: str


class Contract(BaseModel):
    """Main contract entity representing a complete contract analysis."""

    model_config = ConfigDict(use_enum_values=True)

    document_id: str
    contract_type: str  # e.g., "Employment Agreement", "NDA", "Service Agreement"
    parties: list[Party] = Field(default_factory=list)
    clauses: list[Clause] = Field(default_factory=list)
    effective_date: datetime | None = None
    expiration_date: datetime | None = None
    jurisdiction: str | None = None
    governing_law: str | None = None
    risks: list[RiskAssessment] = Field(default_factory=list)
    overall_assessment: str | None = None
