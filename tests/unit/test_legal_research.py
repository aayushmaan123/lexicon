"""Unit tests for LegalResearchService."""

import pytest

from lexicon.services.legal_research import LegalResearchService


class TestLegalResearchService:
    """Test suite for LegalResearchService."""

    def test_init_with_default_providers(self, mock_openai_client):
        """Test initialization with default providers."""
        service = LegalResearchService()
        
        assert service.llm is not None
        assert service.retry_handler is not None

    def test_init_with_custom_provider(self, mock_openai_provider):
        """Test initialization with custom LLM provider."""
        service = LegalResearchService(llm_provider=mock_openai_provider)
        
        assert service.llm == mock_openai_provider

    def test_research_query_returns_results(self, sample_legal_query, mock_openai_provider):
        """Test research_query returns legal research results."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        mock_response = LegalResearchResponse(
            query_summary="Summary of query",
            relevant_cases=[
                {
                    "case_name": "Smith v. Jones",
                    "citation": "123 F.3d 456",
                    "summary": "Case summary"
                }
            ],
            relevant_statutes=[
                {
                    "title": "U.C.C. § 2-201",
                    "citation": "U.C.C. § 2-201",
                    "summary": "Statute of frauds"
                }
            ],
            analysis="Legal analysis",
            recommendations=["Recommendation 1"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(sample_legal_query)
        
        assert result is not None
        assert "query_summary" in result
        assert "relevant_cases" in result
        assert "relevant_statutes" in result

    def test_find_similar_cases_returns_list(self, mock_openai_provider):
        """Test find_similar_cases returns list of cases."""
        query = "breach of contract damages"
        mock_openai_provider.generate.return_value = (
            "1. Smith v. Jones - Breach of contract case\n"
            "2. Doe v. Acme - Damages calculation"
        )
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        cases = service.find_similar_cases(query)
        
        assert isinstance(cases, list)
        assert len(cases) > 0

    def test_find_relevant_statutes_returns_list(self, mock_openai_provider):
        """Test find_relevant_statutes returns list of statutes."""
        query = "contract formation requirements"
        mock_openai_provider.generate.return_value = (
            "1. U.C.C. § 2-201 - Statute of frauds\n"
            "2. Restatement (Second) of Contracts § 17"
        )
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        statutes = service.find_relevant_statutes(query)
        
        assert isinstance(statutes, list)
        assert len(statutes) > 0

    def test_analyze_legal_issue_returns_analysis(self, mock_openai_provider):
        """Test analyze_legal_issue returns detailed analysis."""
        issue = "Can a contract be enforced without consideration?"
        mock_openai_provider.generate.return_value = "Detailed legal analysis..."
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        analysis = service.analyze_legal_issue(issue)
        
        assert isinstance(analysis, str)
        assert len(analysis) > 0

    def test_generate_legal_memo_returns_memo(self, sample_legal_query, mock_openai_provider):
        """Test generate_legal_memo returns formatted memo."""
        mock_openai_provider.generate.return_value = (
            "LEGAL MEMORANDUM\n\n"
            "ISSUE: ...\n"
            "BRIEF ANSWER: ...\n"
            "ANALYSIS: ..."
        )
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        memo = service.generate_legal_memo(sample_legal_query)
        
        assert isinstance(memo, str)
        assert len(memo) > 0
        assert "LEGAL MEMORANDUM" in memo or "ISSUE" in memo.upper()

    def test_research_query_with_jurisdiction_filter(self, sample_legal_query, mock_openai_provider):
        """Test that research_query uses jurisdiction information."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        sample_legal_query.jurisdiction = "California"
        
        mock_response = LegalResearchResponse(
            query_summary="Summary",
            relevant_cases=[],
            relevant_statutes=[],
            analysis="Analysis specific to California",
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(sample_legal_query)
        
        # Verify the prompt includes jurisdiction
        call_args = mock_openai_provider.generate_structured.call_args
        prompt = call_args[0][0]
        assert "California" in prompt

    def test_research_query_with_legal_area(self, sample_legal_query, mock_openai_provider):
        """Test that research_query uses legal area information."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        sample_legal_query.legal_area = "Contract Law"
        
        mock_response = LegalResearchResponse(
            query_summary="Summary",
            relevant_cases=[],
            relevant_statutes=[],
            analysis="Contract law analysis",
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(sample_legal_query)
        
        # Verify the prompt includes legal area
        call_args = mock_openai_provider.generate_structured.call_args
        prompt = call_args[0][0]
        assert "Contract Law" in prompt

    @pytest.mark.parametrize("query_text", [
        "simple query",
        "Complex query with multiple issues and jurisdictions",
        "Query with special characters: @#$%",
    ])
    def test_research_query_handles_various_inputs(self, query_text, mock_openai_provider):
        """Test that research_query handles various query formats."""
        from lexicon.domain.entities.legal_research import ResearchQuery
        from lexicon.services.legal_research import LegalResearchResponse
        from datetime import datetime
        
        query = ResearchQuery(
            query_id="test",
            query_text=query_text,
            jurisdiction="US",
            legal_area="General",
            created_at=datetime.now()
        )
        
        mock_response = LegalResearchResponse(
            query_summary="Summary",
            relevant_cases=[],
            relevant_statutes=[],
            analysis="Analysis",
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(query)
        
        assert result is not None
