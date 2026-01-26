"""Integration tests for legal research workflow."""

import pytest
from datetime import datetime

from lexicon.domain.entities.legal_research import LegalQuery
from lexicon.services.legal_research import LegalResearchService


class TestResearchWorkflow:
    """Integration tests for the complete legal research workflow."""

    def test_full_research_workflow(self, sample_legal_query, mock_openai_provider):
        """Test complete research workflow from query to results."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        mock_response = LegalResearchResponse(
            query_summary="Analysis of contract formation requirements",
            relevant_cases=[
                {
                    "case_name": "Lucy v. Zehmer",
                    "citation": "196 Va. 493",
                    "summary": "Objective theory of contract formation",
                    "court": "Virginia Supreme Court",
                    "year": "1954"
                },
                {
                    "case_name": "Carlill v. Carbolic Smoke Ball Co.",
                    "citation": "[1893] 1 QB 256",
                    "summary": "Unilateral contract formation",
                    "court": "Court of Appeal",
                    "year": "1893"
                }
            ],
            relevant_statutes=[
                {
                    "title": "Uniform Commercial Code § 2-204",
                    "citation": "U.C.C. § 2-204",
                    "summary": "Formation of sales contracts",
                    "jurisdiction": "United States"
                },
                {
                    "title": "Restatement (Second) of Contracts § 17",
                    "citation": "Restatement § 17",
                    "summary": "Requirement of a bargain",
                    "jurisdiction": "United States"
                }
            ],
            analysis="A valid contract requires mutual assent (offer and acceptance), "
                    "consideration, legal capacity, and legal purpose. The objective "
                    "theory of contracts looks at outward manifestations of intent.",
            recommendations=[
                "Ensure clear offer and acceptance",
                "Document consideration",
                "Verify legal capacity of parties"
            ]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(sample_legal_query)
        
        assert result is not None
        assert "query_summary" in result
        assert "relevant_cases" in result
        assert "relevant_statutes" in result
        assert len(result["relevant_cases"]) >= 2
        assert len(result["relevant_statutes"]) >= 2
        assert len(result["analysis"]) > 0

    def test_research_workflow_jurisdiction_specific(self, mock_openai_provider):
        """Test research workflow for jurisdiction-specific queries."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        query = LegalQuery(
            query_id="query-ca",
            query_text="What are the statute of limitations for breach of contract in California?",
            jurisdiction="California",
            legal_area="Contract Law",
            created_at=datetime.now()
        )
        
        mock_response = LegalResearchResponse(
            query_summary="California statute of limitations for contract breach",
            relevant_cases=[
                {
                    "case_name": "April Enterprises v. KTTV",
                    "citation": "147 Cal.App.3d 805",
                    "summary": "Statute of limitations application",
                    "court": "California Court of Appeal",
                    "year": "1983"
                }
            ],
            relevant_statutes=[
                {
                    "title": "California Code of Civil Procedure § 337",
                    "citation": "Cal. Civ. Proc. Code § 337",
                    "summary": "4-year statute for written contracts",
                    "jurisdiction": "California"
                },
                {
                    "title": "California Code of Civil Procedure § 339",
                    "citation": "Cal. Civ. Proc. Code § 339",
                    "summary": "2-year statute for oral contracts",
                    "jurisdiction": "California"
                }
            ],
            analysis="California has different statutes of limitations for written "
                    "(4 years) and oral (2 years) contracts.",
            recommendations=["File within applicable time period"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(query)
        
        # Verify jurisdiction-specific results
        assert "California" in result["analysis"]
        assert any("California" in str(s) for s in result["relevant_statutes"])

    def test_research_workflow_finds_cases_and_statutes(
        self, sample_legal_query, mock_openai_provider
    ):
        """Test that workflow finds both cases and statutes."""
        mock_openai_provider.generate.side_effect = [
            "1. Smith v. Jones - Contract formation case\n2. Doe v. Roe - Consideration case",
            "1. U.C.C. § 2-201 - Statute of frauds\n2. U.C.C. § 2-204 - Formation"
        ]
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        
        cases = service.find_similar_cases(sample_legal_query.query_text)
        statutes = service.find_relevant_statutes(sample_legal_query.query_text)
        
        assert len(cases) >= 2
        assert len(statutes) >= 2

    def test_research_workflow_generates_legal_memo(
        self, sample_legal_query, mock_openai_provider
    ):
        """Test that workflow can generate legal memo."""
        memo_text = """
        LEGAL MEMORANDUM
        
        TO: Client
        FROM: Legal Research Team
        DATE: January 15, 2024
        RE: Contract Formation Requirements
        
        ISSUE:
        What are the requirements for a valid contract?
        
        BRIEF ANSWER:
        A valid contract requires mutual assent, consideration, capacity, and legal purpose.
        
        DISCUSSION:
        [Detailed analysis with case citations]
        
        CONCLUSION:
        The requirements are well-established in law.
        """
        mock_openai_provider.generate.return_value = memo_text
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        memo = service.generate_legal_memo(sample_legal_query)
        
        assert "LEGAL MEMORANDUM" in memo or "ISSUE" in memo.upper()
        assert len(memo) > 100

    def test_research_workflow_analyzes_legal_issue(
        self, mock_openai_provider
    ):
        """Test detailed legal issue analysis."""
        issue = "Can a contract be enforced without consideration?"
        analysis_text = """
        Generally, consideration is required for contract enforceability. However,
        there are exceptions including:
        
        1. Promissory Estoppel: Where detrimental reliance occurs (Restatement § 90)
        2. Past Consideration: In limited circumstances under UCC § 2-205
        3. Modification under Seal: In some jurisdictions
        
        Courts will examine the specific facts to determine applicability of exceptions.
        """
        mock_openai_provider.generate.return_value = analysis_text
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        analysis = service.analyze_legal_issue(issue)
        
        assert len(analysis) > 50
        assert "consideration" in analysis.lower()

    @pytest.mark.parametrize("legal_area", [
        "Contract Law",
        "Tort Law",
        "Constitutional Law",
        "Criminal Law"
    ])
    def test_research_workflow_different_legal_areas(
        self, legal_area, mock_openai_provider
    ):
        """Test research workflow across different legal areas."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        query = LegalQuery(
            query_id=f"query-{legal_area}",
            query_text=f"Question about {legal_area}",
            jurisdiction="United States",
            legal_area=legal_area,
            created_at=datetime.now()
        )
        
        mock_response = LegalResearchResponse(
            query_summary=f"Analysis of {legal_area} question",
            relevant_cases=[],
            relevant_statutes=[],
            analysis=f"Analysis specific to {legal_area}",
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(query)
        
        assert legal_area in result["analysis"]

    def test_research_workflow_complex_query(self, mock_openai_provider):
        """Test workflow with complex multi-part query."""
        from lexicon.services.legal_research import LegalResearchResponse
        
        complex_query = LegalQuery(
            query_id="complex",
            query_text="""
            What are the requirements for enforcing a non-compete agreement in California,
            and how do they differ from New York? What recent case law is relevant?
            """,
            jurisdiction="Multi-State",
            legal_area="Employment Law",
            created_at=datetime.now()
        )
        
        mock_response = LegalResearchResponse(
            query_summary="Comparative analysis of non-compete enforceability",
            relevant_cases=[
                {
                    "case_name": "Edwards v. Arthur Andersen",
                    "citation": "44 Cal.4th 937",
                    "summary": "California's strong policy against non-competes",
                    "court": "California Supreme Court",
                    "year": "2008"
                }
            ],
            relevant_statutes=[
                {
                    "title": "California Business and Professions Code § 16600",
                    "citation": "Cal. Bus. & Prof. Code § 16600",
                    "summary": "Makes non-competes void except in limited circumstances",
                    "jurisdiction": "California"
                }
            ],
            analysis="California generally prohibits non-compete agreements while "
                    "New York enforces them if reasonable in scope.",
            recommendations=["Review state-specific requirements"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = LegalResearchService(llm_provider=mock_openai_provider)
        result = service.research_query(complex_query)
        
        assert len(result["query_summary"]) > 0
        assert "California" in result["analysis"] or "New York" in result["analysis"]
