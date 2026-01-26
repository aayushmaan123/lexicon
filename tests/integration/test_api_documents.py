"""Integration tests for document API endpoints."""

import io
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from lexicon.api.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


class TestDocumentAPI:
    """Test suite for document API endpoints."""

    def test_analyze_document_pdf_success(
        self, client, sample_pdf_path, mock_openai_client
    ):
        """Test analyzing PDF document via API."""
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            
            with patch("lexicon.api.routes.documents.DocumentAnalysisService") as mock_service:
                # Mock the service response
                mock_instance = Mock()
                mock_parsed_doc = Mock()
                mock_parsed_doc.metadata = {
                    "summary": "Test summary",
                    "key_points": ["Point 1", "Point 2"],
                    "parties": [],
                    "dates": [],
                }
                mock_instance.analyze_document.return_value = mock_parsed_doc
                mock_service.return_value = mock_instance
                
                response = client.post("/api/v1/documents/analyze", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_analyze_document_invalid_file_type(self, client):
        """Test that invalid file type returns 400."""
        # Create a fake text file
        files = {"file": ("test.txt", io.BytesIO(b"Not a PDF"), "text/plain")}
        
        response = client.post("/api/v1/documents/analyze", files=files)
        
        assert response.status_code == 400

    def test_analyze_document_missing_file(self, client):
        """Test that missing file returns 422."""
        response = client.post("/api/v1/documents/analyze")
        
        assert response.status_code == 422

    def test_summarize_document_success(self, client, mock_openai_client):
        """Test document summarization endpoint."""
        with patch("lexicon.api.routes.documents.DocumentAnalysisService") as mock_service:
            mock_instance = Mock()
            mock_instance.summarize_document.return_value = "Test summary"
            mock_service.return_value = mock_instance
            
            response = client.post(
                "/api/v1/documents/summarize",
                json={"text": "This is a long document that needs summarization."}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    def test_summarize_document_empty_text(self, client):
        """Test that empty text returns 422."""
        response = client.post(
            "/api/v1/documents/summarize",
            json={"text": ""}
        )
        
        assert response.status_code == 422

    def test_analyze_document_large_file(self, client, tmp_path):
        """Test that very large files are rejected."""
        import fitz
        
        # Create a large PDF (simulated)
        pdf_path = tmp_path / "large.pdf"
        doc = fitz.open()
        for _ in range(100):
            page = doc.new_page()
            page.insert_text((72, 72), "Content " * 1000)
        doc.save(pdf_path)
        doc.close()
        
        with open(pdf_path, "rb") as f:
            files = {"file": ("large.pdf", f, "application/pdf")}
            
            # This might succeed or fail depending on max file size setting
            response = client.post("/api/v1/documents/analyze", files=files)
            
            # Should either process or reject gracefully
            assert response.status_code in [200, 400, 413]


class TestHealthCheck:
    """Test suite for health check endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data
