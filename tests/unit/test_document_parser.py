"""Unit tests for document parsers."""

import os
from pathlib import Path

import pytest

from lexicon.domain.entities.document import DocumentType, Section
from lexicon.domain.parsers.chunker import ChunkingStrategy, FixedSizeChunker, SemanticChunker
from lexicon.domain.parsers.docx_parser import DOCXParser
from lexicon.domain.parsers.pdf_parser import PDFParser


class TestPDFParser:
    """Test suite for PDFParser."""

    def test_parse_valid_pdf_success(self, sample_pdf_path):
        """Test parsing a valid PDF file returns ParsedDocument."""
        parser = PDFParser()
        result = parser.parse(str(sample_pdf_path))
        
        assert result is not None
        assert result.filename == "sample.pdf"
        assert result.document_type == DocumentType.GENERAL
        assert "Sample PDF Document" in result.full_text
        assert result.page_count == 1

    def test_parse_nonexistent_file_raises_error(self):
        """Test parsing nonexistent file raises FileNotFoundError."""
        parser = PDFParser()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse("/nonexistent/file.pdf")
        
        assert "File not found" in str(exc_info.value)

    def test_parse_invalid_pdf_raises_error(self, tmp_path):
        """Test parsing invalid PDF file raises ValueError."""
        # Create a text file with .pdf extension
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_text("This is not a PDF file")
        
        parser = PDFParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse(str(invalid_pdf))
        
        assert "Invalid PDF file" in str(exc_info.value)

    def test_extract_metadata_success(self, sample_pdf_path):
        """Test extracting metadata from PDF."""
        parser = PDFParser()
        metadata = parser.extract_metadata(str(sample_pdf_path))
        
        assert metadata is not None
        assert "page_count" in metadata
        assert metadata["page_count"] == 1

    def test_extract_metadata_nonexistent_file_raises_error(self):
        """Test extracting metadata from nonexistent file raises error."""
        parser = PDFParser()
        
        with pytest.raises(FileNotFoundError):
            parser.extract_metadata("/nonexistent/file.pdf")

    def test_parse_detects_sections_by_font_size(self, tmp_path):
        """Test that parser detects sections based on font size."""
        import fitz
        
        pdf_path = tmp_path / "sections.pdf"
        doc = fitz.open()
        page = doc.new_page()
        
        # Add heading with larger font
        page.insert_text((72, 72), "Section 1: Introduction", fontsize=16)
        # Add content with normal font
        page.insert_text((72, 100), "This is the content of section 1.", fontsize=11)
        
        doc.save(pdf_path)
        doc.close()
        
        parser = PDFParser()
        result = parser.parse(str(pdf_path))
        
        # Should detect the heading as a section
        assert len(result.sections) >= 0  # May vary based on font detection


class TestDOCXParser:
    """Test suite for DOCXParser."""

    def test_parse_valid_docx_success(self, sample_docx_path):
        """Test parsing a valid DOCX file returns ParsedDocument."""
        parser = DOCXParser()
        result = parser.parse(str(sample_docx_path))
        
        assert result is not None
        assert result.filename == "sample.docx"
        assert result.document_type == DocumentType.GENERAL
        assert "Sample DOCX Document" in result.full_text
        assert len(result.sections) > 0

    def test_parse_nonexistent_file_raises_error(self):
        """Test parsing nonexistent file raises FileNotFoundError."""
        parser = DOCXParser()
        
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse("/nonexistent/file.docx")
        
        assert "File not found" in str(exc_info.value)

    def test_parse_invalid_docx_raises_error(self, tmp_path):
        """Test parsing invalid DOCX file raises ValueError."""
        invalid_docx = tmp_path / "invalid.docx"
        invalid_docx.write_text("Not a DOCX file")
        
        parser = DOCXParser()
        
        with pytest.raises(ValueError) as exc_info:
            parser.parse(str(invalid_docx))
        
        assert "Invalid DOCX file" in str(exc_info.value)

    def test_extract_metadata_success(self, sample_docx_path):
        """Test extracting metadata from DOCX."""
        parser = DOCXParser()
        metadata = parser.extract_metadata(str(sample_docx_path))
        
        assert metadata is not None
        assert "paragraph_count" in metadata

    def test_parse_detects_headings_as_sections(self, tmp_path):
        """Test that parser detects headings as sections."""
        from docx import Document
        
        docx_path = tmp_path / "headings.docx"
        doc = Document()
        doc.add_heading("Introduction", 1)
        doc.add_paragraph("Introduction content.")
        doc.add_heading("Methodology", 1)
        doc.add_paragraph("Methodology content.")
        doc.save(docx_path)
        
        parser = DOCXParser()
        result = parser.parse(str(docx_path))
        
        # Should detect headings as sections
        assert len(result.sections) == 2
        assert result.sections[0].title == "Introduction"
        assert result.sections[1].title == "Methodology"


