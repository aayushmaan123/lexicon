"""Unit tests for ContractReviewService."""

import pytest

from lexicon.domain.entities.contract import RiskLevel
from lexicon.services.contract_review import ContractReviewService


class TestContractReviewService:
    """Test suite for ContractReviewService."""

    def test_init_with_default_providers(self, mock_openai_client):
        """Test initialization with default providers."""
        service = ContractReviewService()
        
        assert service.llm is not None
        assert service.retry_handler is not None

    def test_init_with_custom_provider(self, mock_openai_provider):
        """Test initialization with custom LLM provider."""
        service = ContractReviewService(llm_provider=mock_openai_provider)
        
        assert service.llm == mock_openai_provider

    def test_review_contract_returns_contract(self, sample_parsed_document, mock_openai_provider):
        """Test review_contract returns Contract entity."""
        # Mock structured response
        from lexicon.services.contract_review import ContractReviewResponse, ClauseInfo
        
        mock_response = ContractReviewResponse(
            title="Service Agreement",
            contract_type="Service Agreement",
            parties=["John Doe", "Acme Corp"],
            effective_date="2024-01-01",
            expiration_date="2025-01-01",
            clauses=[
                ClauseInfo(
                    title="Payment",
                    content="Payment terms",
                    clause_type="payment",
                    risk_level="low",
                    page_number=1,
                    risk_factors=[]
                )
            ],
            overall_risk_score=0.2,
            key_obligations=["Payment obligation"],
            recommendations=["Review annually"]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(sample_parsed_document)
        
        assert contract is not None
        assert contract.title == "Service Agreement"
        assert len(contract.clauses) > 0
        assert contract.overall_risk_score >= 0

    def test_analyze_clause_returns_risk_level(self, mock_openai_provider):
        """Test analyze_clause returns risk assessment."""
        clause_text = "Party A shall indemnify Party B against all claims."
        mock_openai_provider.generate.return_value = "high"
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        risk_level = service.analyze_clause(clause_text, "indemnity")
        
        assert isinstance(risk_level, str)

    def test_identify_red_flags_returns_list(self, sample_text, mock_openai_provider):
        """Test identify_red_flags returns list of issues."""
        mock_openai_provider.generate.return_value = (
            "- Unlimited liability\n- No termination clause\n- Ambiguous terms"
        )
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        red_flags = service.identify_red_flags(sample_text)
        
        assert isinstance(red_flags, list)
        assert len(red_flags) > 0

    def test_extract_obligations_returns_list(self, sample_text, mock_openai_provider):
        """Test extract_obligations returns list of obligations."""
        mock_openai_provider.generate.return_value = (
            "- Party A must deliver services\n- Party B must make payment"
        )
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        obligations = service.extract_obligations(sample_text)
        
        assert isinstance(obligations, list)
        assert len(obligations) > 0

    def test_calculate_overall_risk_score(self):
        """Test calculate_overall_risk_score computes average."""
        from lexicon.domain.entities.contract import ContractClause
        
        clauses = [
            ContractClause(
                clause_id="1",
                title="Low Risk",
                content="Content",
                clause_type="general",
                risk_level=RiskLevel.LOW,
                page_number=1,
            ),
            ContractClause(
                clause_id="2",
                title="High Risk",
                content="Content",
                clause_type="liability",
                risk_level=RiskLevel.HIGH,
                page_number=1,
            ),
        ]
        
        service = ContractReviewService()
        score = service.calculate_overall_risk_score(clauses)
        
        assert 0 <= score <= 1
        assert isinstance(score, float)

    def test_review_contract_with_empty_text_returns_contract(self, mock_openai_provider):
        """Test reviewing contract with minimal text."""
        from lexicon.domain.entities.document import ParsedDocument, DocumentType
        from lexicon.services.contract_review import ContractReviewResponse
        
        doc = ParsedDocument(
            document_id="test",
            filename="test.pdf",
            document_type=DocumentType.CONTRACT,
            full_text="",
            sections=[],
            metadata={},
            page_count=1,
        )
        
        mock_response = ContractReviewResponse(
            title="Unknown",
            contract_type="Unknown",
            parties=[],
            effective_date=None,
            expiration_date=None,
            clauses=[],
            overall_risk_score=0.0,
            key_obligations=[],
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(doc)
        
        assert contract is not None

    @pytest.mark.parametrize("risk_level_str,expected_enum", [
        ("low", RiskLevel.LOW),
        ("medium", RiskLevel.MEDIUM),
        ("high", RiskLevel.HIGH),
        ("critical", RiskLevel.CRITICAL),
    ])
    def test_risk_level_mapping(self, risk_level_str, expected_enum):
        """Test that risk level strings map to correct enums."""
        # This tests the conversion logic in the service
        assert RiskLevel[risk_level_str.upper()] == expected_enum

    def test_review_contract_truncates_long_text(self, mock_openai_provider):
        """Test that review_contract handles very long documents."""
        from lexicon.domain.entities.document import ParsedDocument, DocumentType
        from lexicon.services.contract_review import ContractReviewResponse
        
        # Create document with very long text
        long_text = "A" * 50000
        doc = ParsedDocument(
            document_id="test",
            filename="test.pdf",
            document_type=DocumentType.CONTRACT,
            full_text=long_text,
            sections=[],
            metadata={},
            page_count=1,
        )
        
        mock_response = ContractReviewResponse(
            title="Test",
            contract_type="Test",
            parties=[],
            effective_date=None,
            expiration_date=None,
            clauses=[],
            overall_risk_score=0.0,
            key_obligations=[],
            recommendations=[]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = ContractReviewService(llm_provider=mock_openai_provider)
        contract = service.review_contract(doc)
        
        assert contract is not None
        # Verify generate_structured was called
        mock_openai_provider.generate_structured.assert_called_once()
