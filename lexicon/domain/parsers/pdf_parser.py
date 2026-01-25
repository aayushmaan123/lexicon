"""PDF document parser using PyMuPDF."""

import os
from typing import Any

import fitz  # PyMuPDF

from lexicon.domain.entities.document import DocumentType, ParsedDocument, Section
from lexicon.domain.parsers.base import DocumentParser


class PDFParser(DocumentParser):
    """PDF document parser using PyMuPDF (fitz)."""

    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a PDF document and return structured data.

        Args:
            file_path: Path to the PDF file

        Returns:
            ParsedDocument with extracted text and structure

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file is not a valid PDF
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Invalid PDF file: {e}") from e

        try:
            full_text = []
            sections = []
            current_section = None
            current_section_text = []

            for page_num in range(len(doc)):
                page = doc[page_num]

                # Extract text with layout preservation
                text = page.get_text("text")
                full_text.append(text)

                # Try to detect sections using text blocks
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" not in block:
                        continue

                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content = span["text"].strip()
                            if not text_content:
                                continue

                            # Detect headings by font size
                            font_size = span["size"]
                            is_heading = font_size > 12 and len(text_content) < 200

                            if is_heading:
                                # Save previous section
                                if current_section and current_section_text:
                                    current_section.content = "\n".join(current_section_text)
                                    sections.append(current_section)

                                # Start new section
                                current_section = Section(
                                    title=text_content,
                                    content="",
                                    page_number=page_num + 1,
                                    level=1,
                                )
                                current_section_text = []
                            elif current_section:
                                current_section_text.append(text_content)

            # Save last section
            if current_section and current_section_text:
                current_section.content = "\n".join(current_section_text)
                sections.append(current_section)

            metadata = self.extract_metadata(file_path)
            page_count = len(doc)

            doc.close()

            return ParsedDocument(
                document_id=os.path.basename(file_path),
                filename=os.path.basename(file_path),
                document_type=DocumentType.GENERAL,
                full_text="\n\n".join(full_text),
                sections=sections,
                metadata=metadata,
                page_count=page_count,
            )

        except Exception as e:
            doc.close()
            raise ValueError(f"Error parsing PDF: {e}") from e

    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file is not a valid PDF
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata or {}

            result = {
                "author": metadata.get("author", ""),
                "title": metadata.get("title", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "page_count": len(doc),
            }

            doc.close()
            return result

        except Exception as e:
            raise ValueError(f"Error extracting PDF metadata: {e}") from e
