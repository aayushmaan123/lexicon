"""Base document parser interface."""

from abc import ABC, abstractmethod
from typing import Any

from lexicon.domain.entities.document import ParsedDocument


class DocumentParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """Parse a document and return structured data.

        Args:
            file_path: Path to the document file

        Returns:
            ParsedDocument with extracted text and structure

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid or unsupported
        """
        pass

    @abstractmethod
    def extract_metadata(self, file_path: str) -> dict[str, Any]:
        """Extract metadata from a document.

        Args:
            file_path: Path to the document file

        Returns:
            Dictionary containing document metadata

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is invalid
        """
        pass
