"""Citation formatter for legal documents in Bluebook format."""

import logging
import re

from lexicon.domain.entities.legal_research import CaseLaw, Statute

logger = logging.getLogger(__name__)


class CitationFormatter:
    """Formats legal citations in Bluebook style."""

    def format_case_citation(self, case: CaseLaw) -> str:
        """Format case law citation in Bluebook format.

        Bluebook format for cases: Case Name, Volume Reporter Page (Court Year)
        Example: Brown v. Board of Education, 347 U.S. 483 (1954)

        Args:
            case: CaseLaw entity to format

        Returns:
            Formatted citation string
        """
        try:
            citation_parts = [case.case_name]

            # Add citation if available
            if case.citation:
                citation_parts.append(case.citation)

            # Add court and year in parentheses
            court_year = []
            if case.court:
                court_year.append(case.court)
            if case.decision_date:
                court_year.append(str(case.decision_date.year))

            if court_year:
                citation_parts.append(f"({' '.join(court_year)})")

            formatted = ", ".join(citation_parts)
            logger.debug(f"Formatted case citation: {formatted}")
            return formatted

        except Exception as e:
            logger.error(f"Failed to format case citation: {str(e)}")
            return case.case_name

    def format_statute_citation(self, statute: Statute) -> str:
        """Format statute citation in Bluebook format.

        Bluebook format for statutes: Title § Section (Year)
        Example: 42 U.S.C. § 1983 (2018)

        Args:
            statute: Statute entity to format

        Returns:
            Formatted citation string
        """
        try:
            citation_parts = []

            # Start with citation if available
            if statute.citation:
                citation_parts.append(statute.citation)
            else:
                citation_parts.append(statute.title)

            # Add section number if available
            if statute.section_number:
                if "§" not in statute.citation:
                    citation_parts.append(f"§ {statute.section_number}")

            # Add year in parentheses if available
            if statute.effective_date:
                citation_parts.append(f"({statute.effective_date.year})")

            formatted = " ".join(citation_parts)
            logger.debug(f"Formatted statute citation: {formatted}")
            return formatted

        except Exception as e:
            logger.error(f"Failed to format statute citation: {str(e)}")
            return statute.title

    def parse_citation(self, citation_text: str) -> dict:
        """Parse a citation string into components.

        Attempts to extract:
        - Case name or statute title
        - Volume and reporter (for cases)
        - Page number
        - Court
        - Year

        Args:
            citation_text: Citation string to parse

        Returns:
            Dictionary with parsed citation components
        """
        try:
            result = {
                "type": "unknown",
                "raw": citation_text,
                "case_name": None,
                "statute_title": None,
                "volume": None,
                "reporter": None,
                "page": None,
                "section": None,
                "court": None,
                "year": None,
            }

            # Try to parse as case citation
            # Pattern: Case Name, Volume Reporter Page (Court Year)
            case_pattern = r"^(.+?),\s*(\d+)\s+([A-Za-z.\s]+)\s+(\d+)\s*(?:\((.+?)\s+(\d{4})\))?$"
            case_match = re.match(case_pattern, citation_text.strip())

            if case_match:
                result["type"] = "case"
                result["case_name"] = case_match.group(1).strip()
                result["volume"] = case_match.group(2)
                result["reporter"] = case_match.group(3).strip()
                result["page"] = case_match.group(4)
                if case_match.group(5):
                    result["court"] = case_match.group(5).strip()
                if case_match.group(6):
                    result["year"] = case_match.group(6)
                return result

            # Try to parse as statute citation
            # Pattern: Title § Section (Year) or Title Code § Section (Year)
            statute_pattern = r"^(.+?)\s*§\s*(\S+)(?:\s*\((\d{4})\))?$"
            statute_match = re.match(statute_pattern, citation_text.strip())

            if statute_match:
                result["type"] = "statute"
                result["statute_title"] = statute_match.group(1).strip()
                result["section"] = statute_match.group(2)
                if statute_match.group(3):
                    result["year"] = statute_match.group(3)
                return result

            # If no pattern matches, try to extract year at least
            year_match = re.search(r"\((\d{4})\)", citation_text)
            if year_match:
                result["year"] = year_match.group(1)

            logger.debug(f"Parsed citation: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to parse citation '{citation_text}': {str(e)}")
            return {
                "type": "unknown",
                "raw": citation_text,
                "error": str(e),
            }
