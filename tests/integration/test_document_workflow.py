"""Integration tests for document analysis workflow."""

import pytest

from lexicon.domain.entities.document import Document, DocumentType
from lexicon.services.document_analysis import DocumentAnalysisService


class TestDocumentWorkflow:
    """Integration tests for the complete document analysis workflow."""

    def test_full_document_analysis_workflow_pdf(
        self, sample_pdf_path, mock_openai_provider
    ):
        """Test complete workflow: parse PDF -> analyze -> extract insights."""
        # Create document entity
        document = Document(
            document_id="test-doc-1",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        # Run full analysis
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(document)
        
        # Verify complete workflow
        assert result is not None
        assert result.document_id == "test-doc-1"
        assert result.full_text is not None
        assert len(result.full_text) > 0
        assert "summary" in result.metadata
        assert "key_points" in result.metadata
        assert "parties" in result.metadata
        assert "dates" in result.metadata

    def test_full_document_analysis_workflow_docx(
        self, sample_docx_path, mock_openai_provider
    ):
        """Test complete workflow: parse DOCX -> analyze -> extract insights."""
        document = Document(
            document_id="test-doc-2",
            filename="sample.docx",
            file_path=str(sample_docx_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(document)
        
        assert result is not None
        assert result.document_id == "test-doc-2"
        assert len(result.sections) > 0
        assert result.metadata.get("summary") is not None

    def test_document_workflow_with_sections(
        self, tmp_path, mock_openai_provider
    ):
        """Test workflow preserves document structure with sections."""
        from docx import Document as DocxDocument
        
        # Create DOCX with multiple sections
        docx_path = tmp_path / "structured.docx"
        doc = DocxDocument()
        doc.add_heading("Section 1: Introduction", 1)
        doc.add_paragraph("Introduction content here.")
        doc.add_heading("Section 2: Analysis", 1)
        doc.add_paragraph("Analysis content here.")
        doc.save(docx_path)
        
        document = Document(
            document_id="test-structured",
            filename="structured.docx",
            file_path=str(docx_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(document)
        
        # Verify sections were detected
        assert len(result.sections) >= 2
        section_titles = [s.title for s in result.sections]
        assert "Section 1: Introduction" in section_titles
        assert "Section 2: Analysis" in section_titles

    def test_document_workflow_handles_extraction_failure(
        self, sample_pdf_path, mock_openai_provider
    ):
        """Test workflow handles LLM extraction failures gracefully."""
        # Make LLM raise exception for certain operations
        mock_openai_provider.generate.side_effect = Exception("API Error")
        
        document = Document(
            document_id="test-error",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=1024,
        )
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        
        # Should raise exception from LLM
        with pytest.raises(Exception):
            service.analyze_document(document)

    def test_document_workflow_metadata_extraction(
        self, sample_pdf_path, mock_openai_provider
    ):
        """Test that workflow extracts and preserves metadata."""
        document = Document(
            document_id="test-metadata",
            filename="sample.pdf",
            file_path=str(sample_pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=2048,
        )
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(document)
        
        # Check metadata preservation
        assert "page_count" in result.metadata
        assert result.page_count > 0

    def test_document_workflow_different_types(
        self, sample_pdf_path, mock_openai_provider
    ):
        """Test workflow with different document types."""
        document_types = [
            DocumentType.CONTRACT,
            DocumentType.CASE_LAW,
            DocumentType.STATUTE,
            DocumentType.GENERAL,
        ]
        
        for doc_type in document_types:
            document = Document(
                document_id=f"test-{doc_type.value}",
                filename="sample.pdf",
                file_path=str(sample_pdf_path),
                document_type=doc_type,
                uploaded_at=None,
                file_size=1024,
            )
            
            service = DocumentAnalysisService(llm_provider=mock_openai_provider)
            result = service.analyze_document(document)
            
            assert result is not None
            assert result.document_type == doc_type

    @pytest.mark.parametrize("file_size", [100, 1000, 10000])
    def test_document_workflow_various_sizes(
        self, tmp_path, file_size, mock_openai_provider
    ):
        """Test workflow handles documents of various sizes."""
        import fitz
        
        # Create PDF with specific content size
        pdf_path = tmp_path / f"test_{file_size}.pdf"
        doc = fitz.open()
        page = doc.new_page()
        
        # Add text to approximate size
        text = "Test content. " * (file_size // 15)
        page.insert_text((72, 72), text)
        doc.save(pdf_path)
        doc.close()
        
        document = Document(
            document_id=f"test-size-{file_size}",
            filename=f"test_{file_size}.pdf",
            file_path=str(pdf_path),
            document_type=DocumentType.GENERAL,
            uploaded_at=None,
            file_size=file_size,
        )
        
        service = DocumentAnalysisService(llm_provider=mock_openai_provider)
        result = service.analyze_document(document)
        
        assert result is not None
        assert len(result.full_text) > 0
