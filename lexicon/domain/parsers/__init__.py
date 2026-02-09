"""Document parsers package."""

from lexicon.domain.parsers.base import DocumentParser
from lexicon.domain.parsers.chunker import (
    clause_aware_chunker,
    section_based_chunker,
    sliding_window_chunker,
)
from lexicon.domain.parsers.docx_parser import DOCXParser
from lexicon.domain.parsers.pdf_parser import PDFParser

__all__ = [
    "DocumentParser",
    "PDFParser",
    "DOCXParser",
    "clause_aware_chunker",
    "section_based_chunker",
    "sliding_window_chunker",
]
