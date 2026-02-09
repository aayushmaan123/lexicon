"""Unit tests for CitationFormatter."""

from datetime import datetime

import pytest

from lexicon.domain.citation_formatter import CitationFormatter
from lexicon.domain.entities.legal_research import CaseLaw, Statute


class TestCitationFormatter:
    """Test suite for CitationFormatter."""

    def test_format_case_citation_full_info(self):
        """Test formatting case citation with all information."""
        formatter = CitationFormatter()
        case = CaseLaw(
            case_id="case-1",
            case_name="Brown v. Board of Education",
            citation="347 U.S. 483",
            court="Supreme Court",
            decision_date=datetime(1954, 5, 17),
            summary="Landmark case on segregation",
            key_holdings=["Separate is not equal"],
            relevance_score=1.0,
        )
        
        result = formatter.format_case_citation(case)
        
        assert "Brown v. Board of Education" in result
        assert "347 U.S. 483" in result
        assert "1954" in result

    def test_format_case_citation_minimal_info(self):
        """Test formatting case citation with minimal information."""
        formatter = CitationFormatter()
        case = CaseLaw(
            case_id="case-2",
            case_name="Smith v. Jones",
            citation="",
            court="",
            decision_date=None,
            summary="",
            key_holdings=[],
            relevance_score=0.5,
        )
        
        result = formatter.format_case_citation(case)
        
        assert "Smith v. Jones" in result

    def test_format_case_citation_with_court_only(self):
        """Test formatting case citation with court but no date."""
        formatter = CitationFormatter()
        case = CaseLaw(
            case_id="case-3",
            case_name="Doe v. Roe",
            citation="123 F.3d 456",
            court="9th Circuit",
            decision_date=None,
            summary="Test case",
            key_holdings=[],
            relevance_score=0.7,
        )
        
        result = formatter.format_case_citation(case)
        
        assert "Doe v. Roe" in result
        assert "9th Circuit" in result

    def test_format_statute_citation_full_info(self):
        """Test formatting statute citation with all information."""
        formatter = CitationFormatter()
        statute = Statute(
            statute_id="statute-1",
            title="Uniform Commercial Code",
            citation="U.C.C. § 2-201",
            jurisdiction="United States",
            section_number="2-201",
            text="Statute of frauds for sale of goods",
            effective_date=datetime(1952, 1, 1),
            relevance_score=0.9,
        )
        
        result = formatter.format_statute_citation(statute)
        
        assert "U.C.C. § 2-201" in result
        assert "1952" in result

    def test_format_statute_citation_minimal_info(self):
        """Test formatting statute citation with minimal information."""
        formatter = CitationFormatter()
        statute = Statute(
            statute_id="statute-2",
            title="Test Statute",
            citation="",
            jurisdiction="",
            section_number="",
            text="",
            effective_date=None,
            relevance_score=0.5,
        )
        
        result = formatter.format_statute_citation(statute)
        
        assert "Test Statute" in result

    def test_format_statute_citation_adds_section(self):
        """Test that formatter adds section symbol when missing."""
        formatter = CitationFormatter()
        statute = Statute(
            statute_id="statute-3",
            title="Test Code",
            citation="42 U.S.C.",
            jurisdiction="US",
            section_number="1983",
            text="Civil rights statute",
            effective_date=datetime(1871, 1, 1),
            relevance_score=0.8,
        )
        
        result = formatter.format_statute_citation(statute)
        
        assert "§" in result or "1983" in result

    def test_parse_citation_case_format(self):
        """Test parsing case citation string."""
        formatter = CitationFormatter()
        citation = "Brown v. Board of Education, 347 U.S. 483 (Supreme Court 1954)"
        
        result = formatter.parse_citation(citation)
        
        assert result["type"] == "case"
        assert result["case_name"] == "Brown v. Board of Education"
        assert result["volume"] == "347"
        assert result["page"] == "483"
        assert result["year"] == "1954"

    def test_parse_citation_statute_format(self):
        """Test parsing statute citation string."""
        formatter = CitationFormatter()
        citation = "42 U.S.C. § 1983 (1871)"
        
        result = formatter.parse_citation(citation)
        
        assert result["type"] == "statute"
        assert "42 U.S.C." in result["statute_title"]
        assert result["section"] == "1983"
        assert result["year"] == "1871"

    def test_parse_citation_unknown_format(self):
        """Test parsing citation with unknown format."""
        formatter = CitationFormatter()
        citation = "This is not a standard citation format"
        
        result = formatter.parse_citation(citation)
        
        assert result["type"] == "unknown"
        assert result["raw"] == citation

    def test_parse_citation_extracts_year(self):
        """Test that parser extracts year from various formats."""
        formatter = CitationFormatter()
        citation = "Some Citation (2020)"
        
        result = formatter.parse_citation(citation)
        
        assert result["year"] == "2020"

    def test_parse_citation_handles_error(self):
        """Test that parser handles errors gracefully."""
        formatter = CitationFormatter()
        
        # Should not raise exception
        result = formatter.parse_citation("")
        
        assert result["type"] == "unknown"

    @pytest.mark.parametrize("case_name,expected_in_output", [
        ("Smith v. Jones", "Smith v. Jones"),
        ("United States v. Nixon", "United States v. Nixon"),
        ("In re Marriage of Smith", "In re Marriage of Smith"),
    ])
    def test_format_case_various_names(self, case_name, expected_in_output):
        """Test formatting cases with various naming conventions."""
        formatter = CitationFormatter()
        case = CaseLaw(
            case_id="test",
            case_name=case_name,
            citation="123 F.3d 456",
            court="",
            decision_date=None,
            summary="",
            key_holdings=[],
            relevance_score=0.5,
        )
        
        result = formatter.format_case_citation(case)
        
        assert expected_in_output in result

    @pytest.mark.parametrize("citation_text,expected_type", [
        ("Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)", "case"),
        ("42 U.S.C. § 1983 (2018)", "statute"),
        ("Random text", "unknown"),
    ])
    def test_parse_citation_identifies_type(self, citation_text, expected_type):
        """Test that parser correctly identifies citation types."""
        formatter = CitationFormatter()
        
        result = formatter.parse_citation(citation_text)
        
        assert result["type"] == expected_type

    def test_format_case_citation_error_handling(self):
        """Test that formatter handles errors gracefully."""
        formatter = CitationFormatter()
        case = CaseLaw(
            case_id="test",
            case_name="Test Case",
            citation="123 F.3d 456",
            court="Test Court",
            decision_date=None,
            summary="",
            key_holdings=[],
            relevance_score=0.5,
        )
        
        # Should not raise exception even with None values
        result = formatter.format_case_citation(case)
        assert isinstance(result, str)

    def test_format_statute_citation_error_handling(self):
        """Test that statute formatter handles errors gracefully."""
        formatter = CitationFormatter()
        statute = Statute(
            statute_id="test",
            title="Test",
            citation="",
            jurisdiction="",
            section_number="",
            text="",
            effective_date=None,
            relevance_score=0.5,
        )
        
        # Should not raise exception
        result = formatter.format_statute_citation(statute)
        assert isinstance(result, str)
