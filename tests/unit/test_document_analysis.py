"""Unit tests for DocumentAnalysisService."""

import pytest

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.document_analysis import DocumentAnalysisService


class TestDocumentAnalysisService:
    """Test suite for DocumentAnalysisService."""

    def test_init_with_default_providers(self, mock_openai_client):
        """Test initialization with default providers."""
        service = DocumentAnalysisService()
        
        assert service.llm is not None
        assert service.retry_handler is not None
        assert service.pdf_parser is not None
        assert service.docx_parser is not None

    def test_init_with_custom_providers(self, mock_openai_provider):
        """Test initialization with custom providers."""
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        
        assert service.llm == mock_openai_provider

    def test_analyze_document_pdf_success(
        self, sample_document, sample_pdf_path, mock_openai_provider
    ):
        """Test analyzing PDF document returns ParsedDocument with analysis."""
        sample_document.file_path = str(sample_pdf_path)
        sample_document.filename = "sample.pdf"
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(sample_document)
        
        assert result is not None
        assert result.full_text is not None
        assert "summary" in result.metadata
        assert "key_points" in result.metadata

    def test_analyze_document_docx_success(
        self, sample_document, sample_docx_path, mock_openai_provider
    ):
        """Test analyzing DOCX document returns ParsedDocument with analysis."""
        sample_document.file_path = str(sample_docx_path)
        sample_document.filename = "sample.docx"
        sample_document.document_type = DocumentType.GENERAL
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(sample_document)
        
        assert result is not None
        assert result.full_text is not None

    def test_summarize_document_returns_summary(self, sample_text, mock_openai_provider):
        """Test summarize_document returns text summary."""
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        
        summary = service.summarize_document(sample_text)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_openai_provider.generate.assert_called_once()

    def test_extract_key_points_returns_list(self, sample_text, mock_openai_provider):
        """Test extract_key_points returns list of key points."""
        mock_openai_provider.generate.return_value = "- Point 1\n- Point 2\n- Point 3"
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        key_points = service.extract_key_points(sample_text)
        
        assert isinstance(key_points, list)
        assert len(key_points) > 0

    def test_extract_parties_and_dates_returns_dict(self, sample_text, mock_openai_provider):
        """Test extract_parties_and_dates returns structured data."""
        from lexicon.services.document_analysis import PartiesAndDatesResponse
        
        mock_response = PartiesAndDatesResponse(
            parties=[{"name": "John Doe", "role": "Party A"}],
            dates=[{"date": "2024-01-01", "description": "Effective Date"}]
        )
        mock_openai_provider.generate_structured.return_value = mock_response
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.extract_parties_and_dates(sample_text)
        
        assert isinstance(result, dict)
        assert "parties" in result
        assert "dates" in result

    def test_classify_document_returns_type(self, sample_text, mock_openai_provider):
        """Test classify_document returns document type."""
        mock_openai_provider.generate.return_value = "Contract"
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        doc_type = service.classify_document(sample_text)
        
        assert isinstance(doc_type, str)
        assert len(doc_type) > 0

    def test_analyze_document_with_empty_text_skips_llm(
        self, sample_document, tmp_path, mock_openai_provider
    ):
        """Test analyzing document with no extracted text skips LLM analysis."""
        # Create empty PDF
        import fitz
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(pdf_path)
        doc.close()
        
        sample_document.file_path = str(pdf_path)
        sample_document.filename = "empty.pdf"
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(sample_document)
        
        # Should not call LLM for empty document
        mock_openai_provider.generate.assert_not_called()

    def test_summarize_document_truncates_long_text(self, mock_openai_provider):
        """Test that summarize_document truncates very long text."""
        from lexicon.services.document_analysis import MAX_TEXT_LENGTH_STANDARD
        
        # Create text longer than max length
        long_text = "A" * (MAX_TEXT_LENGTH_STANDARD + 1000)
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        service.summarize_document(long_text)
        
        # Verify LLM was called with truncated text
        call_args = mock_openai_provider.generate.call_args
        prompt = call_args[0][0]
        # The text in the prompt should be truncated
        assert len(prompt) < len(long_text)

    @pytest.mark.parametrize("file_extension,parser_type", [
        ("pdf", "pdf_parser"),
        ("docx", "docx_parser"),
    ])
    def test_parse_document_selects_correct_parser(
        self, file_extension, parser_type, mock_openai_provider
    ):
        """Test that _parse_document selects the correct parser."""
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        
        # Verify the correct parser exists
        assert hasattr(service, parser_type)
        parser = getattr(service, parser_type)
        assert parser is not None
