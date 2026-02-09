"""Integration tests for contract review workflow."""

import pytest

from lexicon.domain.entities.document import DocumentType, ParsedDocument, Section
from lexicon.services.contract_review import ContractReviewService


class TestContractWorkflow:
    """Integration tests for the complete contract review workflow."""

    def test_full_contract_review_workflow(
        self, sample_parsed_document, mock_openai_provider
    ):
        """Test complete contract review workflow from parsed document to contract."""
        from lexicon.services.contract_review import ContractReviewResponse, ClauseInfo
        
        # Setup parsed contract document
        contract_text = """
        SERVICE AGREEMENT
        
        This Agreement is entered into on January 1, 2024, between:
        Party A: John Doe ("Consultant")
        Party B: Acme Corporation ("Client")
        
        1. SERVICES
        Consultant shall provide consulting services as described in Exhibit A.
        
        2. PAYMENT
        Client shall pay Consultant $10,000 per month.
        Payment is due within 30 days of invoice.
        
        3. INDEMNIFICATION
        Consultant shall indemnify and hold harmless Client from all claims.
        
        4. TERMINATION
        Either party may terminate with 30 days written notice.
        """
        
        sample_parsed_document.full_text = contract_text
        sample_parsed_document.document_type = DocumentType.CONTRACT
        
        # Mock contract review response
        mock_response = ContractReviewResponse(
            title="Service Agreement",
            contract_type="Service Agreement",
            parties=["John Doe (Consultant)", "Acme Corporation (Client)"],
            effective_date="2024-01-01",
            expiration_date=None,
            clauses=[
                ClauseInfo(
                    title="Services",
                    content="Consultant shall provide consulting services",
                    clause_type="services",
                    risk_level="low",
                    page_number=1,
                    risk_factors=[]
                ),
                ClauseInfo(
                    title="Indemnification",
                    content="Consultant shall indemnify Client",
                    clause_type="indemnity",
                    risk_level="high",
                    page_number=1,
                    risk_factors=["Broad indemnification"]
                ),
            ],
            overall_risk_score=0.4,
            key_obligations=["Provide services", "Pay $10,000/month"],
            recommendations=["Review indemnification clause", "Define termination procedures"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        # Run contract review
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        # Verify complete workflow
        assert contract is not None
        assert contract.title == "Service Agreement"
        assert len(contract.parties) == 2
        assert len(contract.clauses) == 2
        assert contract.overall_risk_score > 0
        assert len(contract.metadata.get("key_obligations", [])) > 0

    def test_contract_workflow_identifies_high_risk_clauses(
        self, sample_parsed_document, mock_openai_provider
    ):
        """Test that workflow identifies and flags high-risk clauses."""
        from lexicon.services.contract_review import ContractReviewResponse, ClauseInfo
        from lexicon.domain.entities.contract import RiskLevel
        
        sample_parsed_document.document_type = DocumentType.CONTRACT
        
        mock_response = ContractReviewResponse(
            title="High Risk Contract",
            contract_type="Service Agreement",
            parties=["Party A", "Party B"],
            effective_date="2024-01-01",
            expiration_date=None,
            clauses=[
                ClauseInfo(
                    title="Unlimited Liability",
                    content="Party A assumes unlimited liability",
                    clause_type="liability",
                    risk_level="critical",
                    page_number=1,
                    risk_factors=["Unlimited liability", "No caps", "Broad scope"]
                ),
            ],
            overall_risk_score=0.9,
            key_obligations=["Accept unlimited liability"],
            recommendations=["Negotiate liability cap", "Add insurance requirement"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        # Find high-risk clauses
        high_risk_clauses = [
            c for c in contract.clauses 
            if c.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        ]
        
        assert len(high_risk_clauses) > 0
        assert contract.overall_risk_score > 0.5

    def test_contract_workflow_extracts_obligations(
        self, sample_parsed_document, mock_openai_provider
    ):
        """Test that workflow extracts key obligations."""
        from lexicon.services.contract_review import ContractReviewResponse
        
        sample_parsed_document.document_type = DocumentType.CONTRACT
        
        mock_response = ContractReviewResponse(
            title="Contract",
            contract_type="Service Agreement",
            parties=["Party A", "Party B"],
            effective_date="2024-01-01",
            expiration_date=None,
            clauses=[],
            overall_risk_score=0.2,
            key_obligations=[
                "Deliver services by specified deadlines",
                "Maintain confidentiality of information",
                "Pay invoices within 30 days"
            ],
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        obligations = contract.metadata.get("key_obligations", [])
        assert len(obligations) >= 3
        assert any("services" in o.lower() for o in obligations)
        assert any("confidentiality" in o.lower() for o in obligations)

    def test_contract_workflow_generates_recommendations(
        self, sample_parsed_document, mock_openai_provider
    ):
        """Test that workflow generates actionable recommendations."""
        from lexicon.services.contract_review import ContractReviewResponse
        
        sample_parsed_document.document_type = DocumentType.CONTRACT
        
        mock_response = ContractReviewResponse(
            title="Contract",
            contract_type="Service Agreement",
            parties=["Party A", "Party B"],
            effective_date="2024-01-01",
            expiration_date=None,
            clauses=[],
            overall_risk_score=0.5,
            key_obligations=[],
            recommendations=[
                "Add a dispute resolution clause",
                "Clarify intellectual property ownership",
                "Include force majeure provisions"
            ]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        recommendations = contract.metadata.get("recommendations", [])
        assert len(recommendations) >= 3

    def test_contract_workflow_handles_complex_structure(
        self, mock_openai_provider
    ):
        """Test workflow with complex multi-section contract."""
        from lexicon.services.contract_review import ContractReviewResponse, ClauseInfo
        
        # Create complex contract document
        complex_doc = ParsedDocument(
            document_id="complex-contract",
            filename="complex.pdf",
            document_type=DocumentType.CONTRACT,
            full_text="Complex contract with many sections...",
            sections=[
                Section(title="Definitions", content="Terms defined...", page_number=1, level=1),
                Section(title="Scope of Work", content="Services described...", page_number=2, level=1),
                Section(title="Payment Terms", content="Payment schedule...", page_number=3, level=1),
                Section(title="Warranties", content="Warranties provided...", page_number=4, level=1),
                Section(title="Indemnification", content="Indemnity terms...", page_number=5, level=1),
            ],
            metadata={},
            page_count=5,
        )
        
        mock_response = ContractReviewResponse(
            title="Complex Contract",
            contract_type="Master Services Agreement",
            parties=["Party A", "Party B"],
            effective_date="2024-01-01",
            expiration_date="2025-01-01",
            clauses=[
                ClauseInfo(
                    title="Scope of Work",
                    content="Services",
                    clause_type="services",
                    risk_level="low",
                    page_number=2,
                    risk_factors=[]
                ),
                ClauseInfo(
                    title="Payment Terms",
                    content="Payment",
                    clause_type="payment",
                    risk_level="medium",
                    page_number=3,
                    risk_factors=["Late payment penalties"]
                ),
            ],
            overall_risk_score=0.35,
            key_obligations=["Deliver services", "Make timely payments"],
            recommendations=["Review payment terms"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(complex_doc)
        
        # Verify complex structure is processed
        assert contract is not None
        assert len(contract.clauses) >= 2
        assert contract.expiration_date is not None

    @pytest.mark.parametrize("risk_score,expected_severity", [
        (0.1, "low"),
        (0.4, "medium"),
        (0.7, "high"),
        (0.95, "critical"),
    ])
    def test_contract_workflow_risk_assessment(
        self, risk_score, expected_severity, sample_parsed_document, mock_openai_provider
    ):
        """Test that workflow correctly assesses risk levels."""
        from lexicon.services.contract_review import ContractReviewResponse
        
        sample_parsed_document.document_type = DocumentType.CONTRACT
        
        mock_response = ContractReviewResponse(
            title="Contract",
            contract_type="Agreement",
            parties=["Party A", "Party B"],
            effective_date="2024-01-01",
            expiration_date=None,
            clauses=[],
            overall_risk_score=risk_score,
            key_obligations=[],
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        assert contract.overall_risk_score == pytest.approx(risk_score, abs=0.01)
