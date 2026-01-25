"""Contract review service using LLM for intelligent contract analysis."""

import json
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

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
from lexicon.domain.entities.document import Document
from lexicon.domain.parsers import DOCXParser, PDFParser
from lexicon.infrastructure.openai_client import OpenAIProvider
from lexicon.shared.config import settings
from lexicon.shared.prompts.contract_review import (
    ANALYZE_RISK_PROMPT,
    DETECT_UNUSUAL_CLAUSES_PROMPT,
    EXTRACT_CLAUSES_PROMPT,
    EXTRACT_CONTRACT_METADATA_PROMPT,
    EXTRACT_OBLIGATIONS_PROMPT,
)
from lexicon.shared.retry_handler.handler import RetryHandler

logger = logging.getLogger(__name__)

# Text length limits for different analysis types
MAX_TEXT_LENGTH_FULL = 15000  # For full contract analysis
MAX_TEXT_LENGTH_CLAUSE = 10000  # For clause extraction
MAX_TEXT_LENGTH_METADATA = 8000  # For metadata extraction


class ClausesResponse(BaseModel):
    """Structured response model for clause extraction."""

    clauses: list[dict[str, Any]]


class RisksResponse(BaseModel):
    """Structured response model for risk analysis."""

    risks: list[dict[str, Any]]


class ObligationsResponse(BaseModel):
    """Structured response model for obligations extraction."""

    obligations: list[dict[str, Any]]


class UnusualClausesResponse(BaseModel):
    """Structured response model for unusual clause detection."""

    evaluations: list[dict[str, Any]]


class ContractMetadataResponse(BaseModel):
    """Structured response model for contract metadata extraction."""

    contract_type: str
    parties: list[dict[str, Any]]
    effective_date: str | None
    expiration_date: str | None
    jurisdiction: str | None
    governing_law: str | None
    overall_assessment: str