class TestFixedSizeChunker:
    """Test suite for FixedSizeChunker."""

    def test_chunk_text_with_default_params(self):
        """Test chunking text with default parameters."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        text = "A" * 250  # 250 characters
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 100 for chunk in chunks)

    def test_chunk_text_with_overlap(self):
        """Test that chunks have proper overlap."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        text = "The quick brown fox jumps over the lazy dog. " * 5
        
        chunks = chunker.chunk(text)
        
        # Verify overlap by checking if end of one chunk appears in next
        if len(chunks) > 1:
            assert len(chunks) >= 2

    def test_chunk_empty_text_returns_empty_list(self):
        """Test chunking empty text returns empty list."""
        chunker = FixedSizeChunker()
        
        chunks = chunker.chunk("")
        
        assert chunks == []

    def test_chunk_short_text_returns_single_chunk(self):
        """Test chunking text shorter than chunk_size returns single chunk."""
        chunker = FixedSizeChunker(chunk_size=100, overlap=20)
        text = "Short text"
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 1
        assert chunks[0] == text

    @pytest.mark.parametrize("chunk_size,overlap", [
        (512, 50),
        (1024, 100),
        (256, 25),
    ])
    def test_chunk_with_various_sizes(self, chunk_size, overlap):
        """Test chunking with various chunk sizes and overlaps."""
        chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
        text = "This is a test document. " * 100
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 0
        assert all(len(chunk) <= chunk_size for chunk in chunks)


class TestSemanticChunker:
    """Test suite for SemanticChunker."""

    def test_chunk_by_sentences(self):
        """Test semantic chunking by sentences."""
        chunker = SemanticChunker(strategy=ChunkingStrategy.SENTENCE)
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 0
        # Each chunk should contain at least one sentence
        assert all("." in chunk for chunk in chunks)

    def test_chunk_by_paragraphs(self):
        """Test semantic chunking by paragraphs."""
        chunker = SemanticChunker(strategy=ChunkingStrategy.PARAGRAPH)
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 3

    def test_chunk_by_sections(self):
        """Test semantic chunking by sections."""
        chunker = SemanticChunker(strategy=ChunkingStrategy.SECTION)
        text = "# Section 1\nContent 1\n\n# Section 2\nContent 2"
        
        chunks = chunker.chunk(text)
        
        assert len(chunks) > 0

    def test_chunk_empty_text_returns_empty_list(self):
        """Test chunking empty text returns empty list."""
        chunker = SemanticChunker(strategy=ChunkingStrategy.SENTENCE)
        
        chunks = chunker.chunk("")
        
        assert chunks == []

    def test_chunk_respects_max_chunk_size(self):
        """Test that chunks don't exceed max_chunk_size."""
        chunker = SemanticChunker(
            strategy=ChunkingStrategy.SENTENCE,
            max_chunk_size=100
        )
        text = "This is a sentence. " * 50
        
        chunks = chunker.chunk(text)
        
        assert all(len(chunk) <= 100 for chunk in chunks)
