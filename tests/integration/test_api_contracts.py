"""Integration tests for contract API endpoints."""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from lexicon.api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestContractAPI:
    """Test suite for contract API endpoints."""

    def test_review_contract_success(
        self, client, sample_pdf_path, mock_openai_client
    ):
        """Test contract review via API."""
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("contract.pdf", f, "application/pdf")}
            
            with patch("lexicon.api.routes.contracts.ContractReviewService") as mock_service:
                mock_instance = Mock()
                mock_contract = Mock()
                mock_contract.title = "Service Agreement"
                mock_contract.parties = ["Party A", "Party B"]
                mock_contract.clauses = []
                mock_contract.overall_risk_score = 0.3
                mock_contract.metadata = {"key_obligations": [], "recommendations": []}
                mock_instance.review_contract.return_value = mock_contract
                mock_service.return_value = mock_instance
                
                response = client.post("/api/v1/contracts/review", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data

    def test_review_contract_invalid_file(self, client):
        """Test that invalid file type returns 400."""
        import io
        files = {"file": ("test.txt", io.BytesIO(b"Not a contract"), "text/plain")}
        
        response = client.post("/api/v1/contracts/review", files=files)
        
        assert response.status_code == 400

    def test_analyze_clause_success(self, client, mock_openai_client):
        """Test clause analysis endpoint."""
        with patch("lexicon.api.routes.contracts.ContractReviewService") as mock_service:
            mock_instance = Mock()
            mock_instance.analyze_clause.return_value = "medium"
            mock_service.return_value = mock_instance
            
            response = client.post(
                "/api/v1/contracts/analyze-clause",
                json={
                    "clause_text": "Party A shall indemnify Party B.",
                    "clause_type": "indemnity"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "risk_level" in data

    def test_identify_red_flags_success(self, client, mock_openai_client):
        """Test red flag identification endpoint."""
        with patch("lexicon.api.routes.contracts.ContractReviewService") as mock_service:
            mock_instance = Mock()
            mock_instance.identify_red_flags.return_value = [
                "Unlimited liability",
                "No termination clause"
            ]
            mock_service.return_value = mock_instance
            
            response = client.post(
                "/api/v1/contracts/red-flags",
                json={"text": "Contract text with issues"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "red_flags" in data
        assert isinstance(data["red_flags"], list)