class ContractReviewService:
    """Service for comprehensive contract review and analysis."""

    def __init__(
        self,
        llm_provider: OpenAIProvider | None = None,
        retry_handler: RetryHandler | None = None,
    ):
        """Initialize contract review service.

        Args:
            llm_provider: LLM provider instance (uses GPT-4o by default for complex analysis)
            retry_handler: Retry handler for robustness
        """
        self.llm = llm_provider or OpenAIProvider(
            model=settings.primary_llm_model
        )
        self.retry_handler = retry_handler or RetryHandler(
            max_retries=settings.max_retries,
            backoff_factor=settings.retry_backoff_factor,
        )
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()

    def review_contract(self, document: Document) -> Contract:
        """Perform comprehensive contract review.

        Args:
            document: Document entity to review

        Returns:
            Contract entity with complete analysis

        Raises:
            Exception: If review fails
        """
        logger.info(f"Starting contract review for: {document.filename}")

        try:
            # Parse document
            parsed_doc = self._parse_document(document)
            text = parsed_doc.full_text

            if not text or len(text.strip()) == 0:
                logger.warning(f"No text extracted from {document.filename}")
                raise ValueError("Document contains no extractable text")

            # Extract metadata
            logger.info("Extracting contract metadata")
            metadata = self._extract_metadata(text)

            # Extract clauses
            logger.info("Extracting contract clauses")
            clauses = self.extract_clauses(text)

            # Detect unusual clauses
            logger.info("Detecting unusual clauses")
            clauses = self.detect_unusual_clauses(clauses)

            # Analyze risks
            logger.info("Analyzing contract risks")
            contract_obj = Contract(
                document_id=document.id or parsed_doc.document_id,
                contract_type=metadata["contract_type"],
                parties=metadata["parties"],
                clauses=clauses,
                effective_date=metadata["effective_date"],
                expiration_date=metadata["expiration_date"],
                jurisdiction=metadata["jurisdiction"],
                governing_law=metadata["governing_law"],
                overall_assessment=metadata["overall_assessment"],
            )
            risks = self.analyze_risks(contract_obj)
            contract_obj.risks = risks

            logger.info(
                f"Contract review completed for {document.filename}: "
                f"{len(clauses)} clauses, {len(risks)} risks identified"
            )
            return contract_obj

        except Exception as e:
            logger.error(
                f"Failed to review contract {document.filename}: {e}"
            )
            raise

    def extract_clauses(self, text: str) -> list[Clause]:
        """Extract clauses from contract text using GPT-4o with structured output.

        Args:
            text: Contract text to analyze

        Returns:
            List of extracted clauses

        Raises:
            Exception: If extraction fails
        """
        logger.debug("Extracting clauses with structured output")

        try:
            prompt = EXTRACT_CLAUSES_PROMPT.format(
                text=text[:MAX_TEXT_LENGTH_CLAUSE]
            )

            response = self.retry_handler.execute_with_retry(
                self.llm.generate_structured,
                prompt,
                response_model=ClausesResponse,
                temperature=0.2,
            )

            # Convert response to Clause objects
            clauses = []
            for clause_data in response.clauses:
                try:
                    # Validate and convert clause type
                    clause_type = clause_data.get("type", "general")
                    if clause_type not in [ct.value for ct in ClauseType]:
                        clause_type = "general"

                    clause = Clause(
                        type=ClauseType(clause_type),
                        title=clause_data.get("title", "Untitled Clause"),
                        content=clause_data.get("content", ""),
                        page_number=clause_data.get("page_number"),
                        obligations=clause_data.get("obligations", []),
                    )
                    clauses.append(clause)
                except Exception as e:
                    logger.warning(f"Failed to parse clause: {e}")
                    continue

            logger.info(f"Extracted {len(clauses)} clauses")
            return clauses

        except Exception as e:
            logger.error(f"Failed to extract clauses: {e}")
            raise

    def analyze_risks(self, contract: Contract) -> list[RiskAssessment]:
        """Analyze contract risks using GPT-4o.

        Args:
            contract: Contract entity to analyze

        Returns:
            List of risk assessments

        Raises:
            Exception: If analysis fails
        """
        logger.debug("Analyzing contract risks")

        try:
            # Prepare contract summary for analysis
            contract_text = self._prepare_contract_for_risk_analysis(contract)

            prompt = ANALYZE_RISK_PROMPT.format(
                text=contract_text[:MAX_TEXT_LENGTH_FULL]
            )

            response = self.retry_handler.execute_with_retry(
                self.llm.generate_structured,
                prompt,
                response_model=RisksResponse,
                temperature=0.3,
            )

            # Convert response to RiskAssessment objects
            risks = []
            for risk_data in response.risks:
                try:
                    # Validate and convert enums
                    severity = risk_data.get("severity", "low")
                    if severity not in [rl.value for rl in RiskLevel]:
                        severity = "low"

                    category = risk_data.get("category", "legal")
                    if category not in [rc.value for rc in RiskCategory]:
                        category = "legal"

                    risk = RiskAssessment(
                        severity=RiskLevel(severity),
                        category=RiskCategory(category),
                        description=risk_data.get("description", ""),
                        recommendation=risk_data.get("recommendation", ""),
                    )
                    risks.append(risk)
                except Exception as e:
                    logger.warning(f"Failed to parse risk: {e}")
                    continue

            logger.info(f"Identified {len(risks)} risks")
            return risks

        except Exception as e:
            logger.error(f"Failed to analyze risks: {e}")
            raise

    def extract_obligations(self, text: str) -> list[dict]:
        """Extract obligations from contract text.

        Args:
            text: Contract text to analyze

        Returns:
            List of obligation dictionaries

        Raises:
            Exception: If extraction fails
        """
        logger.debug("Extracting contract obligations")

        try:
            prompt = EXTRACT_OBLIGATIONS_PROMPT.format(
                text=text[:MAX_TEXT_LENGTH_FULL]
            )

            response = self.retry_handler.execute_with_retry(
                self.llm.generate_structured,
                prompt,
                response_model=ObligationsResponse,
                temperature=0.2,
            )

            logger.info(f"Extracted {len(response.obligations)} obligations")
            return response.obligations

        except Exception as e:
            logger.error(f"Failed to extract obligations: {e}")
            raise

    def detect_unusual_clauses(self, clauses: list[Clause]) -> list[Clause]:
        """Detect and mark unusual or non-standard clauses.

        Args:
            clauses: List of clauses to evaluate

        Returns:
            Updated list of clauses with unusual flags set

        Raises:
            Exception: If detection fails
        """
        logger.debug(f"Detecting unusual clauses among {len(clauses)} clauses")

        if not clauses:
            return clauses

        try:
            # Prepare clauses for evaluation
            clauses_json = json.dumps(
                [
                    {
                        "index": i,
                        "type": clause.type,
                        "title": clause.title,
                        "content": clause.content[:500],  # Truncate long content
                    }
                    for i, clause in enumerate(clauses)
                ]
            )

            prompt = DETECT_UNUSUAL_CLAUSES_PROMPT.format(
                clauses_json=clauses_json
            )

            response = self.retry_handler.execute_with_retry(
                self.llm.generate_structured,
                prompt,
                response_model=UnusualClausesResponse,
                temperature=0.3,
            )

            # Update clauses based on evaluations
            unusual_count = 0
            for evaluation in response.evaluations:
                idx = evaluation.get("clause_index")
                if idx is not None and 0 <= idx < len(clauses):
                    if evaluation.get("unusual", False):
                        clauses[idx].unusual = True
                        unusual_count += 1
                        logger.debug(
                            f"Clause {idx} marked as unusual: "
                            f"{evaluation.get('reason', 'No reason provided')}"
                        )

            logger.info(f"Marked {unusual_count} unusual clauses")
            return clauses

        except Exception as e:
            logger.warning(f"Failed to detect unusual clauses: {e}")
            # Return clauses as-is if detection fails
            return clauses

    def _extract_metadata(self, text: str) -> dict[str, Any]:
        """Extract contract metadata using GPT-4o.

        Args:
            text: Contract text to analyze

        Returns:
            Dictionary with contract metadata

        Raises:
            Exception: If extraction fails
        """
        logger.debug("Extracting contract metadata")

        try:
            prompt = EXTRACT_CONTRACT_METADATA_PROMPT.format(
                text=text[:MAX_TEXT_LENGTH_METADATA]
            )

            response = self.retry_handler.execute_with_retry(
                self.llm.generate_structured,
                prompt,
                response_model=ContractMetadataResponse,
                temperature=0.2,
            )

            # Convert parties to Party objects
            parties = []
            for party_data in response.parties:
                try:
                    party_type = party_data.get("type", "other")
                    if party_type not in [pt.value for pt in PartyType]:
                        party_type = "other"

                    party = Party(
                        name=party_data.get("name", "Unknown"),
                        type=PartyType(party_type),
                        role=party_data.get("role", "Unknown"),
                        contact_info=party_data.get("contact_info"),
                    )
                    parties.append(party)
                except Exception as e:
                    logger.warning(f"Failed to parse party: {e}")
                    continue

            # Parse dates
            effective_date = self._parse_date(response.effective_date)
            expiration_date = self._parse_date(response.expiration_date)

            return {
                "contract_type": response.contract_type,
                "parties": parties,
                "effective_date": effective_date,
                "expiration_date": expiration_date,
                "jurisdiction": response.jurisdiction,
                "governing_law": response.governing_law,
                "overall_assessment": response.overall_assessment,
            }

        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise

    def _parse_document(self, document: Document):
        """Parse document file to extract text.

        Args:
            document: Document entity

        Returns:
            ParsedDocument with extracted content

        Raises:
            ValueError: If file format is unsupported
        """
        file_path = document.file_path
        filename_lower = document.filename.lower()

        if filename_lower.endswith(".pdf"):
            return self.pdf_parser.parse(file_path)
        elif filename_lower.endswith((".docx", ".doc")):
            return self.docx_parser.parse(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {document.filename}"
            )

    def _prepare_contract_for_risk_analysis(self, contract: Contract) -> str:
        """Prepare contract summary for risk analysis.

        Args:
            contract: Contract entity

        Returns:
            Formatted text for risk analysis
        """
        parts = [
            f"Contract Type: {contract.contract_type}",
            f"Parties: {', '.join(p.name + ' (' + p.role + ')' for p in contract.parties)}",
        ]

        if contract.governing_law:
            parts.append(f"Governing Law: {contract.governing_law}")

        if contract.jurisdiction:
            parts.append(f"Jurisdiction: {contract.jurisdiction}")

        parts.append("\nKey Clauses:")
        for clause in contract.clauses:
            parts.append(f"\n{clause.title} ({clause.type}):")
            parts.append(clause.content[:500])  # Truncate long clauses

        return "\n".join(parts)

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Parse date string to datetime object.

        Args:
            date_str: Date string in YYYY-MM-DD format or None

        Returns:
            datetime object or None
        """
        if not date_str or date_str == "null":
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            logger.warning(f"Failed to parse date: {date_str}")
            return None
