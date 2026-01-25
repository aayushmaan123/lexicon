"""Document analysis service using LLM for intelligent document processing."""

import json
import logging
from typing import Any

from pydantic import BaseModel

from lexicon.domain.entities.document import Document, ParsedDocument
from lexicon.domain.parsers import DOCXParser, PDFParser
from lexicon.infrastructure.openai_client import OpenAIProvider
from lexicon.shared.config import settings
from lexicon.shared.prompts.document_analysis import (
    CLASSIFY_DOCUMENT_PROMPT,
    EXTRACT_KEY_POINTS_PROMPT,
    EXTRACT_PARTIES_PROMPT,
    SUMMARIZE_DOCUMENT_PROMPT,
)
from lexicon.shared.retry_handler.handler import RetryHandler

logger = logging.getLogger(__name__)


class PartiesAndDatesResponse(BaseModel):
    """Structured response model for parties and dates extraction."""

    parties: list[dict[str, str]]
    dates: list[dict[str, str]]


class DocumentAnalysisService:
    """Service for analyzing documents using LLM."""

    def __init__(
        self,
        llm_provider: OpenAIProvider | None = None,
        retry_handler: RetryHandler | None = None,
    ):
        """Initialize document analysis service.

        Args:
            llm_provider: LLM provider instance (uses GPT-4o-mini by default)
            retry_handler: Retry handler for robustness
        """
        self.llm = llm_provider or OpenAIProvider(
            model=settings.secondary_llm_model
        )
        self.retry_handler = retry_handler or RetryHandler(
            max_retries=settings.max_retries,
            backoff_factor=settings.retry_backoff_factor,
        )
        self.pdf_parser = PDFParser()
        self.docx_parser = DOCXParser()

    def analyze_document(self, document: Document) -> ParsedDocument:
        """Perform full document analysis including parsing and LLM analysis.

        Args:
            document: Document entity to analyze

        Returns:
            ParsedDocument with analysis results in metadata

        Raises:
            Exception: If parsing or analysis fails
        """
        logger.info(f"Starting analysis for document: {document.filename}")

        try:
            # Parse document based on file type
            parsed_doc = self._parse_document(document)

            # Run LLM analysis
            text = parsed_doc.full_text
            if not text or len(text.strip()) == 0:
                logger.warning(
                    f"No text extracted from {document.filename}"
                )
                return parsed_doc

            # Perform analysis
            summary = self.summarize_document(text)
            key_points = self.extract_key_points(text)
            parties_and_dates = self.extract_parties_and_dates(text)
            doc_type = self.classify_document(text)

            # Add analysis to metadata
            parsed_doc.metadata.update(
                {
                    "summary": summary,
                    "key_points": key_points,
                    "parties": parties_and_dates.get("parties", []),
                    "dates": parties_and_dates.get("dates", []),
                    "classified_type": doc_type,
                }
            )

            logger.info(
                f"Analysis completed for {document.filename}: {doc_type}"
            )
            return parsed_doc

        except Exception as e:
            logger.error(f"Failed to analyze document {document.filename}: {e}")
            raise

    def summarize_document(self, text: str) -> str:
        """Generate a concise summary of the document.

        Args:
            text: Document text to summarize

        Returns:
            Summary text

        Raises:
            Exception: If summarization fails
        """
        logger.debug("Generating document summary")

        try:
            prompt = SUMMARIZE_DOCUMENT_PROMPT.format(text=text[:8000])

            summary = self.retry_handler.execute_with_retry(
                self.llm.generate,
                prompt,
                temperature=0.3,
                max_tokens=500,
            )

            return summary.strip()

        except Exception as e:
            logger.error(f"Failed to summarize document: {e}")
            raise

    def extract_key_points(self, text: str) -> list[str]:
        """Extract key points from the document.

        Args:
            text: Document text to analyze

        Returns:
            List of key points

        Raises:
            Exception: If extraction fails
        """
        logger.debug("Extracting key points")

        try:
            prompt = EXTRACT_KEY_POINTS_PROMPT.format(text=text[:8000])

            response = self.retry_handler.execute_with_retry(
                self.llm.generate,
                prompt,
                temperature=0.3,
                max_tokens=600,
            )

            # Parse key points from response
            key_points = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if line.startswith("-") or line.startswith("•"):
                    point = line.lstrip("-•").strip()
                    if point:
                        key_points.append(point)

            return key_points

        except Exception as e:
            logger.error(f"Failed to extract key points: {e}")
            raise

    def extract_parties_and_dates(self, text: str) -> dict[str, Any]:
        """Extract parties and important dates from the document.

        Args:
            text: Document text to analyze

        Returns:
            Dictionary with 'parties' and 'dates' lists

        Raises:
            Exception: If extraction fails
        """
        logger.debug("Extracting parties and dates")

        try:
            prompt = EXTRACT_PARTIES_PROMPT.format(text=text[:8000])

            response = self.retry_handler.execute_with_retry(
                self.llm.generate,
                prompt,
                temperature=0.2,
                max_tokens=800,
            )

            # Parse JSON response
            try:
                result = json.loads(response.strip())
                return {
                    "parties": result.get("parties", []),
                    "dates": result.get("dates", []),
                }
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse JSON response, returning empty result"
                )
                return {"parties": [], "dates": []}

        except Exception as e:
            logger.error(f"Failed to extract parties and dates: {e}")
            raise

    def classify_document(self, text: str) -> str:
        """Classify the document type.

        Args:
            text: Document text to classify

        Returns:
            Document type classification (contract, case_law, or general)

        Raises:
            Exception: If classification fails
        """
        logger.debug("Classifying document type")

        try:
            prompt = CLASSIFY_DOCUMENT_PROMPT.format(text=text[:6000])

            response = self.retry_handler.execute_with_retry(
                self.llm.generate,
                prompt,
                temperature=0.1,
                max_tokens=50,
            )

            # Extract classification from response
            classification = response.strip().lower()

            # Validate classification
            valid_types = ["contract", "case_law", "general"]
            for valid_type in valid_types:
                if valid_type in classification:
                    return valid_type

            # Default to general if classification is unclear
            logger.warning(
                f"Unclear classification '{classification}', defaulting to 'general'"
            )
            return "general"

        except Exception as e:
            logger.error(f"Failed to classify document: {e}")
            raise

    def _parse_document(self, document: Document) -> ParsedDocument:
        """Parse document file to extract text and structure.

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
